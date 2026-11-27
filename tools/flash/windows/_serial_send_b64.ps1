param([string]$Port='COM5',[string]$B64Path='', [string]$Remote='/tmp/dandelion-alpine-3.24.4.tar.gz')
$sp=New-Object System.IO.Ports.SerialPort($Port,115200,'None',8,'One')
$sp.ReadTimeout=1000; $sp.WriteTimeout=60000; $sp.Open(); $sp.DtrEnable=$true; $sp.RtsEnable=$true
$sp.ReadBufferSize=1048576; $sp.WriteBufferSize=1048576
$enc=[System.Text.Encoding]::GetEncoding(28591); $buf=New-Object byte[] 65536
function Drain([int]$ms){$ms2=New-Object System.IO.MemoryStream;$last=[DateTime]::Now;while(([DateTime]::Now-$last).TotalMilliseconds -lt $ms){try{$r=$sp.Read($buf,0,$buf.Length);if($r -gt 0){$ms2.Write($buf,0,$r);$last=[DateTime]::Now}}catch{}};return $enc.GetString($ms2.ToArray())}
[void](Drain 400); $sp.Write("`n"); [void](Drain 600)
$cmd = "rm -f $Remote; base64 -d > $Remote && echo __RCV_OK__ || echo __RCV_FAIL__"
$sp.Write($cmd + "`n")
Start-Sleep -Milliseconds 800
# stream
$bytes = [System.IO.File]::ReadAllBytes($B64Path)
$chunk = 4096
for($i=0; $i -lt $bytes.Length; $i += $chunk){
  $n = [Math]::Min($chunk, $bytes.Length - $i)
  $sp.Write($bytes, $i, $n)
}
# EOF
$sp.Write([byte[]]@(4), 0, 1)
$sp.Write("`n")
Write-Output "SENT $($bytes.Length) bytes, waiting..."
$o = Drain 120000
Write-Output ($o -replace "`r","<CR>")
$sp.Close()
