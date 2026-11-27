# UI 起不来 / 启动缓慢 修复记录（2026-11-22）

## 现象

- 经常出现：有背光、无 UI，看起来像死机，随后看门狗重启
- 启动有时要几分钟；有时卡在 Mi logo
- SSH / NCM 不出现

## 根因（已确认）

cmdline 里有：

```
console=ttyGS0,115200
```

内核把 USB 串口（ACM gadget）当作 **kernel console**。当主机不读取串口时，tty 缓冲写满，`printk` 会**阻塞**，启动停留在很早期：

- 表现为背光/logo，无 UI
- usb0 未初始化 → SSH/NCM 不可用
- 看门狗超时后重启

实验证据：打开串口持续读取后，系统立刻继续启动（日志从卡住处直接跳到 `session-1`，时间戳已到 1611 秒）。

## 修复

从 boot 镜像 cmdline 中删除 `console=ttyGS0,115200`，保留：

```
console=tty0
```

串口调试改为 **userspace getty**（不再作为内核 console）：

```
/etc/systemd/system/getty.target.wants/serial-getty@ttyGS0.service
```

（`serial-getty@ttyGS0.service.d/autologin.conf` 已配置 root 自动登录）

## 结果

| 项 | 修复前 | 修复后 |
|---|---|---|
| 无串口读取时启动 | 卡住/看门狗重启 | 正常 |
| 启动时间 | 数分钟 | **2.0s kernel + 12.0s userspace = 14s** |
| graphical.target | 可能不达 | 9.5s 达到 |
| 串口调试 | 内核 console（会阻塞） | userspace getty（不影响启动） |

两次冷启动（不读串口）均正常进入 Phosh。

## 当前镜像

- 设备：`/root/boot-ui-fix.img`（= audio2 内核 + 去掉 ttyGS0 console 的 cmdline）
- 本地：`rootfs/ubuntu/boot/boot-ui-fix.img`
- 内核版本：#21（2026-11-22 10:43）
- 内容：电量/充电、按键、触摸、显示、USB 网络 + 串口 getty

## 遗留

- 音频 AFE 驱动仍在调试（与本问题无关），见 `audio-handover/`。
- 以后重新打包 boot 时，**不要再把 `console=ttyGS0` 加回 cmdline**。
