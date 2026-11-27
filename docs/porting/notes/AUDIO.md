# 音频移植记录（2026-11-22）

## 现状

| 组件 | 状态 |
|---|---|
| ALSA 核心 | ✅ 已启用（`CONFIG_SOUND/SND/SND_SOC=y`），`/proc/asound` 存在 |
| MT6357 codec | ✅ 已绑定（`/sys/bus/platform/drivers/mt6357-sound/mt6357-sound`） |
| MT6765 AFE | ❌ 主线无驱动，待移植 |
| 机器驱动（sound card） | ❌ 待写 |
| AW87519 功放 | ❌ 主线无驱动（厂商有左右声道两颗） |
| 音频时钟 | ✅ `clk-mt6765-audio.c` 已支持 audsys 门控 |

当前 `/proc/asound/cards` 为空（没有 machine/AFE，只有 codec component）。

## codec 是怎么通的

- PMIC 节点 `/soc/pwrap@1000d000/pmic` 下新增子节点：

```dts
sound {
    compatible = "mediatek,mt6357-sound";
    vaud28-supply = <0x8a>;
};
```

- `vaud28` 由 PMIC 的 `ldo-vaud28` 提供（phandle 0x8a）。
- 之前 dmesg 里的 `mt6357-sound: Failed to locate of_node` 就是因为缺这个子节点。

## 关键侦察结论

**AFE 寄存器与主线现有驱动完全一致**：

| 寄存器 | MT6765(厂商) | MT8183 | MT8365 |
|---|---|---|---|
| AFE_DAC_CON0 | 0x0010 | 0x0010 | 0x0010 |
| AFE_DAC_CON1 | 0x0014 | 0x0014 | 0x0014 |
| AFE_I2S_CON1 | 0x0034 | 0x0034 | 0x0034 |
| AFE_I2S_CON2 | 0x0038 | 0x0038 | 0x0038 |
| AFE_MEMIF_MSB | 0x00cc | 0x00cc | 0x00cc |
| AFE_ADDA_DL_SRC2_CON0 | 0x0108 | 0x0108 | 0x0108 |
| AFE_ADDA_TOP_CON0 | 0x0120 | 0x0120 | 0x0120 |
| AFE_IRQ_MCU_CON0 | 0x03a0 | 0x03a0 | 0x03a0 |

结论：MT6765 的 AFE 是同一代 IP，**可以基于主线驱动做变体**。

## 移植计划

### Phase 2：AFE + 机器驱动（进行中）

**已完成：**
- `sound/soc/mediatek/mt6765/` 由 mt8365 目录克隆、重命名，编译通过。
- Kconfig/Makefile 已加 `SND_SOC_MT6765` / `SND_SOC_MT6765_MT6357`，配置已启用。
- 找到 MT6765 AFE 中断号：**GIC_SPI 153**（厂商 DTS `mt_soc_dl1_pcm@11220000`）。

**已做（#22, boot-audio3.img）：**
- AFE 驱动改成 **syscon**：`syscon_node_to_regmap(dev->parent->of_node)` + `regmap_attach_dev`
- DT 增加：
  - `afe` 子节点（audsys 下，IRQ GIC_SPI 153，phandle 0xc6）
  - `audio-codec`（PMIC 下，MT6357 codec）
  - `sound` 机器节点（`mediatek,mt6765-mt6357`，`mediatek,platform = <&afe>`）
- 机器驱动 pinctrl 改为可选（DT 里没有音频 pinctrl 状态）

**当前阻塞：**
- dmesg: `platform sound: deferred probe pending: mt6765_mt6357: Cannot register card`
- 说明某个 DAI 组件（大概率是 AFE）没注册成功
- 还没拿到 AFE 的 probe 错误（SSH/串口在系统高负载时不稳定）
- 时钟映射仍是猜测（APLL1 + audsys 门控 + 复用 engen1/aud1 填 engen2/aud2）

