$sp=New-Object System.IO.Ports.SerialPort('COM5',115200,'None',8,'One')
$sp.ReadTimeout=500; $sp.WriteTimeout=30000; $sp.Open(); $sp.DtrEnable=$true; $sp.RtsEnable=$true
$enc=[System.Text.Encoding]::GetEncoding(28591); $buf=New-Object byte[] 65536
function Drain([int]$ms){$ms2=New-Object System.IO.MemoryStream;$last=[DateTime]::Now;while(([DateTime]::Now-$last).TotalMilliseconds -lt $ms){try{$r=$sp.Read($buf,0,$buf.Length);if($r -gt 0){$ms2.Write($buf,0,$r);$last=[DateTime]::Now}}catch{}};return $enc.GetString($ms2.ToArray())}
function Cmd([string]$c,[int]$ms){$sp.Write($c+"`n");$o=Drain $ms;Write-Output "===== $c =====";Write-Output ($o -replace "`r","<CR>")}
[void](Drain 400); $sp.Write("`n"); [void](Drain 800)
Cmd "ls -l /dev/fb* /dev/dri/* 2>&1 | head -30" 2000
Cmd "cat /sys/class/graphics/fb0/name 2>&1; cat /sys/class/graphics/fb0/modes 2>&1 | head -5; cat /sys/class/graphics/fb0/virtual_size 2>&1" 2000
Cmd "dmesg | grep -iE 'drm|dsi|panel|disp|fbcon|mtk|simple|framebuffer|pwm|backlight' | head -60" 4000
Cmd "ps w 2>&1 | head -40" 2000
Cmd "ls -l /usr/local/bin/display-start.sh /etc/init.d/display /var/log/display.log 2>&1" 1500
Cmd "cat /etc/init.d/rcS 2>&1 | head -80" 2000
$sp.Close()
