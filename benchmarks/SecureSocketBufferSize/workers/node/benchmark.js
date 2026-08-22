'use strict';

const fs = require('fs');
const {EventEmitter} = require('events');
const http = require('http');
const https = require('https');
const net = require('net');
const tls = require('tls');

const args = Object.fromEntries(process.argv.slice(2).filter(x => x.startsWith('--')).map(x => {
  const at = x.indexOf('=');
  return [x.slice(2, at), x.slice(at + 1)];
}));
const integer = (name, fallback) => Number(args[name] ?? fallback);
const boolean = name => args[name] === 'true';
const payload = Buffer.alloc(integer('payload'));

function json(value) {
  process.stdout.write(`${JSON.stringify(value)}\n`);
}

async function serve() {
  const protocol = args.protocol;
  const port = integer('port');
  const secure = boolean('tls');
  if (protocol === 'io') {
    const onConnection = socket => {
      socket.setNoDelay(true);
      socket.pipe(socket);
    };
    const server = secure
      ? tls.createServer({cert: fs.readFileSync(args.cert), key: fs.readFileSync(args.key)}, onConnection)
      : net.createServer(onConnection);
    await new Promise((resolve, reject) => server.once('error', reject).listen(port, '127.0.0.1', resolve));
  } else if (protocol === 'http') {
    const handler = (request, response) => {
      request.on('data', () => {});
      request.on('end', () => {
        response.writeHead(200, {'content-length': payload.length, 'content-type': 'application/octet-stream'});
        response.end(payload);
      });
      request.on('error', () => response.destroy());
    };
    const server = secure
      ? https.createServer({cert: fs.readFileSync(args.cert), key: fs.readFileSync(args.key)}, handler)
      : http.createServer(handler);
    server.keepAliveTimeout = 60_000;
    server.headersTimeout = 65_000;
    server.requestTimeout = 0;
    await new Promise((resolve, reject) => server.once('error', reject).listen(port, '127.0.0.1', resolve));
  } else {
    throw new Error(`unknown protocol ${protocol}`);
  }
  json({event: 'ready', port});
  await new Promise(() => {});
}

function summarize(completed, elapsedSeconds, latencies, errors) {
  latencies.sort((a, b) => a - b);
  const percentile = p => latencies.length ? latencies[Math.round((latencies.length - 1) * p)] : 0;
  const mean = latencies.length ? Math.round(latencies.reduce((a, b) => a + b, 0) / latencies.length) : 0;
  return {
    completed,
    elapsed_seconds: elapsedSeconds,
    qps: completed / elapsedSeconds,
    latency_mean_ns: mean,
    latency_p50_ns: percentile(.50),
    latency_p95_ns: percentile(.95),
    latency_p99_ns: percentile(.99),
    errors,
  };
}

class StreamingSession {
  constructor(send, emitter, window) {
    this.send = send;
    this.window = window;
    this.phase = null;
    emitter.on('data', () => this.onResponse());
    emitter.on('error', error => this.onError(error));
  }

  run(durationMs, record) {
    return new Promise((resolve, reject) => {
      const phase = {
        startedAt: process.hrtime.bigint(),
        durationNs: BigInt(durationMs) * 1000000n,
        elapsedSeconds: durationMs / 1000,
        started: [],
        head: 0,
        outstanding: 0,
        completed: 0,
        latencies: [],
        errors: 0,
        record,
        expired: false,
        resolve,
        reject,
      };
      this.phase = phase;
      for (let i = 0; i < this.window; i++) this.issue(phase);
      setTimeout(() => {
        phase.expired = true;
        if (phase.outstanding === 0) this.finish(phase);
      }, durationMs);
    });
  }

  issue(phase) {
    phase.outstanding++;
    phase.started.push(process.hrtime.bigint());
    this.send();
  }

  onResponse() {
    const phase = this.phase;
    if (!phase || phase.outstanding === 0) return;
    const now = process.hrtime.bigint();
    const started = phase.started[phase.head++];
    phase.outstanding--;
    if (!phase.expired && now - phase.startedAt < phase.durationNs) {
      if (phase.record) {
        phase.completed++;
        phase.latencies.push(Number(now - started));
      }
      this.issue(phase);
    } else {
      phase.expired = true;
      if (phase.outstanding === 0) this.finish(phase);
    }
  }

