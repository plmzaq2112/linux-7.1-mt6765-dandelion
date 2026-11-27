#!/usr/bin/env python3
"""more dmabuf instrumentation: attach / vmap entry / vmap ok"""
from pathlib import Path

p = Path('/home/a12bbb/AI_Project/Redmi_9A/kernel_7.1_mainline/drivers/misc/pvr/ddk/services/server/env/linux/physmem_dmabuf.c')
s = p.read_text()

old = '''static int PVRDmaBufOpsVmap(struct dma_buf *psDmaBuf, struct iosys_map *psMap)
{
'''
new = '''static int PVRDmaBufOpsVmap(struct dma_buf *psDmaBuf, struct iosys_map *psMap)
{
	pr_info("pvr-dmabuf: vmap called\\n");
'''
assert s.count(old) == 1, 'vmap entry'
s = s.replace(old, new, 1)

old2 = '''	iosys_map_set_vaddr(psMap, pvAddr);
	return 0;
'''
new2 = '''	iosys_map_set_vaddr(psMap, pvAddr);
	pr_info("pvr-dmabuf: vmap ok addr=%px pages=%u\\n", pvAddr, uiNumPages);
	return 0;
'''
assert s.count(old2) == 1, 'vmap ok'
s = s.replace(old2, new2, 1)

old3 = '''	psAttachment->priv = NULL;
	return 0;
}
'''
new3 = '''	psAttachment->priv = NULL;
	pr_info("pvr-dmabuf: attach dev=%s\\n",
	        psAttachment->dev ? dev_name(psAttachment->dev) : "?");
	return 0;
}
'''
assert s.count(old3) == 1, 'attach'
s = s.replace(old3, new3, 1)

p.write_text(s)
print('instrumented attach/vmap')
