#!/bin/sh
set -e
cp /usr/local/sbin/dandelion-audio-mixer.sh /root/dandelion-audio-mixer.sh.orig
cat /root/audio/dandelion-audio-mixer.sh > /usr/local/sbin/dandelion-audio-mixer.sh
chmod 755 /usr/local/sbin/dandelion-audio-mixer.sh
systemctl restart dandelion-audio
systemctl is-active dandelion-audio
echo "=== mixer after restart ==="
cd /root/audio
python3 mixer3.py vols | grep -iE 'lineout|handset'
python3 mixer3.py show "Line Out Source"
runuser -u dandelion -- env XDG_RUNTIME_DIR=/run/user/1000 wpctl get-volume @DEFAULT_AUDIO_SINK@
