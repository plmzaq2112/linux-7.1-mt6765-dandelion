/* SPDX-License-Identifier: GPL-2.0
 *
 * MediaTek 8365 audio driver common definitions
 *
 * Copyright (c) 2024 MediaTek Inc.
 * Authors: Jia Zeng <jia.zeng@mediatek.com>
 *          Alexandre Mergnat <amergnat@baylibre.com>
 */

#ifndef _MT6765_AFE_COMMON_H_
#define _MT6765_AFE_COMMON_H_

#include <linux/clk.h>
#include <linux/list.h>
#include <linux/regmap.h>
#include <sound/soc.h>
#include <sound/asound.h>
#include "../common/mtk-base-afe.h"
#include "mt6765-reg.h"

enum {
	MT6765_AFE_MEMIF_DL1,
	MT6765_AFE_MEMIF_DL2,
	MT6765_AFE_MEMIF_TDM_OUT,
	/*
	 * MT6765_AFE_MEMIF_SPDIF_OUT,
	 */
	MT6765_AFE_MEMIF_AWB,
	MT6765_AFE_MEMIF_VUL,
	MT6765_AFE_MEMIF_VUL2,
	MT6765_AFE_MEMIF_VUL3,
	MT6765_AFE_MEMIF_TDM_IN,
	/*
	 * MT6765_AFE_MEMIF_SPDIF_IN,
	 */
	MT6765_AFE_MEMIF_NUM,
	MT6765_AFE_BACKEND_BASE = MT6765_AFE_MEMIF_NUM,
	MT6765_AFE_IO_TDM_OUT = MT6765_AFE_BACKEND_BASE,
	MT6765_AFE_IO_TDM_IN,
	MT6765_AFE_IO_I2S,
	MT6765_AFE_IO_2ND_I2S,
	MT6765_AFE_IO_PCM1,
	MT6765_AFE_IO_VIRTUAL_DL_SRC,
	MT6765_AFE_IO_VIRTUAL_TDM_OUT_SRC,
	MT6765_AFE_IO_VIRTUAL_FM,
	MT6765_AFE_IO_DMIC,
	MT6765_AFE_IO_INT_ADDA,
	MT6765_AFE_IO_GASRC1,
	MT6765_AFE_IO_GASRC2,
	MT6765_AFE_IO_TDM_ASRC,
	MT6765_AFE_IO_HW_GAIN1,
	MT6765_AFE_IO_HW_GAIN2,
	MT6765_AFE_BACKEND_END,
	MT6765_AFE_BACKEND_NUM = (MT6765_AFE_BACKEND_END -
				  MT6765_AFE_BACKEND_BASE),
};

enum {
	MT6765_AFE_IRQ1,
	MT6765_AFE_IRQ2,
	MT6765_AFE_IRQ3,
	MT6765_AFE_IRQ4,
	MT6765_AFE_IRQ5,
	MT6765_AFE_IRQ6,
	MT6765_AFE_IRQ7,
	MT6765_AFE_IRQ8,
	MT6765_AFE_IRQ9,
	MT6765_AFE_IRQ10,
	MT6765_AFE_IRQ_NUM,
};

enum {
	MT6765_TOP_CG_AFE,
	MT6765_TOP_CG_I2S_IN,
	MT6765_TOP_CG_22M,
	MT6765_TOP_CG_24M,
	MT6765_TOP_CG_INTDIR_CK,
	MT6765_TOP_CG_APLL2_TUNER,
	MT6765_TOP_CG_APLL_TUNER,
	MT6765_TOP_CG_SPDIF,
	MT6765_TOP_CG_TDM_OUT,
	MT6765_TOP_CG_TDM_IN,
	MT6765_TOP_CG_ADC,
	MT6765_TOP_CG_DAC,
	MT6765_TOP_CG_DAC_PREDIS,
	MT6765_TOP_CG_TML,
	MT6765_TOP_CG_I2S1_BCLK,
	MT6765_TOP_CG_I2S2_BCLK,
	MT6765_TOP_CG_I2S3_BCLK,
	MT6765_TOP_CG_I2S4_BCLK,
	MT6765_TOP_CG_DMIC0_ADC,
	MT6765_TOP_CG_DMIC1_ADC,
	MT6765_TOP_CG_DMIC2_ADC,
	MT6765_TOP_CG_DMIC3_ADC,
	MT6765_TOP_CG_CONNSYS_I2S_ASRC,
	MT6765_TOP_CG_GENERAL1_ASRC,
	MT6765_TOP_CG_GENERAL2_ASRC,
	MT6765_TOP_CG_TDM_ASRC,
	MT6765_TOP_CG_NUM
};

