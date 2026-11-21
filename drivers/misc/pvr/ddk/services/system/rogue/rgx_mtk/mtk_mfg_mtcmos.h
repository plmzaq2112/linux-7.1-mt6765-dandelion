/* SPDX-License-Identifier: GPL-2.0 */
/*
 * MT6765 MFG MTCMOS bring-up (rewritten from vendor clk-mt6765-pg.c).
 *
 * Why this exists: on the vendor 4.19 kernel the GPU is powered up by MTK's
 * MTCMOS driver (clk-mt6765-pg.c), not by the PowerVR DDK. Mainline's
 * mtk-pm-domains only handles SRAM PDN bits and does not run the MFG
 * bus-protect (TOPAXI) handshake, so the refactored stack makes the sequence
 * explicit here.
 *
 * FACT sources:
 *   drivers/clk/mediatek/clk-mt6765-pg.c:1335-1469  (mfg bus_prot / mfg pwr)
 *   drivers/clk/mediatek/clk-mt6765-pg.c:1703-1801  (mfg_core0 pwr)
 *   drivers/clk/mediatek/clk-mt6765-pg.c:1803-1870  (mfg_async pwr)
 *   drivers/clk/mediatek/clk-mt6765-pg.c:3088-3091  (power-on order)
 *
 * HYPOTHESIS: bounded timeouts (vendor waits forever) are safe; ACK bits are
 * the same ones the vendor polls.
 */
#ifndef DANDELION_MTK_MFG_MTCMOS_H
#define DANDELION_MTK_MFG_MTCMOS_H

#include <linux/device.h>
#include <linux/types.h>

struct mtk_mfg_mtcmos {
	struct device *dev;
	void __iomem *spm;   /* SPM 0x10006000 */
	void __iomem *infra; /* INFRACFG 0x10001000 */
	bool powered;
};

/* ioremap SPM/INFRA (no register writes). */
int mtk_mfg_mtcmos_probe(struct device *dev, struct mtk_mfg_mtcmos *m);

/* Unmap; does not touch hardware. */
void mtk_mfg_mtcmos_remove(struct mtk_mfg_mtcmos *m);

/*
 * Vendor power-on order: async -> mfg -> bus_prot(release) -> core0.
 * Idempotent: domains already on are still re-acked, bus protect is released.
 * Returns 0 on success, -ETIMEDOUT on a stuck ACK (registers are logged).
 */
int mtk_mfg_mtcmos_power_on(struct mtk_mfg_mtcmos *m);

/* Reverse order, used only when the driver is unloaded for A/B testing. */
int mtk_mfg_mtcmos_power_off(struct mtk_mfg_mtcmos *m);

/* Log PWR_STATUS / PWR_STATUS_2ND / PWR_CON / TOPAXI protect state. */
void mtk_mfg_mtcmos_dump(struct mtk_mfg_mtcmos *m, const char *tag);

#endif /* DANDELION_MTK_MFG_MTCMOS_H */
