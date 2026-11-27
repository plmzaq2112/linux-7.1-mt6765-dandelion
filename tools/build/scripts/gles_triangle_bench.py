#!/usr/bin/env python3
"""gles_triangle: GLES_LOOP=N benchmark of vendor 3D draw (no clear)"""
from pathlib import Path

p = Path('/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/scripts/gles_triangle.c')
s = p.read_text()

old = '''    glViewport(0, 0, w, hgt);
    glDrawArrays(GL_TRIANGLES, 0, 3);
    glFinish();
'''
new = '''    glViewport(0, 0, w, hgt);

    if (getenv("GLES_LOOP")) {
        int loop = atoi(getenv("GLES_LOOP"));
        struct timespec a, b;
        double tot = 0.0;

        for (int i = 0; i < loop; i++) {
            clock_gettime(CLOCK_MONOTONIC, &a);
            glDrawArrays(GL_TRIANGLES, 0, 3);
            glFinish();
            clock_gettime(CLOCK_MONOTONIC, &b);
            tot += (b.tv_sec - a.tv_sec) + (b.tv_nsec - a.tv_nsec) / 1e9;
        }
        printf("gles tri bench %dx%d: %d frames, %.2f ms/frame\\n", w, hgt, loop,
               1000.0 * tot / loop);
    }

    glDrawArrays(GL_TRIANGLES, 0, 3);
    glFinish();
'''
assert s.count(old) == 1, 'draw anchor'
s = s.replace(old, new, 1)

if '#include <time.h>' not in s:
    s = s.replace('#include <string.h>', '#include <string.h>\n#include <time.h>', 1)

p.write_text(s)
print('gles tri bench added')
