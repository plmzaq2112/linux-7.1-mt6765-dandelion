#!/bin/sh
echo "=== regulators ==="
for r in /sys/class/regulator/*; do
    n=$(cat "$r/name" 2>/dev/null)
    st=$(cat "$r/state" 2>/dev/null)
    mv=$(cat "$r/microvolts" 2>/dev/null)
    echo "$(basename $r) $n state=$st uV=$mv"
done
