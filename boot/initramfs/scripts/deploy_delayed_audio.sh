#!/bin/sh
K=$(uname -r)
M=/lib/modules/$K/extra/dandelion-audio
mkdir -p "$M"
cp /root/audio-modules-off/*.ko "$M"/ 2>/dev/null
depmod -a "$K"
install -m 644 /root/audio/dandelion-audio-blacklist.conf /etc/modprobe.d/dandelion-audio-blacklist.conf
install -m 644 /root/audio/dandelion-audio.service /etc/systemd/system/dandelion-audio.service
systemctl daemon-reload
systemctl enable dandelion-audio.service
echo "--- modules ---"
ls "$M"
echo "--- blacklist ---"
cat /etc/modprobe.d/dandelion-audio-blacklist.conf
sync
systemctl reboot
