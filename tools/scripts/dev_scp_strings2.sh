#!/bin/sh
B=/dev/disk/by-partlabel
for p in scp1 scp2 sspm_1 sspm_2; do
    [ -e "$B/$p" ] || { echo "== $p missing"; continue; }
    echo "== $p ($(blockdev --getsize64 "$B/$p" 2>/dev/null) bytes)"
    dd if="$B/$p" bs=1M status=none 2>/dev/null \
        | tr -c '[:print:]' '\n' | grep -iE 'sensor|als|proximity|light' | sort -u | head -12
done
echo
echo "== super =="
ls -l "$B/super" 2>/dev/null
blockdev --getsize64 "$B/super" 2>/dev/null
