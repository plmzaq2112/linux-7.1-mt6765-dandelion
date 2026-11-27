param([string]$Cmd, [int]$WaitMs = 1500)

$p = New-Object System.IO.Ports.SerialPort COM5,115200,None,8,one
$p.ReadTimeout = 500
$p.DtrEnable = $false
$p.RtsEnable = $false
$p.Open()
Start-Sleep -Milliseconds 200
$p.DiscardInBuffer()
$p.Write($Cmd + "`r`n")
Start-Sleep -Milliseconds $WaitMs
$buf = $p.ReadExisting()
$p.Close()
$buf
