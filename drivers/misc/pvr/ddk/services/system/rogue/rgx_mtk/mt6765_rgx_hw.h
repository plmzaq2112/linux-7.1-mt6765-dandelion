/* SPDX-License-Identifier: GPL-2.0 */
/*
 * Hardware-fact definitions for Redmi 9A (dandelion, MT6765 platform path)
 * PowerVR GE8320 / Rogue BVNC 22.87.104.18 (MIPS firmware).
 *
 * Single source of truth for addresses, offsets, masks and polarities.
 * FACTs: notes/hw-baseline.md, Redmi 9A.txt, GPU-PORT.md.
 */
#ifndef DANDELION_MT6765_RGX_HW_H
#define DANDELION_MT6765_RGX_HW_H

#include <linux/bits.h>
#include <linux/types.h>

/* --- Identity (FACT) --- */
#define RGX_CORE_ID_EXPECTED        0x08470000u
#define RGX_CORE_REV_EXPECTED       0x00680012u /* B=22 V=87 N=104 C=18 */
#define RGX_BVNC_B                  22u
#define RGX_BVNC_V                  87u
#define RGX_BVNC_N                  104u
#define RGX_BVNC_C                  18u

/* --- Physical windows (FACT) --- */
#define MTK_RGX_REG_BASE            0x13000000ul
#define MTK_RGX_REG_SIZE            0x80000ul
#define MTK_MFGCFG_BASE             0x13ffe000ul
#define MTK_MFGCFG_SIZE             0x1000ul
#define MTK_SPM_BASE                0x10006000ul
#define MTK_SPM_SIZE                0x1000ul
#define MTK_INFRACFG_AO_BASE        0x10001000ul
#define MTK_TOPAXI_PROTECTEN        0x220u

/* --- IRQ (FACT) --- */
#define MTK_RGX_SPI                 259u
#define MTK_RGX_LINUX_IRQ           204u

/* --- Clocks / CG (FACT) --- */
#define MTK_MFG_FREQ_HZ             390000000ul /* validated bring-up */
#define MTK_MFGCFG_CG_STA           0x00u
#define MTK_MFGCFG_CG_SET           0x04u /* write 1 -> gate off */
#define MTK_MFGCFG_CG_CLR           0x08u /* write 1 -> enable */
#define MTK_MFGCFG_CG_ALL           0x0fu

/* --- SPM power domains (FACT) --- */
#define SPM_PWR_STATUS              0x180u
#define SPM_PWR_STATUS_2ND          0x184u
#define SPM_PWR_MFG_ASYNC_CON       0x334u
#define SPM_PWR_MFG_CON             0x338u
#define SPM_PWR_MFG_CORE0_CON       0x34cu
#define SPM_PWR_MFG_BIT             BIT(4)
#define SPM_PWR_MFG_CORE0_BIT       BIT(7)
#define SPM_PWR_MFG_ASYNC_BIT       BIT(23)

/* --- MTCMOS / bus protect (FACT: vendor 4.19 clk-mt6765-pg.c) ---
 * Vendor power-on order (clk-mt6765-pg.c:3088-3091):
 *   mfg_async_pwr -> mfg_pwr -> mfg_bus_prot -> mfg_core0_pwr
 * Register bases: SPM = 0x10006000, INFRA = 0x10001000.
 */
#define MTK_INFRA_TOPAXI_PROTECTEN_SET   0x2A0u
#define MTK_INFRA_TOPAXI_PROTECTEN_CLR   0x2A4u
#define MTK_INFRA_TOPAXI_PROTECTEN_STA1  0x228u

/* clk-mt6765-pg.c:293-298 */
#define MTK_MFG_PROT_STEP1_0             BIT(25)
#define MTK_MFG_PROT_STEP2_0             (BIT(21) | BIT(22))

/* clk-mt6765-pg.c:132-136,341-343 (PWR_CON bits) */
#define MTK_MTCMOS_PWR_RST_B             BIT(0)
#define MTK_MTCMOS_PWR_ISO               BIT(1)
#define MTK_MTCMOS_PWR_ON                BIT(2)
#define MTK_MTCMOS_PWR_ON_2ND            BIT(3)
#define MTK_MTCMOS_PWR_CLK_DIS           BIT(4)
#define MTK_MTCMOS_SRAM_PDN              BIT(8)
#define MTK_MTCMOS_SRAM_PDN_ACK          BIT(12)

/* --- MTK HW APM (MFGCFG, FACT: residual vs vendor writes) --- */
#define MTK_APM_CTRL                0x24u
#define MTK_APM_CTRL_ENABLE_SEQ1    0x9004001bu
#define MTK_APM_CTRL_ENABLE_SEQ2    0x8004001bu

/* --- RGX core registers (FACT, subset) --- */
#define RGX_CR_CLK_CTRL             0x0000u
#define RGX_CR_CLK_STATUS           0x0008u
#define RGX_CR_CORE_ID              0x0018u
#define RGX_CR_CORE_REVISION        0x0020u
#define RGX_CR_SOFT_RESET           0x0100u
#define RGX_CR_MIPS_WRAPPER_CONFIG  0x0810u
#define RGX_CR_MIPS_IRQ_ENABLE      0x08A0u
#define RGX_CR_MIPS_IRQ_STATUS      0x08A8u
#define RGX_CR_MIPS_EXC_STATUS      0x08D0u
#define RGX_CR_META_BOOT            0x0BF8u /* unused on MIPS core (FACT) */
#define RGX_CR_MTS_SCHEDULE         0x0B00u /* MTS schedule doorbell */

/* MTS_SCHEDULE fields (FACT: hwdefs/rogue/km/rgx_cr_defs_km.h) */
#define RGX_MTS_DM_SHIFT            0u
#define RGX_MTS_DM_CLRMSK           0xFFFFFFF0u
#define RGX_MTS_DM_DM0              0x00000000u /* GP in native path maps here (FACT) */
#define RGX_MTS_TASK_SHIFT          4u
#define RGX_MTS_TASK_NON_COUNTED    0x00000000u
#define RGX_MTS_TASK_COUNTED        0x00000010u
#define RGX_MTS_CONTEXT_INTCTX      0x00000020u
#define RGX_MTS_HOST_HOST           0x00000100u

/* --- Firmware / memory layout (FACT) --- */
#define RGX_FW_VA_BASE              0xC0000000ull
#define RGX_FW_CODE_DEVVADDR        0xe1c0000000ull
#define RGX_FW_PAGE_SIZE            0x1000u
#define RGX_FW_DMA_MASK_BITS        32u

/* KCCB (FACT) */
#define RGX_KCCB_CMD_SIZE_BYTES     72u
#define RGX_KCCB_SLOT_COUNT         128u
#define RGX_KCCB_WRAP_MASK          127u

/* Shared FWs VA / host PA (runtime examples, FACT; allocation-dependent) */
#define RGX_FWVA_KCCB_CTL_EX        0xc0018880ull
#define RGX_FWVA_KCCB_CMD_EX        0xc001a000ull
#define RGX_FWVA_POW_SYNC_PRIM_EX   0xc0019000ull
#define RGX_FWVA_OSDATA_EX          0xc0018b00ull

/* MIPS exception healthy idle (FACT: MIUI/working state) */
#define RGX_MIPS_EXC_SLEEP          0x20u

#endif /* DANDELION_MT6765_RGX_HW_H */
