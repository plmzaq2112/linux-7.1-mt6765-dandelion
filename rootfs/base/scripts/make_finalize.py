import os

D = os.path.expanduser("~/dandelion-ubuntu")
R = os.path.join(D, "rootfs")

with open(os.path.join(R, "root/finalize.sh"), "w") as f:
    f.write(r"""#!/bin/sh
set -e
export DEBIAN_FRONTEND=noninteractive

# serial console fallback password
echo 'root:dandelion' | chpasswd

# greetd: autologin root -> phosh on tty1
mkdir -p /etc/greetd
cat > /etc/greetd/config.toml <<'EOF'
[terminal]
vt = 1

[default_session]
command = "phosh"
user = "root"
EOF

# services
systemctl enable greetd.service 2>/dev/null || true
systemctl enable focaltech-touch.service 2>/dev/null || true
systemctl enable ssh.service 2>/dev/null || true
systemctl enable systemd-timesyncd.service 2>/dev/null || true
systemctl set-default graphical.target 2>/dev/null || true

echo "== sessions"
ls /usr/share/wayland-sessions/ 2>/dev/null
echo "== enabled units"
ls /etc/systemd/system/multi-user.target.wants/ 2>/dev/null | head -12
echo "== touch unit"
cat /etc/systemd/system/focaltech-touch.service 2>/dev/null | head -6
echo FINALIZE_OK
""")
print("finalize.sh written")
