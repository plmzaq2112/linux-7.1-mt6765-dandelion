# AW87519 / 扬声器功放：设备上挖到的线索

## 数据来源（FACT）

1. `p35 = dtbo`（8 MiB），已导出：`audio-handover/vendor-dtb/dtbo.dts`
   - 设备侧路径：`/dev/mmcblk0p35`
2. 原厂 boot 镜像自带的完整 board DTB：
   `dandelion-kernel/01-pure-baseline/base/boot-1020-base.img` 内嵌 DTB
   已导出：`audio-handover/vendor-dtb/board.dts`（126 KB）

## 功放节点（FACT，来自 dtbo）

```
fragment@38 {
    __overlay__ {
        clock-frequency = <0x61a80>;      /* 400 kHz */
        mediatek,use-open-drain;

        speaker_amp@34 {
            compatible = "mediatek,speaker_amp";
            reg = <0x34>;
            status = "okay";
        };
    };
};
```

- **vendor 驱动名是 `mediatek,speaker_amp`**，不是单独的 aw87519 驱动。
- I2C 地址 **0x34**。
- 所在总线：**i2c3@1100f000**（base DTB `i2c3`，`id = <3>`，SCL/SDA = GPIO **50/51**）。

## 使能与接口（FACT，来自 dtbo 的 pinctrl）

```
aud_pins_extamp_high { pinmux = <0x9900>; output-high; };   /* SoC GPIO 153 */
aud_pins_extamp_low  { pinmux = <0x9900>; output-low;  };
aud_pins_smartpa_on  { pinmux = <0x1106 0x1206 0x1306 0x1406>; };
aud_pins_smartpa_off { pinmux = <0x1100 0x1200 0x1300 0x1400>; };
```

- 功放使能：**SoC GPIO 153**（0x99），高有效。
  - 主线全局 GPIO 编号 = pinctrl base **512** + 153 = **665**。
- smart PA 接口：SoC GPIO **17/18/19/20**，func 6。

## 声卡节点（FACT，来自 base DTB）

```
audio_snd_card {
    compatible = "mediatek,audio_snd_card";
};
```

## 已做的设备实验

1. 加载 `ampen.ko`，把全局 GPIO 665（SoC pin 153）拉高：
   - `/sys/kernel/debug/gpio` 显示 `gpio-153 | speaker-amp-en | out hi`
   - 但 `i2c3 0x34` 仍然 **errno 110（超时）**。
2. 扫全部 i2c 总线的 0x34：
   ```
   i2c-0 no ack, i2c-1 no ack, i2c-5 no ack
   i2c-2/3/4/6 err 110（总线本身超时）
   ```
   → 0x34 没有任何总线 ACK；i2c3 本身也有超时，可能是总线/mux/上拉或功放把 SDA 拉低。

## 下一步需要

- vendor 的 **`speaker_amp.c`**（搜 `mediatek,speaker_amp`，通常在
  `sound/soc/codecs/speaker_amp.c` 或 `sound/soc/mediatek/common/`）。
  重点看：
  1. probe 时是否还拉别的 GPIO / regulator / reset
  2. `aud_smartpa_on/off`、`extamp-pullhigh/low` 的使用顺序
  3. I2C 读写寄存器（确认芯片 ID、是否需要初始化序列）
- 拿到后可以判断：是 GPIO 使能不够，还是 i2c3 总线本身在我们主线 DTB 上没配对。
## 4.19 vendor 源码里的结论（FACT）

位置：`~/dandelion-linux-kernel/01-pure-baseline`（4.19）

- `mediatek,speaker_amp` 是一个**分发器**：`sound/soc/mediatek/common/mtk-sp-spk-amp.c`
  - 按顺序 probe 子驱动：RT5509、MT6660
- vendor defconfig（`arch/arm64/configs/stock_defconfig`）：
  - `CONFIG_SND_SOC_RT5509=y`
  - `CONFIG_SND_SOC_MT6660 is not set`
  - 结论：dandelion 的功放是 **RT5509（Richtek）**
