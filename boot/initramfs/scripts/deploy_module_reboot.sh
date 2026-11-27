#!/bin/sh
K=$(uname -r)
M=/lib/modules/$K/extra/dandelion-audio
cp /root/audio/snd-soc-mt6765-pcm.ko "$M"/
depmod -a "$K"
sync
systemctl reboot
