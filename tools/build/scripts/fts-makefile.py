p = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/input/touchscreen/ft8006s_spi/Makefile"
s = open(p).read()

# keep only our module aggregation, drop the per-object obj- lines
lines = []
for line in s.splitlines():
    if line.startswith("obj-$(CONFIG_TOUCHSCREEN_FTS)") and "+=" in line:
        continue
    lines.append(line)
s = "\n".join(lines)

s += """

# single combined module (multiple .o must be linked together)
focaltech_ts-y := focaltech_core.o focaltech_spi.o focaltech_ex_fun.o \\
                  focaltech_ex_mode.o focaltech_gesture.o focaltech_esdcheck.o \\
                  focaltech_point_report_check.o
obj-$(CONFIG_TOUCHSCREEN_FTS) += focaltech_ts.o
"""
open(p, "w").write(s)
print(open(p).read())
