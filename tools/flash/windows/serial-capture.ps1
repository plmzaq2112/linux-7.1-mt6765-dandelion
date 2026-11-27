$port = New-Object System.IO.Ports.SerialPort COM5,115200,None,8,one
$port.Open()
$port.ReadTimeout = 500
$sw = New-Object System.IO.StreamWriter "C:\Users\31806\Documents\AI_Project\Redmi_9A\silex-linux-dandelion\artifacts\diag/logs/serial-bootloop.log"
$until = (Get-Date).AddSeconds(180)
while ((Get-Date) -lt $until) {
    try { $sw.Write($port.ReadExisting()) } catch {}
    Start-Sleep -Milliseconds 100
}
$sw.Close()
$port.Close()
