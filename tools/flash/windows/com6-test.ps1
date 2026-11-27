$ErrorActionPreference = 'Stop'
$log = 'C:\Users\31806\Documents\AI_Project\Redmi_9A\silex-linux-dandelion\artifacts\diag/logs/com6-test.log'
function L($m) { Add-Content -Path $log -Value ("{0:HH:mm:ss.fff} {1}" -f (Get-Date), $m) }
Remove-Item $log -ErrorAction SilentlyContinue
L "start"
$p = New-Object System.IO.Ports.SerialPort('COM6', 115200, 'None', 8, 'One')
$p.ReadTimeout = 500
$p.WriteTimeout = 500
L "opening"
try { $p.Open() } catch { L ("open exception: " + $_.Exception.Message); exit 1 }
L "opened"
try { $p.DtrEnable = $true; L "dtr on" } catch { L ("dtr exc: " + $_.Exception.Message) }
try { $p.RtsEnable = $true; L "rts on" } catch { L ("rts exc: " + $_.Exception.Message) }
Start-Sleep -Milliseconds 300
try { $p.Write("`r`n"); L "wrote CRLF" } catch { L ("write exc: " + $_.Exception.Message) }
Start-Sleep -Milliseconds 1500
try { $out = $p.ReadExisting(); L ("read: [" + $out + "]") } catch { L ("read exc: " + $_.Exception.Message) }
try { $p.Close(); L "closed" } catch { L ("close exc: " + $_.Exception.Message) }
L "done"
