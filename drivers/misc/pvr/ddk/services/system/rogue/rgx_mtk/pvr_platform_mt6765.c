// SPDX-License-Identifier: GPL-2.0
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

/* GPU memory usage reporting hooks referenced by the DDK */
static unsigned int pvr_gpu_mem_usage(void)
{
	return 0;
}

static void pvr_gpu_mem_dump(void)
{
}

unsigned int (*mtk_get_gpu_memory_usage_fp)(void) = pvr_gpu_mem_usage;
void (*mtk_dump_gpu_memory_usage_fp)(void) = pvr_gpu_mem_dump;
