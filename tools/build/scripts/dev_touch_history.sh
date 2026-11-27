#!/bin/sh
echo "=== pstore ==="
ls -l /sys/fs/pstore/ 2>/dev/null
for f in /sys/fs/pstore/*; do
    [ -f "$f" ] || continue
    echo "-- $f ($(wc -c < "$f") bytes)"
    grep -i "FTS_TS" "$f" 2>/dev/null | tail -12
done
echo
echo "=== journal previous boots: fts ==="
journalctl --list-boots --no-pager 2>/dev/null | tail -6
for b in -1 -2 -3; do
    echo "-- boot $b"
    journalctl -b $b --no-pager 2>/dev/null | grep -i "FTS_TS" | tail -6
done
