#!/bin/sh
for p in scp1 scp2 sspm_1; do
    echo "== $p"
    dd if=/dev/block/by-name/$p bs=1M status=none 2>/dev/null \
        | tr -c '[:print:]' '\n' | grep -iE 'sensor|als|proximity' | sort -u | head -12
    echo "-- size: $(blockdev --getsize64 /dev/block/by-name/$p 2>/dev/null)"
done
echo
echo "== super / partition table hints =="
ls /dev/block/by-name/ | wc -l
