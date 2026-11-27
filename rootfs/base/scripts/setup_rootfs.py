import os, shutil, stat

W = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/ubuntu"
D = os.path.expanduser("~/dandelion-ubuntu")
R = os.path.join(D, "rootfs")

os.makedirs(D, exist_ok=True)

for f in ("enter.sh", "sources.list"):
    shutil.copyfile(os.path.join(W, f), os.path.join(D, f))

os.chmod(os.path.join(D, "enter.sh"), 0o755)

shutil.copyfile(os.path.join(D, "sources.list"), os.path.join(R, "etc/apt/sources.list"))

with open(os.path.join(R, "etc/apt/apt.conf.d/99sandbox"), "w") as f:
    f.write('APT::Sandbox::User "root";\nAPT::Get::Assume-Yes "true";\n')

shutil.copyfile("/etc/resolv.conf", os.path.join(R, "etc/resolv.conf"))

with open(os.path.join(R, "etc/hostname"), "w") as f:
    f.write("ubuntu-dandelion\n")
with open(os.path.join(R, "etc/hosts"), "w") as f:
    f.write("127.0.0.1 localhost\n127.0.1.1 ubuntu-dandelion\n")

print("rootfs configured")
print(os.listdir(D))
