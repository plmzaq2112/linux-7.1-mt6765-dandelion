#!/usr/bin/env python3
"""把 TI 的 libsrv_um.so 里 UM 侧 BVNC 硬校验改成"期望值 = 本机 GE8320"。

背景（反汇编证据，TI 1.13.5776728 libsrv_um.so）：
    vaddr 0x1222c 附近的 CompatibilityCheck 函数：
        121d0: cmp w2, #0xd0        ; 期望 BVNC 的 B 分量 = 208
        1222c: cmp w3, #0x13e       ; 期望 BVNC 的 V 分量 = 318
        1223c: b.ne 0x12380         ; 不匹配 -> 打日志后返回错误
    日志串（vaddr 0x56160）："%s: Unsupported core version (expected %d.%d.%d.%d, detected %d.%d.%d.%d)"

用法：
    python patch-ti-um-bvnc.py <输入 libsrv_um.so> [输出文件]
    默认输出到 <输入>.ge8320

改完的等价效果：把"我必须是 22.0.208.318"改成"我必须是 22.0.104.18"，
不是简单跳过检查，后面继续走正常的初始化路径。
"""
import sys

# (文件偏移, 原指令, 新指令, 说明)
# 文件偏移 = vaddr - 0x2000（该库 .text 段 vaddr 0x9ce0 / off 0x4a008 之前的映射
# 由本脚本运行时按 program header 计算，这里直接用 va->file 转换表）
PATCHES = [
    (0x121D0, 0x7103405F, 0x7101A05F, "cmp w2,#0xd0 -> #0x68  (B: 208 -> 104)"),
    (0x1222C, 0x7104F87F, 0x7100487F, "cmp w3,#0x13e -> #0x12 (V: 318 -> 18)"),
    (0x1223C, 0x54000A21, 0xD503201F, "b.ne mismatch -> nop"),
]


def va_to_off(data, va):
    import struct
    phoff = struct.unpack_from("<Q", data, 0x20)[0]
    phentsize, phnum = struct.unpack_from("<HH", data, 0x36)
    for i in range(phnum):
        p_type, _flags, p_off, p_va, _pa, p_fsz = struct.unpack_from(
            "<IIQQQQ", data, phoff + i * phentsize)
        if p_type == 1 and p_va <= va < p_va + p_fsz:
            return p_off + (va - p_va)
    raise ValueError("va %#x not in any PT_LOAD" % va)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else src + ".ge8320"
    data = bytearray(open(src, "rb").read())

    changed = 0
    for va, old, new, note in PATCHES:
        off = va_to_off(data, va)
        cur = int.from_bytes(data[off:off + 4], "little")
        if cur == new:
            print("  skip   %#x (已是新指令)" % va)
            continue
        if cur != old:
            print("  !!     %#x 期望 %08x 实际 %08x，跳过" % (va, old, cur))
            continue
        data[off:off + 4] = new.to_bytes(4, "little")
        changed += 1
        print("  patch  %#x  %08x -> %08x  %s" % (va, old, new, note))

    open(dst, "wb").write(data)
    print("写入 %s（%d 处）" % (dst, changed))
    return 0 if changed else 2


if __name__ == "__main__":
    sys.exit(main())
