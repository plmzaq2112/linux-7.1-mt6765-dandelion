R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk"
p = R + "/services/server/env/linux/physmem_osmem_linux.c"
s = open(p).read()

old = """\t\tvirt_addr = dma_alloc_coherent(dev, alloc_size, &bus_addr, gfp_flags);
#endif"""
new = """\t\tvirt_addr = dma_alloc_coherent(dev, alloc_size, &bus_addr, gfp_flags);
\t\tpr_info("pvr-mtk: cma alloc dev=%s size=%zu gfp=%#x va=%px dma=0x%llx\\n",
\t\t        dev ? dev_name(dev) : "NULL", alloc_size, gfp_flags,
\t\t        virt_addr, (unsigned long long)bus_addr);
#endif"""
assert old in s, "pattern not found"
s = s.replace(old, new, 1)
open(p, "w").write(s)
print("cma alloc log added")
