import os

R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk"
S = os.path.join(R, "include/mtk_plat_stub")
os.makedirs(os.path.join(S, "mach"), exist_ok=True)

open(os.path.join(S, "ged_dvfs.h"), "w").write("""#ifndef __GED_DVFS_STUB_H
#define __GED_DVFS_STUB_H

typedef enum {
	GED_DVFS_COMMIT_NORMAL = 0,
	GED_DVFS_COMMIT_HARD = 1,
	GED_DVFS_COMMIT_SOFT = 2,
} GED_DVFS_COMMIT_TYPE;

#endif
""")

open(os.path.join(S, "ged_log.h"), "w").write("""#ifndef __GED_LOG_STUB_H
#define __GED_LOG_STUB_H
#endif
""")
open(os.path.join(S, "ged_base.h"), "w").write("""#ifndef __GED_BASE_STUB_H
#define __GED_BASE_STUB_H
#endif
""")
open(os.path.join(S, "mtk_gpufreq.h"), "w").write("""#ifndef __MTK_GPUFREQ_STUB_H
#define __MTK_GPUFREQ_STUB_H
#endif
""")
open(os.path.join(S, "mtk_boot.h"), "w").write("""#ifndef __MTK_BOOT_STUB_H
#define __MTK_BOOT_STUB_H
#endif
""")
open(os.path.join(S, "mtk_gpu_utility.h"), "w").write("""#ifndef __MTK_GPU_UTILITY_STUB_H
#define __MTK_GPU_UTILITY_STUB_H
#endif
""")
open(os.path.join(S, "mach/mtk_hibernate_dpm.h"), "w").write("""#ifndef __MTK_HIBERNATE_DPM_STUB_H
#define __MTK_HIBERNATE_DPM_STUB_H
#endif
""")
open(os.path.join(S, "mach/mt_irq.h"), "w").write("""#ifndef __MT_IRQ_STUB_H
#define __MT_IRQ_STUB_H
#endif
""")
open(os.path.join(S, "mach/irqs.h"), "w").write("""#ifndef __IRQS_STUB_H
#define __IRQS_STUB_H
#endif
""")

plat = os.path.join(R, "services/system/rogue/rgx_mtk/pvr_platform_mt6765.c")
open(plat, "w").write(r'''// SPDX-License-Identifier: GPL-2.0
/* Minimal mainline platform layer for the vendor PowerVR DDK (S1/S2 bring-up). */
#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/io.h>
#include <linux/clk.h>
#include <linux/of.h>

#include "mtk_mfgsys.h"
#include "sysconfig.h"

int MTKRGXDeviceInit(PVRSRV_DEVICE_CONFIG *psDevConfig)
{
	pr_info("pvr-mtk: MTKRGXDeviceInit %p\n", psDevConfig);
	return 0;
}

int MTKRGXDeviceDeInit(PVRSRV_DEVICE_CONFIG *psDevConfig)
{
	return 0;
}

PVRSRV_ERROR MTKDevPrePowerState(IMG_HANDLE hSysData,
				 PVRSRV_DEV_POWER_STATE eNewPowerState,
				 PVRSRV_DEV_POWER_STATE eCurrentPowerState,
				 IMG_BOOL bForced)
{
	return PVRSRV_OK;
}

PVRSRV_ERROR MTKDevPostPowerState(IMG_HANDLE hSysData,
				  PVRSRV_DEV_POWER_STATE eNewPowerState,
				  PVRSRV_DEV_POWER_STATE eCurrentPowerState,
				  IMG_BOOL bForced)
{
	return PVRSRV_OK;
}

PVRSRV_ERROR MTKSystemPrePowerState(PVRSRV_SYS_POWER_STATE eNewPowerState)
{
	return PVRSRV_OK;
}

PVRSRV_ERROR MTKSystemPostPowerState(PVRSRV_SYS_POWER_STATE eNewPowerState)
{
	return PVRSRV_OK;
}

PVRSRV_ERROR MTKMFGSystemInit(void)
{
	return PVRSRV_OK;
}

void MTKMFGSystemDeInit(void)
{
}

int mtk_mfg_async_init(void)
{
	return 0;
}

int mtk_mfg_2d_init(void)
{
	return 0;
}

void mtk_fdvfs_update_cur_freq(int ui32GPUFreq)
{
}

void MTKFWDump(void)
{
}

struct ion_client *MTKGetIonClient(void)
{
	return NULL;
}
''')
print("platform layer written")

# Makefile: swap objects and add stub include path
mp = os.path.join(R, "Makefile")
s = open(mp).read()
s = s.replace("services/system/rogue/rgx_mtk/$(MTK_PLATFORM)/mtk_mfgsys.o",
              "services/system/rogue/rgx_mtk/pvr_platform_mt6765.o")
s = s.replace("\tservices/system/rogue/rgx_mtk/ion_support.o \\\n", "")
if "mtk_plat_stub" not in s:
    s = s.replace("ccflags-y += -I$(RGX_TOP)/include/kernel_libc_compat",
                  "ccflags-y += -I$(RGX_TOP)/include/kernel_libc_compat\n"
                  "ccflags-y += -I$(RGX_TOP)/include/mtk_plat_stub", 1)
open(mp, "w").write(s)
print("Makefile updated")
