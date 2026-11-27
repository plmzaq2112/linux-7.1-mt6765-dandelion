import os, subprocess

home = os.path.expanduser("~")
src = os.path.join(home, "r96-pwmbl.dts")
out = os.path.join(home, "r96-pwmbl2.dtb")

s = open(src).read()
if "0xf4240" not in s:
    raise SystemExit("period value not found")
s = s.replace("0xf4240", "0x186a0")   # 1 ms -> 100 us (10 kHz)
tmp = os.path.join(home, "r96-pwmbl2.dts")
open(tmp, "w").write(s)
subprocess.run(["dtc", "-I", "dts", "-O", "dtb", "-o", out, tmp], check=True)
print("dtb:", out, os.path.getsize(out))
d = subprocess.run(["dtc", "-I", "dtb", "-O", "dts", "-o", "/tmp/bl2.dts", out], capture_output=True)
print(subprocess.run(["grep", "-A4", "pwm-backlight", "/tmp/bl2.dts"], capture_output=True, text=True).stdout)
