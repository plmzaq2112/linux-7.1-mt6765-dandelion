// SPDX-License-Identifier: GPL-2.0
/*
 * Mainline platform layer for the vendor PowerVR DDK (MT6765 / dandelion).
 */
#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/pm_runtime.h>
#include <linux/dma-mapping.h>
#include <linux/io.h>
#include <linux/clk.h>
#include <linux/of.h>
#include <linux/mfd/syscon.h>
#include <linux/regmap.h>

#include "mtk_mfgsys.h"
#include "sysconfig.h"

static struct clk *mfg_clk;
static struct regmap *mfgcfg_rm;
static void __iomem *gpu_regs;
static struct device *gpu_dev;
static bool mfg_clk_enabled;

static int pvr_apm;
module_param(pvr_apm, int, 0644);
MODULE_PARM_DESC(pvr_apm,
	"MTK HW APM: 0=off (default), 1=full (dust+0x24), 2=dust-only (0x504-0x528)");

static int pvr_rate_mhz = 390;
module_param(pvr_rate_mhz, int, 0644);
MODULE_PARM_DESC(pvr_rate_mhz, "MFG clock in MHz (default 390)");

static void pvr_mtk_init_apm(void)
{
	static const struct { unsigned int off, val; } apm[] = {
		{ 0x504, 0x01a80000 }, { 0x508, 0x00080010 }, { 0x50c, 0x00100008 },
		{ 0x510, 0x00b800c8 }, { 0x514, 0x00b000c0 }, { 0x518, 0x00c000c8 },
		{ 0x51c, 0x00b000b8 }, { 0x520, 0x00d000d0 }, { 0x524, 0x00d000d0 },
		{ 0x528, 0x00d00000 },
	};
	unsigned int i;

	if (pvr_apm <= 0 || !mfgcfg_rm)
		return;

	for (i = 0; i < ARRAY_SIZE(apm); i++)
		regmap_write(mfgcfg_rm, apm[i].off, apm[i].val);

	if (pvr_apm == 1) {
		regmap_write(mfgcfg_rm, 0x24, 0x9004001b);
		regmap_write(mfgcfg_rm, 0x24, 0x8004001b);
	}
}

static int pvr_mtk_clk_enable(void)
{
	int ret = 0;

	if (!mfg_clk_enabled && mfg_clk && !IS_ERR(mfg_clk)) {
		ret = clk_prepare_enable(mfg_clk);
		if (ret)
			return ret;
		mfg_clk_enabled = true;
	}

	if (mfgcfg_rm) {
		/* CLR register: writing 1 enables the gated MFG clocks */
		regmap_write(mfgcfg_rm, 0x8, 0xf);
		pvr_mtk_init_apm();
	}

	return 0;
}

static void pvr_mtk_clk_disable(void)
{
	if (mfg_clk_enabled && mfg_clk && !IS_ERR(mfg_clk)) {
		clk_disable_unprepare(mfg_clk);
		mfg_clk_enabled = false;
	}
}

