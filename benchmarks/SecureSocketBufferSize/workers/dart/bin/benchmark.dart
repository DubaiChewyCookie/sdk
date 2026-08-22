import 'dart:async';
import 'dart:collection';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

Future<void> main(List<String> arguments) async {
  final args = _Args(arguments);
  if (args.string('mode') == 'server') {
    await _serve(args);
  } else {
    await _client(args);
  }
}

Future<void> _serve(_Args args) async {
  final protocol = args.string('protocol');
  final payloadBytes = args.integer('payload');
  final payload = Uint8List(payloadBytes);
  final port = args.integer('port');
  final tls = args.boolean('tls');
  final bufferSize = args.integer('buffer-size', 8 * 1024);
  if (protocol == 'io') {
    final Stream<Socket> server;
    if (tls) {
      server = await SecureServerSocket.bind(
        InternetAddress.loopbackIPv4,
        port,
        _serverContext(args, bufferSize),
      );
    } else {
      server = await ServerSocket.bind(InternetAddress.loopbackIPv4, port);
    }
    server.listen((socket) {
      socket.setOption(SocketOption.tcpNoDelay, true);
      socket.listen(
        socket.add,
        onDone: socket.destroy,
        onError: (_) => socket.destroy(),
      );
    });
  } else if (protocol == 'http') {
    final HttpServer server;
    if (tls) {
      server = await HttpServer.bindSecure(
        InternetAddress.loopbackIPv4,
        port,
        _serverContext(args, bufferSize),
      );
    } else {
      server = await HttpServer.bind(InternetAddress.loopbackIPv4, port);
    }
    server.listen((request) async {
      await request.drain<void>();
      request.response.contentLength = payload.length;
      request.response.add(payload);
      await request.response.close();
    });
  } else {
    throw ArgumentError.value(protocol, 'protocol');
  }
  stdout.writeln(jsonEncode({'event': 'ready', 'port': port}));
  await stdout.flush();
  await Completer<void>().future;
}

Future<void> _client(_Args args) async {
  final protocol = args.string('protocol');
  final payloadBytes = args.integer('payload');
  final tls = args.boolean('tls');
  final bufferSize = args.integer('buffer-size', 8 * 1024);
  final warmup = Duration(milliseconds: args.integer('warmup-ms'));
  final duration = Duration(milliseconds: args.integer('duration-ms'));
  final window = args.integer('window');
  final barrier = File(args.string('barrier'));
  final payload = Uint8List(payloadBytes);
  late final _Measurements measurements;

  if (protocol == 'io') {
    final Socket socket;
    if (tls) {
      socket = await SecureSocket.connect(
        'localhost',
        args.integer('port'),
        context: _clientContext(args, bufferSize),
      );
    } else {
      socket = await Socket.connect(
        InternetAddress.loopbackIPv4,
        args.integer('port'),
      );
    }
    socket.setOption(SocketOption.tcpNoDelay, true);
    final responses = StreamController<void>();
    var received = 0;
    socket.listen(
      (bytes) {
        received += bytes.length;
        while (received >= payloadBytes) {
          received -= payloadBytes;
          responses.add(null);
        }
      },
      onError: responses.addError,
      onDone: responses.close,
    );
    final session = _StreamingSession(
      send: () => socket.add(payload),
      responses: responses.stream,
      window: window,
    );
    await session.run(warmup, record: false);
    await _barrier(barrier);
    measurements = await session.run(duration, record: true);
    socket.destroy();
  } else if (protocol == 'http') {
    final context = tls ? _clientContext(args, bufferSize) : null;
    final client = HttpClient(context: context)
      ..maxConnectionsPerHost = window
      ..idleTimeout = const Duration(minutes: 1);
    final scheme = tls ? 'https' : 'http';
    final uri = Uri.parse('$scheme://localhost:${args.integer('port')}/echo');
    Future<void> request() async {
      final req = await client.postUrl(uri);
      req.contentLength = payload.length;
      req.add(payload);
      final response = await req.close();
      var received = 0;
      await for (final bytes in response) {
        received += bytes.length;
      }
      if (response.statusCode != HttpStatus.ok || received != payloadBytes) {
        throw StateError(
          'bad HTTP response: ${response.statusCode}, $received',
        );
      }
    }

    await _runHttpPhase(request, warmup, window, record: false);
    await _barrier(barrier);
    measurements = await _runHttpPhase(request, duration, window, record: true);
    client.close(force: true);
  } else {
    throw ArgumentError.value(protocol, 'protocol');
  }

  stdout.writeln(jsonEncode({'event': 'result', ...measurements.toJson()}));
  await stdout.flush();
  await _resultAck(barrier);
}

Future<void> _barrier(File file) async {
  stdout.writeln(jsonEncode({'event': 'measurement_ready'}));
  await stdout.flush();
  while (!file.existsSync()) {
    await Future<void>.delayed(const Duration(milliseconds: 2));
  }
}

Future<void> _resultAck(File barrier) async {
  final ack = File('${barrier.path}.ack');
  while (!ack.existsSync()) {
    await Future<void>.delayed(const Duration(milliseconds: 2));
  }
}