**下一步：**
1. 确认 AFE 是否 probe：`/sys/bus/platform/drivers/mt6765-afe-pcm/`、dmesg `mt6765-afe-pcm`
2. 根据错误修时钟（可能需要 fixed-clock 占位）
3. 卡片注册后用 aplay/Phosh 测试
4. 再上 AW87519 功放（i2c-3 @0x34）

**环境问题：** 启动约 4 分钟；SSH/串口在高负载下会短暂不可用，迭代成本高。可考虑先禁用 `e2scrub_reap.service` 减少启动负担。


模板选择：**mt8365**（同款 MT6357 codec，machine 驱动现成）。

1. 复制 `sound/soc/mediatek/mt8365/` → `mt6765/`，做符号重命名。
2. 适配时钟模型：
   - MT8365 需要 `top_audio_sel / audio_i2s0-3_m / engen1-2 / aud1-2 / i2s*_m_sel / top_clk26m_clk`
   - MT6765 只有 APLL1：`audio_sel / aud_1_sel / aud_engen1_sel / apll1 / apll1_d2,d4,d8 / apll12_div0-3` + audsys 门控 `aud_afe/dac/adc/22m/apll_tuner/tml/i2s1-4_bclk`
   - 需要去掉 engen2 / aud2 / i2s*_m 相关路径
3. 补 Kconfig / Makefile。
4. DT 增加：
   - `afe` 节点（`mediatek,mt6765-audio`，寄存器 0x11220000，IRQ GIC_SPI 97？需确认，MT6765 厂商 IRQ 号）
   - `sound` 机器节点（`mediatek,mt6765-mt6357`），DAI link 指向 AFE 与 codec
5. 编译 → 刷机 → 看 `/proc/asound/cards`。

### Phase 3：扬声器

- 移植 AW87519 驱动（i2c-3 @0x34，厂商 `sound/soc/mediatek/aw87519/`）
- 加 DAPM 路由与 machine 控件

### Phase 4：麦克风/耳机检测

- MT6357 accdet（主线有 `mt6359-accdet.c`，MT6357 需确认）
- 麦克风偏置、耳机检测

## 风险

- IRQ 号、power-domain、reset 在 MT6765 上需确认（主线 mt6765.dtsi 里 audsys 无 afe 子节点）。
- 时钟模型差异最大，可能导致 `clk_set_rate/parent` 失败。
- AFE 的 DAI 数量/内存接口数量可能与 MT8365 不同。
- 需要多轮编译+刷机迭代。

## 当前 boot

- 设备：`/root/boot-audio1.img`（内核 #19 + codec DT 节点）
- 本地：`rootfs/ubuntu/boot/boot-audio1.img`
- 回滚：`/root/boot-power8.img`（电量版，codec 未启用）

## 2026-11-22 晚：模块化与硬挂定位

### 接手人更新（14:09 / 14:12）

- `mt6765-afe-pcm.c` 回退了 12:28 的 `enable_main_clk` 常开修复（恢复为 `enable_top_cg(MT6765_TOP_CG_AFE)`）。
- `audio-wip.patch`：所有 `DANDELION` 打印由 `dev_info` 改为 `dev_dbg`，保留跳过 `snd_soc_dapm_new_widgets` 的实验。
- 其余 mt6765 文件、clk 改动与树内一致。

### 本次实验

| 项 | 内容 |
|---|---|
| 内核 | #30（2026-11-22 17:22），`boot-audio13.img` |
| cmdline | 无 `console=ttyGS0`（`console=tty0` 只有） |
| 构建 | `SND_SOC_MEDIATEK=m`、`SND_SOC_MT6765=m`、`SND_SOC_MT6765_MT6357=m`，`SND_SOC_MT6357=y` |
| 诊断 | `ccflags-y += -DDEBUG`（sound/soc 三个目录），DANDELION 的 `dev_dbg` 可输出 |
| 新增 | routes 循环逐条打印 subdai 名、route 序号、source/sink/control |

### 结果

