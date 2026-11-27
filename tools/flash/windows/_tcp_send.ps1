param([string]$File,[string]$HostIp='169.254.195.201',[int]$TcpPort=3333)
$c=New-Object System.Net.Sockets.TcpClient
$c.Connect($HostIp,$TcpPort)
$ns=$c.GetStream()
$fs=[System.IO.File]::OpenRead($File)
$buf=New-Object byte[] 65536
$total=0
while(($n=$fs.Read($buf,0,$buf.Length)) -gt 0){ $ns.Write($buf,0,$n); $total+=$n }
$fs.Close(); $ns.Flush(); $c.Close()
Write-Output "sent $total bytes"
