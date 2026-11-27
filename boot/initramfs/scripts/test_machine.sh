#!/bin/sh
# Load the machine driver in a detached subshell so the SSH command returns
# even if the card registration hangs.
cd /root/audio || exit 1
( insmod mt6765-mt6357.ko; echo $? > machine.rc ) > machine.log 2>&1 &
sleep 5
echo "--- rc:"
if [ -f machine.rc ]; then cat machine.rc; else echo "(still running)"; fi
echo "--- cards:"
cat /proc/asound/cards 2>/dev/null
echo "--- dmesg tail:"
dmesg | tail -50
