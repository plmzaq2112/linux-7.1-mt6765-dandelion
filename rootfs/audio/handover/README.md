# 音频（AFE + codec + 功放）移植交接说明

> 目标：Redmi 9A（dandelion / MT6762G）在主线 Linux 7.1 + Ubuntu 24.04 上实现内置音频（扬声器/耳机/麦克风）。
> 当前状态：**未完成**。codec 已通，AFE 已能 probe，但卡在 ASoC card 注册阶段。

---

## 1. 代码位置

| 内容 | 位置 |
|---|---|
| 公开仓库 | `https://github.com/plmzaq2112/linux-7.1-mt6765-dandelion`（分支 `dandelion-7.1`） |
| 本地内核树（WSL） | `~/AI Project/Redmi 9A/kernel 7.1 mainline` |
| 新增 AFE 驱动目录 | `sound/soc/mediatek/mt6765/`（由 `mt8365/` 克隆 + 重命名 + 修改） |
| 本次改动补丁 | `rootfs/ubuntu/audio-handover/audio-wip.patch`（6551 行） |
| 改动统计 | `rootfs/ubuntu/audio-handover/diffstat.txt` |
| 带音频节点的 DTS | `rootfs/ubuntu/audio-handover/dandelion-audio.dts`（从运行中的 DTB 反编译） |
| DTB 生成脚本 | `rootfs/ubuntu/audio-handover/make_audio_boot2.py` |
| 启动日志（pstore） | `rootfs/ubuntu/audio-handover/console-audio*.log` |

> 注意：`audio-wip.patch` 里包含 `sound/soc/soc-core.c` 的**调试打印**，正式提交前应删除。

### 内核配置（`out/.config`）

```
CONFIG_SOUND=y
CONFIG_SND=y
CONFIG_SND_SOC=y
CONFIG_SND_SOC_MT6357=y
CONFIG_SND_SOC_MT6765=y
CONFIG_SND_SOC_MT6765_MT6357=y
CONFIG_MEDIATEK_MT6359_AUXADC=y
CONFIG_GENERIC_ADC_BATTERY=y
CONFIG_CHARGER_BQ256XX=y
CONFIG_DRM_PVR_LEGACY=m
```

构建命令：

```bash
cd "$HOME/AI Project/Redmi 9A/kernel 7.1 mainline"
make O=out ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j8 Image.gz
```

---

## 2. 硬件信息

| 项 | 值 |
|---|---|
| 机型 | Xiaomi Redmi 9A，代号 **dandelion**，型号 M2006C3LG |
| SoC | MediaTek **MT6762G**（Helio G25，8×A53） |
| PMIC | **MT6357**（挂在 pwrap，不是 i2c） |
| 音频 codec | **MT6357 内置 codec** |
| 音频前端 AFE | 基址 **0x11220000**，中断 **GIC_SPI 153**（`IRQ_TYPE_LEVEL_LOW`） |
| 音频时钟 | audsys（`0x11220000`，compatible `mediatek,mt6765-audsys`）+ topckgen（`0x10000000`，`mediatek,mt6765-topckgen`） |
| 扬声器功放 | **AW87519**（i2c-3 @ **0x34**，DT 名字 `speaker_amp`；厂商有左右声道两颗驱动） |
| 充电 IC | **TI BQ25601**（i2c-5 `11016000` @ **0x6B**，REG0B PN=2）；SGM41513(0x1A) 和 MT6370(0x34) **不存在** |
| 电池电压 | MT6357 AUXADC **BATADC 通道 0**（raw ≈ 26809 → 4.4V） |
| 触摸 | FocalTech FT8006S（SPI3.0，模块 `focaltech_ts.ko`） |
| 显示 | DSI 720x1600（`mediatek-drm`，`card1-DSI-1`） |
| 音量/电源键 | PMIC keys + MTK keypad 矩阵（KPCOL0） |
| 存储 | eMMC 58.2GiB（mmc0）+ microSD（mmc1） |
| USB | musb gadget（ACM `ttyGS0` + NCM `usb0`） |

