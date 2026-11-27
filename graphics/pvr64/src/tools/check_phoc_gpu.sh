#!/bin/sh
# check_phoc_gpu.sh - verify phoc is rendering on the PowerVR GE8320.
# usage (from Windows): Get-Content src\pvr64\tools\check_phoc_gpu.sh | ssh root@phone "tr -d '\r' | sh"
P=$(pgrep -u dandelion -x phoc)
echo "== phoc pid: $P"
ps -o pid,etime,pcpu,rss,args -p "$P"
echo "== graphics libraries mapped by phoc"
grep -oE '/[^ ]*(IMGegl|GLES|gbm|EGL|pixman|llvm|swrast|mesa|pvr-bridge)[^ ]*' "/proc/$P/maps" | sort -u
echo "== pvrsrvkm interrupts over 5 s"
a=$(awk '/pvrsrvkm/ {print $2}' /proc/interrupts)
sleep 5
b=$(awk '/pvrsrvkm/ {print $2}' /proc/interrupts)
echo "$a -> $b ($(( (b - a) / 5 ))/s)"
echo "== renderer lines in phosh.log"
grep -E 'GL renderer|GL version|Software rendering|CRITICAL' "/home/dandelion/phosh.log" | grep -v -E 'EDID|Xwayland|libinput' | tail -15
echo "== kernel pvr messages"
dmesg | grep -iE 'pvr|rgx' | tail -5
