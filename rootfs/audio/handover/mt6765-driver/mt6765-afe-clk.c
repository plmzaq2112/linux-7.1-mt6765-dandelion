// SPDX-License-Identifier: GPL-2.0
/*
 * MediaTek 8365 AFE clock control
 *
 * Copyright (c) 2024 MediaTek Inc.
 * Authors: Jia Zeng <jia.zeng@mediatek.com>
 *          Alexandre Mergnat <amergnat@baylibre.com>
 */

#include "mt6765-afe-clk.h"
#include "mt6765-afe-common.h"
#include "mt6765-reg.h"
#include "../common/mtk-base-afe.h"
#include <linux/device.h>
#include <linux/mfd/syscon.h>

static const char *aud_clks[MT6765_CLK_NUM] = {
	[MT6765_CLK_TOP_AUD_SEL] = "top_audio_sel",
	[MT6765_CLK_AUD_I2S0_M] = "audio_i2s0_m",
	[MT6765_CLK_AUD_I2S1_M] = "audio_i2s1_m",
	[MT6765_CLK_AUD_I2S2_M] = "audio_i2s2_m",
	[MT6765_CLK_AUD_I2S3_M] = "audio_i2s3_m",
	[MT6765_CLK_ENGEN1] = "engen1",
	[MT6765_CLK_ENGEN2] = "engen2",
	[MT6765_CLK_AUD1] = "aud1",
	[MT6765_CLK_AUD2] = "aud2",
	[MT6765_CLK_I2S0_M_SEL] = "i2s0_m_sel",
	[MT6765_CLK_I2S1_M_SEL] = "i2s1_m_sel",
	[MT6765_CLK_I2S2_M_SEL] = "i2s2_m_sel",
	[MT6765_CLK_I2S3_M_SEL] = "i2s3_m_sel",
	[MT6765_CLK_CLK26M] = "top_clk26m_clk",
	[MT6765_CLK_AUD_AFE] = "aud_afe",
};

int mt6765_afe_init_audio_clk(struct mtk_base_afe *afe)
{
	size_t i;
	struct mt6765_afe_private *afe_priv = afe->platform_priv;

	for (i = 0; i < ARRAY_SIZE(aud_clks); i++) {
		afe_priv->clocks[i] = devm_clk_get(afe->dev, aud_clks[i]);
		if (IS_ERR(afe_priv->clocks[i])) {
			dev_err(afe->dev, "%s devm_clk_get %s fail\n",
				__func__, aud_clks[i]);
			return PTR_ERR(afe_priv->clocks[i]);
		}
	}
	return 0;
}

void mt6765_afe_disable_clk(struct mtk_base_afe *afe, struct clk *clk)
{
	clk_disable_unprepare(clk);
}

int mt6765_afe_set_clk_rate(struct mtk_base_afe *afe, struct clk *clk,
			    unsigned int rate)
{
	int ret;

	if (clk) {
		ret = clk_set_rate(clk, rate);
		if (ret) {
			dev_err(afe->dev, "Failed to set rate\n");
			return ret;
		}
	}
	return 0;
}

int mt6765_afe_set_clk_parent(struct mtk_base_afe *afe, struct clk *clk,
			      struct clk *parent)
{
	int ret;

	if (clk && parent) {
		ret = clk_set_parent(clk, parent);
		if (ret) {
			dev_err(afe->dev, "Failed to set parent\n");
			return ret;
		}
	}
	return 0;
}

static unsigned int get_top_cg_reg(unsigned int cg_type)
{
	switch (cg_type) {
	case MT6765_TOP_CG_AFE:
	case MT6765_TOP_CG_I2S_IN:
	case MT6765_TOP_CG_22M:
	case MT6765_TOP_CG_24M:
	case MT6765_TOP_CG_INTDIR_CK:
	case MT6765_TOP_CG_APLL2_TUNER:
	case MT6765_TOP_CG_APLL_TUNER:
	case MT6765_TOP_CG_SPDIF:
	case MT6765_TOP_CG_TDM_OUT:
	case MT6765_TOP_CG_TDM_IN:
	case MT6765_TOP_CG_ADC:
	case MT6765_TOP_CG_DAC:
	case MT6765_TOP_CG_DAC_PREDIS:
	case MT6765_TOP_CG_TML:
		return AUDIO_TOP_CON0;
	case MT6765_TOP_CG_I2S1_BCLK:
	case MT6765_TOP_CG_I2S2_BCLK:
	case MT6765_TOP_CG_I2S3_BCLK:
	case MT6765_TOP_CG_I2S4_BCLK:
	case MT6765_TOP_CG_DMIC0_ADC:
	case MT6765_TOP_CG_DMIC1_ADC:
	case MT6765_TOP_CG_DMIC2_ADC:
	case MT6765_TOP_CG_DMIC3_ADC:
	case MT6765_TOP_CG_CONNSYS_I2S_ASRC:
	case MT6765_TOP_CG_GENERAL1_ASRC:
	case MT6765_TOP_CG_GENERAL2_ASRC:
	case MT6765_TOP_CG_TDM_ASRC:
		return AUDIO_TOP_CON1;
	default:
		return 0;
	}
}

