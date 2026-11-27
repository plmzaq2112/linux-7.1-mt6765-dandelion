for b in 0 1 2 3 4 5 6; do
	echo "== bus $b =="
	timeout 8 i2cdetect -y -r $b 2>/dev/null | tail -n +2
done
echo done
