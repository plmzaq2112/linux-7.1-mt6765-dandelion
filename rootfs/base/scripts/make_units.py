import os, tarfile

D = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/ubuntu"
S = os.path.join(D, "units")
os.makedirs(S, exist_ok=True)

unmark = """[Unit]
Description=Clear one-shot Ubuntu boot marker
DefaultDependencies=no
After=local-fs.target
Before=sysinit.target
Conflicts=shutdown.target

[Service]
Type=oneshot
ExecStart=/bin/rm -f /etc/dandelion-rootfs-ok

[Install]
WantedBy=sysinit.target
"""
open(os.path.join(S, "ubuntu-unmark.service"), "w").write(unmark)

mark = """[Unit]
Description=Confirm a successful Ubuntu boot
After=graphical.target
Wants=graphical.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c 'touch /etc/dandelion-rootfs-ok'

[Install]
WantedBy=graphical.target
"""
open(os.path.join(S, "ubuntu-mark.service"), "w").write(mark)

out = os.path.join(D, "units.tar.gz")
with tarfile.open(out, "w:gz") as t:
    for n in ("ubuntu-unmark.service", "ubuntu-mark.service"):
        t.add(os.path.join(S, n), arcname=n)
print("packed", out, os.path.getsize(out))
