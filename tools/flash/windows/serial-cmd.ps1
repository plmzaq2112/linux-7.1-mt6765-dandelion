param(
  [string]$Port = 'COM5',
  [string]$CmdFile,
  [string]$OutFile,
  [int]$TimeoutSec = 120
)
$sp = New-Object System.IO.Ports.SerialPort($Port, 115200, 'None', 8, 'One')
$sp.ReadTimeout = 200
$sp.WriteTimeout = 2000
$sp.Open()
$sp.DtrEnable = $true
$sp.RtsEnable = $true
$sp.DiscardInBuffer()

$marker = '__R5DONE__'
$log = New-Object System.Text.StringBuilder

function ReadUntilMarker([int]$timeoutSec) {
  $sb = New-Object System.Text.StringBuilder
  $end = [DateTime]::Now.AddSeconds($timeoutSec)
  while ([DateTime]::Now -lt $end) {
    try {
      $c = $sp.ReadExisting()
      if ($c) { [void]$sb.Append($c) }
    } catch { }
    $t = $sb.ToString()
    $cnt = ([regex]::Matches($t, [regex]::Escape($marker))).Count
    if ($cnt -ge 2) { break }
    Start-Sleep -Milliseconds 15
  }
  return $sb.ToString()
}

foreach ($cmd in (Get-Content $CmdFile)) {
  if ([string]::IsNullOrWhiteSpace($cmd)) { continue }
  $cmd = $cmd.TrimEnd()
  [void]$log.AppendLine("### CMD: $cmd")
  $sp.Write("$cmd; echo $marker`r")
  $out = ReadUntilMarker $TimeoutSec
  # drop the echoed command line itself (it contains the marker once)
  [void]$log.AppendLine(($out -replace "`r", "<CR>"))
  [void]$log.AppendLine()
}

$sp.Close()
$log.ToString() | Out-File -Encoding utf8 $OutFile
$log.ToString()
