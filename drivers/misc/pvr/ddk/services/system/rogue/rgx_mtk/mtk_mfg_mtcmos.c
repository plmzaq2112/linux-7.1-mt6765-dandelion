// SPDX-License-Identifier: GPL-2.0
/*
 * MT6765 MFG MTCMOS bring-up (rewritten from vendor clk-mt6765-pg.c).
 * See mtk_mfg_mtcmos.h for the FACT references and ordering.
 */
#include <linux/io.h>
#include <linux/iopoll.h>
#include <linux/kernel.h>
#include <linux/module.h>

#include "mtk_mfg_mtcmos.h"
#include "mt6765_rgx_hw.h"

#define MTK_MTCMOS_POLL_US   100u
#define MTK_MTCMOS_TIMEOUT_US 100000u /* 100 ms, HYPOTHESIS: vendor waits forever */

static inline u32 spm_rd(struct mtk_mfg_mtcmos *m, u32 off)
{
	return readl(m->spm + off);
}

static inline void spm_wr(struct mtk_mfg_mtcmos *m, u32 off, u32 val)
{
	writel(val, m->spm + off);
	/* MTCMOS writes must be visible before the ACK poll (vendor uses mb()). */
	mb();
}

static int mtcmos_wait_mask(struct mtk_mfg_mtcmos *m, u32 off, u32 mask, bool set)
{
	u32 v;
	int ret;

	ret = readl_poll_timeout(m->spm + off, v, (!!(v & mask)) == set,
				 MTK_MTCMOS_POLL_US, MTK_MTCMOS_TIMEOUT_US);
	if (ret)
		dev_err(m->dev,
			"mtk-mtcmos: timeout waiting %s 0x%08x in SPM[%03x] (now %08x)\n",
			set ? "set" : "clear", mask, off, spm_rd(m, off));
	return ret;
}

static int mtcmos_domain_on(struct mtk_mfg_mtcmos *m, u32 con_off, u32 sta_mask,
			    bool clear_sram_pdn)
{
	u32 v;
	int ret;

	/* clk-mt6765-pg.c: PWR_ON -> PWR_ON_2ND -> wait status -> CLK_DIS/ISO/RST_B */
	spm_wr(m, con_off, spm_rd(m, con_off) |
			   MTK_MTCMOS_PWR_ON | MTK_MTCMOS_PWR_ON_2ND);

	ret = mtcmos_wait_mask(m, SPM_PWR_STATUS, sta_mask, true);
	if (ret)
		return ret;
	ret = mtcmos_wait_mask(m, SPM_PWR_STATUS_2ND, sta_mask, true);
	if (ret)
		return ret;

	v = spm_rd(m, con_off);
	v &= ~(MTK_MTCMOS_PWR_CLK_DIS | MTK_MTCMOS_PWR_ISO);
	v |= MTK_MTCMOS_PWR_RST_B;
	spm_wr(m, con_off, v);

	if (clear_sram_pdn) {
		spm_wr(m, con_off, spm_rd(m, con_off) & ~MTK_MTCMOS_SRAM_PDN);
		ret = mtcmos_wait_mask(m, con_off, MTK_MTCMOS_SRAM_PDN_ACK, false);
	}
	return ret;
}

static int mtcmos_domain_off(struct mtk_mfg_mtcmos *m, u32 con_off, u32 sta_mask,
			     bool set_sram_pdn)
{
	int ret;

	if (set_sram_pdn) {
		spm_wr(m, con_off, spm_rd(m, con_off) | MTK_MTCMOS_SRAM_PDN);
		ret = mtcmos_wait_mask(m, con_off, MTK_MTCMOS_SRAM_PDN_ACK, true);
		if (ret)
			return ret;
	}

	spm_wr(m, con_off, spm_rd(m, con_off) |
			   MTK_MTCMOS_PWR_ISO | MTK_MTCMOS_PWR_CLK_DIS);
	spm_wr(m, con_off, spm_rd(m, con_off) & ~MTK_MTCMOS_PWR_RST_B);
	spm_wr(m, con_off, spm_rd(m, con_off) & ~MTK_MTCMOS_PWR_ON);
	spm_wr(m, con_off, spm_rd(m, con_off) & ~MTK_MTCMOS_PWR_ON_2ND);

	ret = mtcmos_wait_mask(m, SPM_PWR_STATUS, sta_mask, false);
	if (ret)
		return ret;
	return mtcmos_wait_mask(m, SPM_PWR_STATUS_2ND, sta_mask, false);
}

