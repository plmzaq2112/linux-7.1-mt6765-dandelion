#!/bin/sh
set -e
groupadd -f i2c 2>/dev/null || true
usermod -aG i2c dandelion

cat > /etc/udev/rules.d/99-als-i2c.rules <<'EOF'
SUBSYSTEM=="i2c-dev", KERNEL=="i2c-8", GROUP="i2c", MODE="0660"
EOF
udevadm control --reload-rules || true
[ -e /dev/i2c-8 ] && chgrp i2c /dev/i2c-8 && chmod 0660 /dev/i2c-8 || true

cp /root/audio/alsd.py /usr/local/bin/alsd.py
chmod 0755 /usr/local/bin/alsd.py

cat > /etc/systemd/system/alsd.service <<'EOF'
[Unit]
Description=Ambient light auto brightness (dandelion ALS)
After=systemd-modules-load.service
Wants=systemd-modules-load.service

[Service]
Type=simple
User=dandelion
Environment=XDG_RUNTIME_DIR=/run/user/1000
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
Environment=ALS_BUS=8
ExecStart=/usr/local/bin/alsd.py
Restart=always
RestartSec=3
Nice=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable alsd.service
systemctl restart alsd.service
sleep 3
systemctl is-active alsd.service
journalctl -u alsd --no-pager -n 5 | tail -4
