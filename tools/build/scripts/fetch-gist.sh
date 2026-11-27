#!/bin/bash
cd "$HOME"
timeout 60 curl -sL https://api.github.com/gists/bd991ef60538bf37115d0f6befb615ae -o gist.json
ls -l gist.json
python3 - <<'PY'
import json, os
p = os.path.expanduser("~/gist.json")
try:
    d = json.load(open(p))
except Exception as e:
    print("json error:", e)
    raise SystemExit(1)
out = os.path.expanduser("~/alpican-gist")
os.makedirs(out, exist_ok=True)
for name, f in d.get("files", {}).items():
    fp = os.path.join(out, name)
    open(fp, "w").write(f.get("content", ""))
    print(name, len(f.get("content", "")))
PY
