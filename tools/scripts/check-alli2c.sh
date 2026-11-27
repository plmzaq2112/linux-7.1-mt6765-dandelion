dtc -I dtb -O dts -o /tmp/chk.dts "$HOME/r96-alli2c.dtb" 2>/dev/null
echo "=== i2c statuses ==="
for n in 11007000 11008000 11009000 1100f000 11011000 11016000 1100d000; do
	echo -n "i2c@$n: "
	grep -A20 "i2c@$n {" /tmp/chk.dts | grep -m1 status
done
echo "=== pinctrl refs ==="
grep -c "pinctrl-0 = <0x" /tmp/chk.dts
echo "=== pin groups ==="
grep -n "i2c[0-6]-pins" /tmp/chk.dts | head
