p = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/input/touchscreen/ft8006s_spi/fts_stub.c"
s = open(p).read()
for line in [
    "int lct_create_procfs(struct fts_ts_data *ts_data) { return 0; }\n",
    "int lct_remove_procfs(struct fts_ts_data *ts_data) { return 0; }\n",
    "int lct_fts_set_charger_mode(bool en) { return 0; }\n",
]:
    s = s.replace(line, "")
open(p, "w").write(s)
print("removed duplicate stubs")
