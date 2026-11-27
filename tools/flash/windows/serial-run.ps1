param(
  [string]$Port = 'COM5',
  [string]$CmdFile,
  [string]$OutFile
)
$sp = New-Object System.IO.Ports.SerialPort($Port, 115200, 'None', 8, 'One')
$sp.ReadTimeout = 300
$sp.WriteTimeout = 1000
try { $sp.Open() } catch {
  "OPEN FAILED: $($_.Exception.Message)" | Out-File -Encoding utf8 $OutFile
  exit 1
}
$sp.DtrEnable = $true
$sp.RtsEnable = $true

function Drain([int]$ms) {
  $sb = New-Object System.Text.StringBuilder
  $end = [DateTime]::Now.AddMilliseconds($ms)
  while ([DateTime]::Now -lt $end) {
    try {
      $c = $sp.ReadExisting()
      if ($c) { [void]$sb.Append($c); $end = [DateTime]::Now.AddMilliseconds(400) }
    } catch { }
    Start-Sleep -Milliseconds 40
  }
  return $sb.ToString()
}

$log = New-Object System.Text.StringBuilder
[void]$log.AppendLine("== OPEN $Port ok ==")
[void]$log.AppendLine((Drain 500))

foreach ($cmd in (Get-Content $CmdFile)) {
  if ([string]::IsNullOrWhiteSpace($cmd)) { continue }
  $sp.Write($cmd + "`r")
  Start-Sleep -Milliseconds 120
  $out = Drain 1500
  [void]$log.AppendLine("### " + $cmd)
  [void]$log.Append($out)
  [void]$log.AppendLine()
}
$sp.Close()
$log.ToString() | Out-File -Encoding utf8 $OutFile
