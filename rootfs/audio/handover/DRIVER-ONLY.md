# MT6765 AFE 驱动（接手说明）

> 这是从 `sound/soc/mediatek/mt8365/` 克隆改造的 **MT6765 AFE 驱动**，用于 Redmi 9A（dandelion / MT6762G）+ MT6357 codec 的内置音频。
> 目前已能编译、AFE 能 probe（注册 15 个 DAI），但在 ASoC card 注册阶段 **挂死**。

---

## 1. 文件

`mt6765-driver/` 即为 `sound/soc/mediatek/mt6765/` 的完整内容：

```
Makefile
mt6765-afe-clk.c / .h
mt6765-afe-common.h
mt6765-afe-pcm.c        ← 主要改动（syscon regmap）
mt6765-dai-adda.c
mt6765-dai-dmic.c
mt6765-dai-i2s.c
mt6765-dai-pcm.c
mt6765-mt6357.c         ← machine 驱动（pinctrl 已改为可选）
mt6765-reg.h
```

放入内核树的位置：`sound/soc/mediatek/mt6765/`

### 需要配套的非驱动改动

1. `sound/soc/mediatek/Kconfig` 增加：

```
config SND_SOC_MT6765
	tristate "ASoC support for MediaTek MT6765 chip"
	depends on ARCH_MEDIATEK || COMPILE_TEST
	select SND_SOC_MEDIATEK
	help
	  This adds ASoC platform driver support for MediaTek MT6765 chip
	  that can be used with other codecs.

config SND_SOC_MT6765_MT6357
	tristate "ASoC audio driver for MT6765 with MT6357 codec"
	depends on SND_SOC_MT6765 && MTK_PMIC_WRAP
	select SND_SOC_MT6357
	help
	  This adds support for ASoC machine driver for MediaTek MT6765
	  boards with the MT6357 PMIC codec.
```

2. `sound/soc/mediatek/Makefile` 增加：

```
obj-$(CONFIG_SND_SOC_MT6765) += mt6765/
```

3. `drivers/clk/mediatek/clk-mt6765-audio.c`：probe 里增加
   `devm_of_platform_populate(&pdev->dev);`（模仿 mt8183，否则 AFE 子节点不会实例化）。

4. 内核配置：

```
CONFIG_SOUND=y
CONFIG_SND=y
CONFIG_SND_SOC=y
CONFIG_SND_SOC_MT6357=y
CONFIG_SND_SOC_MT6765=y
CONFIG_SND_SOC_MT6765_MT6357=y
```

---

## 2. DT 节点（必需）

```dts
/* audsys 时钟控制器下（0x11220000），afe 作为子节点 */
audio: clock-controller@11220000 {
    compatible = "mediatek,mt6765-audsys", "syscon";
    reg = <0 0x11220000 0 0x1000>;
    #clock-cells = <1>;

    afe: audio-controller {
        compatible = "mediatek,mt6765-afe-pcm";
        interrupts = <GIC_SPI 153 IRQ_TYPE_LEVEL_LOW>;
        #sound-dai-cells = <0>;
        clocks = <&clk26m>, <&topckgen 111>, <&audio 7>, <&audio 8>,
                 <&audio 9>, <&audio 10>, <&topckgen 64>, <&topckgen 64>,
                 <&topckgen 63>, <&topckgen 63>,
                 <&topckgen 78>, <&topckgen 79>, <&topckgen 80>, <&topckgen 81>, <&audio 0>;
        clock-names = "top_clk26m_clk", "top_audio_sel",
                      "audio_i2s0_m", "audio_i2s1_m", "audio_i2s2_m", "audio_i2s3_m",
                      "engen1", "engen2", "aud1", "aud2",
                      "i2s0_m_sel", "i2s1_m_sel", "i2s2_m_sel", "i2s3_m_sel", "aud_afe";
        status = "okay";
    };
};

/* PMIC 下（MT6357） */
pmic {
    audio-codec {
        compatible = "mediatek,mt6357-sound";
        vaud28-supply = <&mt6357_vaud28_reg>;
    };
};

/* 根节点 */
sound {
    compatible = "mediatek,mt6765-mt6357";
    mediatek,platform = <&afe>;
};
```

时钟编号（`include/dt-bindings/clock/mt6765-clk.h`）：

```
CLK_TOP_AUDIO_SEL=111, CLK_TOP_AUD_1_SEL=113, CLK_TOP_AUD_ENGEN1_SEL=114
CLK_TOP_AUDIO=62, CLK_TOP_AUD_1=63, CLK_TOP_AUD_ENGEN1=64
audsys: CLK_AUDIO_AFE=0, 22M=1, APLL_TUNER=2, ADC=3, DAC=4, DAC_PREDIS=5,
        TML=6, I2S1_BCLK=7, I2S2_BCLK=8, I2S3_BCLK=9, I2S4_BCLK=10
```

> **MT6765 只有 APLL1**，没有 APLL2 / engen2 / aud2 / i2s*_m（master clock）。
> 当前映射里 engen2/aud2 复用 engen1/aud1，audio_i2s*_m 用 audsys 的 I2S BCLK 门控代替——这是**猜测**，也是重点怀疑对象。

---

## 3. 已做的关键改动

