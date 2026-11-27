param([string]$Cmd, [int]$WaitMs = 1500, [switch]$CtrlC)

$p = New-Object System.IO.Ports.SerialPort COM5,115200,None,8,one
$p.ReadTimeout = 500
$p.DtrEnable = $false
$p.RtsEnable = $false
$p.Open()
Start-Sleep -Milliseconds 200
$p.DiscardInBuffer()
if ($CtrlC) {
    $p.Write([char]3)
    Start-Sleep -Milliseconds 600
}
if ($Cmd) { $p.Write($Cmd + "`r`n") }
Start-Sleep -Milliseconds $WaitMs
$buf = $p.ReadExisting()
$p.Close()
$buf
