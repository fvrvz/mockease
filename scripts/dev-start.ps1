param ([switch]$Background)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
& (Join-Path $ScriptDir "dev.ps1") -Action start -Background:$Background
