import os

D = os.path.expanduser("~/dandelion-ubuntu")
R = os.path.join(D, "rootfs")

os.makedirs(os.path.join(R, "root"), exist_ok=True)

with open(os.path.join(R, "root/test.sh"), "w") as f:
    f.write("#!/bin/sh\necho HELLO_FROM_GUEST\nuname -m\nid -u\n")
print("test.sh written")

build = """#!/bin/sh
set -e
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends \\
    phosh phoc squeekboard \\
    sudo openssh-server network-manager \\
    curl ca-certificates
apt-get clean
echo BUILD_OK
"""
with open(os.path.join(R, "root/build.sh"), "w") as f:
    f.write(build)
print("build.sh written")
