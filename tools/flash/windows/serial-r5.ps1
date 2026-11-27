param(
  [string]$Port = 'COM5',
  [string]$OutFile = 'C:\Users\31806\Documents\AI_Project\Redmi_9A\silex-linux-dandelion\artifacts\diag/logs/serial-r5.txt'
)
$sp = New-Object System.IO.Ports.SerialPort($Port, 115200, 'None', 8, 'One')
$sp.ReadTimeout = 200
$sp.WriteTimeout = 2000
$sp.Open()
$sp.DtrEnable = $true
$sp.RtsEnable = $true
$sp.DiscardInBuffer()

function DrainMs([int]$ms) {
  $sb = New-Object System.Text.StringBuilder
  $end = [DateTime]::Now.AddMilliseconds($ms)
  while ([DateTime]::Now -lt $end) {
    try { $c = $sp.ReadExisting(); if ($c) { [void]$sb.Append($c) } } catch { }
    Start-Sleep -Milliseconds 15
  }
  return $sb.ToString()
}

$all = New-Object System.Text.StringBuilder
function Emit([string]$s) { [void]$all.Append($s) }

Emit "===== pending before handshake (3s) ====="
$p = DrainMs 3000
Emit ("len=" + $p.Length)
Emit ($p -replace "`r", "<CR>")

Emit "`n===== sending CR handshake ====="
$sp.Write("`r")

$rx = DrainMs 15000
Emit ("rx bytes after handshake: " + $rx.Length)
$z = ($rx.ToCharArray() | Where-Object { $_ -eq 'Z' }).Count
Emit ("Z count: " + $z)
Emit "----- first 200 chars -----"
Emit ($rx.Substring(0, [Math]::Min(200, $rx.Length)) -replace "`r", "<CR>")
Emit "----- last 400 chars -----"
$tailStart = [Math]::Max(0, $rx.Length - 400)
Emit ($rx.Substring($tailStart) -replace "`r", "<CR>")

Emit "`n===== sending 'echo SHELL-OK' ====="
$sp.Write("echo SHELL-OK`r")
$r2 = DrainMs 4000
Emit ("rx bytes: " + $r2.Length)
Emit ($r2 -replace "`r", "<CR>")

Emit "`n===== sending 'uname -a; cat /proc/consoles' ====="
$sp.Write("uname -a; cat /proc/consoles`r")
$r3 = DrainMs 4000
Emit ("rx bytes: " + $r3.Length)
Emit ($r3 -replace "`r", "<CR>")

$sp.Close()
$all.ToString() | Out-File -Encoding utf8 $OutFile
$all.ToString()
