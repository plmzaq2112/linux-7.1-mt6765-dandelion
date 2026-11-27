import os
D = os.path.expanduser("~/dandelion-ubuntu")
R = os.path.join(D, "rootfs")
with open(os.path.join(R, "root/install.sh"), "w") as f:
    f.write("""#!/bin/sh
set -e
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends \
    phosh phoc phosh-osk-stub phosh-mobile-settings \
    gnome-terminal network-manager sudo openssh-server \
    greetd seatd curl ca-certificates
apt-get clean
echo INSTALL_OK
""")
print("install.sh written")