1. **Clocked AFE regmap** (`mt6765-afe-pcm.c`): the AFE maps the parent AUDSYS resource with `devm_regmap_init_mmio_clk(..., "aud_afe", ...)`. This lets regmap acquire the CCF AFE gate for every access, including ASoC control callbacks. The main clock helper also holds `top_audio_sel` and `aud_afe` across multi-register sequences.
2. **machine 驱动 pinctrl 可选**（`mt6765-mt6357.c`）：
   DT 没有音频 pinctrl 状态，缺失时跳过而不是 -ENODEV。

3. AFE 子节点实例化依赖 `clk-mt6765-audio.c` 里的 `devm_of_platform_populate()`。

---

## 3.1 AFE clock gate correction (2026-11-22)

The earlier attempt to hold `mt6765_afe_enable_main_clk()` from probe until remove was reverted. It was an unverified workaround and prevented the clock from following runtime use.

The driver now obtains MT6765's AUDSYS `aud_afe` gate (`CLK_AUDIO_AFE`, ID 0) and enables it together with `top_audio_sel` around AFE register access. The CCF gate owns `AUDIO_TOP_CON0` bit 2; the driver no longer toggles that gate through a second, private reference counter. The AFE DT node must include `<&audio 0>` named `aud_afe`.

This change is based on the upstream MT6765 audio clock provider. It has not yet been built or boot-tested on the device. The last `routes loop` marker still does not prove a route call hung; serial-console blocking remains a possible cause.
### 3.2 补充：启动环境本身也有问题

多次刷机测试后确认：

- 带 `console=ttyGS0` 的内核：主机不读串口时，`printk` 会阻塞，表现为卡 Mi logo、USB gadget 不枚举、看门狗重启。**不是驱动挂死**。
- 去掉 `console=ttyGS0` 的镜像（audio10/audio12）：**连内核日志都没有**，pstore 不更新，卡 Mi logo。原因未查明（疑似 bootloader/cmdline 处理，与驱动无关）。
- 同一镜像 audio11 曾成功启动到 1.197s（日志 `console-audio11*.log`），之后重复启动又出现 gadget 不枚举的早期失败。

因此接手人调试驱动时，**必须确保有一个可靠的串口读取端**（或改用其它 console 方案），否则“挂死点”会被 printk 阻塞误导。

---

## 4. 当前故障

运行日志（pstore，见 `console-audio7.log`）：

```
mt6765-afe-pcm 11220000.clock-controller:audio-controller: mtk_afe_combine_sub_dai(), num of dai 15
mt6765_mt6357 sound: ... DANDELION audio: before register_card
mt6765-afe-pcm ...: DANDELION soc: component probe enter
mt6765-afe-pcm ...: DANDELION afe comp: init_regmap
mt6765-afe-pcm ...: DANDELION afe comp: init_regmap done
mt6765-afe-pcm ...: DANDELION afe comp: adding sub dai ctl
（无后续输出，看门狗重启）
```

**挂死点**：`sound/soc/mediatek/common/mtk-afe-platform-driver.c` 的
`mtk_afe_add_sub_dai_control()`，位于 `snd_soc_register_card()` → AFE component probe 内。

该函数：

1. 遍历 `afe->sub_dais`，`snd_soc_add_component_controls()` + `snd_soc_dapm_new_controls()`
2. 遍历 `afe->sub_dais`，`snd_soc_dapm_add_routes()`
3. `snd_soc_dapm_new_widgets(component->card)`

### 怀疑原因

1. **AFE 总线时钟未开时访问寄存器 → AXI 挂死**（失去 mmio_clk 保护后最可能）。
2. `snd_soc_dapm_new_widgets()` 在 component probe 中重复调用导致锁问题。
3. MT6765 的 sub-DAI/widget 列表与 MT8365 不一致（当前 15 个 DAI）。

### 已试但未验证

- 去掉 `mtk_afe_add_sub_dai_control()` 里的 `snd_soc_dapm_new_widgets()`（`boot-audio9.img`）。
- 去掉内核 console `ttyGS0` 以避免 printk 阻塞（`boot-audio10.img`）。

---

## 5. 调试环境

- 内核：`7.1.0-mt6765+`，arm64，`out/.config`
- 构建：`make O=out ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j8 Image.gz`
- boot 分区：`/dev/mmcblk0p33`（64MiB，Android boot header v2）
- 串口：USB ACM `ttyGS0`（115200）；**主机不读时 printk 可能阻塞**
- 日志：TWRP 里读 `/sys/fs/pstore/console-ramoops-0`
- 可用基线镜像：`boot-audio2.img`（codec 通、AFE 未实例化、能正常启动）
- 失败镜像：`boot-audio7/9/10.img`

---

## 6. 建议的下一步

1. 在 `mtk_afe_add_sub_dai_control()` 的每个子步骤前打印/或二分，
   确认挂死发生在 controls / widgets / routes / new_widgets 哪一步。
2. Verify the runtime clock tree on device. The clocked regmap now gates each AFE register access with `aud_afe`; DAI startup also reports CCF enable failures. This does not validate the guessed I2S MCLK/APLL parent mappings.
3. 核对 MT6765 的 I2S mclk 方案（vendor DTS 里 `audclk` 的使用方式）。
4. 参考厂商实现：`drivers/.../mtk-auddrv-afe.c`（旧框架，寄存器偏移与主线一致）。
