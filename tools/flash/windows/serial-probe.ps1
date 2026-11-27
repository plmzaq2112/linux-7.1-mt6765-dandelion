param([string]$Port = 'COM5', [string]$OutFile = 'C:\Users\31806\Documents\AI_Project\Redmi_9A\silex-linux-dandelion\artifacts\diag/logs/serial-probe.txt')
$sp = New-Object System.IO.Ports.SerialPort($Port, 115200, 'None', 8, 'One')
$sp.ReadTimeout = 300
$sp.WriteTimeout = 2000
$sp.Open()
$sp.DtrEnable = $true
$sp.RtsEnable = $true

function Drain([int]$ms) {
  $sb = New-Object System.Text.StringBuilder
  $end = [DateTime]::Now.AddMilliseconds($ms)
  while ([DateTime]::Now -lt $end) {
    try {
      $c = $sp.ReadExisting()
      if ($c) { [void]$sb.Append($c); $end = [DateTime]::Now.AddMilliseconds(500) }
    } catch { }
    Start-Sleep -Milliseconds 30
  }
  return $sb.ToString()
}

function Show([string]$title, [string]$s) {
  Write-Output "===== $title ====="
  Write-Output ($s -replace "`r", "<CR>")
}

$log = New-Object System.Text.StringBuilder
function Emit([string]$s) { [void]$log.AppendLine($s) }

$pending = Drain 4000
Emit "===== pending after open ====="
Emit ($pending -replace "`r", "<CR>")

$sp.Write("`r")
Start-Sleep -Milliseconds 400
$r = Drain 2000
Emit "===== after CR ====="
Emit ($r -replace "`r", "<CR>")

$sp.Write("echo HELLO-R4`r")
Start-Sleep -Milliseconds 400
$r = Drain 3000
Emit "===== after echo HELLO-R4 ====="
Emit ($r -replace "`r", "<CR>")

$sp.Write("cat /proc/consoles; cat /proc/cmdline`r")
Start-Sleep -Milliseconds 400
$r = Drain 4000
Emit "===== after consoles/cmdline ====="
Emit ($r -replace "`r", "<CR>")

$sp.Close()
$log.ToString() | Out-File -Encoding utf8 $OutFile
$log.ToString()
