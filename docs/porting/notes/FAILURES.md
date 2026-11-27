# dandelion Ubuntu/Phosh 启动失败记录与修复

记录自 2026-11-21 的 bring-up。每条格式：现象 → 假设 → 操作 → 结果 → 结论。

## 1. 系统进入 emergency mode，`mount: /: must be superuser`

- 现象：Ubuntu 启动后 `local-fs.target` 失败，`systemctl is-system-running = maintenance`，屏幕黑屏。
- 假设：rootfs 文件属主错误导致 setuid 二进制失效。
- 操作：`ls -ln /usr/bin/mount` → `-rwsr-xr-x 1 1000 1000`；`ls -lnd /` → `1000 1000`。
- 结果：确认整个 rootfs 属主是 uid 1000（proot 构建 + `tar --numeric-owner` 原样保留）。
- 结论：`chown -R` 到 root 后，`mount` 以 root 执行时 euid 变成 1000，报 "must be superuser"。
- 修复：`chown -R 0:0`（注意：**chown 会清除所有 setuid/setgid 位**，必须重新补回）。

## 2. 登录一律失败（锁定/串口）

- 现象：`pam_unix(...): authentication failure`，密码确认正确仍失败。
- 假设 A：shadow 的“最后修改日期”在未来。
  - 操作：把 `sp_lstchg` 设为 0。
  - 结果：更糟，`pam_unix: expired password for user root (root enforced)`。
  - 结论：shadow 里 `lstchg=0` 表示**强制下次登录改密码**，不能用 0。正确值是过去的日期（如 19000）。
- 假设 B：`unix_chkpwd` 被 chown 清掉 setgid，无法读 shadow。
  - 操作：`chown root:shadow; chmod 2755 /sbin/unix_chkpwd`。
  - 结果：直接测试仍返回 7。
  - 结论：**测试方法错误**——该辅助程序走 PAM 协议，stdin 必须是 `密码 + NUL`，不是换行。
  - 验证：`printf '1234\0' | /sbin/unix_chkpwd dandelion nullok` → rc=0；错误密码 → rc=7。
- 最终结论：PAM 链路本身正常；锁屏失败的真实原因是屏幕键盘（`phosh-osk-stub`）未运行，锁屏只剩数字键盘，无法输入字母密码。

## 3. greetd 反复重启，phosh 不显示

- 现象：`greetd: check_children: greeter exited without creating a session`；`/var/log/phosh.log` 里 `cannot open display`。
- 原因 1：配置里用了 `/usr/libexec/phosh`（shell 本体，需要合成器），正确入口是 `phosh-session`（内部为 `phoc -S -E gnome-session --session=phosh`）。
- 原因 2：缺少 `gnome-session-bin`（`--no-install-recommends` 装漏），报 `gnome-session: not found`。
- 原因 3：缺少 `gnome-settings-daemon`，phosh 崩溃于 `Settings schema 'org.gnome.settings-daemon.peripherals.touchscreen' is not installed`。
- 原因 4：phoc 拒绝软件渲染，需 `WLR_RENDERER_ALLOW_SOFTWARE=1`。
- 修复：补齐上述包 + 启动脚本改用 `phosh-session` 并设置该环境变量。

## 4. 触摸驱动不加载

- 现象：`focaltech-touch.service: status=203/EXEC`。
- 原因：系统里没有 `kmod`，`/sbin/insmod` 不存在。
- 修复：安装 kmod，service 改为 `ExecStart=-/usr/sbin/insmod /lib/modules/focaltech_ts.ko`。
- 结果：`[FTS_TS] fts_ts_probe: Touch Screen(SPI BUS) driver probe successfully`，`/dev/input/event2` 为 `fts_ts`。

## 5. 锁屏“数字键盘无法输入字母密码”

- 原因：phosh 的屏幕键盘 D-Bus 服务文件缺失（包内没有 `sm.puri.OSK0.service`），phosh 无法拉起 OSK。
- 修复：手写 `/usr/share/dbus-1/services/sm.puri.OSK0.service`（`Exec=/usr/bin/phosh-osk-stub`）。

## 6. 电源键唤醒失败（疑似挂起后无法恢复）

- 现象：息屏后按电源键无反应，按音量键才亮。
- 原因：logind `HandlePowerKey=suspend`，而主线内核 suspend 在该机不能正常恢复。
- 修复：`/etc/systemd/logind.conf.d/99-dandelion.conf` 设为 `ignore`；mask `sleep/suspend/hibernate/hybrid-sleep.target`；`power-button-action=nothing`、`idle-delay=0`。