- RT5509 驱动：`sound/soc/codecs/rt5509.c`、`rt5509-regmap.c`、`rt5509-calib.c`、`rt5509.h`
  - DAI 名：`rt5509-aif1`、`rt5509-aif2`
  - 纯 I2C 控制，DT 里没有 GPIO/regulator 属性
  - probe 流程：`_rt5509_power_on` → `sw_reset` → 读 chip rev
  - 主线 `03-mainline-7.1` 没有 rt5509 驱动
- AW87519 驱动（`awinic,aw87519_left/right`）是别的机型/立体声用的，
  dandelion 的 DTS 里没有 awinic 节点

## 扬声器路径（推断，待验证）

AFE → **2ND I2S** → RT5509（I2S 输入的 smart PA）→ 扬声器
RT5509 通过 **i2c3 @0x34** 初始化和控制；`extamp` GPIO 153 可能负责功放供电/使能。

## 当前阻塞

- 主线 i2c3（0x1100f000，GPIO 50/51）传输超时（errno 110），
  即使 GPIO 153 已拉高。可能是功放没供电、总线被拉低，或主线 i2c3 的时钟/mux 配置问题。
- 下一步：先让 i2c3 能 ACK 0x34，再移植 RT5509 驱动、加机器驱动的 I2S link 和 smartpa pinctrl。
## 2026-11-23 深夜：i2c3 调查结果

### 结论

1. **i2c3 总线本身没问题**
   - 解绑 MTK i2c3 控制器后，用 GPIO 50/51 做 bit-bang（i2c-gpio），总线工作正常。
   - 全量扫描找到 **0x50、0x57** —— 正好是 vendor DTS 里的
     `ext_buck_lp4x@50` 和 `ext_buck_lp4@57`，证明总线、引脚、时序都对。
2. **MTK i2c3 控制器在主线上超时**
   - 时钟 `ifr_i2c_ap` 已使能、IRQ（SPI 87）已注册但从不触发；
   - 400k/100k 都一样；总线引脚空闲电平为高（SCL=1、SDA=1），不是被拉死；
   - 这是 i2c-mt65xx 驱动/控制器配置问题，与功放无关。
3. **功放 0x34 不应答**
   - 即使 extamp GPIO 153 按 vendor 方式 LOW→HIGH 脉冲 3 次，仍然 NAK；
   - 说明 RT5509 没上电或没使能。

### 硬件布局（FACT，vendor cust.dtsi）

`&i2c3`（400 kHz，open-drain）：

| 地址 | 设备 |
|---|---|
| 0x34 | speaker_amp（RT5509 分发器） |
| 0x4b | slave_charger |
| 0x57 | ext_buck_lp4 |
| 0x50 | ext_buck_lp4x |

- i2c4：相机；i2c5：switching_charger@6b；i2c6：ext_buck_vgpu@55、lcd_bias@3e。

### 下一步

- 0x50/0x57 两个外部 buck 在线，但主线没有驱动/配置；它们很可能就是功放 VDD 的来源。
  vendor 的 `ext_buck_lp4/lp4x` 驱动不在 `01-pure-baseline` 源码树里（可能在 vendor_dlkm），
  需要找驱动或直接确认功放的供电轨。
- 临时可用 **i2c-gpio**（GPIO 50/51）绕过 MTK i2c3 控制器问题；
  但前提是功放先上电。
## 2026-11-23：扬声器硬证据（不再假设）

### 1. vendor 内核自己也连不上 RT5509

来自 `dandelion-system-repair/notes/dmesg-pe-a11.txt`（vendor 内核日志）：

```
rt5509_driver_init
speaker_amp 3-0034: mtk_spk_i2c_probe()
+rt5509_i2c_probe
speaker_amp 3-0034: power on fail 1
speaker_amp 3-0034: error -121
speaker_amp: probe of 3-0034 failed with error -121
...
mtk_spk_update_dai_link(), mtk_spk_type 0
ext_Speaker_Multimedia, codec dai name = snd-soc-dummy-dai
```

