param(
  [string]$Port = 'COM5',
  [string]$LogFile = 'C:\Users\31806\Documents\AI_Project\Redmi_9A\silex-linux-dandelion\artifacts\diag/logs/serial-agent.log',
  [string]$CmdFile = 'C:\Users\31806\Documents\AI_Project\Redmi_9A\silex-linux-dandelion\artifacts\installer/windows/serial-agent.cmd'
)
$enc = [System.Text.Encoding]::GetEncoding(28591)
if (-not (Test-Path $LogFile)) { New-Item -ItemType File -Path $LogFile | Out-Null }
if (-not (Test-Path $CmdFile)) { New-Item -ItemType File -Path $CmdFile | Out-Null }

Add-Content -Path $LogFile -Value "`n=== AGENT START $(Get-Date -Format o) ===`n"

$sp = $null
$sent = 0
while ($true) {
  if ($null -eq $sp -or -not $sp.IsOpen) {
    try {
      $sp = New-Object System.IO.Ports.SerialPort($Port, 115200, 'None', 8, 'One')
      $sp.ReadBufferSize = 1MB
      $sp.ReadTimeout = 100
      $sp.WriteTimeout = 5000
      $sp.Open()
      $sp.DtrEnable = $true
      $sp.RtsEnable = $true
      Add-Content -Path $LogFile -Value "`n=== PORT OPEN $(Get-Date -Format HH:mm:ss) ===`n"
    } catch {
      $sp = $null
      Start-Sleep -Seconds 2
      continue
    }
  }
  try {
    $n = $sp.BytesToRead
    if ($n -gt 0) {
      $b = New-Object byte[] $n
      $r = $sp.Read($b, 0, $n)
      [System.IO.File]::AppendAllText($LogFile, $enc.GetString($b, 0, $r), $enc)
    }
  } catch {
    Add-Content -Path $LogFile -Value "`n=== READ ERROR $(Get-Date -Format HH:mm:ss) $($_.Exception.Message) ===`n"
    try { $sp.Close() } catch { }
    $sp = $null
    Start-Sleep -Seconds 1
    continue
  }
  try {
    $lines = @(Get-Content -Path $CmdFile -ErrorAction Stop)
    while ($sent -lt $lines.Count) {
      $sp.Write($lines[$sent] + "`n")
      $sent++
    }
  } catch { }
  Start-Sleep -Milliseconds 20
}
