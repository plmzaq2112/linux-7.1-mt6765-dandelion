import os

D = os.path.expanduser("~/dandelion-ubuntu")
R = os.path.join(D, "rootfs")

p = os.path.join(R, "etc/greetd/config.toml")
with open(p, "w") as f:
    f.write("""[terminal]
vt = 1

[default_session]
command = "/usr/libexec/phosh"
user = "root"
""")
print(open(p).read())
