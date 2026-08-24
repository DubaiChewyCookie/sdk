// Copyright (c) 2026, the Dart project authors.  Please see the AUTHORS file
// for details. All rights reserved. Use of this source code is governed by a
// BSD-style license that can be found in the LICENSE file.
//
// VMOptions=
// VMOptions=--short_socket_read
// VMOptions=--short_socket_write
// VMOptions=--short_socket_read --short_socket_write
// OtherResources=certificates/server_chain.pem
// OtherResources=certificates/server_key.pem
// OtherResources=certificates/trusted_certs.pem

import "dart:async";
import "dart:io";
import "dart:typed_data";

import "package:expect/expect.dart";

String localFile(String path) => Platform.script.resolve(path).toFilePath();

final SecurityContext serverContext = SecurityContext()
  ..useCertificateChain(localFile('certificates/server_chain.pem'))
  ..usePrivateKey(
    localFile('certificates/server_key.pem'),
    password: 'dartdart',
  );

final SecurityContext clientContext = SecurityContext()
  ..setTrustedCertificates(localFile('certificates/trusted_certs.pem'));

Uint8List makePayload(int length) {
  final result = Uint8List(length);
  for (var i = 0; i < result.length; i++) {
    result[i] = (i * 31 + i ~/ 251) & 0xff;
  }
  return result;
}

int checksum(List<int> data) {
  var result = 0;
  for (final byte in data) {
    result = (result + byte) & 0x7fffffff;
  }
  return result;
}

class DelegatingRawSocket extends Stream<RawSocketEvent> implements RawSocket {
  final RawSocket socket;

  DelegatingRawSocket(this.socket);

  bool get readEventsEnabled => socket.readEventsEnabled;
  set readEventsEnabled(bool value) => socket.readEventsEnabled = value;

  bool get writeEventsEnabled => socket.writeEventsEnabled;
  set writeEventsEnabled(bool value) => socket.writeEventsEnabled = value;

  int available() => socket.available();
  Uint8List? read([int? len]) => socket.read(len);
  SocketMessage? readMessage([int? count]) => socket.readMessage(count);
  int write(List<int> buffer, [int offset = 0, int? count]) =>
      socket.write(buffer, offset, count);
  int sendMessage(
    List<SocketControlMessage> controlMessages,
    List<int> data, [
    int offset = 0,
    int? count,
  ]) => socket.sendMessage(controlMessages, data, offset, count);

  int get port => socket.port;
  int get remotePort => socket.remotePort;
  InternetAddress get address => socket.address;
  InternetAddress get remoteAddress => socket.remoteAddress;

  Future<RawSocket> close() async {
    await socket.close();
    return this;
  }

  void shutdown(SocketDirection direction) => socket.shutdown(direction);
  bool setOption(SocketOption option, bool enabled) =>
      socket.setOption(option, enabled);
  Uint8List getRawOption(RawSocketOption option) => socket.getRawOption(option);
  void setRawOption(RawSocketOption option) => socket.setRawOption(option);

  StreamSubscription<RawSocketEvent> listen(
    void Function(RawSocketEvent)? onData, {
    Function? onError,
    void Function()? onDone,
    bool? cancelOnError,
  }) => socket.listen(
    onData,
    onError: onError,
    onDone: onDone,
    cancelOnError: cancelOnError,
  );
}

class SynchronousErrorRawSocket extends DelegatingRawSocket {
  Function? _onError;
  bool _errorSent = false;

  SynchronousErrorRawSocket(super.socket);

  void _sendSynchronousError() {
    if (_errorSent) return;
    _errorSent = true;
    final handler = _onError;
    if (handler != null) {
      Function.apply(handler, [
        const SocketException('Synchronous transport failure'),
        StackTrace.current,
      ]);
    }
  }

  @override
  Uint8List? read([int? len]) {
    _sendSynchronousError();
    return null;
  }

  @override
  int write(List<int> buffer, [int offset = 0, int? count]) {
    _sendSynchronousError();
    return 0;
  }

  @override
  StreamSubscription<RawSocketEvent> listen(
    void Function(RawSocketEvent)? onData, {
    Function? onError,
    void Function()? onDone,
    bool? cancelOnError,
  }) {
    _onError = onError;
    return super.listen(
      onData,
      onError: onError,
      onDone: onDone,
      cancelOnError: cancelOnError,
    );
  }
}

Future<(int, int)> consume(Stream<List<int>> stream) async {
  var length = 0;
  var sum = 0;
  await for (final data in stream) {
    length += data.length;
    sum = (sum + checksum(data)) & 0x7fffffff;
  }
  return (length, sum);
}