static unsigned int get_top_cg_mask(unsigned int cg_type)
{
	switch (cg_type) {
	case MT6765_TOP_CG_AFE:
		return AUD_TCON0_PDN_AFE;
	case MT6765_TOP_CG_I2S_IN:
		return AUD_TCON0_PDN_I2S_IN;
	case MT6765_TOP_CG_22M:
		return AUD_TCON0_PDN_22M;
	case MT6765_TOP_CG_24M:
		return AUD_TCON0_PDN_24M;
	case MT6765_TOP_CG_INTDIR_CK:
		return AUD_TCON0_PDN_INTDIR;
	case MT6765_TOP_CG_APLL2_TUNER:
		return AUD_TCON0_PDN_APLL2_TUNER;
	case MT6765_TOP_CG_APLL_TUNER:
		return AUD_TCON0_PDN_APLL_TUNER;
	case MT6765_TOP_CG_SPDIF:
		return AUD_TCON0_PDN_SPDIF;
	case MT6765_TOP_CG_TDM_OUT:
		return AUD_TCON0_PDN_TDM_OUT;
	case MT6765_TOP_CG_TDM_IN:
		return AUD_TCON0_PDN_TDM_IN;
	case MT6765_TOP_CG_ADC:
		return AUD_TCON0_PDN_ADC;
	case MT6765_TOP_CG_DAC:
		return AUD_TCON0_PDN_DAC;
	case MT6765_TOP_CG_DAC_PREDIS:
		return AUD_TCON0_PDN_DAC_PREDIS;
	case MT6765_TOP_CG_TML:
		return AUD_TCON0_PDN_TML;
	case MT6765_TOP_CG_I2S1_BCLK:
		return AUD_TCON1_PDN_I2S1_BCLK;
	case MT6765_TOP_CG_I2S2_BCLK:
		return AUD_TCON1_PDN_I2S2_BCLK;
	case MT6765_TOP_CG_I2S3_BCLK:
		return AUD_TCON1_PDN_I2S3_BCLK;
	case MT6765_TOP_CG_I2S4_BCLK:
		return AUD_TCON1_PDN_I2S4_BCLK;
	case MT6765_TOP_CG_DMIC0_ADC:
		return AUD_TCON1_PDN_DMIC0_ADC;
	case MT6765_TOP_CG_DMIC1_ADC:
		return AUD_TCON1_PDN_DMIC1_ADC;
	case MT6765_TOP_CG_DMIC2_ADC:
		return AUD_TCON1_PDN_DMIC2_ADC;
	case MT6765_TOP_CG_DMIC3_ADC:
		return AUD_TCON1_PDN_DMIC3_ADC;
	case MT6765_TOP_CG_CONNSYS_I2S_ASRC:
		return AUD_TCON1_PDN_CONNSYS_I2S_ASRC;
	case MT6765_TOP_CG_GENERAL1_ASRC:
		return AUD_TCON1_PDN_GENERAL1_ASRC;
	case MT6765_TOP_CG_GENERAL2_ASRC:
		return AUD_TCON1_PDN_GENERAL2_ASRC;
	case MT6765_TOP_CG_TDM_ASRC:
		return AUD_TCON1_PDN_TDM_ASRC;
	default:
		return 0;
	}
}

static unsigned int get_top_cg_on_val(unsigned int cg_type)
{
	return 0;
}

static unsigned int get_top_cg_off_val(unsigned int cg_type)
{
	return get_top_cg_mask(cg_type);
}

int mt6765_afe_enable_top_cg(struct mtk_base_afe *afe, unsigned int cg_type)
{
	struct mt6765_afe_private *afe_priv = afe->platform_priv;
	unsigned int reg = get_top_cg_reg(cg_type);
	unsigned int mask = get_top_cg_mask(cg_type);
	unsigned int val = get_top_cg_on_val(cg_type);
	unsigned long flags;

	spin_lock_irqsave(&afe_priv->afe_ctrl_lock, flags);

	afe_priv->top_cg_ref_cnt[cg_type]++;
	if (afe_priv->top_cg_ref_cnt[cg_type] == 1)
		regmap_update_bits(afe->regmap, reg, mask, val);

	spin_unlock_irqrestore(&afe_priv->afe_ctrl_lock, flags);

	return 0;
}

