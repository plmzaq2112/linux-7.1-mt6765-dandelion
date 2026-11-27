#!/bin/sh
KO=/root/audio/rail_en2.ko
RAILS="vcn18,vcn28,vldo28,vcamio,vcama,vcamd,vfe28,vcn33-bt,vcn33-wifi,vefuse,vrf18,vsim1,vsim2,vefuse"
echo "== baseline (no extra rails)"
timeout 200 python3 /root/audio/dev_probe_all.py

insmod "$KO" names=$RAILS || { echo "insmod failed"; exit 1; }
sleep 0.4
echo "== all candidate rails on"
timeout 200 python3 /root/audio/dev_probe_all.py
rmmod rail_en2
echo done
