param([string]$Port = 'COM5', [string]$OutFile = 'C:\Users\31806\Documents\AI_Project\Redmi_9A\silex-linux-dandelion\artifacts\diag/logs/serial-passive.txt')
$sp = New-Object System.IO.Ports.SerialPort($Port, 115200, 'None', 8, 'One')
$sp.ReadTimeout = 300
$sp.Open()
$sp.DtrEnable = $true
$sp.RtsEnable = $true
$sb = New-Object System.Text.StringBuilder
$end = [DateTime]::Now.AddSeconds(20)
while ([DateTime]::Now -lt $end) {
  try {
    $c = $sp.ReadExisting()
    if ($c) { [void]$sb.Append($c) }
  } catch { }
  Start-Sleep -Milliseconds 25
}
$sp.Close()
$s = $sb.ToString()
"bytes read: " + $s.Length
$s | Out-File -Encoding utf8 $OutFile
($s -replace "`r", "<CR>")