enum {
	MT6765_CLK_TOP_AUD_SEL,
	MT6765_CLK_AUD_I2S0_M,
	MT6765_CLK_AUD_I2S1_M,
	MT6765_CLK_AUD_I2S2_M,
	MT6765_CLK_AUD_I2S3_M,
	MT6765_CLK_ENGEN1,
	MT6765_CLK_ENGEN2,
	MT6765_CLK_AUD1,
	MT6765_CLK_AUD2,
	MT6765_CLK_I2S0_M_SEL,
	MT6765_CLK_I2S1_M_SEL,
	MT6765_CLK_I2S2_M_SEL,
	MT6765_CLK_I2S3_M_SEL,
	MT6765_CLK_CLK26M,
	MT6765_CLK_AUD_AFE,
	MT6765_CLK_NUM
};

enum {
	MT6765_AFE_APLL1 = 0,
	MT6765_AFE_APLL2,
	MT6765_AFE_APLL_NUM,
};

enum {
	MT6765_AFE_1ST_I2S = 0,
	MT6765_AFE_2ND_I2S,
	MT6765_AFE_I2S_SETS,
};

enum {
	MT6765_AFE_I2S_SEPARATE_CLOCK = 0,
	MT6765_AFE_I2S_SHARED_CLOCK,
};

enum {
	MT6765_AFE_TDM_OUT_I2S = 0,
	MT6765_AFE_TDM_OUT_TDM,
	MT6765_AFE_TDM_OUT_I2S_32BITS,
};

enum mt6765_afe_tdm_ch_start {
	AFE_TDM_CH_START_O28_O29 = 0,
	AFE_TDM_CH_START_O30_O31,
	AFE_TDM_CH_START_O32_O33,
	AFE_TDM_CH_START_O34_O35,
	AFE_TDM_CH_ZERO,
};

enum {
	MT6765_PCM_FORMAT_I2S = 0,
	MT6765_PCM_FORMAT_EIAJ,
	MT6765_PCM_FORMAT_PCMA,
	MT6765_PCM_FORMAT_PCMB,
};

enum {
	MT6765_FS_8K = 0,
	MT6765_FS_11D025K,
	MT6765_FS_12K,
	MT6765_FS_384K,
	MT6765_FS_16K,
	MT6765_FS_22D05K,
	MT6765_FS_24K,
	MT6765_FS_130K,
	MT6765_FS_32K,
	MT6765_FS_44D1K,
	MT6765_FS_48K,
	MT6765_FS_88D2K,
	MT6765_FS_96K,
	MT6765_FS_176D4K,
	MT6765_FS_192K,
};

enum {
	FS_8000HZ  = 0, /* 0000b */
	FS_11025HZ = 1, /* 0001b */
	FS_12000HZ = 2, /* 0010b */
	FS_384000HZ = 3, /* 0011b */
	FS_16000HZ = 4, /* 0100b */
	FS_22050HZ = 5, /* 0101b */
	FS_24000HZ = 6, /* 0110b */
	FS_130000HZ = 7, /* 0111b */
	FS_32000HZ = 8, /* 1000b */
	FS_44100HZ = 9, /* 1001b */
	FS_48000HZ = 10, /* 1010b */
	FS_88200HZ = 11, /* 1011b */
	FS_96000HZ = 12, /* 1100b */
	FS_176400HZ = 13, /* 1101b */
	FS_192000HZ = 14, /* 1110b */
	FS_260000HZ = 15, /* 1111b */
};

enum {
	MT6765_AFE_DEBUGFS_AFE,
	MT6765_AFE_DEBUGFS_MEMIF,
	MT6765_AFE_DEBUGFS_IRQ,
	MT6765_AFE_DEBUGFS_CONN,
	MT6765_AFE_DEBUGFS_DBG,
	MT6765_AFE_DEBUGFS_NUM,
};

enum {
	MT6765_AFE_IRQ_DIR_MCU = 0,
	MT6765_AFE_IRQ_DIR_DSP,
	MT6765_AFE_IRQ_DIR_BOTH,
};

