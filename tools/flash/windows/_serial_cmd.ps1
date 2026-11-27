param([string]$Port='COM5',[string]$Cmd='',[int]$WaitMs=3000)
$sp=New-Object System.IO.Ports.SerialPort($Port,115200,'None',8,'One')
$sp.ReadTimeout=500; $sp.WriteTimeout=30000; $sp.Open(); $sp.DtrEnable=$true; $sp.RtsEnable=$true
$enc=[System.Text.Encoding]::GetEncoding(28591); $buf=New-Object byte[] 65536
function Drain([int]$ms){$ms2=New-Object System.IO.MemoryStream;$last=[DateTime]::Now;while(([DateTime]::Now-$last).TotalMilliseconds -lt $ms){try{$r=$sp.Read($buf,0,$buf.Length);if($r -gt 0){$ms2.Write($buf,0,$r);$last=[DateTime]::Now}}catch{}};return $enc.GetString($ms2.ToArray())}
[void](Drain 400); $sp.Write("`n"); [void](Drain 600)
$sp.Write($Cmd+"`n")
$o=Drain $WaitMs
Write-Output ($o -replace "`r","<CR>")
$sp.Close()