### AFE 寄存器与主线现有驱动一致

| 寄存器 | MT6765 厂商 | MT8183 | MT8365 |
|---|---|---|---|
| AFE_DAC_CON0 | 0x0010 | 0x0010 | 0x0010 |
| AFE_DAC_CON1 | 0x0014 | 0x0014 | 0x0014 |
| AFE_I2S_CON1 | 0x0034 | 0x0034 | 0x0034 |
| AFE_I2S_CON2 | 0x0038 | 0x0038 | 0x0038 |
| AFE_MEMIF_MSB | 0x00cc | 0x00cc | 0x00cc |
| AFE_ADDA_DL_SRC2_CON0 | 0x0108 | 0x0108 | 0x0108 |
| AFE_ADDA_TOP_CON0 | 0x0120 | 0x0120 | 0x0120 |
| AFE_IRQ_MCU_CON0 | 0x03a0 | 0x03a0 | 0x03a0 |

### MT6765 时钟（关键差异：只有 APLL1，没有 APLL2/engen2）

`include/dt-bindings/clock/mt6765-clk.h`：

```
topckgen: CLK_TOP_AUDIO_SEL=111, CLK_TOP_AUD_1_SEL=113, CLK_TOP_AUD_ENGEN1_SEL=114,
          CLK_TOP_AUDIO=62, CLK_TOP_AUD_1=63, CLK_TOP_AUD_ENGEN1=64,
          CLK_TOP_APLL1=41, APLL1_D2=42, D4=43, D8=44, APLL12_DIV0..3=78..81
audsys:   CLK_AUDIO_AFE=0, 22M=1, APLL_TUNER=2, ADC=3, DAC=4, DAC_PREDIS=5, TML=6,
          I2S1_BCLK=7, I2S2_BCLK=8, I2S3_BCLK=9, I2S4_BCLK=10
```

当前 DT 里 AFE 的时钟映射（**这是主要可疑点**）：

```
top_clk26m_clk  = <&clk26m>
top_audio_sel   = <&topckgen 111>
audio_i2s0_m    = <&audio 7>     (I2S1_BCLK 门控)
audio_i2s1_m    = <&audio 8>
audio_i2s2_m    = <&audio 9>
audio_i2s3_m    = <&audio 10>
engen1          = <&topckgen 64>
engen2          = <&topckgen 64>   (复用)
aud1            = <&topckgen 63>
aud2            = <&topckgen 63>   (复用)
i2s0_m_sel      = <&topckgen 78>
i2s1_m_sel      = <&topckgen 79>
i2s2_m_sel      = <&topckgen 80>
i2s3_m_sel      = <&topckgen 81>
```

---

## 3. 已完成的工作

1. **ALSA 核心**：`CONFIG_SOUND/SND/SND_SOC=y`，`/proc/asound` 正常。
2. **MT6357 codec 绑定**：PMIC 节点下新增

```dts
audio-codec {
    compatible = "mediatek,mt6357-sound";
    vaud28-supply = <&mt6357_vaud28_reg>;
};
```

3. **AFE 驱动**：`sound/soc/mediatek/mt6765/`（mt8365 克隆），改动：
   - 改为 **syscon regmap**（父节点 audsys）：
     ```c
     afe->regmap = syscon_node_to_regmap(dev->parent->of_node);
     regmap_attach_dev(dev, afe->regmap, &mt6765_afe_regmap_config);
     ```
   - 删除原来的 `devm_regmap_init_mmio_clk(..., "top_audio_sel", ...)`
4. **AFE 子节点实例化**：`drivers/clk/mediatek/clk-mt6765-audio.c` 增加
   `devm_of_platform_populate(&pdev->dev)`（模仿 mt8183）。
