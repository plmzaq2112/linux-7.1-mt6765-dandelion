param([string]$Port = 'COM5')
$sp = New-Object System.IO.Ports.SerialPort($Port, 115200, 'None', 8, 'One')
$sp.ReadBufferSize = 1MB
$sp.ReadTimeout = 300
$sp.WriteTimeout = 30000
$sp.Open(); $sp.DtrEnable = $true; $sp.RtsEnable = $true
$sp.DiscardInBuffer()
$enc = [System.Text.Encoding]::GetEncoding(28591)
$buf = New-Object byte[] 65536
function Drain([int]$ms) {
  $ms2 = New-Object System.IO.MemoryStream
  $last = [DateTime]::Now
  while (([DateTime]::Now - $last).TotalMilliseconds -lt $ms) {
    try { $r = $sp.Read($buf, 0, $buf.Length); if ($r -gt 0) { $ms2.Write($buf, 0, $r); $last = [DateTime]::Now } } catch [TimeoutException] { }
  }
  return $enc.GetString($ms2.ToArray())
}
function Cmd([string]$c, [int]$ms) {
  $sp.Write($c + "`n")
  $o = Drain $ms
  Write-Output ("### " + $c)
  Write-Output ($o -replace "`r", "<CR>")
}

Write-Output ("pending: " + (Drain 1000).Length)
$sp.Write([char]3); [void](Drain 400)
$sp.Write("`n"); [void](Drain 400)
Cmd "stty -a" 1500
Cmd "stty -echo" 600
Cmd "stty -a" 1500
Cmd "stty sane" 800
Cmd "echo BACK-OK" 1500
$sp.Close()
