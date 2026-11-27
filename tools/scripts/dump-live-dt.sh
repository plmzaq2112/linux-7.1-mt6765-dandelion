D=/proc/device-tree/soc/i2c@11016000
echo "== i2c5 children =="
ls "$D" 2>/dev/null
echo "== pmic compatible =="
for c in "$D"/*/compatible; do
	printf '%s: ' "$c"
	tr -d '\0' < "$c" 2>/dev/null
	echo
done
echo "== pmic reg =="
for r in "$D"/*/reg; do
	printf '%s: ' "$r"
	od -An -tx1 "$r" 2>/dev/null | head -1
done
