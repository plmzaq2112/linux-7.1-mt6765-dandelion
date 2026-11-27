#!/bin/sh
B=/dev/disk/by-partlabel/scp2
dd if="$B" bs=1M status=none 2>/dev/null | tr -c '[:print:]' '\n' > /tmp/scp.txt
echo "lines: $(wc -l < /tmp/scp.txt)"
echo
echo "== chip name candidates =="
grep -ioE 'stk[0-9a-z]{3,}|ltr[0-9a-z]{3,}|tmd[0-9a-z]{3,}|vcnl[0-9a-z]{3,}|isl[0-9]{4,}|ap3[0-9]{3,}|cm3[0-9]{4,}|epl[0-9]{3,}|rpr[0-9]{4,}|opt3[0-9]{3,}|veml[0-9]{4,}|tcs[0-9]{4,}|alsps[a-z0-9_]*|als[a-z0-9_]*' /tmp/scp.txt | sort | uniq -c | sort -rn | head -40
echo
echo "== lines containing ALS =="
grep -i 'als' /tmp/scp.txt | grep -viE 'false|also|als_' | sort -u | head -20