int mt6765_afe_disable_top_cg(struct mtk_base_afe *afe, unsigned int cg_type)
{
	struct mt6765_afe_private *afe_priv = afe->platform_priv;
	unsigned int reg = get_top_cg_reg(cg_type);
	unsigned int mask = get_top_cg_mask(cg_type);
	unsigned int val = get_top_cg_off_val(cg_type);
	unsigned long flags;

	spin_lock_irqsave(&afe_priv->afe_ctrl_lock, flags);

	afe_priv->top_cg_ref_cnt[cg_type]--;
	if (afe_priv->top_cg_ref_cnt[cg_type] == 0)
		regmap_update_bits(afe->regmap, reg, mask, val);
	else if (afe_priv->top_cg_ref_cnt[cg_type] < 0)
		afe_priv->top_cg_ref_cnt[cg_type] = 0;

	spin_unlock_irqrestore(&afe_priv->afe_ctrl_lock, flags);

	return 0;
}

int mt6765_afe_enable_main_clk(struct mtk_base_afe *afe)
{
	struct mt6765_afe_private *afe_priv = afe->platform_priv;
	int ret;

	ret = clk_prepare_enable(afe_priv->clocks[MT6765_CLK_TOP_AUD_SEL]);
	if (ret)
		return ret;

	ret = clk_prepare_enable(afe_priv->clocks[MT6765_CLK_AUD_AFE]);
	if (ret) {
		clk_disable_unprepare(afe_priv->clocks[MT6765_CLK_TOP_AUD_SEL]);
		return ret;
	}

	mt6765_afe_enable_afe_on(afe);

	return 0;
}

int mt6765_afe_disable_main_clk(struct mtk_base_afe *afe)
{
	struct mt6765_afe_private *afe_priv = afe->platform_priv;

	mt6765_afe_disable_afe_on(afe);
	mt6765_afe_disable_clk(afe, afe_priv->clocks[MT6765_CLK_AUD_AFE]);
	mt6765_afe_disable_clk(afe, afe_priv->clocks[MT6765_CLK_TOP_AUD_SEL]);

	return 0;
}

int mt6765_afe_emi_clk_on(struct mtk_base_afe *afe)
{
	return 0;
}

int mt6765_afe_emi_clk_off(struct mtk_base_afe *afe)
{
	return 0;
}

int mt6765_afe_enable_afe_on(struct mtk_base_afe *afe)
{
	struct mt6765_afe_private *afe_priv = afe->platform_priv;
	unsigned long flags;

	spin_lock_irqsave(&afe_priv->afe_ctrl_lock, flags);

	afe_priv->afe_on_ref_cnt++;
	if (afe_priv->afe_on_ref_cnt == 1)
		regmap_update_bits(afe->regmap, AFE_DAC_CON0, 0x1, 0x1);

	spin_unlock_irqrestore(&afe_priv->afe_ctrl_lock, flags);

	return 0;
}

int mt6765_afe_disable_afe_on(struct mtk_base_afe *afe)
{
	struct mt6765_afe_private *afe_priv = afe->platform_priv;
	unsigned long flags;

	spin_lock_irqsave(&afe_priv->afe_ctrl_lock, flags);

	afe_priv->afe_on_ref_cnt--;
	if (afe_priv->afe_on_ref_cnt == 0)
		regmap_update_bits(afe->regmap, AFE_DAC_CON0, 0x1, 0x0);
	else if (afe_priv->afe_on_ref_cnt < 0)
		afe_priv->afe_on_ref_cnt = 0;

	spin_unlock_irqrestore(&afe_priv->afe_ctrl_lock, flags);

	return 0;
}

static int mt6765_afe_hd_engen_enable(struct mtk_base_afe *afe, bool apll1)
{
	if (apll1)
		regmap_update_bits(afe->regmap, AFE_HD_ENGEN_ENABLE,
				   AFE_22M_PLL_EN, AFE_22M_PLL_EN);
	else
		regmap_update_bits(afe->regmap, AFE_HD_ENGEN_ENABLE,
				   AFE_24M_PLL_EN, AFE_24M_PLL_EN);

	return 0;
}

static int mt6765_afe_hd_engen_disable(struct mtk_base_afe *afe, bool apll1)
{
	if (apll1)
		regmap_update_bits(afe->regmap, AFE_HD_ENGEN_ENABLE,
				   AFE_22M_PLL_EN, ~AFE_22M_PLL_EN);
	else
		regmap_update_bits(afe->regmap, AFE_HD_ENGEN_ENABLE,
				   AFE_24M_PLL_EN, ~AFE_24M_PLL_EN);

	return 0;
}

