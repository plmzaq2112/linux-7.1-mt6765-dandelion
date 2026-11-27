import os

R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk"

# 1. APM init in the platform layer (vendor MTKInitHWAPM)
p = os.path.join(R, "services/system/rogue/rgx_mtk/pvr_platform_mt6765.c")
s = open(p).read()

apm = r'''
static void pvr_mtk_init_apm(void)
{
	static const struct { unsigned int off, val; } apm[] = {
		{ 0x504, 0x01a80000 }, { 0x508, 0x00080010 }, { 0x50c, 0x00100008 },
		{ 0x510, 0x00b800c8 }, { 0x514, 0x00b000c0 }, { 0x518, 0x00c000c8 },
		{ 0x51c, 0x00b000b8 }, { 0x520, 0x00d000d0 }, { 0x524, 0x00d000d0 },
		{ 0x528, 0x00d00000 },
	};
	unsigned int i;

	for (i = 0; i < ARRAY_SIZE(apm); i++)
		regmap_write(mfgcfg_rm, apm[i].off, apm[i].val);
	regmap_write(mfgcfg_rm, 0x24, 0x9004001b);
	regmap_write(mfgcfg_rm, 0x24, 0x8004001b);
}
'''

if "pvr_mtk_init_apm" not in s:
    s = s.replace("int MTKRGXDeviceInit(PVRSRV_DEVICE_CONFIG *psDevConfig)",
                  apm + "\nint MTKRGXDeviceInit(PVRSRV_DEVICE_CONFIG *psDevConfig)")
    s = s.replace('\t/* CLR register: writing 1 enables the gated clocks */',
                  '\tpvr_mtk_init_apm();\n\tdev_info(dev, "pvr-mtk: APM registers written\\n");\n\n'
                  '\t/* CLR register: writing 1 enables the gated clocks */')
    open(p, "w").write(s)
    print("APM init added")

# 2. firmware load logging
p = os.path.join(R, "services/server/env/linux/fwload.c")
s = open(p).read()
old = """	psFWImage = (OS_FW_IMAGE *)psFW;
"""
new = """	pr_info("pvr-mtk: firmware '%s' loaded, %zu bytes\\n",
		pszBVNCString, psFW->size);

	psFWImage = (OS_FW_IMAGE *)psFW;
"""
if "firmware '%s' loaded" not in s:
    s = s.replace(old, new, 1)
    open(p, "w").write(s)
    print("fw logging added")
