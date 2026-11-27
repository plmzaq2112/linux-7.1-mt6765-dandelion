param(
  [string]$Port = 'COM5',
  [string]$DumpFile = 'C:\Users\31806\Documents\AI_Project\Redmi_9A\silex-linux-dandelion\artifacts\diag/logs/dmesg-r5.txt'
)
$sp = New-Object System.IO.Ports.SerialPort($Port, 115200, 'None', 8, 'One')
$sp.ReadBufferSize = 1MB
$sp.ReadTimeout = 3000
$sp.WriteTimeout = 3000
$sp.Open()
$sp.DtrEnable = $true
$sp.RtsEnable = $true
$sp.DiscardInBuffer()

$buf = New-Object byte[] 65536
$enc = [System.Text.Encoding]::GetEncoding(28591)

function Pump([System.IO.MemoryStream]$ms2, [int]$idleMs) {
  # blocking read: returns as soon as at least one byte is available
  $last = [DateTime]::Now
  while (([DateTime]::Now - $last).TotalMilliseconds -lt $idleMs) {
    try {
      $r = $sp.Read($buf, 0, $buf.Length)
      if ($r -gt 0) { $ms2.Write($buf, 0, $r); $last = [DateTime]::Now }
    } catch [TimeoutException] { }
  }
}

function ReadFor([int]$ms) {
  $ms2 = New-Object System.IO.MemoryStream
  Pump $ms2 $ms
  return $ms2.ToArray()
}

function ReadUntil([string]$pat, [int]$timeoutMs) {
  $ms2 = New-Object System.IO.MemoryStream
  $sw = [Diagnostics.Stopwatch]::StartNew()
  while ($sw.ElapsedMilliseconds -lt $timeoutMs) {
    try {
      $r = $sp.Read($buf, 0, $buf.Length)
      if ($r -gt 0) {
        $ms2.Write($buf, 0, $r)
        if ($enc.GetString($ms2.ToArray()).Contains($pat)) { break }
      }
    } catch [TimeoutException] { }
  }
  return $ms2.ToArray()
}

[void](ReadFor 300)
$sp.Write("stty -echo -opost`r")
[void](ReadFor 500)

$sp.Write("dmesg > /tmp/d.txt; wc -c < /tmp/d.txt; md5sum /tmp/d.txt; echo R5M1`r")
$r = $enc.GetString((ReadUntil "R5M1" 20000))
Write-Output "----- meta -----"
Write-Output ($r -replace "`r", "<CR>")

$size = $null; $md5 = $null
foreach ($line in ($r -split "`n")) {
  $t = $line.Trim()
  if ($t -match '^(\d+)$') { $size = [int]$Matches[1] }
  if ($t -match '^([0-9a-f]{32})\s') { $md5 = $Matches[1] }
}
Write-Output "size=$size md5=$md5"
if (-not $size) { $sp.Close(); Write-Output "ERROR: no size"; exit 1 }

$sp.Write("cat /tmp/d.txt`r")
$data = New-Object System.IO.MemoryStream
$sw2 = [Diagnostics.Stopwatch]::StartNew()
while ($data.Length -lt $size -and $sw2.ElapsedMilliseconds -lt 60000) {
  try {
    $n = $sp.Read($buf, 0, [Math]::Min($buf.Length, $size - $data.Length))
    if ($n -gt 0) { $data.Write($buf, 0, $n) }
  } catch [TimeoutException] { }
}
$bytes = $data.ToArray()
Write-Output ("captured " + $bytes.Length + " of " + $size + " bytes")
[System.IO.File]::WriteAllBytes($DumpFile, $bytes)

$h = [System.Security.Cryptography.MD5]::Create()
$hash = ($h.ComputeHash($bytes) | ForEach-Object { $_.ToString('x2') }) -join ''
Write-Output "local md5=$hash  match=$($hash -eq $md5)"

$sp.Write("stty echo opost`r")
[void](ReadFor 800)
$sp.Close()
