# dandelion 按键修复记录

日期：2026-11-22

## 现象

| 按键 | 修复前 |
|---|---|
| 音量上 | 变成“减音量” |
| 音量下 | 无反应 |
| 电源 | 无输入事件（但 PMIC IRQ 有触发） |

## 事实与根因

### 1. 音量键：矩阵键盘驱动没 probe

- GPIO93 的 pinmux 是 `KPCOL0`，音量键走 MTK 键盘矩阵，不是普通 GPIO。
- dmesg：
  ```
  mt6779-keypad 10010000.keyboard: number of keypad rows/columns not specified
  mt6779-keypad ... probe with driver mt6779-keypad failed with error -22
  ```
- DT 里只有厂商属性 `mediatek,kpd-*`，缺主线驱动要的 `keypad,num-rows` / `keypad,num-columns` / `linux,keymap`。
- 当时唯一能工作的 `gpio-keys` 节点是遗留 hack：物理“音量上”键被写成 `KEY_VOLUMEDOWN(114)`。

### 2. 电源键：主线没启用松开中断

- `mtk-pmic-keys` 只请求了按下中断，驱动在线程化处理里读 `TOPSTATUS`。
- 诊断打印（临时补丁）：
  ```
  DANDELION key irq=187 code=116 raw=0xc mask=0x2 deb=0x0 pressed=1
  ```
  按下能识别，但没有松开事件 → 按键卡住，甚至会断开 phosh 会话。
- 主线 MFD 其实已经注册了 4 个命名中断：
  ```
  powerkey / homekey / powerkey_r / homekey_r   (hwirq 48/49/50/51)
  ```
  只是 input 驱动里 `mt6357_regs` 少了 `.key_release_irq = true`（厂商版本有）。

## 修复

### A. DTB（音量键）

在 **运行中的合并 DTB** 上修改（`boot-keys.img` / `boot/assets/dandelion-keys-patched.dtb`）：

```
keyboard@10010000 {
    status = "okay";
    keypad,num-rows = <9>;
    keypad,num-columns = <8>;
    debounce-delay-ms = <15>;
    linux,keymap = <0x00000073 0x00010072>;  /* (0,0)=KEY_VOLUMEUP, (0,1)=KEY_VOLUMEDOWN */
};
```

同时删除误映射的 `gpio-keys` 节点（它占用 KPCOL0）。

说明：运行中的 DTB 不是由 `03-mainline-7.1` 源码直接构建的，而是 `~/r96-gpu.dtb`（已合并厂商属性）。因此本次是对合并后的 DTB 做反编译 + 修改 + 重编译。补丁后的 dts/dtb 已保存在 `rootfs/ubuntu/boot/`。

### B. 驱动（电源键）

`drivers/input/keyboard/mtk-pmic-keys.c` 中 `mt6357_regs` 增加一行：

```c
.key_release_irq = true,
```

然后重新编译 `Image.gz` 并重打包 boot。

## 结果

```
KEY_POWER       value=1 / 0
KEY_VOLUMEUP    value=1 / 0
KEY_VOLUMEDOWN  value=1 / 0
```

- 音量上/下方向正确
- 电源键有完整的按下/松开
- 电源短按 = 锁屏（logind `HandlePowerKey=lock`）
- 长按 2 秒 = PMIC 硬件关机（DT `power-off-time-sec = 2`）

## 当前 boot 镜像

- 设备内：`/root/boot-keys4.img`（keypad DTB + release IRQ 内核，#13）
- 回滚：`/root/boot-prev.img`（最早版本）、`/root/boot-keys-prev.img`（仅 keypad DTB）
- 本地：`rootfs/ubuntu/boot/boot-keys4.img`

## 未完成

- DTB 修改尚未回写到内核源码树（当前是对合并 DTB 的二进制级修改）。
- 若以后重新构建 DTB，需要把上述 keypad 节点和删除 gpio-keys 的改动加到对应的 DTS 源。
