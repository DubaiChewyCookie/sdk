package main

import (
	"bytes"
	"context"
	"crypto/tls"
	"crypto/x509"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"sort"
	"sync"
	"time"
)

type options struct {
	mode, protocol, cert, key, ca, barrier      string
	port, payload, warmupMS, durationMS, window int
	tls                                         bool
}

func main() {
	var o options
	flag.StringVar(&o.mode, "mode", "", "server or client")
	flag.StringVar(&o.protocol, "protocol", "", "io or http")
	flag.StringVar(&o.cert, "cert", "", "certificate path")
	flag.StringVar(&o.key, "key", "", "private key path")
	flag.StringVar(&o.ca, "ca", "", "CA certificate path")
	flag.StringVar(&o.barrier, "barrier", "", "measurement barrier path")
	flag.IntVar(&o.port, "port", 0, "listen port")
	flag.IntVar(&o.payload, "payload", 0, "payload bytes")
	flag.IntVar(&o.warmupMS, "warmup-ms", 0, "warmup milliseconds")
	flag.IntVar(&o.durationMS, "duration-ms", 0, "measurement milliseconds")
	flag.IntVar(&o.window, "window", 1, "outstanding operations")
	flag.BoolVar(&o.tls, "tls", false, "enable TLS")
	_ = flag.Int("buffer-size", 8*1024, "accepted for runner symmetry")
	flag.Parse()
	var err error
	if o.mode == "server" {
		err = serve(o)
	} else {
		err = client(o)
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func emit(value any) {
	if err := json.NewEncoder(os.Stdout).Encode(value); err != nil {
		panic(err)
	}
}

func serve(o options) error {
	payload := make([]byte, o.payload)
	listener, err := net.Listen("tcp4", fmt.Sprintf("127.0.0.1:%d", o.port))
	if err != nil {
		return err
	}
	if o.protocol == "io" {
		if o.tls {
			config, err := serverTLS(o)
			if err != nil {
				return err
			}
			listener = tls.NewListener(listener, config)
		}
		go func() {
			for {
				conn, err := listener.Accept()
				if err != nil {
					return
				}
				if tcp, ok := conn.(*net.TCPConn); ok {
					_ = tcp.SetNoDelay(true)
				}
				go func() { _, _ = io.Copy(conn, conn); _ = conn.Close() }()
			}
		}()
	} else if o.protocol == "http" {
		if o.tls {
			config, err := serverTLS(o)
			if err != nil {
				return err
			}
			listener = tls.NewListener(listener, config)
		}
		server := &http.Server{Handler: http.HandlerFunc(func(response http.ResponseWriter, request *http.Request) {
			_, _ = io.Copy(io.Discard, request.Body)
			_ = request.Body.Close()
			response.Header().Set("Content-Type", "application/octet-stream")
			response.Header().Set("Content-Length", fmt.Sprint(len(payload)))
			_, _ = response.Write(payload)
		})}
		go func() { _ = server.Serve(listener) }()
	} else {
		return fmt.Errorf("unknown protocol %q", o.protocol)
	}
	emit(map[string]any{"event": "ready", "port": o.port})
	select {}
}

func serverTLS(o options) (*tls.Config, error) {
	certificate, err := tls.LoadX509KeyPair(o.cert, o.key)
	if err != nil {
		return nil, err
	}
	return &tls.Config{Certificates: []tls.Certificate{certificate}, MinVersion: tls.VersionTLS12}, nil
}

func clientTLS(o options) (*tls.Config, error) {
	contents, err := os.ReadFile(o.ca)
	if err != nil {
		return nil, err
	}
	roots := x509.NewCertPool()
	if !roots.AppendCertsFromPEM(contents) {
		return nil, errors.New("could not parse CA")
	}
	return &tls.Config{RootCAs: roots, ServerName: "localhost", MinVersion: tls.VersionTLS12}, nil
}

type responseEvent struct{ err error }

type measurements struct {
	Event          string  `json:"event,omitempty"`
	Completed      int64   `json:"completed"`
	ElapsedSeconds float64 `json:"elapsed_seconds"`
	QPS            float64 `json:"qps"`
	LatencyMeanNS  int64   `json:"latency_mean_ns"`
	LatencyP50NS   int64   `json:"latency_p50_ns"`
	LatencyP95NS   int64   `json:"latency_p95_ns"`
	LatencyP99NS   int64   `json:"latency_p99_ns"`
	Errors         int64   `json:"errors"`
}

func summarize(completed int64, duration time.Duration, latencies []int64, errorCount int64) measurements {
	sort.Slice(latencies, func(i, j int) bool { return latencies[i] < latencies[j] })
	percentile := func(p float64) int64 {
		if len(latencies) == 0 {
			return 0
		}
		return latencies[int(float64(len(latencies)-1)*p+0.5)]
	}
	var total int64
	for _, latency := range latencies {
		total += latency
	}
	var mean int64
	if len(latencies) != 0 {
		mean = total / int64(len(latencies))
	}
	seconds := duration.Seconds()
	return measurements{
		Completed: completed, ElapsedSeconds: seconds, QPS: float64(completed) / seconds,
		LatencyMeanNS: mean, LatencyP50NS: percentile(.50), LatencyP95NS: percentile(.95),
		LatencyP99NS: percentile(.99), Errors: errorCount,
	}
}

func runStreaming(send func() error, responses <-chan responseEvent, duration time.Duration, window int, record bool) (measurements, error) {
	startedAt := time.Now()
	deadline := startedAt.Add(duration)
	started := make([]int64, 0, window*2)
	head, outstanding := 0, 0
	for i := 0; i < window; i++ {
		started = append(started, nowNS())
		outstanding++
		if err := send(); err != nil {
			return measurements{}, err
		}
	}
	latencies := make([]int64, 0, 8192)
	var completed int64
	for outstanding > 0 {
		event := <-responses
		if event.err != nil {
			return measurements{}, event.err
		}
		now := time.Now()
		operationStarted := started[head]
		head++
		outstanding--
		if now.Before(deadline) {
			if record {
				completed++
				latencies = append(latencies, nowNS()-operationStarted)
			}
			started = append(started, nowNS())
			outstanding++
			if err := send(); err != nil {
				return measurements{}, err
			}
		}
	}
	return summarize(completed, duration, latencies, 0), nil
}

func waitBarrier(path string) {
	emit(map[string]any{"event": "measurement_ready"})
	for {
		if _, err := os.Stat(path); err == nil {
			return
		}
		time.Sleep(2 * time.Millisecond)
	}
}

func runHTTP(request func() error, duration time.Duration, concurrency int, record bool) measurements {
	startedAt := time.Now()
	deadline := startedAt.Add(duration)
	latencies := make([]int64, 0, 8192)
	var lock sync.Mutex
	var completed, errorCount int64
	var workers sync.WaitGroup
	for i := 0; i < concurrency; i++ {
		workers.Add(1)
		go func() {
			defer workers.Done()
			for time.Now().Before(deadline) {
				started := nowNS()
				if err := request(); err != nil {
					lock.Lock()
					errorCount++
					lock.Unlock()
				} else if record && time.Now().Before(deadline) {
					latency := nowNS() - started
					lock.Lock()
					completed++
					latencies = append(latencies, latency)
					lock.Unlock()
				}
			}
		}()
	}
	workers.Wait()
	return summarize(completed, duration, latencies, errorCount)
}

func client(o options) error {
	payload := make([]byte, o.payload)
	warmup := time.Duration(o.warmupMS) * time.Millisecond
	duration := time.Duration(o.durationMS) * time.Millisecond
	var result measurements
	if o.protocol == "io" {
		var conn net.Conn
		var err error
		if o.tls {
			config, configErr := clientTLS(o)
			if configErr != nil {
				return configErr
			}
			conn, err = tls.Dial("tcp4", fmt.Sprintf("localhost:%d", o.port), config)
		} else {
			conn, err = net.Dial("tcp4", fmt.Sprintf("127.0.0.1:%d", o.port))
		}
		if err != nil {
			return err
		}
		defer conn.Close()
		responses := make(chan responseEvent, o.window*2)
		go func() {
			buffer := make([]byte, o.payload)
			for {
				_, err := io.ReadFull(conn, buffer)
				responses <- responseEvent{err: err}
				if err != nil {
					return
				}
			}
		}()
		send := func() error {
			written := 0
			for written < len(payload) {
				n, err := conn.Write(payload[written:])
				if err != nil {
					return err
				}
				written += n
			}
			return nil
		}
		if _, err := runStreaming(send, responses, warmup, o.window, false); err != nil {
			return err
		}
		waitBarrier(o.barrier)
		result, err = runStreaming(send, responses, duration, o.window, true)
		if err != nil {
			return err
		}
	} else if o.protocol == "http" {
		transport := &http.Transport{
			MaxIdleConns: o.window, MaxIdleConnsPerHost: o.window, MaxConnsPerHost: o.window,
			IdleConnTimeout: time.Minute,
			// Keep this path HTTP/1.1 like Dart HttpClient and Node's http/https modules.
			TLSNextProto: map[string]func(string, *tls.Conn) http.RoundTripper{},
		}
		scheme := "http"
		if o.tls {
			config, err := clientTLS(o)
			if err != nil {
				return err
			}
			transport.TLSClientConfig = config
			scheme = "https"
		}
		httpClient := &http.Client{Transport: transport}
		request := func() error {
			req, err := http.NewRequestWithContext(context.Background(), http.MethodPost,
				fmt.Sprintf("%s://localhost:%d/echo", scheme, o.port), bytes.NewReader(payload))
			if err != nil {
				return err
			}
			response, err := httpClient.Do(req)
			if err != nil {
				return err
			}
			received, copyErr := io.Copy(io.Discard, response.Body)
			_ = response.Body.Close()
			if copyErr != nil {
				return copyErr
			}
			if response.StatusCode != http.StatusOK || received != int64(o.payload) {
				return fmt.Errorf("bad HTTP response: %d, %d", response.StatusCode, received)
			}
			return nil
		}
		_ = runHTTP(request, warmup, o.window, false)
		waitBarrier(o.barrier)
		result = runHTTP(request, duration, o.window, true)
		transport.CloseIdleConnections()
	} else {
		return fmt.Errorf("unknown protocol %q", o.protocol)
	}
	result.Event = "result"
	emit(result)
	for {
		if _, err := os.Stat(o.barrier + ".ack"); err == nil {
			break
		}
		time.Sleep(2 * time.Millisecond)
	}
	return nil
}
