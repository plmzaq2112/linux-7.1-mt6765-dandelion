$sp=New-Object System.IO.Ports.SerialPort('COM5',115200,'None',8,'One')
$sp.ReadTimeout=500; $sp.WriteTimeout=30000; $sp.Open(); $sp.DtrEnable=$true; $sp.RtsEnable=$true
$enc=[System.Text.Encoding]::GetEncoding(28591); $buf=New-Object byte[] 65536
function Drain([int]$ms){$ms2=New-Object System.IO.MemoryStream;$last=[DateTime]::Now;while(([DateTime]::Now-$last).TotalMilliseconds -lt $ms){try{$r=$sp.Read($buf,0,$buf.Length);if($r -gt 0){$ms2.Write($buf,0,$r);$last=[DateTime]::Now}}catch{}};return $enc.GetString($ms2.ToArray())}
function Cmd([string]$c,[int]$ms){$sp.Write($c+"`n");$o=Drain $ms;Write-Output "===== $c =====";Write-Output ($o -replace "`r","<CR>")}
[void](Drain 400); $sp.Write("`n"); [void](Drain 800)
Cmd "ls /sys/class/backlight 2>&1; cat /sys/class/backlight/*/brightness 2>&1; cat /sys/class/backlight/*/max_brightness 2>&1" 2000
Cmd "cat /sys/class/drm/card1-DSI-1/status 2>&1; cat /sys/class/drm/card1-DSI-1/enabled 2>&1; cat /sys/class/drm/card1-DSI-1/modes 2>&1 | head -5" 2000
Cmd "mount | grep mmcblk1; ls /mnt/sd 2>&1 | head -20; ls /mnt 2>&1" 2000
Cmd "ls /usr/local/bin 2>&1; ls /usr/local/share 2>&1" 1500
$sp.Close()
