import os, subprocess

home = os.path.expanduser("~")
src = os.path.join(home, "r96-gpu.dts")
s = open(src).read()

old = "size = <0x02000000>;"
new = "size = <0x00 0x02000000>;"
assert old in s, "cma size line not found"
s = s.replace(old, new, 1)
open(src, "w").write(s)
print("cma size fixed to 2 cells")

out_dtb = os.path.join(home, "r96-gpu.dtb")
subprocess.run(["dtc", "-I", "dts", "-O", "dtb", "-o", out_dtb, src],
               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("dtb:", out_dtb, os.path.getsize(out_dtb))

chk = subprocess.run(["dtc", "-I", "dtb", "-O", "dts", "-o", "/tmp/cmachk2.dts", out_dtb],
                     capture_output=True, text=True)
print(subprocess.run(["grep", "-A10", "linux,cma", "/tmp/cmachk2.dts"],
                     capture_output=True, text=True).stdout)
