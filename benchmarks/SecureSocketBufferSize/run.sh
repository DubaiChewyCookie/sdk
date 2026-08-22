#!/usr/bin/env bash

set -euo pipefail

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
readonly BENCHMARK_COMMAND="${1:-quick}"
readonly PYTHON_BIN="${PYTHON:-python3}"

if (( $# > 0 )); then
  shift
fi

exec "$PYTHON_BIN" "$SCRIPT_DIR/benchmark.py" "$BENCHMARK_COMMAND" "$@"