- `boot-audio13.img` 正常启动，UI/SSH 可用（无串口读者也正常）。
- `insmod snd-soc-mtk-common.ko` OK；`insmod snd-soc-mt6765-pcm.ko`（回退版）→ **整机硬挂**（ping 1/3，SSH 超时），只能断电。
- 结论：`enable_main_clk()` 是 AFE 寄存器访问的必要条件，不是调试手段；回退不可用。

### 恢复与下一步

- 已恢复 `enable_main_clk` / `disable_main_clk`（保留 dev_dbg + route 打印），只重编模块：`snd-soc-mt6765-pcm.ko` md5 `fd397265c0f76239969e7e36188ccc87`。
- 备份：`rootfs/ubuntu/boot/assets/backup-mt6765-afe-pcm-clockfix.c`。
- 下一步：
  1. 断电重启后读 `/sys/fs/pstore/`，确认上次硬挂最后一条日志。
  2. `insmod` AFE（带 main clock，应能完成 probe）。
  3. 后台加载机器驱动（`mt6765-mt6357.ko`），观察逐条 route 打印停在哪一条；若整机仍硬挂，用 ramoops 最后一屏定位。

### 当前 boot

- `boot-audio13.img`（内核 #30，音频模块在 `/root/audio/`，不自动加载）
- 基线回滚：`boot-ui-fix.img`

## 2026-11-22 深夜：AFE 模块可加载，声卡注册成功

### 根因：AFE 中断极性写反

- DT 里原来写的是 `interrupts = <0x00 0x99 0x04>`，`0x04 = IRQ_TYPE_LEVEL_HIGH`。
- MTK AFE 中断是 **低电平有效**（主线 mt8365：`interrupts = <GIC_SPI 97 IRQ_TYPE_LEVEL_LOW>`）。
- 极性写反后，GIC 认为中断线一直有效；`devm_request_irq()` 一注册就无限进中断，**整机瞬间冻结，没有任何日志**。

二分证据：

| 测试 | 结果 |
|---|---|
| `afe_stage=0`（probe 入口返回，不注册中断） | 稳定 |
| `afe_stage=1`（包含 `request_irq`） | 必挂 |
| CMDQ 关闭（mmsys 去掉 mboxes）后加载 AFE | 仍挂 → 与显示无关 |

### 修复

- DTB：`interrupts = <0x00 0x99 0x08>`（LEVEL_LOW）
- 镜像：`rootfs/ubuntu/boot/images/boot-stable2.img`
- 同时 `boot-stable1.img` 去掉了 mmsys 的 `mboxes`，显示改用 CPU 直写，CMDQ timeout 消失（另一个真实问题）。

### 结果

- AFE 模块完整加载，probe 走完（clocks / regmap / IRQ / 15 DAI / init registers）。
- 机器驱动加载后注册成功：

```
0 [mt6765evk      ]: mt6765-evk - mt6765-evk
```

- PCM：`MultiMedia1_PLayback` / `MultiMedia2_PLayback` / `DL1_AWB_Record` / `MultiMedia1_Capture`。
- 播放链路：必须先打开 DAPM 连接矩阵开关（否则 DPCM 报 "no valid Playback path"）：

```
mixer2.py set "O03 I05" 1
mixer2.py set "INT ADDA O03_O04" 1
```

- 之后 `alsa_test.py hw:0,0 15 440` 可完整播放（661500/661500 frames）。
- 耳机输出：`Headphone Left/Right Source` 设为 `DAC`。
- 扬声器：AW87519 功放仍未驱动，需要单独移植。

### 后续

1. 把上述 mixer 开关做成 UCM 配置（PipeWire/WirePlumber 才会创建 sink）。
2. 扬声器 AW87519（i2c-3 @0x34）驱动 + enable GPIO。
3. 修正 AFE 的时钟映射（audio_i2s*_m 目前指向 audsys gate，不是 topckgen AUD_I2S*_M）。
4. 正式提交时去掉 DANDELION 调试打印和 `-DDEBUG`。

