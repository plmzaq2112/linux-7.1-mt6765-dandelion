#!/bin/sh
set -e
KREL=$(uname -r)
mkdir -p /lib/modules/$KREL/extra
cp /root/audio/regulator-vibrator.ko /lib/modules/$KREL/extra/
depmod -a

echo regulator-vibrator > /etc/modules-load.d/regulator-vibrator.conf

cat > /etc/systemd/system/vibrator-perms.service <<'EOF'
[Unit]
Description=Allow desktop user to access the vibrator LED
After=systemd-modules-load.service
Wants=systemd-modules-load.service

[Service]
Type=oneshot
ExecStart=/bin/sh -c 'for f in activate state duration brightness; do [ -e /sys/class/leds/vibrator/$f ] && chgrp input /sys/class/leds/vibrator/$f && chmod 0660 /sys/class/leds/vibrator/$f; done'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

id -nG dandelion | grep -qw input || usermod -aG input dandelion

systemctl daemon-reload
systemctl enable --now vibrator-perms.service
systemctl is-enabled vibrator-perms.service
ls -l /sys/class/leds/vibrator/activate /sys/class/leds/vibrator/duration
id -nG dandelion
