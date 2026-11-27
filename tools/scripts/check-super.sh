echo "== super partition (p38) header =="
dd if=/dev/mmcblk0p38 bs=4 count=2 2>/dev/null | od -An -tx1
echo "== size =="
cat /sys/class/block/mmcblk0p38/size 2>/dev/null
echo "== p38 fstype (read-only probe) =="
blkid /dev/mmcblk0p38 2>/dev/null
