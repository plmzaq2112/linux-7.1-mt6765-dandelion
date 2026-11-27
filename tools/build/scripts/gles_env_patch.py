#!/usr/bin/env python3
from pathlib import Path

p = Path("/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/scripts/gles_clear.c")
s = p.read_text()

if "EGL_LIB" not in s:
    s = s.replace(
        '    void *he = dlopen("libEGL_mtk.so", RTLD_NOW);',
        '    const char *egln = getenv("EGL_LIB"); if (!egln) egln = "libEGL_mtk.so";\n'
        '    const char *gln = getenv("GLES_LIB"); if (!gln) gln = "libGLESv2_mtk.so";\n'
        '    void *he = dlopen(egln, RTLD_NOW);')
    s = s.replace(
        '    void *hg = dlopen("libGLESv2_mtk.so", RTLD_NOW);',
        '    void *hg = dlopen(gln, RTLD_NOW);')
    p.write_text(s)
    print("patched")
else:
    print("already patched")
