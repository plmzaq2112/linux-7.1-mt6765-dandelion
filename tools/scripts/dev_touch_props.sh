#!/bin/sh
B=/proc/device-tree/soc/spi@11013000
echo "=== children with compatible ==="
for d in "$B"/*/; do
    n=$(basename "$d")
    c=$(tr -d '\0' < "$d/compatible" 2>/dev/null | tr '\0' ' ')
    echo "$n : $c"
done

echo
echo "=== touch node full props ==="
for d in "$B"/*/; do
    c=$(tr -d '\0' < "$d/compatible" 2>/dev/null)
    case "$c" in
    *focal*|*fts*)
        echo "-- $d"
        for f in "$d"*; do
            [ -f "$f" ] || continue
            v=$(tr -d '\0' < "$f" 2>/dev/null | head -c 60)
            case "$v" in
            *[![:print:]]*) echo "   $(basename $f) = <bin>";;
            *) echo "   $(basename $f) = $v";;
            esac
        done
        ;;
    esac
done
