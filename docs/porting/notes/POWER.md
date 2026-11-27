# 充电 / 电量支持记录（2026-11-22）

## 硬件识别

- 充电 IC 实际接在 **i2c-5 (11016000) 0x6B**，PN 寄存器 REG0B=0x14（PN=2）→ **TI BQ25601**。
  - 厂商 DT 里的 SGM41513（0x1A）和 MT6370（0x34）**都没有应答**，是同一份 DT 里的备选方案。
- 电池电压来自 **MT6357 PMIC 的 AUXADC BATADC 通道**（channel 0），不是充电 IC。
  - 原始计数 26809，换算 `raw * 5400 / 32768` ≈ 4.42V，与满电状态吻合。

## 内核改动

### 1. bq256xx 充电器驱动（主线）

- `drivers/power/supply/bq256xx_charger.c`
  - of_match 表新增 `"ti,bq2560x_charger"`（厂商 DT 的 compatible），映射到 BQ25601。
  - **修复主线 bug 1**：OF 匹配时 `id = i2c_client_get_device_id()` 为 NULL，`strscpy(bq->model_name, id->name)` 直接 panic（`sized_strscpy` 空指针）。
  - **修复主线 bug 2**：`bq256xx_hw_init()` 中 `power_supply_get_battery_info()` 失败（非 -ENOMEM）时仍解引用未初始化的 `bat_info`，并且结尾把无效指针传给 `power_supply_put_battery_info()`。改为使用本地 `bat_defaults` 并跳过 put。
- 配置：`CONFIG_CHARGER_BQ256XX=y`

### 2. MT6357 AUXADC（主线）

- `drivers/iio/adc/mt6359-auxadc.c`
  - `IIO_CHAN_INFO_SCALE` 漏除 `2^realbits`，导致 processed 值放大 32768 倍（表现为 `voltage_now` 溢出为负数）。改为返回 `vref*num / (2^realbits*den)`。
  - BATADC 通道类型从 `IIO_RESISTANCE` 改为 `IIO_VOLTAGE`。
- 配置：`CONFIG_MEDIATEK_MT6359_AUXADC=y`

### 3. generic-adc-battery（主线）补容量

- `drivers/power/supply/generic-adc-battery.c`
  - 主线只上报 STATUS/VOLTAGE/CURRENT/TEMP，**没有 CAPACITY**。
  - 新增：读取 `monitored-battery` 的 `power_supply_battery_info`，用 `power_supply_find_ocv2cap_table()` + `power_supply_ocv2cap_simple()` 从电压算百分比。
- 配置：`CONFIG_GENERIC_ADC_BATTERY=y`

### 4. DTB 节点（合并 DTB 二进制级修改）

在根节点新增：

```dts
battery {
    compatible = "simple-battery";
    voltage-min-design-microvolt = <3400000>;
    voltage-max-design-microvolt = <4400000>;
    charge-full-design-microamp-hours = <5000000>;
    ocv-capacity-table-0 = <4380000 100 4300000 95 ... 3400000 0>;
    ocv-capacity-celsius = <25>;        /* 必需，否则内核不解析 OCV 表 */
    phandle = <0xc5>;
};

adc-battery {
    compatible = "adc-battery";
    io-channels = <&pmic_adc 0>;        /* MT6357_AUXADC_BATADC */
    io-channel-names = "voltage";
    monitored-battery = <&battery>;
};
```

## 结果

```
/sys/class/power_supply/adc-battery:
  voltage_now = 4416000 (4.416V)
  capacity    = 100
  status      = Charging
/sys/class/power_supply/bq256xx-charger:
  type=USB online=1 status=Full health=Good
```

UPower / Phosh：

```
DisplayDevice: present=yes state=charging percentage=100% icon=battery-full-charging
```

## 局限

- 电量是 **OCV 电压查表**，没有库仑计，百分比会随负载波动、精度有限。
- 未上报充电电流、电池温度。
- 充电 IC 没有中断线，状态靠轮询（UPower 会定时轮询）。
- 同时存在 `bq256xx-battery`（无容量）和 `adc-battery` 两个 battery supply，UPower 聚合显示正常，但后续可考虑精简。
- 启动偏慢（约 3–4 分钟）是独立问题，待查（e2scrub / 服务顺序 / i2c 探测）。

## 当前 boot 镜像

- 设备内：`/root/boot-power8.img`
- 本地：`rootfs/ubuntu/boot/boot-power8.img`（内核 #18 + DTB 含 battery/adc-battery）
- 回滚：`/root/boot-keys4.img`（按键修复版，无电源驱动）