## 2026-11-23 凌晨：可以出声，但周期咔哒声

### 已验证

- 接手人的“每次寄存器访问都用 aud_afe 门控”方案 + DT 增加 `aud_afe` 时钟（`boot-stable3.img`）工作正常。
- 加载顺序：`snd-soc-mtk-common` → `snd-soc-mt6765-pcm` → `mt6765-mt6357`，声卡注册成功。
- 打开 DAPM 连接矩阵开关后可以完整播放：

```
python3 mixer3.py set "O03 I05" 1
python3 mixer3.py set "INT ADDA O03_O04" 1
python3 alsa_test.py hw:0,0 15 660   # 661500/661500 frames
```

- 实测听到 660Hz 音调（听筒路径：`Handset Source = Playback`，`Handset` 音量从 0 调到 18）。

### 剩余问题：周期咔哒声（约 0.3~0.5 秒一次）

- 原因：**AFE period 中断没有触发**，ALSA 应用无法及时续数据，每个 buffer 回绕就 underrun 一次。
- 证据（播放 RUNNING 期间）：

```
/proc/interrupts  IRQ 206 (Afe_ISR_Handle) 计数保持不变
AFE_IRQ_MCU_CON (0x3a0)    = 0xa1   (IRQ1 enable bit0 = 1，FS=0xa)
AFE_IRQ_MCU_STATUS (0x3a4) = 0x02020000  (bit17 / bit25，不在 0x3ff 内)
AFE_IRQ_MCU_CNT1 (0x3ac)   = 0x1770 (6000)
AFE_IRQ_MCU_EN (0x3b4)     = 0xffff
```

- handler 里 `reg_value &= mcu_irq_mask`（0xffff）后为 0，既不会处理也不会清 bit17/25；但也没有中断风暴，说明这些位不是当前 GIC 线的来源。
- 采样率改成 48k 也一样（不是 44.1k APLL 的问题）。
- 在 `enable_main_clk` 里补开 `aud1`（CLK_TOP_AUD_1）测试，仍然没有 period 中断。

### 结论 / 下一步

- 时钟门控和寄存器访问已经不是问题；**MT6765 的 AFE IRQ 寄存器布局（STATUS/CLR/EN 的位定义）与 mt8365 的 0x3ff 假设不一致**。
- 需要 vendor `mt6768-reg.h` / `mt6768-afe-pcm.c` 确认：
  1. `AFE_IRQ_MCU_STATUS` 的 IRQ1 状态位是第几位
  2. `AFE_IRQ_MCU_CLR` 的清除方式（W1C？位映射是否与 STATUS 相同）
  3. `AFE_IRQ_MCU_EN` 的位映射
  4. IRQ counter 的时钟（22M/26M/engen1）和全局使能位
- 拿到上述信息后，改 `irq_data[]` / `AFE_IRQ_STATUS_BITS` / handler 的 mask 即可，不需要动 DAPM。
- 扬声器仍需要 AW87519 驱动；听筒路径已可用。

## 2026-11-23 白天：PipeWire 与音量键

### PipeWire 噪音（S32_LE）

- WirePlumber 默认让 ALSA 设备跑 `S32_LE @ 48000`，但当前 AFE/codec 路径下 32-bit 数据是噪音（S16 正常）。
- 已加 `/etc/wireplumber/main.lua.d/51-alsa-format.lua`，对 `alsa_output.*` 强制 `audio.format = S16LE`、`audio.rate = 44100`。
- 效果：`hw_params` 变为 `S16_LE / 44100`，`pw-play` 播放干净。
- 根因（待修）：S32 路径在 AFE/codec 的格式协商或 24-bit 连接配置上有问题，现在只是绕过。

### 音量键

- 现象：按音量键无反应。
- 根因：`org.gnome.settings-daemon.plugins.media-keys` 的 `volume-up/down/mute` 是空绑定（`['']`），gsd-media-keys 收到按键也不处理。
- 修复：

