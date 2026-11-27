#!/bin/sh
K=$(uname -r)
M=/lib/modules/$K/extra/dandelion-audio
U="env XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus"

cp /root/audio/snd-soc-mt6765-pcm.ko "$M"/
sync

sudo -u dandelion $U systemctl --user stop wireplumber pipewire pipewire-pulse
sleep 1
rmmod mt6765_mt6357
rmmod snd_soc_mt6765_pcm
insmod "$M/snd-soc-mt6765-pcm.ko"
insmod "$M/mt6765-mt6357.ko"
sleep 1
sudo -u dandelion $U systemctl --user start pipewire pipewire-pulse wireplumber
sleep 2

cd /root/audio || exit 1
python3 mixer3.py set "O03 I05" 1
python3 mixer3.py set "INT ADDA O03_O04" 1
python3 mixer3.py volset Handset 100
python3 mixer3.py enum "Handset Source" 2
python3 mixer3.py set "Handset" 1
python3 alsa_test2.py hw:0,0 6 660 44100 s16
