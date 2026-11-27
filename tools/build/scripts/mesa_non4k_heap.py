#!/usr/bin/env python3
"""mesa: PVR13_NON4K=1 routes the general heap to 'General NON-4K' (16 KB pages)"""
from pathlib import Path

p = Path('/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan/winsys/pvrsrvkm/pvr_srv.c')
s = p.read_text()

old = '''      if (pvr_srv_heap_needs_init(general_heap_idx, heap_name,
                                  PVR_SRV_GENERAL_HEAP_IDENT)) {
         general_heap_idx = i;
'''
new = '''      if (getenv("PVR13_NON4K") && general_heap_idx == -1 &&
          strncmp(heap_name, "General NON-4K",
                  sizeof("General NON-4K")) == 0) {
         general_heap_idx = i;
         fprintf(stderr, "pvr-heap: using '%s' (idx %u) as general heap\\n",
                 heap_name, i);

      } else if (pvr_srv_heap_needs_init(general_heap_idx, heap_name,
                                         PVR_SRV_GENERAL_HEAP_IDENT)) {
         general_heap_idx = i;
'''
assert s.count(old) == 1, 'heap select anchor'
s = s.replace(old, new, 1)

p.write_text(s)
print('non-4k heap switch added')
