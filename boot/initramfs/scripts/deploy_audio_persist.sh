#!/bin/sh
set -x
K=$(uname -r)
M=/lib/modules/$K/extra/dandelion-audio
mkdir -p "$M" /usr/local/lib/dandelion-audio
cp /root/audio/snd-soc-mtk-common.ko /root/audio/snd-soc-mt6765-pcm.ko /root/audio/mt6765-mt6357.ko "$M"/
depmod -a "$K"
cp /root/audio/mixer3.py /usr/local/lib/dandelion-audio/
install -m 755 /root/audio/dandelion-audio-init.sh /usr/local/sbin/dandelion-audio-init.sh
install -m 644 /root/audio/dandelion-audio.service /etc/systemd/system/dandelion-audio.service
systemctl daemon-reload
systemctl enable dandelion-audio.service
systemctl restart dandelion-audio.service
sleep 2
systemctl is-active dandelion-audio.service
ls -l "$M"
