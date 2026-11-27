import re, os

p = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/pinctrl/mediatek/pinctrl-mtk-mt6765.h")
txt = open(p).read()

# split on MTK_PIN( entries
entries = txt.split("MTK_PIN(")
pins = {}
cur = None
for e in entries[1:]:
    m = re.match(r'\s*(\d+),\s*"([^"]+)"', e)
    if not m:
        continue
    pin = int(m.group(1))
    for fm in re.finditer(r'MTK_FUNCTION\((\d+),\s*"([^"]+)"\)', e):
        func, name = int(fm.group(1)), fm.group(2)
        pins.setdefault(name, (pin, func))

for bus in range(7):
    for kind in ("SCL", "SDA"):
        name = f"{kind}{bus}"
        if name in pins:
            print(name, "pin", pins[name][0], "func", pins[name][1])
        else:
            print(name, "MISSING")