```
gsettings set org.gnome.settings-daemon.plugins.media-keys volume-up "['XF86AudioRaiseVolume']"
gsettings set org.gnome.settings-daemon.plugins.media-keys volume-down "['XF86AudioLowerVolume']"
gsettings set org.gnome.settings-daemon.plugins.media-keys volume-mute "['XF86AudioMute']"
```

- 验证：音量键可以改 sink 音量（0.46 → 0.72）。
- 听感：sink 音量过半后听筒不再变大——听筒物理上限，codec 的 `Handset` 已经 18/18；不是软件问题。

### 当前播放方式

- 音乐：`pw-play /tmp/apex.wav`（PipeWire → ALSA S16/44.1k → AFE DL1 → INT ADDA → MT6357 听筒）。
- 直接 ALSA 也正常：`python3 wav_play.py <wav>`（S16/44.1k）。
- 扬声器仍然需要 AW87519 驱动。

## 2026-11-23 下午：pop 问题排查

### 已做的正规化

- 模块安装在 `/lib/modules/$(uname -r)/extra/dandelion-audio/`，由 udev 按 DT compatible 自动加载，不再用 `insmod` 脚本。
- 去掉了 `blacklist` + `sleep 20` 这种 hack。
- probe 阶段不再碰音频硬件：
  - `set_clk_parent(TOP_AUD_SEL, 26M)` 移到 `mt6765_afe_enable_main_clk()`（stream start 才执行）
  - 去掉 probe 里的 `enable_main_clk`（DAC 不再在 probe 开关）
  - `CONN_24BIT` 写入移到 `enable_main_clk()`
- 结果：probe 里已经没有会触发听筒 pop 的 AFE 寄存器操作。

### 仍存在的 pop

- 开机（card bind 时）一下。
- 每次播放开始/结束各一下；中间干净。
- 不加载音频模块 → 开机完全安静；手动加载 AFE 或机器驱动 → 也没有 pop。
- 说明是 **早期 boot 时 card bind / codec 上电时序**，不是我们的 probe 代码。
- 现场：`vaud28` 由 `mt6357-sound-vaud28` 在 card 运行时才 enable（use count 1），早期上电与 codec bias 上电叠加，容易产生 pop。

### 候选修法

1. DT 给 `vaud28` 加 `regulator-always-on`（简单，需刷 DTB，可能有效）。
2. codec 侧按 vendor 的 `mt6357` bias/HP/handset 上电顺序加 mute/ramp（正解，需要 vendor 代码）。
3. 暂不处理：功能已通，pop 只在开/停瞬间。

## 2026-11-23 晚：pop 收尾

### 已解决：开机 pop

- 接手人的 `mt6357-pop-fix`：VAUD28 使能后 `usleep_range(500, 1000)`，再注册 codec component。
- 内核 #31，镜像 `boot-stable4.img`（stable3 DTB + 新 Image.gz）。
- 结果：开机 pop 消失。

### 已解决：播放开始 pop

- probe 阶段不再碰音频硬件（set_clk_parent / DAC / CONN_24BIT 全部移到 stream start）后，开始干净。

### 仍存在：播放结束 pop

- 现象：stop 时一下。
- 原因：DAI shutdown 里 `mt6765_afe_disable_main_clk()` 先把 AFE DAC 关掉，而 codec 的听筒是之后才由 DAPM 下电，中间有直流跳变。
- 试过“跨 stream 保持 AFE 主时钟/DAC”，结果开始也响，已回退。
- 正解：在 ADDA shutdown 里先按 vendor 顺序把 ADDA/输出 mute 或 ramp 到 -40dB，等待，再关 DAC；需要 vendor `mt6768-dai-adda.c` 的 shutdown 序列。

### 当前基线

