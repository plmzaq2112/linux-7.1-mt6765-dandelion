param([string]$Port = 'COM5', [string]$OutFile)
$sp = New-Object System.IO.Ports.SerialPort($Port, 115200, 'None', 8, 'One')
$sp.ReadTimeout = 300
$sp.WriteTimeout = 1000
$sp.Open()
$sp.DtrEnable = $true
$sp.RtsEnable = $true
function Drain([int]$ms) {
  $sb = New-Object System.Text.StringBuilder
  $end = [DateTime]::Now.AddMilliseconds($ms)
  while ([DateTime]::Now -lt $end) {
    try { $c = $sp.ReadExisting(); if ($c) { [void]$sb.Append($c); $end = [DateTime]::Now.AddMilliseconds(400) } } catch { }
    Start-Sleep -Milliseconds 40
  }
  return $sb.ToString()
}
$log = New-Object System.Text.StringBuilder
[void]$log.AppendLine("=== pending (3s) ===")
[void]$log.AppendLine((Drain 3000) -replace "`r", "<CR>")

[void]$log.AppendLine("=== send LF ===")
$sp.Write("`n"); Start-Sleep -Milliseconds 300
[void]$log.AppendLine((Drain 1500) -replace "`r", "<CR>")

[void]$log.AppendLine("=== send 'echo MARK-1' + LF ===")
$sp.Write("echo MARK-1`n"); Start-Sleep -Milliseconds 300
[void]$log.AppendLine((Drain 2500) -replace "`r", "<CR>")

[void]$log.AppendLine("=== send 'uname -a' + CRLF ===")
$sp.Write("uname -a`r`n"); Start-Sleep -Milliseconds 300
[void]$log.AppendLine((Drain 2500) -replace "`r", "<CR>")

[void]$log.AppendLine("=== send ^C + LF ===")
$sp.Write([char]3); $sp.Write("`n"); Start-Sleep -Milliseconds 200
[void]$log.AppendLine((Drain 1200) -replace "`r", "<CR>")

$sp.Close()
$log.ToString() | Out-File -Encoding utf8 $OutFile
