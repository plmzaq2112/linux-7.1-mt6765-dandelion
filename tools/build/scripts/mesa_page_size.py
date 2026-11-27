#!/usr/bin/env python3
"""mesa: allow overriding the PVR PMR page size (PVR13_PAGE_LOG2)

Hypothesis: 4 KB GPU pages make every new page a TLB miss handled by the
firmware (~40 us each), which would explain the 24x gap vs the vendor driver.
"""
from pathlib import Path

p = Path('/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan/winsys/pvrsrvkm/pvr_srv.c')
s = p.read_text()

old = '''   os_get_page_size(&srv_ws->base.page_size);
   srv_ws->base.log2_page_size = util_logbase2(srv_ws->base.page_size);
'''
new = '''   os_get_page_size(&srv_ws->base.page_size);
   srv_ws->base.log2_page_size = util_logbase2(srv_ws->base.page_size);

   /* Experimental: bigger GPU pages to cut TLB misses. */
   if (getenv("PVR13_PAGE_LOG2")) {
      uint32_t log2 = (uint32_t)atoi(getenv("PVR13_PAGE_LOG2"));

      if (log2 >= 12 && log2 <= 20) {
         srv_ws->base.log2_page_size = log2;
         srv_ws->base.page_size = 1U << log2;
         fprintf(stderr, "pvr-page: log2_page_size=%u\\n", log2);
      }
   }
'''
assert s.count(old) == 1, 'page size anchor'
s = s.replace(old, new, 1)

p.write_text(s)
print('page size override added')
