param([string]$Port='COM5',[string]$Cmd='')
$sp=New-Object System.IO.Ports.SerialPort($Port,115200,'None',8,'One')
$sp.ReadTimeout=500; $sp.WriteTimeout=10000
$sp.Open(); $sp.DtrEnable=$true; $sp.RtsEnable=$true
Start-Sleep -Milliseconds 300
$sp.Write($Cmd+"`n")
Start-Sleep -Milliseconds 600
$sp.Close()
Write-Output "sent: $Cmd"
