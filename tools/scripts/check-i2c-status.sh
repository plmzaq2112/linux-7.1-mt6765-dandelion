D="/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline"/data/dts/dts-r96.dts
echo "=== mmc1 pin group ==="
grep -n -A8 'mmc1-default-pins' "$D" | head -14
echo "=== i2c node statuses ==="
for n in 11007000 11008000 11009000 1100f000 11011000 1100d000 11016000; do
	echo -n "i2c@$n: "
	grep -A16 "i2c@$n {" "$D" | grep -m1 status
done