- boot：`boot-stable4.img`（内核 #31）
- 模块：`/lib/modules/7.1.0-mt6765+/extra/dandelion-audio/`，udev 自动加载
- 路由服务：`dandelion-audio.service`（只设连接矩阵，等 UCM 替代）
- PipeWire：`/etc/wireplumber/main.lua.d/51-alsa-format.lua` 强制 S16LE/44100
- 音量键：`gsd-media-keys` 绑定已补

## 2026-11-23：收尾状态

### 当前基线

- 内核 #34，镜像 `rootfs/ubuntu/boot/images/boot-stable8.img`
- 声卡 `mt6765-evk`，模块在 `/lib/modules/7.1.0-mt6765+/extra/dandelion-audio/`，udev 自动加载
- `dandelion-audio.service`：设连接矩阵 + 听筒路由
- PipeWire 强制 S16LE/44100
- 音量键可用（gsd-media-keys 绑定已补）

### 能用

- 听筒：干净播放，开始/结束 pop 已修（VAUD28 settle 500–1000us）
- 30 分钟以上稳定，无 freeze

### 外放（未完成）

- 主线 codec 的 LO/扬声器路径已按 vendor `Speaker_Amp_Change` 对齐
  （CON0/4/6/12/13、NCP、ZCD 全部一致，寄存器实测）
- 外部功放 RT5509（i2c3 0x34）不 ACK；逐个打开候选 PMIC 轨也无变化
- vendor 内核日志里同样 `-121`，回退 `MTK_SPK_NOT_SMARTPA`
- 需要原理图确认 RT5509 的 VDD/EN，或原厂 ROM 播放时的
  `MTK_SPK_TYPE_GET` / regulator / GPIO 状态

### 源码状态

- 测试用的 `-DDEBUG` 已从三个 Makefile 移除（当前已刷内核仍带，下次构建干净）
- `mt6357.c` 保留：VAUD28 settle、LO 的 `configure_downlinks`、CON6 CMFB/CON4 对齐
- 调试脚本/模块仍在 `rootfs/ubuntu/boot/` 和 `/root/audio`，不影响系统


## 2026-11-24：外放（扬声器）修复

### 根因
- codec LO 路径本身早已正常；外放需要板级 `extamp` 使能。
- vendor `Ext_Speaker_Amp_Change()` 对 GPIO153 做 **LOW -> 3 次 HIGH 脉冲 -> 保持 HIGH**；之前只试过静态高/低，功放没有真正上电。

### 内核修复（machine driver）
- `sound/soc/mediatek/mt6765/mt6765-mt6357.c`：
  - `devm_gpio_request_one(card->dev, 665, GPIOF_OUT_INIT_LOW, "spk-amp-en")`
  - 新增 DAPM supply `"Speaker Amp"`，路由 `{"Line out", NULL, "Speaker Amp"}`
  - `PRE_PMU` 执行 vendor 脉冲序列；功放关闭提前到 PCM `shutdown`
    （早于 codec LO 下电），避免结束爆音
- 仅更新内核模块，未改 DTB、未刷机；`mt6765-mt6357.ko` 已部署到 `/lib/modules/7.1.0-mt6765+/extra/dandelion-audio/`，开机自动加载。
- 旧模块备份：`/root/mt6765-mt6357.ko.orig`。

### 音量与噪声
- `Lineout` ALSA 值 18 -> ZCD_CON1 `0x0000`（最大），0 -> `0x0912`（最小）；25% 软件音量时硬件已在最小。
- 硬件 LO 固定最低，响度交给 PipeWire；默认 sink 音量 25%。
- 1 kHz 纯音干净；之前音乐中的“噪音”是高增益削波，降低音量后消失。

### 开机路由
- `dandelion-audio-mixer.sh` 改为外放：`Line Out Source=Playback`、`Handset/Headphone=Open`、`Lineout=0`。
- 听筒需要时把 `Handset Source` 改回 `Playback`。

### 验证
- DAPM 事件：播放前 GPIO 低 -> 播放中高 -> 停止后低（`/sys/kernel/debug/gpio`）。
- 25% 软件音量 + 硬件最低：音量合适，纯音干净。