int MTKRGXDeviceInit(PVRSRV_DEVICE_CONFIG *psDevConfig)
{
	struct platform_device *pdev;
	struct device *dev;
	u32 core_id, core_rev;
	int ret;

	if (!psDevConfig || !psDevConfig->pvOSDevice)
		return -EINVAL;

	pdev = to_platform_device((struct device *)psDevConfig->pvOSDevice);
	dev = &pdev->dev;
	gpu_dev = dev;

	mfgcfg_rm = syscon_regmap_lookup_by_phandle(dev->of_node, "mediatek,mfgcfg");
	if (IS_ERR(mfgcfg_rm)) {
		dev_err(dev, "pvr-mtk: no mfgcfg syscon (%ld)\n", PTR_ERR(mfgcfg_rm));
		mfgcfg_rm = NULL;
		return -ENODEV;
	}

	mfg_clk = devm_clk_get(dev, "mfg");
	if (IS_ERR(mfg_clk)) {
		dev_err(dev, "pvr-mtk: no mfg clock\n");
		return PTR_ERR(mfg_clk);
	}

	/* The MIPS firmware processor is 32-bit: keep its FW/CMA memory below 4GB */
	ret = dma_set_mask_and_coherent(dev, DMA_BIT_MASK(32));
	if (ret)
		dev_warn(dev, "pvr-mtk: dma_set_mask(32) failed (%d)\n", ret);

	pm_runtime_enable(dev);
	ret = pm_runtime_get_sync(dev);
	if (ret < 0) {
		dev_err(dev, "pvr-mtk: pm_runtime_get_sync failed (%d)\n", ret);
		pm_runtime_put_noidle(dev);
		pm_runtime_disable(dev);
		return ret;
	}

	ret = clk_set_rate(mfg_clk, (unsigned long)pvr_rate_mhz * 1000000UL);
	if (ret)
		dev_warn(dev, "pvr-mtk: clk_set_rate failed (%d)\n", ret);

	ret = pvr_mtk_clk_enable();
	if (ret) {
		dev_err(dev, "pvr-mtk: clk_enable failed (%d)\n", ret);
		pm_runtime_put_sync(dev);
		pm_runtime_disable(dev);
		return ret;
	}

	gpu_regs = devm_platform_ioremap_resource(pdev, 0);
	if (IS_ERR(gpu_regs)) {
		dev_err(dev, "pvr-mtk: ioremap failed\n");
		pvr_mtk_clk_disable();
		pm_runtime_put_sync(dev);
		pm_runtime_disable(dev);
		return PTR_ERR(gpu_regs);
	}

	core_id = readl(gpu_regs + 0x18);
	core_rev = readl(gpu_regs + 0x20);
	dev_info(dev, "pvr-mtk: RGX CORE_ID=%08x CORE_REVISION=%08x rate=%lu\n",
		 core_id, core_rev, clk_get_rate(mfg_clk));

	if (core_id == 0xffffffff || core_id == 0) {
		dev_err(dev, "pvr-mtk: GPU block not responding\n");
		pvr_mtk_clk_disable();
		pm_runtime_put_sync(dev);
		pm_runtime_disable(dev);
		return -ENODEV;
	}

	return 0;
}

int MTKRGXDeviceDeInit(PVRSRV_DEVICE_CONFIG *psDevConfig)
{
	pvr_mtk_clk_disable();
	if (gpu_dev) {
		pm_runtime_put_sync(gpu_dev);
		pm_runtime_disable(gpu_dev);
	}
	return 0;
}

PVRSRV_ERROR MTKDevPrePowerState(IMG_HANDLE hSysData,
				 PVRSRV_DEV_POWER_STATE eNewPowerState,
				 PVRSRV_DEV_POWER_STATE eCurrentPowerState,
				 IMG_BOOL bForced)
{
	if (eCurrentPowerState == PVRSRV_DEV_POWER_STATE_ON &&
	    eNewPowerState == PVRSRV_DEV_POWER_STATE_OFF) {
		pvr_mtk_clk_disable();
	}
	return PVRSRV_OK;
}

PVRSRV_ERROR MTKDevPostPowerState(IMG_HANDLE hSysData,
				  PVRSRV_DEV_POWER_STATE eNewPowerState,
				  PVRSRV_DEV_POWER_STATE eCurrentPowerState,
				  IMG_BOOL bForced)
{
	if (eCurrentPowerState == PVRSRV_DEV_POWER_STATE_OFF &&
	    eNewPowerState == PVRSRV_DEV_POWER_STATE_ON) {
		if (pvr_mtk_clk_enable())
			return PVRSRV_ERROR_DEVICE_POWER_CHANGE_FAILURE;
	}
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

static unsigned int pvr_gpu_mem_usage(void)
{
	return 0;
}

static void pvr_gpu_mem_dump(void)
{
}

unsigned int (*mtk_get_gpu_memory_usage_fp)(void) = pvr_gpu_mem_usage;
void (*mtk_dump_gpu_memory_usage_fp)(void) = pvr_gpu_mem_dump;