`dandelion-system-repair/notes/tinymix.txt`：

```
MTK_SPK_TYPE_GET          MTK_SPK_NOT_SMARTPA
Speaker_Amp_Switch        Off
Ext_Speaker_Amp_Switch    Off
```

结论：**外部 smart PA（RT5509）在这台机器上不可用**，vendor 自己也回退到
`MTK_SPK_NOT_SMARTPA`（dummy codec）。之前对 0x34 的所有探测结果与 vendor 一致。

### 2. 主线 codec 驱动缺扬声器路径

- `03-mainline-7.1/sound/soc/codecs/mt6357.c` 中搜索 `spk|speaker|auxo` **无任何结果**。
- vendor codec 驱动有完整实现：
  - `Speaker_Amp_Change()`：NCP → cap-less LDO 1.5V → NV -1.2V → LO driver bias/core →
    `apply_speaker_gain()` → AUD_CLK → DAC → LOL mux 到音频 DAC。
  - `AUDIO_ANALOG_VOLUME_SPKL/SPKR`、`AUDIO_ANALOG_DEVICE_OUT_SPEAKERL`、
    `AUDIO_ANALOG_DEVICE_RECEIVER_SPEAKER_SWITCH` 等。
- 已把完整函数保存到 `audio-handover/vendor-dtb/vendor-speaker-amp-change.txt`。

### 3. 结论

扬声器是 **MT6357 内部的 lineout/spk 输出（LOL）**，不是外部功放。
主线缺的是 codec 侧的 SPK/LOL DAPM 路径和那段模拟上电序列。
需要把这个路径移植进 `sound/soc/codecs/mt6357.c`（widgets + 控件 + 寄存器序列），
不是写外部 amp 驱动。

## 2026-11-23 深夜：扬声器移植结果

### 已完成（FACT）

主线 `mt6357.c` 的 LO/扬声器路径现在与 vendor `Speaker_Amp_Change` 的寄存器状态一致
（播放中实测）：

| 寄存器 | 主线 | vendor |
|---|---|---|
| CON0 0x2208 | 3009 | 3009 |
| CON4 0x2210 | 011b | 011b |
| CON6 0x2214 | 0201 | 0201 |
| CON12 0x2220 | 1055 | 1055 |
| CON13 0x2222 | 0001 | 0001 |
| NCP CON3 0x20ba | 0000 (on) | 0000 |
| ZCD_CON1 0x228a | 0000 (max) | 按音量 |

改动：
1. `lo_mux_event` POST_PMU 里补 `configure_downlinks(priv, true)`（NCP/LDO/NV 重新使能）
2. CON6 主 CMFB loop（bit9）使能，bit7 按 vendor 最终值清零

### 仍未解决

- 外放仍然完全没声（整首音乐、最大音量、贴耳也无声）。
- 外部 smart PA（RT5509，i2c3 0x34）**不 ACK**，即使：
  - extamp GPIO 153 高/低都试过
  - 逐个打开 ldo-vio28/vio18/vcn18/vcamio18/vldo28/vaux18/vcama/vcamd/vmch/vmc
- vendor 内核日志里 RT5509 probe 也是 `-121`（无 ACK），回退 `MTK_SPK_NOT_SMARTPA`。

### 结论（当前证据）

codec 侧（LO 扬声器路径）已经按 vendor 配好；剩余问题在 **外部功放的上电/使能**，
不是 codec 寄存器。需要原理图确认 RT5509 的 VDD/EN 来源，或对比原厂运行时该芯片的状态。

### 当前基线

- 内核 #34，镜像 `boot-stable8.img`
- 播放开始/结束 pop 已修（VAUD28 settle）
- 听筒正常；外放待外部功放上电