/* clk-mt6765-pg.c:1335 spm_mtcmos_ctrl_mfg_bus_prot(STA_POWER_ON) */
static int mtcmos_mfg_bus_prot_on(struct mtk_mfg_mtcmos *m)
{
	int ret;

	spm_wr(m, SPM_PWR_MFG_CON, spm_rd(m, SPM_PWR_MFG_CON) & ~MTK_MTCMOS_SRAM_PDN);
	ret = mtcmos_wait_mask(m, SPM_PWR_MFG_CON, MTK_MTCMOS_SRAM_PDN_ACK, false);
	if (ret)
		return ret;

	writel(MTK_MFG_PROT_STEP2_0, m->infra + MTK_INFRA_TOPAXI_PROTECTEN_CLR);
	writel(MTK_MFG_PROT_STEP1_0, m->infra + MTK_INFRA_TOPAXI_PROTECTEN_CLR);
	mb(); /* vendor deliberately skips the release ACK check */
	return 0;
}

/* clk-mt6765-pg.c:1335 spm_mtcmos_ctrl_mfg_bus_prot(STA_POWER_DOWN) */
static int mtcmos_mfg_bus_prot_off(struct mtk_mfg_mtcmos *m)
{
	writel(MTK_MFG_PROT_STEP1_0, m->infra + MTK_INFRA_TOPAXI_PROTECTEN_SET);
	mb();

	/* Vendor polls STA1; do it explicitly with the same mask. */
	{
		u32 v;
		int r = readl_poll_timeout(m->infra + MTK_INFRA_TOPAXI_PROTECTEN_STA1, v,
					   (v & MTK_MFG_PROT_STEP1_0) == MTK_MFG_PROT_STEP1_0,
					   MTK_MTCMOS_POLL_US, MTK_MTCMOS_TIMEOUT_US);
		if (r) {
			dev_err(m->dev, "mtk-mtcmos: TOPAXI step1 ACK timeout (STA1=%08x)\n", v);
			return r;
		}
	}

	writel(MTK_MFG_PROT_STEP2_0, m->infra + MTK_INFRA_TOPAXI_PROTECTEN_SET);
	mb();
	{
		u32 v;
		int r = readl_poll_timeout(m->infra + MTK_INFRA_TOPAXI_PROTECTEN_STA1, v,
					   (v & MTK_MFG_PROT_STEP2_0) == MTK_MFG_PROT_STEP2_0,
					   MTK_MTCMOS_POLL_US, MTK_MTCMOS_TIMEOUT_US);
		if (r) {
			dev_err(m->dev, "mtk-mtcmos: TOPAXI step2 ACK timeout (STA1=%08x)\n", v);
			return r;
		}
	}

	spm_wr(m, SPM_PWR_MFG_CON, spm_rd(m, SPM_PWR_MFG_CON) | MTK_MTCMOS_SRAM_PDN);
	return mtcmos_wait_mask(m, SPM_PWR_MFG_CON, MTK_MTCMOS_SRAM_PDN_ACK, true);
}

int mtk_mfg_mtcmos_probe(struct device *dev, struct mtk_mfg_mtcmos *m)
{
	if (!dev || !m)
		return -EINVAL;

	memset(m, 0, sizeof(*m));
	m->dev = dev;

	m->spm = ioremap(MTK_SPM_BASE, MTK_SPM_SIZE);
	if (!m->spm) {
		dev_err(dev, "mtk-mtcmos: ioremap SPM failed\n");
		return -ENOMEM;
	}
	m->infra = ioremap(MTK_INFRACFG_AO_BASE, MTK_MFGCFG_SIZE);
	if (!m->infra) {
		dev_err(dev, "mtk-mtcmos: ioremap INFRA failed\n");
		iounmap(m->spm);
		m->spm = NULL;
		return -ENOMEM;
	}
	return 0;
}

