#!/bin/sh
K=$(uname -r)
M=/lib/modules/$K/extra/dandelion-audio
mkdir -p "$M" /usr/local/lib/dandelion-audio

# proper auto-load again: no blacklist
rm -f /etc/modprobe.d/dandelion-audio-blacklist.conf

cp /root/audio-modules-off/snd-soc-mtk-common.ko "$M"/
cp /root/audio/snd-soc-mt6765-pcm.ko "$M"/
cp /root/audio-modules-off/mt6765-mt6357.ko "$M"/
depmod -a "$K"

cp /root/audio/mixer3.py /usr/local/lib/dandelion-audio/
install -m 755 /root/audio/dandelion-audio-mixer.sh /usr/local/sbin/dandelion-audio-mixer.sh
install -m 644 /root/audio/dandelion-audio.service /etc/systemd/system/dandelion-audio.service
systemctl daemon-reload
systemctl enable dandelion-audio.service

echo "--- modules ---"
ls -l "$M"
echo "--- service ---"
systemctl cat dandelion-audio.service | head -15
sync
systemctl reboot
