#!/bin/sh
set -eu
id="$1"
root=/host-cgroup
path=""
for candidate in \
  "$root/system.slice/docker-$id.scope" \
  "$root/docker/$id" \
  "$root/docker-$id.scope"; do
  if [ -d "$candidate" ]; then path="$candidate"; break; fi
done
if [ -z "$path" ]; then
  short=$(printf '%s' "$id" | cut -c1-12)
  path=$(find "$root" -type d -name "*$short*" 2>/dev/null | head -n 1 || true)
fi
if [ -z "$path" ]; then echo "cgroup not found for $id" >&2; exit 2; fi

if [ -r "$path/memory.current" ]; then
  usage_usec=$(awk '$1=="usage_usec" {print $2}' "$path/cpu.stat")
  user_usec=$(awk '$1=="user_usec" {print $2}' "$path/cpu.stat")
  system_usec=$(awk '$1=="system_usec" {print $2}' "$path/cpu.stat")
  nr_throttled=$(awk '$1=="nr_throttled" {print $2}' "$path/cpu.stat")
  memory_current=$(cat "$path/memory.current")
  memory_peak=$(cat "$path/memory.peak" 2>/dev/null || printf '%s' "$memory_current")
  memory_max=$(cat "$path/memory.max")
  memory_swap_max=$(cat "$path/memory.swap.max" 2>/dev/null || printf unavailable)
else
  ticks=$(getconf CLK_TCK)
  usage_nsec=$(cat "$path/cpuacct.usage")
  usage_usec=$((usage_nsec / 1000))
  user_ticks=$(awk '$1=="user" {print $2}' "$path/cpuacct.stat")
  system_ticks=$(awk '$1=="system" {print $2}' "$path/cpuacct.stat")
  user_usec=$((user_ticks * 1000000 / ticks))
  system_usec=$((system_ticks * 1000000 / ticks))
  nr_throttled=$(awk '$1=="nr_throttled" {print $2}' "$path/cpu.stat")
  memory_current=$(awk '$1=="total_rss" {print $2}' "$path/memory.stat")
  memory_peak=$(cat "$path/memory.max_usage_in_bytes")
  memory_max=$(cat "$path/memory.limit_in_bytes")
  memory_swap_max=unavailable
fi
printf '{"usage_usec":%s,"user_usec":%s,"system_usec":%s,"nr_throttled":%s,"memory_current":%s,"memory_peak":%s,"memory_max":"%s","memory_swap_max":"%s"}\n' \
  "${usage_usec:-0}" "${user_usec:-0}" "${system_usec:-0}" \
  "${nr_throttled:-0}" "${memory_current:-0}" "${memory_peak:-0}" \
  "${memory_max:-unavailable}" "${memory_swap_max:-unavailable}"
