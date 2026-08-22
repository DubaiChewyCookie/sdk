param(
  [ValidateSet('prepare', 'smoke', 'quick', 'report', 'retry')]
  [string]$Command = 'quick',
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$Rest
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
python "$Root\benchmark.py" $Command @Rest
