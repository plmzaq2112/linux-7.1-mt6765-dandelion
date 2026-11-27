param(
  [string]$Port = 'COM5',
  [string]$Tar = 'C:\Users\31806\Documents\AI_Project\Redmi_9A\silex-linux-dandelion\artifacts\assets/dandelion-alpine-3.24.4.tar.gz',
  [string]$OutFile = 'C:\Users\31806\Documents\AI_Project\Redmi_9A\silex-linux-dandelion\artifacts\serial-xfer.txt'
)
$sp = New-Object System.IO.Ports.SerialPort($Port, 115200, 'None', 8, 'One')
$sp.ReadBufferSize = 1MB
$sp.WriteBufferSize = 64KB
$sp.ReadTimeout = 300
$sp.WriteTimeout = 60000
$sp.Open()
$sp.DtrEnable = $true
$sp.RtsEnable = $true
$sp.DiscardInBuffer()

$enc = [System.Text.Encoding]::GetEncoding(28591)
$buf = New-Object byte[] 65536
$log = New-Object System.Text.StringBuilder
function Emit([string]$s) { [void]$log.AppendLine($s) }

function ReadFor([int]$ms) {
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
  for ($i = 0; $i -lt $b.Length; $i += 8192) {
    $n = [Math]::Min(8192, $b.Length - $i)
    $sp.Write($b, $i, $n)
  }
}

# 0. wake the shell (r7 waits for one host byte)
Send "`n"
[void](ReadFor 1500)

# 1. build base64 wrapped at 76 chars
$raw = [System.IO.File]::ReadAllBytes($Tar)
$b64 = [Convert]::ToBase64String($raw)
$sb = New-Object System.Text.StringBuilder ([int]($b64.Length * 1.02) + 256)
for ($i = 0; $i -lt $b64.Length; $i += 76) {
  $n = [Math]::Min(76, $b64.Length - $i)
  [void]$sb.Append($b64, $i, $n)
  [void]$sb.Append("`n")
}
$payload = $sb.ToString()
Emit ("tar bytes: " + $raw.Length + "  base64 chars: " + $b64.Length + "  payload: " + $payload.Length)

# 2. echo off, then here-doc straight into base64 -d
Send "stty -echo`n"
[void](ReadFor 400)
Send "base64 -d > /tmp/rootfs.tar.gz <<'DANDELIONEOF'`n"
[void](ReadFor 300)

$sw = [Diagnostics.Stopwatch]::StartNew()
Send $payload
Send "DANDELIONEOF`n"
Emit ("payload sent in " + $sw.Elapsed.TotalSeconds.ToString("0.0") + " s")

Send "stty sane`n"
Send "sha256sum /tmp/rootfs.tar.gz; wc -c < /tmp/rootfs.tar.gz; echo XFERDONE`n"
$res = ReadUntil "XFERDONE" 180000
Emit "----- device answer -----"
Emit ($res -replace "`r", "<CR>")

$sp.Close()
$log.ToString() | Out-File -Encoding utf8 $OutFile
$log.ToString()
