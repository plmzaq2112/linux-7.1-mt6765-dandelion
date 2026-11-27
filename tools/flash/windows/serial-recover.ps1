param([string]$Port = 'COM5')
$sp = New-Object System.IO.Ports.SerialPort($Port, 115200, 'None', 8, 'One')
$sp.ReadBufferSize = 1MB
$sp.ReadTimeout = 300
$sp.WriteTimeout = 30000
$sp.Open()
$sp.DtrEnable = $true
$sp.RtsEnable = $true
$sp.DiscardInBuffer()
$enc = [System.Text.Encoding]::GetEncoding(28591)
$buf = New-Object byte[] 65536

function Drain([int]$ms) {
  $ms2 = New-Object System.IO.MemoryStream
  $last = [DateTime]::Now
  while (([DateTime]::Now - $last).TotalMilliseconds -lt $ms) {
    try { $r = $sp.Read($buf, 0, $buf.Length); if ($r -gt 0) { $ms2.Write($buf, 0, $r); $last = [DateTime]::Now } }
    catch [TimeoutException] { }
  }
  return $enc.GetString($ms2.ToArray())
}

$o = Drain 800
Write-Output ("pending: " + $o.Length + " bytes")
Write-Output (($o.Substring([Math]::Max(0, $o.Length - 200))) -replace "`r", "<CR>")

# finish the pending heredoc line, then terminate the here-document
$sp.Write("`n")
Start-Sleep -Milliseconds 300
[void](Drain 500)
$sp.Write("DANDELIONEOF`n")
$o = Drain 3000
Write-Output "----- after terminator -----"
Write-Output (($o.Substring([Math]::Max(0, $o.Length - 600))) -replace "`r", "<CR>")

$sp.Write("`n")
Start-Sleep -Milliseconds 300
$sp.Write("stty sane`n")
Start-Sleep -Milliseconds 300
$sp.Write("echo ALIVE-$((1+1))`n")
$o = Drain 3000
Write-Output "----- alive check -----"
Write-Output ($o -replace "`r", "<CR>")

$sp.Close()
