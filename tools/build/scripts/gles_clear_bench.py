#!/usr/bin/env python3
"""gles_clear: GLES_LOOP=N benchmark of vendor clear+swap"""
from pathlib import Path

p = Path('/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/scripts/gles_clear.c')
s = p.read_text()

old = '''    glClearColor(r, g, b, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT);
    glFinish();
    eglSwapBuffers(d, s);
'''
new = '''    glClearColor(r, g, b, 1.0f);

    if (getenv("GLES_LOOP")) {
        int loop = atoi(getenv("GLES_LOOP"));
        struct timespec a, bb;
        double tot = 0.0;
        for (int i = 0; i < loop; i++) {
            clock_gettime(CLOCK_MONOTONIC, &a);
            glClear(GL_COLOR_BUFFER_BIT);
            glFinish();
            eglSwapBuffers(d, s);
            clock_gettime(CLOCK_MONOTONIC, &bb);
            tot += (bb.tv_sec - a.tv_sec) + (bb.tv_nsec - a.tv_nsec) / 1e9;
        }
        printf("gles bench %dx%d: %d frames, %.2f ms/frame\\n", w, hgt, loop,
               1000.0 * tot / loop);
    }

    glClear(GL_COLOR_BUFFER_BIT);
    glFinish();
    eglSwapBuffers(d, s);
'''
assert s.count(old) == 1, 'clear anchor'
s = s.replace(old, new, 1)

if '#include <time.h>' not in s:
    s = s.replace('#include <stdint.h>', '#include <stdint.h>\n#include <time.h>', 1)

p.write_text(s)
print('gles loop bench added')
