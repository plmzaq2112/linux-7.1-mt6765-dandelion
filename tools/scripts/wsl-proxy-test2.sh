#!/bin/bash
WINIP=$(ip route | awk '/default/ {print $3}' | head -1)
echo "windows ip = $WINIP"
for p in 3128 10808; do
    code=$(curl -s -m 6 -x "http://$WINIP:$p" https://www.google.com -o /dev/null -w '%{http_code}' 2>/dev/null)
    echo "proxy $p -> $code"
done