5. **机器驱动**：`mt6765-mt6357.c` pinctrl 缺失时跳过（DT 没有音频 pinctrl 状态）。
6. **DT**：
   - `afe` 子节点在 audsys 下（IRQ 153、clocks/clock-names、`phandle`）
   - `sound` 机器节点：`compatible = "mediatek,mt6765-mt6357"; mediatek,platform = <&afe>;`

### 目前进到哪一步（audio7 日志，已保存）

```
mt6765-afe-pcm ...: mtk_afe_combine_sub_dai(), num of dai 15
mt6765_mt6357 sound: DANDELION audio: before register_card
DANDELION soc: component probe enter
DANDELION afe comp: init_regmap
DANDELION afe comp: init_regmap done
DANDELION afe comp: adding sub dai ctl
（之后没有任何输出，看门狗重启）
```

结论：**挂在 `mtk_afe_add_sub_dai_control()` 内部**，位置在
`sound/soc/mediatek/common/mtk-afe-platform-driver.c`。

该函数做三件事：
1. 遍历 sub_dais：`snd_soc_add_component_controls` + `snd_soc_dapm_new_controls`
2. 遍历 sub_dais：`snd_soc_dapm_add_routes`
3. `snd_soc_dapm_new_widgets(component->card)`

已尝试但**尚未验证**：把第 3 步的 `snd_soc_dapm_new_widgets` 去掉（audio9 镜像，未来得及确认）。

---

## 4. 待排查的假设

1. **DAPM 控件/路由阶段访问 AFE 寄存器时时钟未开**，导致 AXI 挂死。
   - 原 mt8365 驱动用 `regmap_init_mmio_clk(..., "top_audio_sel", ...)` 保证访问时总线时钟开启；
     改成 syscon 后这个保护没有了。
2. `snd_soc_dapm_new_widgets()` 在 component probe 中被重复调用，可能与 card bind 的锁冲突。
3. MT6765 的 DAI/sub-DAI 数量或 widget 列表与 MT8365 不同（15 个 DAI 是否合理）。

---

## 5. 如何复现与调试

- 串口：USB ACM `ttyGS0`（115200）；cmdline 里目前有 `console=ttyGS0,115200`。
  - **注意**：主机不读串口时 `printk` 可能阻塞，表现为“死机 + 看门狗重启”。
  - 读日志：`ubuntu/units/` 下的串口脚本，或 TWRP 里读 `/sys/fs/pstore/console-ramoops-0`。
- SSH（设备正常启动时）：`root@169.254.195.201`（NCM，已配密钥）。
- 刷机：boot 分区 `/dev/mmcblk0p33`（64MiB，Android boot header v2）。

### 当前镜像

| 镜像 | 内容 | 状态 |
|---|---|---|
| `boot-power8.img` | 电量/按键修复（无音频） | 可用 |
| `boot-audio2.img` | codec + AFE 未实例化 | **可用（推荐作为基线）** |
| `boot-audio7.img` | 带诊断打印 | 挂在 subdai |
| `boot-audio9.img` | 跳过 `new_widgets` | 未验证 |
| `boot-audio10.img` | audio9 + 去掉 `console=ttyGS0` | 未验证（卡 logo） |

---

## 6. 需要帮忙的具体问题

1. MT6765 的 AFE 是否与 MT8365/MT8183 共用寄存器与时钟模型？有没有现成 patch series？
2. `mtk_afe_add_sub_dai_control()` 在 MT6765 上挂死的最可能原因？
3. 正确的 MT6765 AFE 时钟映射（尤其 I2S mclk / engen2 / aud2 的替代方案）？
4. 扬声器 AW87519 的主线驱动是否已有可参考实现？

---

## 7. 联系方式 / 复现材料

- 仓库：`https://github.com/plmzaq2112/linux-7.1-mt6765-dandelion`（分支 `dandelion-7.1`）
- 本目录：补丁、DTS、启动日志、DTB 生成脚本。
