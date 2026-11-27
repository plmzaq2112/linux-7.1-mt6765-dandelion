R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/input/touchscreen/ft8006s_spi"

# 1) flash.c: drop get_fs/set_fs (removed in 7.1)
p = R + "/focaltech_flash.c"
s = open(p).read()
s = s.replace("    mm_segment_t old_fs;\n", "")
s = s.replace("    old_fs = get_fs();\n    set_fs(KERNEL_DS);\n", "")
s = s.replace("    set_fs(old_fs);\n", "")
open(p, "w").write(s)
print("flash.c: set_fs removed")

# 2) Makefile: enable flash again
p = R + "/Makefile"
s = open(p).read()
s = s.replace("#obj-$(CONFIG_TOUCHSCREEN_FTS)\t+=  focaltech_flash.o",
              "")
if "focaltech_flash.o" not in s.split("focaltech_ts-y")[1] if "focaltech_ts-y" in s else True:
    pass
# add flash to combined module
s = s.replace("focaltech_point_report_check.o fts_stub.o",
              "focaltech_point_report_check.o focaltech_flash.o fts_stub.o")
open(p, "w").write(s)
print("Makefile: flash enabled")
