// SPDX-License-Identifier: GPL-2.0
/*
 * Stubs for the Xiaomi/MTK extras that are not needed on mainline:
 *  - mtkfb_lcm_name (vendor display driver global)
 *  - lct_tp_*  (Xiaomi touch info / gesture / selftest / proc)
 *  - fts_fw_recovery (firmware upgrade, disabled)
 */
#include <linux/types.h>
#include <linux/kernel.h>
#include "focaltech_core.h"

char mtkfb_lcm_name[256] = "ft8006s_vdo_hdp_boe_helitai_drv";
EXPORT_SYMBOL(mtkfb_lcm_name);

int fts_fw_recovery(void) { return 0; }

int init_lct_tp_info(char *tp_info_buf, char *tp_lockdown_info_buf) { return 0; }
void uninit_lct_tp_info(void) {}
void update_lct_tp_info(char *tp_info_buf, char *tp_lockdown_info_buf) {}
void set_lct_tp_info_callback(int (*pfun)(const char *)) {}
void uninit_lct_tp_gesture(void) {}
void set_lct_tp_gesture_status(bool en) {}
void lct_tp_selftest_init(void *callback) {}
bool get_lct_tp_work_status(void) { return false; }
int lct_create_procfs(struct fts_ts_data *ts_data) { return 0; }
int lct_remove_procfs(struct fts_ts_data *ts_data) { return 0; }
int lct_fts_set_charger_mode(bool en) { return 0; }
