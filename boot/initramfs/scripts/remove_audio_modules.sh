#!/bin/sh
K=$(uname -r)
mkdir -p /root/audio-modules-off
mv /lib/modules/$K/extra/dandelion-audio/*.ko /root/audio-modules-off/ 2>/dev/null
depmod -a "$K"
echo "remaining ko: $(ls /lib/modules/$K/extra/dandelion-audio/ 2>/dev/null | wc -l)"
sync
systemctl reboot
