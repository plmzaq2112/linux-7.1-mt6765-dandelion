param(
  [string]$Port = 'COM5',
  [string]$File = 'C:\Users\31806\AppData\Local\Temp\opencode\testfile.bin',
  [string]$Dst = '/tmp/testfile.bin',
  [string]$OutFile = 'C:\Users\31806\Documents\AI_Project\Redmi_9A\silex-linux-dandelion\artifacts\diag/logs/serial-xfer2.txt'
)
$sp = New-Object System.IO.Ports.SerialPort($Port, 115200, 'None', 8, 'One')
$sp.ReadBufferSize = 1MB
$sp.WriteBufferSize = 64KB
$sp.ReadTimeout = 300
$sp.WriteTimeout = 120000
$sp.Open()
$sp.DtrEnable = $true
$sp.RtsEnable = $true
$sp.DiscardInBuffer()

$enc = [System.Text.Encoding]::GetEncoding(28591)
$buf = New-Object byte[] 65536
$log = New-Object System.Text.StringBuilder
function Emit([string]$s) { [void]$log.AppendLine($s) }

function Drain([int]$ms) {
  $ms2 = New-Object System.IO.MemoryStream
  $last = [DateTime]::Now
  while (([DateTime]::Now - $last).TotalMilliseconds -lt $ms) {
    try { $r = $sp.Read($buf, 0, $buf.Length); if ($r -gt 0) { $ms2.Write($buf, 0, $r); $last = [DateTime]::Now } }
    catch [TimeoutException] { }
  }
  return $enc.GetString($ms2.ToArray())
}
function ReadUntil([string]$pat, [int]$timeoutMs) {
  $ms2 = New-Object System.IO.MemoryStream
  $sw = [Diagnostics.Stopwatch]::StartNew()
  while ($sw.ElapsedMilliseconds -lt $timeoutMs) {
    try { $r = $sp.Read($buf, 0, $buf.Length); if ($r -gt 0) { $ms2.Write($buf, 0, $r); if ($enc.GetString($ms2.ToArray()).Contains($pat)) { break } } }
    catch [TimeoutException] { }
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

# abort a leftover heredoc, get a clean prompt
$sp.Write([char]3)
Start-Sleep -Milliseconds 300
[void](Drain 500)
Send "`n"
[void](Drain 1500)

$raw = [System.IO.File]::ReadAllBytes($File)
$b64 = [Convert]::ToBase64String($raw)
$sum = (Get-FileHash -Algorithm SHA256 -Path $File).Hash.ToLower()
$n = [int]([Math]::Ceiling($b64.Length / 1024.0) * 1024)
Emit ("file: " + $File + "  bytes: " + $raw.Length + "  b64: " + $b64.Length + "  padded: " + $n)
Emit ("local sha256: " + $sum)

Send "stty raw -echo`n"
Start-Sleep -Milliseconds 300
[void](Drain 300)
$t0 = [DateTime]::Now
Send "dd bs=1 count=$n of=$Dst 2>/dev/null`n"
Start-Sleep -Milliseconds 300

# stream payload, pad with newlines to exactly n bytes
$sw = [Diagnostics.Stopwatch]::StartNew()
Send $b64
if ($n -gt $b64.Length) { Send ("`n" * ($n - $b64.Length)) }
Emit ("payload streamed in " + $sw.Elapsed.TotalSeconds.ToString("0.0") + " s")
Start-Sleep -Milliseconds 500

Send "stty sane`n"
Start-Sleep -Milliseconds 300
Send "sha256sum $Dst; wc -c < $Dst`n"
$res = Drain 8000
Emit "----- device -----"
Emit ($res -replace "`r", "<CR>")

$sp.Close()
$log.ToString() | Out-File -Encoding utf8 $OutFile
$log.ToString()
