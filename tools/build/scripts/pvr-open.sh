for d in /dev/dri/renderD128 /dev/dri/renderD129 /dev/dri/card2; do
	echo "== open $d"
	timeout 60 sh -c "head -c 0 $d" 2>&1
	echo "rc=$?"
done
sleep 1
dmesg | tail -25
ls /proc/pvr 2>&1
