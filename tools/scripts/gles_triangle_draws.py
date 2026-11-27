#!/usr/bin/env python3
"""gles_triangle: GLES_DRAWS=N (per-frame draw count scaling, vendor oracle)"""
from pathlib import Path

p = Path('/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/scripts/gles_triangle.c')
s = p.read_text()

old = '''    glDrawArrays(GL_TRIANGLES, 0, 3);
    glFinish();
'''
new = '''    {
        int ndraws = getenv("GLES_DRAWS") ? atoi(getenv("GLES_DRAWS")) : 1;

        if (ndraws < 1)
            ndraws = 1;
        for (int d = 0; d < ndraws; d++)
            glDrawArrays(GL_TRIANGLES, 0, 3);
    }
    glFinish();
'''
assert s.count(old) == 1, 'draw anchor'
s = s.replace(old, new, 1)

p.write_text(s)
print('gles draws knob added')
