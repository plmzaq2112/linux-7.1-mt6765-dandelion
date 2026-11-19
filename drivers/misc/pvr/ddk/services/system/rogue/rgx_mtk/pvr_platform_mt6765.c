// SPDX-License-Identifier: GPL-2.0
/*
 * Mainline platform layer for the vendor PowerVR DDK (MT6765 / dandelion).
 * Derived from m3's r101/r102 experiments: enable MFG clocks through the
 * 0x13FFE000 CG block (CLR register enables), then probe CORE_ID.
 */
#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/pm_runtime.h>
#include <linux/io.h>
#include <linux/clk.h>
#include <linux/of.h>
#include <linux/mfd/syscon.h>
#include <linux/regmap.h>

#include "mtk_mfgsys.h"
#include "sysconfig.h"

static struct clk *mfg_clk;
static struct clk *mfgpll_clk;
static struct regmap *mfgcfg_rm;
static void __iomem *gpu_regs;
static struct device *gpu_dev;

int MTKRGXDeviceInit(PVRSRV_DEVICE_CONFIG *psDevConfig)
{
	struct platform_device *pdev;
	struct device *dev;
	unsigned int v0 = 0, v4 = 0, v8 = 0;
	u32 core_id, core_rev;
	int ret;

	if (!psDevConfig || !psDevConfig->pvOSDevice)
		return -EINVAL;

	pdev = to_platform_device((struct device *)psDevConfig->pvOSDevice);
	dev = &pdev->dev;
	gpu_dev = dev;

	dev_info(dev, "pvr-mtk: init of_node=%pOF\n", dev->of_node);

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
	mfgpll_clk = devm_clk_get(dev, "mfgpll");
	if (IS_ERR(mfgpll_clk)) {
		dev_err(dev, "pvr-mtk: no mfgpll clock\n");
		return PTR_ERR(mfgpll_clk);
	}

	/* power domains are described in DT; make sure they are on */
	pm_runtime_enable(dev);
	ret = pm_runtime_get_sync(dev);
	dev_info(dev, "pvr-mtk: pm_runtime_get_sync=%d\n", ret);

	ret = clk_set_parent(mfg_clk, mfgpll_clk);
	dev_info(dev, "pvr-mtk: set_parent=%d\n", ret);
	ret = clk_set_rate(mfg_clk, 390000000);
	dev_info(dev, "pvr-mtk: set_rate=%d rate=%lu\n", ret, clk_get_rate(mfg_clk));

	ret = clk_prepare_enable(mfg_clk);
	dev_info(dev, "pvr-mtk: clk_enable=%d\n", ret);

	regmap_read(mfgcfg_rm, 0x0, &v0);
	regmap_read(mfgcfg_rm, 0x4, &v4);
	regmap_read(mfgcfg_rm, 0x8, &v8);
	dev_info(dev, "pvr-mtk: MFG_CFG 0x0=%08x 0x4=%08x 0x8=%08x\n", v0, v4, v8);

	/* CLR register: writing 1 enables the gated clocks */
	regmap_write(mfgcfg_rm, 0x8, 0xf);
	regmap_read(mfgcfg_rm, 0x8, &v8);
	dev_info(dev, "pvr-mtk: MFG_CFG 0x8 after CLR=%08x\n", v8);

	gpu_regs = devm_platform_ioremap_resource(pdev, 0);
	if (IS_ERR(gpu_regs)) {
		dev_err(dev, "pvr-mtk: ioremap failed\n");
		return PTR_ERR(gpu_regs);
	}

	core_id = readl(gpu_regs + 0x18);
	core_rev = readl(gpu_regs + 0x20);
	dev_info(dev, "pvr-mtk: RGX CORE_ID=%08x CORE_REVISION=%08x\n", core_id, core_rev);

	if (core_id == 0xffffffff || core_id == 0) {
		dev_err(dev, "pvr-mtk: GPU block not responding, giving up\n");
		clk_disable_unprepare(mfg_clk);
		return -ENODEV;
	}

	dev_info(dev, "pvr-mtk: GPU alive, continuing device creation\n");
	return 0;
}

int MTKRGXDeviceDeInit(PVRSRV_DEVICE_CONFIG *psDevConfig)
{
	if (mfg_clk && !IS_ERR(mfg_clk))
		clk_disable_unprepare(mfg_clk);
	pm_runtime_put_sync(gpu_dev);
	pm_runtime_disable(gpu_dev);
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

static unsigned int pvr_gpu_mem_usage(void)
{
	return 0;
}

static void pvr_gpu_mem_dump(void)
{
}

unsigned int (*mtk_get_gpu_memory_usage_fp)(void) = pvr_gpu_mem_usage;
void (*mtk_dump_gpu_memory_usage_fp)(void) = pvr_gpu_mem_dump;
