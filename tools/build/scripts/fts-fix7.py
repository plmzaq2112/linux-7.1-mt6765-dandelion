R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/input/touchscreen/ft8006s_spi"

# core.c: init_lct_tp_gesture stub uses tp_gesture_cb_t; declare loosely in stub
p = R + "/fts_stub.c"
s = open(p).read()
add = """
int fts_fwupg_init(struct fts_ts_data *ts_data) { return 0; }
int fts_fwupg_exit(struct fts_ts_data *ts_data) { return 0; }
int fts_upgrade_bin(char *fw_name, bool force) { return 0; }
int fts_enter_test_environment(bool test_state) { return 0; }
int init_lct_tp_gesture(tp_gesture_cb_t callback) { return 0; }
"""
if "fts_fwupg_init" not in s:
    s = s.rstrip("\n") + "\n" + add
open(p, "w").write(s)
print("stub extended")

# ex_fun.c: irq_to_desc removed in 7.1
p = R + "/focaltech_ex_fun.c"
s = open(p).read()
s = s.replace("""    ssize_t count = 0;
    struct irq_desc *desc = irq_to_desc(fts_data->irq);

    count = snprintf(buf, PAGE_SIZE, "irq_depth:%d\\n", desc->depth);""",
"""    ssize_t count = 0;

    count = snprintf(buf, PAGE_SIZE, "irq:%d\\n", fts_data->irq);""")
open(p, "w").write(s)
print("ex_fun irq_to_desc fixed")
