param(
  [string]$Port = 'COM5',
  [string]$File = 'C:\Users\31806\AppData\Local\Temp\opencode\testfile.bin',
  [string]$Dst = '/tmp/testfile.bin',
  [string]$OutFile = 'C:\Users\31806\Documents\AI_Project\Redmi_9A\silex-linux-dandelion\artifacts\serial-xfer3.txt'
)
$sp = New-Object System.IO.Ports.SerialPort($Port, 115200, 'None', 8, 'One')
$sp.ReadBufferSize = 1MB
$sp.WriteBufferSize = 64KB
$sp.ReadTimeout = 300
$sp.WriteTimeout = 120000
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
function Send([string]$s) {
  $b = $enc.GetBytes($s)
  for ($i = 0; $i -lt $b.Length; $i += 4096) {
    $n = [Math]::Min(4096, $b.Length - $i)
    $sp.Write($b, $i, $n)
  }
}

[void](Drain 500)
$sp.Write("`n")
[void](Drain 800)

$raw = [System.IO.File]::ReadAllBytes($File)
$b64 = [Convert]::ToBase64String($raw)
$sum = (Get-FileHash -Algorithm SHA256 -Path $File).Hash.ToLower()

# wrap at 76 chars: canonical tty needs newline-terminated lines <= 4096
$sb = New-Object System.Text.StringBuilder
for ($i = 0; $i -lt $b64.Length; $i += 76) {
  [void]$sb.Append($b64, $i, [Math]::Min(76, $b64.Length - $i))
  [void]$sb.Append("`n")
}
$payload = $sb.ToString()
$n = $payload.Length
# pad to a 1024 boundary with newlines so dd can use an exact count
$pad = (1024 - ($n % 1024)) % 1024
if ($pad -gt 0) { $payload += ("`n" * $pad) }
$n = $payload.Length
Write-Output ("file bytes: $($raw.Length)  b64: $($b64.Length)  payload: $n  pad: $pad")
Write-Output ("local sha256: $sum")

Send "stty -echo`n"
Start-Sleep -Milliseconds 400
Send "dd bs=1 count=$n of=/tmp/r.b64 2>/dev/null`n"
Start-Sleep -Milliseconds 400

$sw = [Diagnostics.Stopwatch]::StartNew()
$chunk = 4096
for ($i = 0; $i -lt $payload.Length; $i += $chunk) {
  $s = $payload.Substring($i, [Math]::Min($chunk, $payload.Length - $i))
  Send $s
  if ((($i / $chunk) % 16) -eq 0) { [void](Drain 15) }
}
Write-Output ("sent in " + $sw.Elapsed.TotalSeconds.ToString("0.0") + " s")

Start-Sleep -Milliseconds 800
Send "stty sane`n"
Start-Sleep -Milliseconds 400
Send "base64 -d /tmp/r.b64 > $Dst; echo DECODE-RC=$?`n"
Start-Sleep -Milliseconds 1500
Send "sha256sum $Dst; wc -c < $Dst`n"
$res = Drain 10000
Write-Output "----- device -----"
Write-Output ($res -replace "`r", "<CR>")
$sp.Close()