/* MCLK */
enum {
	MT6765_I2S0_MCK = 0,
	MT6765_I2S3_MCK,
	MT6765_MCK_NUM,
};

struct mt6765_fe_dai_data {
	bool use_sram;
	unsigned int sram_phy_addr;
	void __iomem *sram_vir_addr;
	unsigned int sram_size;
};

struct mt6765_be_dai_data {
	bool prepared[SNDRV_PCM_STREAM_LAST + 1];
	unsigned int fmt_mode;
};

#define MT6765_CLK_26M 26000000
#define MT6765_CLK_24M 24000000
#define MT6765_CLK_22M 22000000
#define MT6765_CM_UPDATA_CNT_SET 8

enum mt6765_cm_num {
	MT6765_CM1 = 0,
	MT6765_CM2,
	MT6765_CM_NUM,
};

enum mt6765_cm2_mux_in {
	MT6765_FROM_GASRC1 = 1,
	MT6765_FROM_GASRC2,
	MT6765_FROM_TDM_ASRC,
	MT6765_CM_MUX_NUM,
};

enum cm2_mux_conn_in {
	GENERAL2_ASRC_OUT_LCH = 0,
	GENERAL2_ASRC_OUT_RCH = 1,
	TDM_IN_CH0 = 2,
	TDM_IN_CH1 = 3,
	TDM_IN_CH2 = 4,
	TDM_IN_CH3 = 5,
	TDM_IN_CH4 = 6,
	TDM_IN_CH5 = 7,
	TDM_IN_CH6 = 8,
	TDM_IN_CH7 = 9,
	GENERAL1_ASRC_OUT_LCH = 10,
	GENERAL1_ASRC_OUT_RCH = 11,
	TDM_OUT_ASRC_CH0 = 12,
	TDM_OUT_ASRC_CH1 = 13,
	TDM_OUT_ASRC_CH2 = 14,
	TDM_OUT_ASRC_CH3 = 15,
	TDM_OUT_ASRC_CH4 = 16,
	TDM_OUT_ASRC_CH5 = 17,
	TDM_OUT_ASRC_CH6 = 18,
	TDM_OUT_ASRC_CH7 = 19
};

struct mt6765_cm_ctrl_reg {
	unsigned int con0;
	unsigned int con1;
	unsigned int con2;
	unsigned int con3;
	unsigned int con4;
};

struct mt6765_control_data {
	bool bypass_cm1;
	bool bypass_cm2;
	unsigned int loopback_type;
};

enum dmic_input_mode {
	DMIC_MODE_3P25M = 0,
	DMIC_MODE_1P625M,
	DMIC_MODE_812P5K,
	DMIC_MODE_406P25K,
};

enum iir_mode {
	IIR_MODE0 = 0,
	IIR_MODE1,
	IIR_MODE2,
	IIR_MODE3,
	IIR_MODE4,
	IIR_MODE5,
};

enum {
	MT6765_GASRC1 = 0,
	MT6765_GASRC2,
	MT6765_GASRC_NUM,
	MT6765_TDM_ASRC1 = MT6765_GASRC_NUM,
	MT6765_TDM_ASRC2,
	MT6765_TDM_ASRC3,
	MT6765_TDM_ASRC4,
	MT6765_TDM_ASRC_NUM,
};

struct mt6765_gasrc_ctrl_reg {
	unsigned int con0;
	unsigned int con2;
	unsigned int con3;
	unsigned int con4;
	unsigned int con5;
	unsigned int con6;
	unsigned int con9;
	unsigned int con10;
	unsigned int con12;
	unsigned int con13;
};

struct mt6765_gasrc_data {
	bool duplex;
	bool tx_mode;
	bool cali_on;
	bool tdm_asrc_out_cm2;
	bool iir_on;
};

struct mt6765_afe_private {
	struct clk *clocks[MT6765_CLK_NUM];
	struct regmap *topckgen;
	struct mt6765_fe_dai_data fe_data[MT6765_AFE_MEMIF_NUM];
	struct mt6765_be_dai_data be_data[MT6765_AFE_BACKEND_NUM];
	struct mt6765_control_data ctrl_data;
	struct mt6765_gasrc_data gasrc_data[MT6765_TDM_ASRC_NUM];
	int afe_on_ref_cnt;
	int top_cg_ref_cnt[MT6765_TOP_CG_NUM];
	void __iomem *afe_sram_vir_addr;
	unsigned int afe_sram_phy_addr;
	unsigned int afe_sram_size;
	/* locks */
	spinlock_t afe_ctrl_lock;
	struct mutex afe_clk_mutex;	/* Protect & sync APLL TUNER registers access*/
#ifdef CONFIG_DEBUG_FS
	struct dentry *debugfs_dentry[MT6765_AFE_DEBUGFS_NUM];
#endif
	int apll_tuner_ref_cnt[MT6765_AFE_APLL_NUM];
	unsigned int tdm_out_mode;
	unsigned int cm2_mux_input;

