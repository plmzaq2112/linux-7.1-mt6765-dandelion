import os

p = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/power/supply/bq256xx_charger.c")
s = open(p).read()

anchor = '\t{ .compatible = "ti,bq25601", .data = &bq256xx_chip_info_tbl[BQ25601] },'
add = '\n\t{ .compatible = "ti,bq2560x_charger", .data = &bq256xx_chip_info_tbl[BQ25601] },'

if "ti,bq2560x_charger" in s:
    print("already patched")
else:
    assert anchor in s, "anchor not found"
    s = s.replace(anchor, anchor + add, 1)
    open(p, "w").write(s)
    print("patched")