  finish(phase) {
    if (this.phase !== phase) return;
    this.phase = null;
    phase.resolve(summarize(phase.completed, phase.elapsedSeconds, phase.latencies, phase.errors));
  }

  onError(error) {
    if (!this.phase) return;
    this.phase.errors++;
    this.phase.reject(error);
    this.phase = null;
  }
}

async function barrier() {
  json({event: 'measurement_ready'});
  while (!fs.existsSync(args.barrier)) {
    await new Promise(resolve => setTimeout(resolve, 2));
  }
}

async function runHttpPhase(request, durationMs, concurrency, record) {
  const startedAt = process.hrtime.bigint();
  const durationNs = BigInt(durationMs) * 1000000n;
  const latencies = [];
  let completed = 0;
  let errors = 0;
  const errorDetails = [];
  async function worker() {
    while (process.hrtime.bigint() - startedAt < durationNs) {
      const started = process.hrtime.bigint();
      try {
        await request();
        const now = process.hrtime.bigint();
        if (record && now - startedAt <= durationNs) {
          completed++;
          latencies.push(Number(now - started));
        }
      } catch (error) {
        errors++;
        if (errorDetails.length < 5) errorDetails.push(error.stack || String(error));
      }
    }
  }
  await Promise.all(Array.from({length: concurrency}, worker));
  return {...summarize(completed, durationMs / 1000, latencies, errors), error_details: errorDetails};
}

async function client() {
  const protocol = args.protocol;
  const secure = boolean('tls');
  const warmupMs = integer('warmup-ms');
  const durationMs = integer('duration-ms');
  const window = integer('window');
  const port = integer('port');
  let result;
  if (protocol === 'io') {
    const socket = secure
      ? tls.connect({host: 'localhost', port, ca: fs.readFileSync(args.ca), servername: 'localhost'})
      : net.connect({host: '127.0.0.1', port});
    await new Promise((resolve, reject) => {
      socket.once(secure ? 'secureConnect' : 'connect', resolve);
      socket.once('error', reject);
    });
    socket.setNoDelay(true);
    const responses = new EventEmitter();
    let received = 0;
    socket.on('data', bytes => {
      received += bytes.length;
      while (received >= payload.length) {
        received -= payload.length;
        responses.emit('data');
      }
    });
    socket.on('error', error => responses.emit('error', error));
    const session = new StreamingSession(() => socket.write(payload), responses, window);
    await session.run(warmupMs, false);
    await barrier();
    result = await session.run(durationMs, true);
    socket.destroy();
  } else if (protocol === 'http') {
    const transport = secure ? https : http;
    const agent = secure
      ? new https.Agent({keepAlive: true, maxSockets: window, ca: fs.readFileSync(args.ca)})
      : new http.Agent({keepAlive: true, maxSockets: window});
    const request = () => new Promise((resolve, reject) => {
      const req = transport.request({
        host: '127.0.0.1', port, path: '/echo', method: 'POST', agent,
        headers: {'content-length': payload.length},
      }, response => {
        let received = 0;
        response.on('data', bytes => received += bytes.length);
        response.on('end', () => response.statusCode === 200 && received === payload.length
          ? resolve()
          : reject(new Error(`bad HTTP response ${response.statusCode}, ${received}`)));
      });
      req.on('error', reject);
      req.end(payload);
    });
    await runHttpPhase(request, warmupMs, window, false);
    await barrier();
    result = await runHttpPhase(request, durationMs, window, true);
    agent.destroy();
  } else {
    throw new Error(`unknown protocol ${protocol}`);
  }
  json({event: 'result', ...result});
  while (!fs.existsSync(`${args.barrier}.ack`)) {
    await new Promise(resolve => setTimeout(resolve, 2));
  }
}

(args.mode === 'server' ? serve() : client()).catch(error => {
  process.stderr.write(`${error.stack || error}\n`);
  process.exitCode = 1;
});
