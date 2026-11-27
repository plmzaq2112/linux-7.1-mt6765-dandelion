import re

p = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/scripts/init-busybox-r11.sh"
s = open(p, encoding="utf-8").read()

old = """			if mount -t ext4 /dev/$part /newroot 2>/dev/null; then
				msg "switching root to /dev/$part"
				umount /dev/shm 2>/dev/null
				umount /tmp 2>/dev/null
				mount --move /proc /newroot/proc
				mount --move /sys /newroot/sys
				mount --move /dev /newroot/dev
				exec switch_root /newroot /sbin/init
			fi"""
new = """			if mount -t ext4 /dev/$part /newroot 2>/dev/null; then
				msg "switching root to /dev/$part"
				echo "INIT: switching root to /dev/$part" > /newroot/dandelion-init.log
				ls -l /newroot/sbin/init /newroot/etc/inittab >> /newroot/dandelion-init.log 2>&1
				umount /dev/shm 2>/dev/null
				umount /tmp 2>/dev/null
				mount --move /proc /newroot/proc
				mount --move /sys /newroot/sys
				mount --move /dev /newroot/dev
				echo "INIT: exec switch_root" >> /newroot/dandelion-init.log
				exec switch_root /newroot /sbin/init
			fi"""
if "dandelion-init.log" not in s:
    assert old in s
    s = s.replace(old, new, 1)
    open(p, "w", encoding="utf-8").write(s)
    print("init patched")
else:
    print("already patched")
