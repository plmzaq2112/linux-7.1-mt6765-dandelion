// SPDX-License-Identifier: GPL-2.0
/*
 * Mainline platform layer for the vendor PowerVR DDK (MT6765 / dandelion).
 * Derived from m3's r101/r102 experiments: enable MFG clocks through the
 * 0x13FFE000 CG block (CLR register enables), then probe CORE_ID.
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
#include "mtk_mfg_mtcmos.h"

static struct clk *mfg_clk;
static struct clk *mfgpll_clk;
static struct regmap *mfgcfg_rm;
static void __iomem *gpu_regs;
static struct device *gpu_dev;


static int pvr_apm = 0;
module_param(pvr_apm, int, 0644);
MODULE_PARM_DESC(pvr_apm,
	"MTK HW APM: 0=off (default), 1=full (dust+0x24), 2=dust-only (0x504-0x528, no 0x24)");

static int pvr_rate_mhz = 390;
module_param(pvr_rate_mhz, int, 0644);
MODULE_PARM_DESC(pvr_rate_mhz, "MFG clock in MHz (default 390; FW runtime cfg says 400)");

static struct mtk_mfg_mtcmos g_mtcmos;

static int skip_mtcmos = 0;
module_param(skip_mtcmos, int, 0644);
MODULE_PARM_DESC(skip_mtcmos, "skip explicit MFG MTCMOS bring-up (A/B knob)");

static void pvr_mtk_init_apm(void)
{
	if (pvr_apm <= 0)
		return;
	static const struct { unsigned int off, val; } apm[] = {
		{ 0x504, 0x01a80000 }, { 0x508, 0x00080010 }, { 0x50c, 0x00100008 },
		{ 0x510, 0x00b800c8 }, { 0x514, 0x00b000c0 }, { 0x518, 0x00c000c8 },
		{ 0x51c, 0x00b000b8 }, { 0x520, 0x00d000d0 }, { 0x524, 0x00d000d0 },
		{ 0x528, 0x00d00000 },
	};
	unsigned int i;

	for (i = 0; i < ARRAY_SIZE(apm); i++)
		regmap_write(mfgcfg_rm, apm[i].off, apm[i].val);
	/* pvr_apm=2: dust-only (no 0x24 seq) for RASCALDUST A/B.
	 * pvr_apm=1: legacy full sequence (may power-gate MFG_CORE0).
	 */
	if (pvr_apm == 1) {
		regmap_write(mfgcfg_rm, 0x24, 0x9004001b);
		regmap_write(mfgcfg_rm, 0x24, 0x8004001b);
	}
}

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

	/* The MIPS firmware processor is 32-bit: keep its FW/CMA memory below 4GB */
	ret = dma_set_mask_and_coherent(dev, DMA_BIT_MASK(32));
	dev_info(dev, "pvr-mtk: dma_set_mask(32)=%d\n", ret);

	/* power domains are described in DT; make sure they are on */
	pm_runtime_enable(dev);
	ret = pm_runtime_get_sync(dev);
	dev_info(dev, "pvr-mtk: pm_runtime_get_sync=%d\n", ret);

	ret = clk_set_parent(mfg_clk, mfgpll_clk);
	dev_info(dev, "pvr-mtk: set_parent=%d\n", ret);
	ret = clk_set_rate(mfg_clk, (unsigned long)pvr_rate_mhz * 1000000UL);
	dev_info(dev, "pvr-mtk: set_rate=%d rate=%lu\n", ret, clk_get_rate(mfg_clk));

	ret = clk_prepare_enable(mfg_clk);
	dev_info(dev, "pvr-mtk: clk_enable=%d\n", ret);

	regmap_read(mfgcfg_rm, 0x0, &v0);
	regmap_read(mfgcfg_rm, 0x4, &v4);
	regmap_read(mfgcfg_rm, 0x8, &v8);
	dev_info(dev, "pvr-mtk: MFG_CFG 0x0=%08x 0x4=%08x 0x8=%08x\n", v0, v4, v8);

	pvr_mtk_init_apm();
	dev_info(dev, "pvr-mtk: APM mode=%d (%s)\n", pvr_apm,
		 pvr_apm == 1 ? "full" : (pvr_apm == 2 ? "dust-only" : "off"));

	/* CLR register: writing 1 enables the gated clocks */
	regmap_write(mfgcfg_rm, 0x8, 0xf);
	regmap_read(mfgcfg_rm, 0x8, &v8);
	dev_info(dev, "pvr-mtk: MFG_CFG 0x8 after CLR=%08x\n", v8);

	/* Explicit MFG MTCMOS (vendor clk-mt6765-pg.c order). A/B: skip_mtcmos=1 */
	if (!skip_mtcmos) {
		int mret = mtk_mfg_mtcmos_probe(dev, &g_mtcmos);

		if (mret == 0)
			mret = mtk_mfg_mtcmos_power_on(&g_mtcmos);
		if (mret)
			dev_err(dev, "pvr-mtk: MTCMOS bring-up failed (%d)\n", mret);
		else
			mtk_mfg_mtcmos_dump(&g_mtcmos, "post-on");
	} else {
		dev_info(dev, "pvr-mtk: MTCMOS skipped (skip_mtcmos=1)\n");
	}

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
	if (g_mtcmos.powered)
		mtk_mfg_mtcmos_power_off(&g_mtcmos);
	if (g_mtcmos.spm || g_mtcmos.infra)
		mtk_mfg_mtcmos_remove(&g_mtcmos);
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
	if (eCurrentPowerState == PVRSRV_DEV_POWER_STATE_OFF &&
	    eNewPowerState == PVRSRV_DEV_POWER_STATE_ON) {
		/* vendor order: clock -> CG -> APM, right before RGXStart */
		clk_prepare_enable(mfg_clk);
		if (!skip_mtcmos && g_mtcmos.spm && !g_mtcmos.powered)
			mtk_mfg_mtcmos_power_on(&g_mtcmos);
		if (mfgcfg_rm) {
			regmap_write(mfgcfg_rm, 0x8, 0xf);
			pvr_mtk_init_apm();
		}
		pr_info("pvr-mtk: PostPowerState ON (clk+CG+APM reapplied)\n");
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

/*
 * Debug helper: sample the SPM MTCMOS state at FW boot time.
 * MFG_CORE0 (bit 7 of PWR_STATUS) is the domain the MIPS lives in.
 */
void mtk_pvr_dump_spm(const char *tag)
{
	static void __iomem *spm;
	u32 st, st2, c0, mfg, async;

	if (!spm)
		spm = ioremap(0x10006000, 0x1000);
	if (!spm)
		return;

	st    = readl(spm + 0x180);
	st2   = readl(spm + 0x184);
	c0    = readl(spm + 0x34c);
	mfg   = readl(spm + 0x338);
	async = readl(spm + 0x334);

	pr_info("pvr-mtk[%s]: SPM st=%08x/2nd=%08x MFG=%d CORE0=%d ASYNC=%d CORE0_CON=%08x MFG_CON=%08x ASYNC_CON=%08x\n",
		tag, st, st2, !!(st & BIT(4)), !!(st & BIT(7)), !!(st & BIT(23)),
		c0, mfg, async);
}
