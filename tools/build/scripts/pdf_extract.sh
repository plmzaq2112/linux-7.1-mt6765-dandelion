#!/bin/bash
set -e
pip3 install --quiet pypdf 2>&1 | tail -2 || true
ls /tmp/stk3338.pdf
python3 - <<'PY'
from pypdf import PdfReader
r = PdfReader("/tmp/stk3338.pdf")
out = []
for p in r.pages:
    out.append(p.extract_text() or "")
txt = "\n".join(out)
open("/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/logs/stk3338.txt", "w").write(txt)
print("chars", len(txt), "pages", len(r.pages))
PY