void mtk_mfg_mtcmos_remove(struct mtk_mfg_mtcmos *m)
{
	if (!m)
		return;
	if (m->infra)
		iounmap(m->infra);
	if (m->spm)
		iounmap(m->spm);
	m->infra = NULL;
	m->spm = NULL;
}

int mtk_mfg_mtcmos_power_on(struct mtk_mfg_mtcmos *m)
{
	int ret;

	if (!m || !m->spm || !m->infra)
		return -EINVAL;

	/* clk-mt6765-pg.c:3088-3091 order */
	ret = mtcmos_domain_on(m, SPM_PWR_MFG_ASYNC_CON, SPM_PWR_MFG_ASYNC_BIT, false);
	if (ret)
		goto err;
	ret = mtcmos_domain_on(m, SPM_PWR_MFG_CON, SPM_PWR_MFG_BIT, false);
	if (ret)
		goto err;
	ret = mtcmos_mfg_bus_prot_on(m);
	if (ret)
		goto err;
	ret = mtcmos_domain_on(m, SPM_PWR_MFG_CORE0_CON, SPM_PWR_MFG_CORE0_BIT, true);
	if (ret)
		goto err;

	m->powered = true;
	return 0;
err:
	mtk_mfg_mtcmos_dump(m, "power-on-failed");
	return ret;
}

int mtk_mfg_mtcmos_power_off(struct mtk_mfg_mtcmos *m)
{
	int ret;

	if (!m || !m->spm || !m->infra)
		return -EINVAL;

	/* reverse of the vendor on-order */
	ret = mtcmos_domain_off(m, SPM_PWR_MFG_CORE0_CON, SPM_PWR_MFG_CORE0_BIT, true);
	if (ret)
		goto err;
	ret = mtcmos_mfg_bus_prot_off(m);
	if (ret)
		goto err;
	ret = mtcmos_domain_off(m, SPM_PWR_MFG_CON, SPM_PWR_MFG_BIT, false);
	if (ret)
		goto err;
	ret = mtcmos_domain_off(m, SPM_PWR_MFG_ASYNC_CON, SPM_PWR_MFG_ASYNC_BIT, false);
	if (ret)
		goto err;

	m->powered = false;
	return 0;
err:
	mtk_mfg_mtcmos_dump(m, "power-off-failed");
	return ret;
}

void mtk_mfg_mtcmos_dump(struct mtk_mfg_mtcmos *m, const char *tag)
{
	u32 st, st2, async, mfg, core0, prot, sta1;

	if (!m || !m->spm || !m->infra)
		return;

	st    = spm_rd(m, SPM_PWR_STATUS);
	st2   = spm_rd(m, SPM_PWR_STATUS_2ND);
	async = spm_rd(m, SPM_PWR_MFG_ASYNC_CON);
	mfg   = spm_rd(m, SPM_PWR_MFG_CON);
	core0 = spm_rd(m, SPM_PWR_MFG_CORE0_CON);
	prot  = readl(m->infra + MTK_TOPAXI_PROTECTEN);
	sta1  = readl(m->infra + MTK_INFRA_TOPAXI_PROTECTEN_STA1);

	dev_info(m->dev,
		 "mtk-mtcmos[%s]: ST=%08x/2nd=%08x MFG=%d CORE0=%d ASYNC=%d "
		 "ASYNC_CON=%08x MFG_CON=%08x CORE0_CON=%08x TOPAXI=%08x STA1=%08x\n",
		 tag ? tag : "-", st, st2, !!(st & SPM_PWR_MFG_BIT),
		 !!(st & SPM_PWR_MFG_CORE0_BIT), !!(st & SPM_PWR_MFG_ASYNC_BIT),
		 async, mfg, core0, prot, sta1);
}
