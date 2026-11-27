import os, shutil

D = os.path.expanduser("~/dandelion-ubuntu")
R = os.path.join(D, "rootfs")
ART = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/artifacts"

os.makedirs(os.path.join(R, "lib/firmware"), exist_ok=True)
os.makedirs(os.path.join(R, "lib/modules"), exist_ok=True)
os.makedirs(os.path.join(R, "etc/greetd"), exist_ok=True)
os.makedirs(os.path.join(R, "etc/systemd/system/multi-user.target.wants"), exist_ok=True)

# touch module + firmware
shutil.copyfile(os.path.join(ART, "focaltech_ts.ko"), os.path.join(R, "lib/modules/focaltech_ts.ko"))
fw = os.path.join(ART, "fw/focaltech_ab_ts_fw_helitai.bin")
if os.path.exists(fw):
    shutil.copyfile(fw, os.path.join(R, "lib/firmware/focaltech_ab_ts_fw_helitai.bin"))
    print("firmware copied")
else:
    print("WARN: touch firmware missing")

# focaltech module autoload unit
unit = """[Unit]
Description=Load FocalTech FT8006S touchscreen module
After=systemd-udevd.service
Before=greetd.service
DefaultDependencies=no

[Service]
Type=oneshot
ExecStart=/sbin/insmod /lib/modules/focaltech_ts.ko
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
"""
open(os.path.join(R, "etc/systemd/system/focaltech-touch.service"), "w").write(unit)
os.symlink("/etc/systemd/system/focaltech-touch.service",
           os.path.join(R, "etc/systemd/system/multi-user.target.wants/focaltech-touch.service"))

# greetd: autologin root -> phosh
gt = """[terminal]
vt = 1

[default_session]
command = "phosh"
user = "root"
"""
open(os.path.join(R, "etc/greetd/config.toml"), "w").write(gt)

print("prepared touch module, firmware, systemd unit, greetd config")
