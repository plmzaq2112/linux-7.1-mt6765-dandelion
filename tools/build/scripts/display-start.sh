#!/bin/sh
# Wait for the system to settle, then start the KMS player.
# Early modesets (~1-2 s) hang the DSI on this board, so delay first.
sleep 15
A=""
for f in /root/anim.kmsa /usr/local/share/anim.kmsa; do
	if [ -f "$f" ]; then A="$f"; break; fi
done
if [ -n "$A" ]; then
	exec /usr/local/bin/kms-loop /dev/dri/card1 "$A"
else
	exec /usr/local/bin/kms-loop /dev/dri/card1
fi