int mt6765_afe_enable_apll_tuner_cfg(struct mtk_base_afe *afe, unsigned int apll)
{
	struct mt6765_afe_private *afe_priv = afe->platform_priv;

	mutex_lock(&afe_priv->afe_clk_mutex);

	afe_priv->apll_tuner_ref_cnt[apll]++;
	if (afe_priv->apll_tuner_ref_cnt[apll] != 1) {
		mutex_unlock(&afe_priv->afe_clk_mutex);
		return 0;
	}

	if (apll == MT6765_AFE_APLL1) {
		regmap_update_bits(afe->regmap, AFE_APLL_TUNER_CFG,
				   AFE_APLL_TUNER_CFG_MASK, 0x432);
		regmap_update_bits(afe->regmap, AFE_APLL_TUNER_CFG,
				   AFE_APLL_TUNER_CFG_EN_MASK, 0x1);
	} else {
		regmap_update_bits(afe->regmap, AFE_APLL_TUNER_CFG1,
				   AFE_APLL_TUNER_CFG1_MASK, 0x434);
		regmap_update_bits(afe->regmap, AFE_APLL_TUNER_CFG1,
				   AFE_APLL_TUNER_CFG1_EN_MASK, 0x1);
	}

	mutex_unlock(&afe_priv->afe_clk_mutex);
	return 0;
}

int mt6765_afe_disable_apll_tuner_cfg(struct mtk_base_afe *afe, unsigned int apll)
{
	struct mt6765_afe_private *afe_priv = afe->platform_priv;

	mutex_lock(&afe_priv->afe_clk_mutex);

	afe_priv->apll_tuner_ref_cnt[apll]--;
	if (afe_priv->apll_tuner_ref_cnt[apll] == 0) {
		if (apll == MT6765_AFE_APLL1)
			regmap_update_bits(afe->regmap, AFE_APLL_TUNER_CFG,
					   AFE_APLL_TUNER_CFG_EN_MASK, 0x0);
		else
			regmap_update_bits(afe->regmap, AFE_APLL_TUNER_CFG1,
					   AFE_APLL_TUNER_CFG1_EN_MASK, 0x0);

	} else if (afe_priv->apll_tuner_ref_cnt[apll] < 0) {
		afe_priv->apll_tuner_ref_cnt[apll] = 0;
	}

	mutex_unlock(&afe_priv->afe_clk_mutex);
	return 0;
}

int mt6765_afe_enable_apll_associated_cfg(struct mtk_base_afe *afe, unsigned int apll)
{
	struct mt6765_afe_private *afe_priv = afe->platform_priv;
	int ret;

	if (apll == MT6765_AFE_APLL1) {
		ret = clk_prepare_enable(afe_priv->clocks[MT6765_CLK_ENGEN1]);
		if (ret) {
			dev_info(afe->dev, "%s Failed to enable ENGEN1 clk\n",
				 __func__);
			return ret;
		}
		mt6765_afe_enable_top_cg(afe, MT6765_TOP_CG_22M);
		mt6765_afe_hd_engen_enable(afe, true);
		mt6765_afe_enable_top_cg(afe, MT6765_TOP_CG_APLL_TUNER);
		mt6765_afe_enable_apll_tuner_cfg(afe, MT6765_AFE_APLL1);
	} else {
		ret = clk_prepare_enable(afe_priv->clocks[MT6765_CLK_ENGEN2]);
		if (ret) {
			dev_info(afe->dev, "%s Failed to enable ENGEN2 clk\n",
				 __func__);
			return ret;
		}
		mt6765_afe_enable_top_cg(afe, MT6765_TOP_CG_24M);
		mt6765_afe_hd_engen_enable(afe, false);
		mt6765_afe_enable_top_cg(afe, MT6765_TOP_CG_APLL2_TUNER);
		mt6765_afe_enable_apll_tuner_cfg(afe, MT6765_AFE_APLL2);
	}

	return 0;
}

int mt6765_afe_disable_apll_associated_cfg(struct mtk_base_afe *afe, unsigned int apll)
{
	struct mt6765_afe_private *afe_priv = afe->platform_priv;

	if (apll == MT6765_AFE_APLL1) {
		mt6765_afe_disable_apll_tuner_cfg(afe, MT6765_AFE_APLL1);
		mt6765_afe_disable_top_cg(afe, MT6765_TOP_CG_APLL_TUNER);
		mt6765_afe_hd_engen_disable(afe, true);
		mt6765_afe_disable_top_cg(afe, MT6765_TOP_CG_22M);
		clk_disable_unprepare(afe_priv->clocks[MT6765_CLK_ENGEN1]);
	} else {
		mt6765_afe_disable_apll_tuner_cfg(afe, MT6765_AFE_APLL2);
		mt6765_afe_disable_top_cg(afe, MT6765_TOP_CG_APLL2_TUNER);
		mt6765_afe_hd_engen_disable(afe, false);
		mt6765_afe_disable_top_cg(afe, MT6765_TOP_CG_24M);
		clk_disable_unprepare(afe_priv->clocks[MT6765_CLK_ENGEN2]);
	}

	return 0;
}
