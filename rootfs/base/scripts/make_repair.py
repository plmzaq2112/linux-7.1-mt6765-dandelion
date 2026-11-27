import os

D = os.path.expanduser("~/dandelion-ubuntu")
R = os.path.join(D, "rootfs")

# remove the pre-created conffile that blocked dpkg
p = os.path.join(R, "etc/greetd/config.toml")
if os.path.exists(p):
    os.remove(p)
    print("removed pre-created greetd config.toml")

with open(os.path.join(R, "root/repair.sh"), "w") as f:
    f.write("""#!/bin/sh
set -e
export DEBIAN_FRONTEND=noninteractive
echo "== configure pending"
dpkg --configure -a || true
echo "== fix broken"
apt-get -f install -y -o Dpkg::Options::=--force-confnew || true
echo "== reconfigure greetd"
apt-get install -y -o Dpkg::Options::=--force-confnew greetd || true
echo "== status"
dpkg-query -W -f='${Package} ${Status}\\n' phosh phoc phosh-osk-stub greetd network-manager openssh-server 2>/dev/null | sed 's/install ok installed/OK/'
echo "== broken packages"
dpkg -l | awk '/^i[^i]/ {print $2, $1}' | head
echo REPAIR_DONE
""")
print("repair.sh written")
