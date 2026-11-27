#!/usr/bin/env python3
"""解析 rgx_fwif_alignchecks.h 的 RGXFW_ALIGN_CHECKS_INIT 宏，输出 索引 -> 字段 映射。

用途：内核 RGXAlignmentCheck 只打印失配的索引（如 [21]），有了这张表可以直接
定位到具体结构体/成员，便于评估 UM 与 FW 的 ABI 差异范围。
"""
import re
import sys

path = sys.argv[1] if len(sys.argv) > 1 else None
if not path:
    print(__doc__)
    sys.exit(1)

src = open(path, encoding="utf-8", errors="replace").read()

m = re.search(r"#define\s+RGXFW_ALIGN_CHECKS_INIT\w*\s*(.*?)(?=\n\s*#define|\Z)", src, re.S)
if not m:
    sys.exit("RGXFW_ALIGN_CHECKS_INIT not found")
body = m.group(1)

entries = []
for raw in body.split("\n"):
    line = raw.strip()
    if not line or line.startswith("/*") or line.startswith("*"):
        continue
    line = line.rstrip("\\").strip()
    line = re.sub(r"/\*.*?\*/", "", line).strip()
    if not line:
        continue
    entries.append(line)

for i, e in enumerate(entries):
    print("%3d  %s" % (i, e))
print("\n总计 %d 项" % len(entries))