Future<_Measurements> _runHttpPhase(
  Future<void> Function() request,
  Duration duration,
  int concurrency, {
  required bool record,
}) async {
  final watch = Stopwatch()..start();
  final latencies = <int>[];
  var completed = 0;
  var errors = 0;
  Future<void> worker() async {
    while (watch.elapsed < duration) {
      final started = watch.elapsedMicroseconds;
      try {
        await request();
        if (record && watch.elapsed <= duration) {
          completed++;
          latencies.add((watch.elapsedMicroseconds - started) * 1000);
        }
      } catch (_) {
        errors++;
      }
    }
  }

  await Future.wait([for (var i = 0; i < concurrency; i++) worker()]);
  watch.stop();
  return _Measurements(
    completed,
    duration.inMicroseconds / 1e6,
    latencies,
    errors,
  );
}

final class _StreamingSession {
  _StreamingSession({
    required this.send,
    required this.responses,
    required this.window,
  }) {
    responses.listen(_onResponse, onError: _onError);
  }

  final void Function() send;
  final Stream<void> responses;
  final int window;
  _StreamingPhase? _phase;

  Future<_Measurements> run(Duration duration, {required bool record}) async {
    final phase = _StreamingPhase(duration, record);
    _phase = phase;
    for (var i = 0; i < window; i++) {
      _issue(phase);
    }
    Timer(duration, () {
      phase.expired = true;
      if (phase.outstanding == 0 && !phase.done.isCompleted) {
        phase.done.complete();
      }
    });
    await phase.done.future.timeout(duration + const Duration(seconds: 30));
    _phase = null;
    return _Measurements(
      phase.completed,
      duration.inMicroseconds / 1e6,
      phase.latencies,
      phase.errors,
    );
  }

  void _issue(_StreamingPhase phase) {
    phase.outstanding++;
    phase.started.add(phase.watch.elapsedMicroseconds);
    send();
  }

  void _onResponse(void _) {
    final phase = _phase;
    if (phase == null || phase.outstanding == 0) return;
    final started = phase.started.removeFirst();
    phase.outstanding--;
    if (!phase.expired && phase.watch.elapsed < phase.duration) {
      if (phase.record) {
        phase.completed++;
        phase.latencies.add((phase.watch.elapsedMicroseconds - started) * 1000);
      }
      _issue(phase);
    } else {
      phase.expired = true;
      if (phase.outstanding == 0 && !phase.done.isCompleted) {
        phase.done.complete();
      }
    }
  }

  void _onError(Object error, StackTrace stack) {
    final phase = _phase;
    if (phase != null) {
      phase.errors++;
      if (!phase.done.isCompleted) phase.done.completeError(error, stack);
    }
  }
}

final class _StreamingPhase {
  _StreamingPhase(this.duration, this.record);
  final Duration duration;
  final bool record;
  final watch = Stopwatch()..start();
  final started = ListQueue<int>();
  final latencies = <int>[];
  final done = Completer<void>();
  int outstanding = 0;
  int completed = 0;
  int errors = 0;
  bool expired = false;
}

final class _Measurements {
  _Measurements(
    this.completed,
    this.elapsedSeconds,
    this.latenciesNs,
    this.errors,
  );
  final int completed;
  final double elapsedSeconds;
  final List<int> latenciesNs;
  final int errors;

  Map<String, Object> toJson() {
    latenciesNs.sort();
    int percentile(double p) => latenciesNs.isEmpty
        ? 0
        : latenciesNs[((latenciesNs.length - 1) * p).round()];
    final mean = latenciesNs.isEmpty
        ? 0
        : latenciesNs.reduce((a, b) => a + b) ~/ latenciesNs.length;
    return {
      'completed': completed,
      'elapsed_seconds': elapsedSeconds,
      'qps': completed / elapsedSeconds,
      'latency_mean_ns': mean,
      'latency_p50_ns': percentile(.50),
      'latency_p95_ns': percentile(.95),
      'latency_p99_ns': percentile(.99),
      'errors': errors,
    };
  }
}

SecurityContext _serverContext(_Args args, int bufferSize) => SecurityContext()
  ..secureSocketBufferSize = bufferSize
  ..useCertificateChain(args.string('cert'))
  ..usePrivateKey(args.string('key'));

SecurityContext _clientContext(_Args args, int bufferSize) => SecurityContext()
  ..secureSocketBufferSize = bufferSize
  ..setTrustedCertificates(args.string('ca'));

final class _Args {
  _Args(List<String> args) {
    for (final arg in args) {
      if (!arg.startsWith('--') || !arg.contains('=')) continue;
      final split = arg.indexOf('=');
      values[arg.substring(2, split)] = arg.substring(split + 1);
    }
  }
  final values = <String, String>{};
  String string(String name, [String? fallback]) =>
      values[name] ?? fallback ?? (throw ArgumentError('missing --$name'));
  int integer(String name, [int? fallback]) =>
      int.parse(string(name, '$fallback'));
  bool boolean(String name, [bool? fallback]) =>
      string(name, '$fallback').toLowerCase() == 'true';
}
