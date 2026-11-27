#!/bin/sh
# Clean up the runtime test state left from the speaker investigation.
systemctl stop loapex 2>/dev/null
pkill -f wav_play 2>/dev/null
pkill -f alsa_test 2>/dev/null

rmmod ampen 2>/dev/null
rmmod regen 2>/dev/null
rmmod i2cgpio_dev 2>/dev/null
rmmod i2c-gpio 2>/dev/null
rmmod i2c-algo-bit 2>/dev/null

echo 1100f000.i2c > /sys/bus/platform/drivers/i2c-mt65xx/bind 2>/dev/null

systemctl restart dandelion-audio
sleep 1
echo "--- service ---"
systemctl is-active dandelion-audio
echo "--- card ---"
cat /proc/asound/cards
echo "--- i2c ---"
ls /dev/i2c-*
echo "--- module state ---"
lsmod | grep -E 'mt6765|snd_soc|i2c-gpio|ampen|regen' || true