## 7. NetworkManager 不管 usb0

- 原因：`/usr/lib/NetworkManager/conf.d/10-globally-managed-devices.conf` 是 Server 默认，只管理 wifi/gsm。
- 修复：`/etc/NetworkManager/conf.d/99-usb0.conf` 覆盖 `unmanaged-devices=*,except:interface-name:usb0`，并启用 `usb0-static` 配置（169.254.195.201/16）。

## 8. TWRP 无法读写 p41

- 现象：`EXT4-fs: couldn't mount RDWR because of unsupported optional features (0x10000)`。
- 原因：mke2fs 1.47 默认启用 `orphan_file`，TWRP 的 4.19 内核不支持。
- 影响：只能在 7.1 内核（Ubuntu/Alpine/initramfs）里读写 p41。

## 9. 设备无 e2fsprogs，无法 mkfs

- 修复：从 Alpine 3.24 的 apk 提取 `e2fsprogs` + 依赖（musl），放到 p40 的 `/opt/e2fs`，用 `LD_LIBRARY_PATH` 运行 `mke2fs`/`tune2fs`。

## 10. 串口 ttyGS0 偶发“写超时”

- 现象：主机写入 COM5 超时，设备无输出。
- 原因：`u_serial.c:703 gs_close` 的 WARN（多个进程同时开关 ttyGS0 时触发），会把 ACM 端口卡死。
- 规避：只保留一个 getty；现在用 cmdline `console=ttyGS0` 让 systemd 自动生成 `serial-getty@ttyGS0`，并给它配 root 自动登录。

## 11. 音频 AFE 模块 insmod 整机硬挂（2026-11-22）

- 现象：oot-audio13.img（内核 #30）正常启动；insmod snd-soc-mtk-common.ko 后 insmod snd-soc-mt6765-pcm.ko，整机失去响应（ping 1/3，SSH 全部超时），只能长按电源键断电。
- 版本：采用接手人 14:09 的回退版（probe 只 enable_top_cg(MT6765_TOP_CG_AFE)，不开 AFE 总线时钟）。
- 对比：树内保留 mt6765_afe_enable_main_clk() 的版本（audio5/11 使用）AFE probe 能完成，卡点推进到 DAPM routes。
- 结论：enable_main_clk() 不是调试手段，而是访问 AFE 寄存器（syscon regmap）的必要条件；时钟门控关闭时总线访问会挂死，不是 printk 阻塞。
- 恢复：恢复 enable_main_clk / disable_main_clk，音频驱动改为模块加载，避免开机 probe 挂死导致无法 SSH。

## 12. `console=ttyGS0` 导致启动停滞（重要，已修复）

见 `UI-FIX.md`：内核 console 挂在 USB 串口上，主机不读取时 `printk` 阻塞，表现为“有背光无 UI / 启动要几分钟”。

注意：第 10 条曾建议用 `console=ttyGS0` 自动生成 getty，该建议已废弃。现在 cmdline 只保留 `console=tty0`，串口登录改用 userspace 的 `serial-getty@ttyGS0`。

## 13. 加载 AFE 模块整机冻结（根因：中断极性写反）

- 现象：`insmod snd-soc-mt6765-pcm.ko` 后数秒内整机失去响应（ping 部分丢失、SSH 超时），没有任何 oops/lockup 日志，pstore 为空。
- 二分：
  - `afe_stage=0`（probe 入口直接返回，不碰硬件、不注册中断）→ 稳定
  - `afe_stage=1`（包含 `devm_request_irq`）→ 必挂
  - 关闭显示 CMDQ（mmsys 去掉 mboxes）后仍然挂 → 与显示无关
- 根因：DT 里 AFE 中断写成 `interrupts = <0x00 0x99 0x04>`，`0x04` 是 `IRQ_TYPE_LEVEL_HIGH`；MTK AFE 是**低电平有效**（主线 mt8365 用 `IRQ_TYPE_LEVEL_LOW`）。极性写反后 GIC 认为中断线一直有效，注册 handler 后立即中断风暴，整机冻结且来不及打印。
- 修复：`0x04` → `0x08`（LEVEL_LOW），镜像 `boot-stable2.img`。
- 结果：AFE 正常 probe，机器驱动注册声卡成功，`/proc/asound/cards` 出现 `mt6765-evk`。
- 教训：MTK 外设中断基本都是 `IRQ_TYPE_LEVEL_LOW`，手写 DT 节点时不能默认 `0x04`。
