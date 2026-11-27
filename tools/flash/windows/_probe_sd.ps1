$sp=New-Object System.IO.Ports.SerialPort('COM5',115200,'None',8,'One')
$sp.ReadTimeout=500; $sp.WriteTimeout=30000; $sp.Open(); $sp.DtrEnable=$true; $sp.RtsEnable=$true
$enc=[System.Text.Encoding]::GetEncoding(28591); $buf=New-Object byte[] 65536
function Drain([int]$ms){$ms2=New-Object System.IO.MemoryStream;$last=[DateTime]::Now;while(([DateTime]::Now-$last).TotalMilliseconds -lt $ms){try{$r=$sp.Read($buf,0,$buf.Length);if($r -gt 0){$ms2.Write($buf,0,$r);$last=[DateTime]::Now}}catch{}};return $enc.GetString($ms2.ToArray())}
function Cmd([string]$c,[int]$ms){$sp.Write($c+"`n");$o=Drain $ms;Write-Output "===== $c =====";Write-Output ($o -replace "`r","<CR>")}
[void](Drain 400); $sp.Write("`n"); [void](Drain 800)
Cmd "mkdir -p /mnt/sd && mount -t vfat /dev/mmcblk1p1 /mnt/sd 2>&1; echo RC=$?; mount | grep mmcblk1" 4000
Cmd "ls -la /mnt/sd 2>&1 | head -50" 3000
Cmd "find /mnt/sd -maxdepth 3 -type f 2>&1 | head -80" 6000
Cmd "umount /mnt/sd 2>&1; echo done" 2000
$sp.Close()
