param(
    [Parameter(Mandatory=$true)][string]$File,
    [Parameter(Mandatory=$true)][int]$TcpPort,
    [string]$HostIp = "169.254.195.201",
    [int]$TimeoutMs = 30000
)
$ErrorActionPreference = "Stop"
$client = New-Object System.Net.Sockets.TcpClient
$client.ReceiveTimeout = $TimeoutMs
$iar = $client.BeginConnect($HostIp, $TcpPort, $null, $null)
if (-not $iar.AsyncWaitHandle.WaitOne($TimeoutMs)) { Write-Output "connect timeout"; exit 1 }
$client.EndConnect($iar)
$stream = $client.GetStream()
$fs = [System.IO.File]::Create($File)
$buf = New-Object byte[] 65536
$total = 0
while (($n = $stream.Read($buf, 0, $buf.Length)) -gt 0) {
    $fs.Write($buf, 0, $n)
    $total += $n
}
$fs.Close()
$stream.Close()
$client.Close()
Write-Output "recv: $total bytes -> $File"
