#!/bin/sh
set -e
KREL=$(uname -r)
mkdir -p /lib/modules/$KREL/extra /usr/local/bin
cp /root/audio/i2c-algo-bit.ko /root/audio/i2c-gpio.ko /lib/modules/$KREL/extra/ 2>/dev/null || true
depmod -a 2>/dev/null || true

cat > /etc/modules-load.d/i2c-gpio-sensors.conf <<'EOF'
i2c-algo-bit
i2c-gpio
EOF

cat > /etc/systemd/system/alsd.service <<'EOF'
[Unit]
Description=Ambient light auto brightness (dandelion ALS)
After=systemd-modules-load.service
Wants=systemd-modules-load.service

[Service]
Type=simple
ExecStart=/usr/local/bin/alsd.py
Restart=always
RestartSec=3
Nice=5

[Install]
WantedBy=multi-user.target
EOF

chmod +x /usr/local/bin/alsd.py
systemctl daemon-reload
systemctl enable alsd.service
echo installed
