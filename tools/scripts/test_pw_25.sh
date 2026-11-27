#!/bin/sh
cd /root/audio || exit 1
cp -f /root/audio/apex.wav /tmp/apex.wav
chmod 644 /tmp/apex.wav

# hardware LO at minimum, speaker route
python3 mixer3.py volset Lineout 0
python3 mixer3.py enum "Line Out Source" 2
python3 mixer3.py enum "Handset Source" 0
python3 mixer3.py enum "Headphone Left Source" 0
python3 mixer3.py enum "Headphone Right Source" 0

echo "=== sink status ==="
runuser -u dandelion -- env XDG_RUNTIME_DIR=/run/user/1000 wpctl status 2>&1 | head -18

echo "=== set 25% ==="
runuser -u dandelion -- env XDG_RUNTIME_DIR=/run/user/1000 wpctl set-volume @DEFAULT_AUDIO_SINK@ 0.25
runuser -u dandelion -- env XDG_RUNTIME_DIR=/run/user/1000 wpctl get-volume @DEFAULT_AUDIO_SINK@

echo "=== play 15s ==="
timeout 15 runuser -u dandelion -- env XDG_RUNTIME_DIR=/run/user/1000 pw-play /tmp/apex.wav
echo done
