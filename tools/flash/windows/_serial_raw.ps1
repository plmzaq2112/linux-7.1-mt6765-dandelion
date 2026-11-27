param([string]$File, [int]$WaitMs = 2000)
$bytes = [System.IO.File]::ReadAllBytes($File)
$sp = New-Object System.IO.Ports.SerialPort("COM5",115200,"None",8,"One")
$sp.WriteTimeout = 5000
$sp.DtrEnable = $true
$sp.RtsEnable = $true
$sp.Open()
Start-Sleep -Milliseconds 300
$sp.DiscardInBuffer()
$sp.Write($bytes, 0, $bytes.Length)
Start-Sleep -Milliseconds $WaitMs
$out = $sp.ReadExisting()
$sp.Close()
Write-Output $out
