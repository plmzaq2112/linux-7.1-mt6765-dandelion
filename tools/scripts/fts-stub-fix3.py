p = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/input/touchscreen/ft8006s_spi/fts_stub.c"
s = open(p).read()
for line in [
    "int fts_fwupg_init(struct fts_ts_data *ts_data) { return 0; }\n",
    "int fts_fwupg_exit(struct fts_ts_data *ts_data) { return 0; }\n",
    "int fts_upgrade_bin(char *fw_name, bool force) { return 0; }\n",
    "int fts_enter_test_environment(bool test_state) { return 0; }\n",
    "int fts_fw_recovery(void) { return 0; }\n",
]:
    s = s.replace(line, "")
open(p, "w").write(s)
print("flash stubs removed")
