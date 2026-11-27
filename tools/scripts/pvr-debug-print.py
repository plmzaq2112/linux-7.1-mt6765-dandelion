import os

R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk"
p = os.path.join(R, "services/server/env/linux/pvr_debug.c")
s = open(p).read()

old = """#else
inline void PVRSRVDebugPrintf(IMG_UINT32 ui32DebugLevel,
					   const IMG_CHAR *pszFullFileName,
					   IMG_UINT32 ui32Line,
					   const IMG_CHAR *pszFormat,
					   ...)
{
}
#endif /* if 0 */
"""

new = """#else
inline void PVRSRVDebugPrintf(IMG_UINT32 ui32DebugLevel,
					   const IMG_CHAR *pszFullFileName,
					   IMG_UINT32 ui32Line,
					   const IMG_CHAR *pszFormat,
					   ...)
{
	va_list vaArgs;
	char buf[512];

	if (!(gPVRDebugLevel & ui32DebugLevel))
		return;

	va_start(vaArgs, pszFormat);
	vsnprintf(buf, sizeof(buf), pszFormat, vaArgs);
	va_end(vaArgs);

	pr_err("PVR_K:(%u) %s:%u %s\\n", ui32DebugLevel, pszFullFileName,
	       (unsigned int)ui32Line, buf);
}
#endif /* if 0 */
"""

if old not in s:
    raise SystemExit("stub not found")
open(p, "w").write(s.replace(old, new))
print("debug printf enabled")
