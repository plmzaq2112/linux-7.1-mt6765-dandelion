P=/proc/device-tree/soc/pwrap@1000d000
echo "== pwrap children =="
ls "$P" 2>/dev/null
for d in "$P"/*/; do
	[ -d "$d" ] || continue
	echo "--- $d"
	ls "$d" 2>/dev/null | head -20
done
