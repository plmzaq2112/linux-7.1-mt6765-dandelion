#!/usr/bin/env python3
"""mesa: PVR13_HEAPS=1 prints the kernel heaps (name, size, page size)"""
from pathlib import Path

p = Path('/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan/winsys/pvrsrvkm/pvr_srv.c')
s = p.read_text()

old = '''   for (uint32_t i = 0; i < heap_count; i++) {
      result = pvr_srv_get_heap_details(srv_ws->base.render_fd,
                                        i,
                                        sizeof(heap_name),
                                        heap_name,
                                        NULL,
                                        NULL,
                                        NULL,
                                        NULL);'''
new = '''   for (uint32_t i = 0; i < heap_count; i++) {
      pvr_dev_addr_t dump_base;
      uint64_t dump_size = 0, dump_carveout = 0;
      uint32_t dump_log2 = 0;

      result = pvr_srv_get_heap_details(srv_ws->base.render_fd,
                                        i,
                                        sizeof(heap_name),
                                        heap_name,
                                        &dump_base,
                                        &dump_size,
                                        &dump_carveout,
                                        &dump_log2);
      if (getenv("PVR13_HEAPS")) {
         fprintf(stderr,
                 "pvr-heap[%u]: name=%s base=0x%llx size=0x%llx pages=0x%x log2=%u\\n",
                 i, heap_name, (unsigned long long)dump_base.addr,
                 (unsigned long long)dump_size,
                 (unsigned)(1U << dump_log2), dump_log2);
      }'''
assert s.count(old) == 1, 'heap loop anchor'
s = s.replace(old, new, 1)

p.write_text(s)
print('heap dump added')
