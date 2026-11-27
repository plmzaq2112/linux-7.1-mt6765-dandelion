# 振动马达（MT6357 VIBR LDO）

最后更新：2026-11-24

## 结论（FACT）

- 硬件：振动马达由 MT6357 的 `vibr` LDO 供电，**靠电压调强度**，不是 GPIO/PWM 开关
- 原厂：DTB 里 `vibrator@0 { compatible = "mediatek,vibrator"; vib_timer/vib_limit/vib_vol }`，
  驱动在 `drivers/leds/regulator-vibrator.c`
- 主线：原来没有该驱动；已移植 vendor 版本（GPL-2.0）

## 实现

### 1. 驱动

- 源文件：`kernel/modules/regulator-vibrator/regulator-vibrator.c`（vendor 4.19 版本，做了三处适配）
  - 增加 `#include <linux/of.h>`（`of_property_read_u32`）
  - `hrtimer_init()` → `hrtimer_setup(&timer, fn, CLOCK_MONOTONIC, HRTIMER_MODE_REL)`
  - `.remove` 回调改为 `void`（7.x 平台驱动签名）
- 编译为模块：`regulator-vibrator.ko`（446 KB）

### 2. 设备树

```dts
vibrator {
	compatible = "regulator-vibrator";
	vib-supply = <0x8f>;      /* ldo-vibr，1.2–3.3V */
	min-volt = <0x1e8480>;    /* 2.0V */
	max-volt = <0x2dc6c0>;    /* 3.0V */
	min-limit = <0x0f>;       /* 15ms */
	max-limit = <0x3a98>;     /* 15s */
};
```

`0x8f` 是 `/soc/pwrap@1000d000/pmic/regulators/ldo-vibr` 的 phandle（`regulator-name = "vibr"`）。

### 3. 用户接口

```
/sys/class/leds/vibrator/duration     # 毫秒
/sys/class/leds/vibrator/activate     # 写 1 触发一次
/sys/class/leds/vibrator/state        # 当前状态
```

实测：

```sh
echo 400 > /sys/class/leds/vibrator/duration
echo 1   > /sys/class/leds/vibrator/activate
```

400ms × 3，用户确认有明显振感（FACT）。

### 4. 开机自动加载与权限

- `/lib/modules/$(uname -r)/extra/regulator-vibrator.ko`
- `/etc/modules-load.d/regulator-vibrator.conf` → `regulator-vibrator`
- `/etc/systemd/system/vibrator-perms.service`：启动后把
  `activate/state/duration/brightness` 设为 `root:input 0660`
- `dandelion` 用户加入 `input` 组（已验证非 root 可写）

## 注意

- 不要给 `vibr` 上电却不管控制信号：直接把 LDO 打开（调试用 `rail_en.ko name=vibr`），
  马达会一直转，直到 LDO 关闭（曾发生过 90 秒连续振动）
- `regulator-vibrator.c` 里的闪烁（PWM-like）是靠 hrtimer 反复开关 LDO 实现的，
  高频触发时会有轻微噪音，属于预期行为

## 相关镜像

- `boot-stable18-vibr.img`：加入振动节点
- `boot-stable19-i2carb.img`：在 18 基础上加了 i2c1/2/5 的 arbiter 时钟（传感器实验，无效果但保留）
