for a in /sys/class/i2c-adapter/i2c-*; do
	echo "$a -> $(readlink $a/device 2>/dev/null)"
done
for d in /dev/i2c-*; do
	b=${d#/dev/i2c-}
	echo "== $d (bus $b)"
	i2cdetect -y $b 2>/dev/null | grep '^[0-9a-f]0:'
	echo -n "   0x34: "
	i2ctransfer -y $b w1@0x34 0x00 >/dev/null 2>&1 && echo ACK || echo NACK
done
