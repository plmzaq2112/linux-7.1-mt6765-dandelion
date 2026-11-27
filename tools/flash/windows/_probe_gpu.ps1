$sp=New-Object System.IO.Ports.SerialPort('COM5',115200,'None',8,'One')
$sp.ReadTimeout=500; $sp.WriteTimeout=30000; $sp.Open(); $sp.DtrEnable=$true; $sp.RtsEnable=$true
$enc=[System.Text.Encoding]::GetEncoding(28591); $buf=New-Object byte[] 65536
function Drain([int]$ms){$ms2=New-Object System.IO.MemoryStream;$last=[DateTime]::Now;while(([DateTime]::Now-$last).TotalMilliseconds -lt $ms){try{$r=$sp.Read($buf,0,$buf.Length);if($r -gt 0){$ms2.Write($buf,0,$r);$last=[DateTime]::Now}}catch{}};return $enc.GetString($ms2.ToArray())}
function Cmd([string]$c,[int]$ms){$sp.Write($c+"`n");$o=Drain $ms;Write-Output "===== $c =====";Write-Output ($o -replace "`r","<CR>")}
[void](Drain 400); $sp.Write("`n"); [void](Drain 800)
Cmd "lsmod 2>&1 | head -20; echo ---; ls /lib/modules 2>&1; echo ---; ls -l /lib/firmware/rgx* 2>&1; echo ---; ls /proc/pvr 2>&1; echo ---; ls /dev/dri 2>&1" 4000
Cmd "cat /proc/pvr/status 2>&1 | head -40" 3000
$sp.Close()
