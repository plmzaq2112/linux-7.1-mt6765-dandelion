#!/bin/bash
set -e
D=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/logs
mkdir -p "$D"
curl -sL --max-time 90 -o "$D/stk3338.pdf" "https://uploadcdn.oneyac.com/attachments/files/brand_pdf/sensortek/STK3338-V.pdf"
ls -l "$D/stk3338.pdf"
pip3 install --quiet --break-system-packages pypdf 2>&1 | tail -1 || true
python3 - "$D/stk3338.pdf" "$D/stk3338.txt" <<'PY'
import sys
from pypdf import PdfReader
src, dst = sys.argv[1], sys.argv[2]
r = PdfReader(src)
txt = "\n".join((p.extract_text() or "") for p in r.pages)
open(dst, "w").write(txt)
print("pages", len(r.pages), "chars", len(txt))
PY