	/* dai */
	bool dai_on[MT6765_AFE_BACKEND_END];
	void *dai_priv[MT6765_AFE_BACKEND_END];
};

static inline u32 rx_frequency_palette(unsigned int fs)
{
	/* *
	 * A = (26M / fs) * 64
	 * B = 8125 / A
	 * return = DEC2HEX(B * 2^23)
	 */
	switch (fs) {
	case FS_8000HZ:		return 0x050000;
	case FS_11025HZ:	return 0x06E400;
	case FS_12000HZ:	return 0x078000;
	case FS_16000HZ:	return 0x0A0000;
	case FS_22050HZ:	return 0x0DC800;
	case FS_24000HZ:	return 0x0F0000;
	case FS_32000HZ:	return 0x140000;
	case FS_44100HZ:	return 0x1B9000;
	case FS_48000HZ:	return 0x1E0000;
	case FS_88200HZ:	return 0x372000;
	case FS_96000HZ:	return 0x3C0000;
	case FS_176400HZ:	return 0x6E4000;
	case FS_192000HZ:	return 0x780000;
	default:		return 0x0;
	}
}

static inline u32 AutoRstThHi(unsigned int fs)
{
	switch (fs) {
	case FS_8000HZ:		return 0x36000;
	case FS_11025HZ:	return 0x27000;
	case FS_12000HZ:	return 0x24000;
	case FS_16000HZ:	return 0x1B000;
	case FS_22050HZ:	return 0x14000;
	case FS_24000HZ:	return 0x12000;
	case FS_32000HZ:	return 0x0D800;
	case FS_44100HZ:	return 0x09D00;
	case FS_48000HZ:	return 0x08E00;
	case FS_88200HZ:	return 0x04E00;
	case FS_96000HZ:	return 0x04800;
	case FS_176400HZ:	return 0x02700;
	case FS_192000HZ:	return 0x02400;
	default:		return 0x0;
	}
}

static inline u32 AutoRstThLo(unsigned int fs)
{
	switch (fs) {
	case FS_8000HZ:		return 0x30000;
	case FS_11025HZ:	return 0x23000;
	case FS_12000HZ:	return 0x20000;
	case FS_16000HZ:	return 0x18000;
	case FS_22050HZ:	return 0x11000;
	case FS_24000HZ:	return 0x0FE00;
	case FS_32000HZ:	return 0x0BE00;
	case FS_44100HZ:	return 0x08A00;
	case FS_48000HZ:	return 0x07F00;
	case FS_88200HZ:	return 0x04500;
	case FS_96000HZ:	return 0x04000;
	case FS_176400HZ:	return 0x02300;
	case FS_192000HZ:	return 0x02000;
	default:		return 0x0;
	}
}

bool mt6765_afe_rate_supported(unsigned int rate, unsigned int id);
bool mt6765_afe_channel_supported(unsigned int channel, unsigned int id);

int mt6765_dai_i2s_register(struct mtk_base_afe *afe);
int mt6765_dai_set_priv(struct mtk_base_afe *afe,
			int id,
			int priv_size,
			const void *priv_data);

int mt6765_afe_fs_timing(unsigned int rate);

void mt6765_afe_set_i2s_out_enable(struct mtk_base_afe *afe, bool enable);
int mt6765_afe_set_i2s_out(struct mtk_base_afe *afe, unsigned int rate,	int bit_width);

int mt6765_dai_adda_register(struct mtk_base_afe *afe);
int mt6765_dai_enable_adda_on(struct mtk_base_afe *afe);
int mt6765_dai_disable_adda_on(struct mtk_base_afe *afe);

int mt6765_dai_dmic_register(struct mtk_base_afe *afe);

int mt6765_dai_pcm_register(struct mtk_base_afe *afe);

int mt6765_dai_tdm_register(struct mtk_base_afe *afe);

#endif
