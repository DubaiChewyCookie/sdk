//go:build windows

package main

import (
	"golang.org/x/sys/windows"
	"unsafe"
)

var (
	queryPerformanceCounter   = windows.NewLazySystemDLL("kernel32.dll").NewProc("QueryPerformanceCounter")
	queryPerformanceFrequency = windows.NewLazySystemDLL("kernel32.dll").NewProc("QueryPerformanceFrequency")
	performanceFrequency      = performanceTicksPerSecond()
)

func performanceTicksPerSecond() int64 {
	var frequency int64
	result, _, callError := queryPerformanceFrequency.Call(uintptr(unsafe.Pointer(&frequency)))
	if result == 0 {
		panic(callError)
	}
	return frequency
}

func nowNS() int64 {
	var counter int64
	result, _, callError := queryPerformanceCounter.Call(uintptr(unsafe.Pointer(&counter)))
	if result == 0 {
		panic(callError)
	}
	return counter * 1_000_000_000 / performanceFrequency
}