Future<ServerSocket> bindServer() =>
    ServerSocket.bind(InternetAddress.loopbackIPv4, 0);

Future<void> testSlowReceiverBackpressure(Uint8List payload) async {
  final received = Completer<(int, int)>();
  final serverDone = Completer<void>();
  final server = await bindServer();
  final serverSubscription = server.listen((socket) async {
    try {
      final secureSocket = await SecureSocket.secureServer(
        socket,
        serverContext,
        bufferedData: const [],
      );
      // Let the sender fill its bounded plaintext queue before consuming.
      await Future<void>.delayed(const Duration(milliseconds: 20));
      received.complete(await consume(secureSocket));
      await secureSocket.close();
      serverDone.complete();
    } catch (error, stackTrace) {
      if (!received.isCompleted) {
        received.completeError(error, stackTrace);
      }
      if (!serverDone.isCompleted) {
        serverDone.completeError(error, stackTrace);
      }
    }
  });

  final client = await SecureSocket.connect(
    InternetAddress.loopbackIPv4,
    server.port,
    context: clientContext,
  );
  client.add(payload);
  await client.flush();
  await client.close();

  final result = await received.future;
  client.destroy();
  Expect.equals(payload.length, result.$1);
  Expect.equals(checksum(payload), result.$2);
  await serverDone.future;
  await server.close();
  await serverSubscription.cancel();
}

Future<void> testPublicRawSocketImplementation(Uint8List payload) async {
  final server = await bindServer();
  final serverConnection = server.first;
  final secureServerConnection = serverConnection.then(
    (socket) => SecureSocket.secureServer(
      socket,
      serverContext,
      bufferedData: const [],
    ),
  );
  final rawClient = await RawSocket.connect(
    InternetAddress.loopbackIPv4,
    server.port,
  );
  final client = await RawSecureSocket.secure(
    DelegatingRawSocket(rawClient),
    context: clientContext,
  );
  final serverClient = await secureServerConnection;

  final received = BytesBuilder(copy: false);
  final readClosed = Completer<void>();
  final clientSubscription = client.listen((event) {
    if (event == RawSocketEvent.read) {
      while (true) {
        final data = client.read();
        if (data == null) break;
        received.add(data);
      }
    } else if (event == RawSocketEvent.readClosed) {
      if (!readClosed.isCompleted) readClosed.complete();
    }
  });

  serverClient.add(payload);
  await serverClient.flush();
  await serverClient.close();
  serverClient.destroy();
  await readClosed.future;

  final result = received.takeBytes();
  Expect.equals(payload.length, result.length);
  Expect.equals(checksum(payload), checksum(result));

  await client.close();
  await clientSubscription.cancel();
  await server.close();
}

Future<void> testUpgradeAfterNativeReadClosed() async {
  final server = await bindServer();
  final serverClosed = server.first.then((socket) => socket.close());
  final rawClient = await RawSocket.connect(
    InternetAddress.loopbackIPv4,
    server.port,
  );
  final readClosed = Completer<void>();
  final subscription = rawClient.listen((event) {
    if (event == RawSocketEvent.readClosed && !readClosed.isCompleted) {
      readClosed.complete();
    }
  });
  await readClosed.future;

  Object? handshakeError;
  try {
    await RawSecureSocket.secure(
      rawClient,
      subscription: subscription,
      context: clientContext,
    );
  } catch (error) {
    handshakeError = error;
  }
  Expect.isTrue(handshakeError is HandshakeException);

  await rawClient.close();
  await subscription.cancel();
  final closedServerClient = await serverClosed;
  closedServerClient.destroy();
  await server.close();
}

Future<void> testSynchronousFallbackTransportError() async {
  final server = await bindServer();
  final serverConnection = server.first;
  final rawClient = await RawSocket.connect(
    InternetAddress.loopbackIPv4,
    server.port,
  );
  final serverClient = await serverConnection;

  Object? handshakeError;
  try {
    await RawSecureSocket.secure(
      SynchronousErrorRawSocket(rawClient),
      context: clientContext,
    );
  } catch (error) {
    handshakeError = error;
  }
  Expect.isTrue(handshakeError is SocketException);

  await rawClient.close();
  await serverClient.close();
  serverClient.destroy();
  await server.close();
}

Future<void> main() async {
  // This is hundreds of times larger than the default 8 KiB plaintext rings
  // and exercises repeated wraparound without an encrypted staging ring.
  final payload = makePayload(2 * 1024 * 1024 + 257);
  await testSlowReceiverBackpressure(payload);
  await testPublicRawSocketImplementation(payload.sublist(0, 64 * 1024 + 17));
  await testUpgradeAfterNativeReadClosed();
  await testSynchronousFallbackTransportError();
}
