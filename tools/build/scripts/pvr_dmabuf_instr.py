#!/usr/bin/env python3
"""instrument the new dmabuf map path"""
from pathlib import Path

p = Path('/home/a12bbb/AI_Project/Redmi_9A/kernel_7.1_mainline/drivers/misc/pvr/ddk/services/server/env/linux/physmem_dmabuf.c')
s = p.read_text()

old = '''	eError = PMR_DevPhysAddr(psPMR, PAGE_SHIFT, uiNumPages, 0, pasAddr,
	                         pabValid);
	if (eError != PVRSRV_OK)
		goto err_free;
'''
new = '''	pr_info("pvr-dmabuf: map size=%llu pages=%u attach_dev=%s\\n",
	        (unsigned long long)uiSize, uiNumPages,
	        psAttachment->dev ? dev_name(psAttachment->dev) : "?");

	eError = PMR_DevPhysAddr(psPMR, PAGE_SHIFT, uiNumPages, 0, pasAddr,
	                         pabValid);
	pr_info("pvr-dmabuf: PMR_DevPhysAddr=%d phys0=%llx valid0=%d\\n", eError,
	        (unsigned long long)pasAddr[0].uiAddr, pabValid[0]);
	if (eError != PVRSRV_OK)
		goto err_free;
'''
assert s.count(old) == 1
s = s.replace(old, new, 1)

old2 = '''		for (i = 0; i < uiNumPages; i++) {
		if (!pabValid[i]) {'''
old2 = '''	for (i = 0; i < uiNumPages; i++) {
		if (!pabValid[i]) {'''
new2 = '''	for (i = 0; i < uiNumPages; i++) {
		if (!pabValid[i]) {
			pr_info("pvr-dmabuf: page %u invalid\\n", i);'''
assert s.count(old2) == 1
s = s.replace(old2, new2, 1)

old3 = '''	psTable->nents = psTable->orig_nents = uiSegs;
'''
new3 = '''	psTable->nents = psTable->orig_nents = uiSegs;
	pr_info("pvr-dmabuf: sg_table segs=%u nents=%u\\n", uiSegs,
	        psTable->nents);
'''
assert s.count(old3) == 1
s = s.replace(old3, new3, 1)

p.write_text(s)
print('instrumented')
