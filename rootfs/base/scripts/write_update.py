import os
D = os.path.expanduser("~/dandelion-ubuntu")
R = os.path.join(D, "rootfs")
with open(os.path.join(R, "root/update.sh"), "w") as f:
    f.write("#!/bin/sh\nset -e\napt-get update\napt-cache policy phosh phoc squeekboard | head -30\necho UPDATE_OK\n")
print("update.sh written")
