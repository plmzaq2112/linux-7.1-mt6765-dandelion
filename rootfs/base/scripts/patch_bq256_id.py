import os

p = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/power/supply/bq256xx_charger.c")
s = open(p).read()

old = '\tstrscpy(bq->model_name, id->name, sizeof(bq->model_name));'
new = """\tif (id)
\t\tstrscpy(bq->model_name, id->name, sizeof(bq->model_name));
\telse
\t\tstrscpy(bq->model_name, client->name, sizeof(bq->model_name));"""

if new in s:
    print("already patched")
else:
    assert old in s, "anchor not found"
    s = s.replace(old, new, 1)
    open(p, "w").write(s)
    print("patched null id")
