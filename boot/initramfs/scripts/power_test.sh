#!/bin/sh
echo "=== power supplies ==="
for d in /sys/class/power_supply/*; do
    echo "== $d"
    grep -E 'POWER_SUPPLY_(NAME|STATUS|VOLTAGE_NOW|CURRENT_NOW|CAPACITY|HEALTH|VOLTAGE_MIN_DESIGN|INPUT_CURRENT_LIMIT|CONSTANT_CHARGE_CURRENT|CHARGE_TYPE|ONLINE)' "$d/uevent"
done
echo "=== load test (4 busy loops, 12s) ==="
for i in 1 2 3 4; do timeout 12 yes > /dev/null & done
i=0
while [ $i -lt 20 ]; do
    i=$((i + 1))
    printf 't=%s ' "$i"
    for d in /sys/class/power_supply/*; do
        v=$(grep VOLTAGE_NOW "$d/uevent" | cut -d= -f2)
        c=$(grep CURRENT_NOW "$d/uevent" | cut -d= -f2)
        printf '%s:V=%s,I=%s ' "$(basename "$d")" "$v" "$c"
    done
    echo
    sleep 0.5
done
wait
echo "load test done"
