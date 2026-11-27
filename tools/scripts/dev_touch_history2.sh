#!/bin/sh
for b in 0 -1 -2 -3 -4; do
    echo "=== boot $b kernel lines: $(journalctl -k -b $b --no-pager 2>/dev/null | wc -l)"
    journalctl -k -b $b --no-pager 2>/dev/null | grep -iE "fts_ts_probe|not focal IC|input: fts_ts" | tail -4
done
