import os
D = os.path.expanduser("~/dandelion-ubuntu")
R = os.path.join(D, "rootfs")
with open(os.path.join(R, "root/check.sh"), "w") as f:
    f.write("""#!/bin/sh
for p in phosh-osk-stub squeekboard greetd seatd gnome-terminal network-manager sudo openssh-server phosh-mobile-settings gnome-control-center; do
  printf "%-24s " "$p"
  apt-cache policy "$p" 2>/dev/null | awk '/Candidate:/ {print $2}'
done
echo CHECK_OK
""")
print("check.sh written")
