#!/usr/bin/env python3
"""Add a gated TQ command dump to the DDK 1.13 transfer submit path."""
from pathlib import Path

P = Path("/home/a12bbb/AI_Project/Redmi_9A/kernel_7.1_mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxtransfer.c")
src = P.read_text(encoding="utf-8")

if "pvr_dump_tq" not in src:
    anchor = "PVRSRV_ERROR PVRSRVRGXSubmitTransferKM(RGX_SERVER_TQ_CONTEXT\t*psTransferContext,"
    idx = src.index(anchor)
    # insert module param + helper before the function
    helper = """static int pvr_dump_tq;
module_param(pvr_dump_tq, int, 0644);
MODULE_PARM_DESC(pvr_dump_tq, "Dump next N SubmitTransfer TQ command blobs to dmesg");

"""
    src = src[:idx] + helper + src[idx:]

    anchor2 = "\tIMG_UINT32   ui32PreparesDone = 0;\n"
    j = src.index(anchor2, idx) + len(anchor2)
    dump = """
\tif (unlikely(pvr_dump_tq > 0)) {
\t\tIMG_UINT32 ui32DumpPrepare;

\t\tpvr_dump_tq--;
\t\tfor (ui32DumpPrepare = 0; ui32DumpPrepare < ui32PrepareCount; ui32DumpPrepare++) {
\t\t\tpr_info("pvr-dump-TQ: prepare=%u size=%u\\n",
\t\t\t\tui32DumpPrepare, paui32FWCommandSize[ui32DumpPrepare]);
\t\t\tif (papaui8FWCommand[ui32DumpPrepare] && paui32FWCommandSize[ui32DumpPrepare])
\t\t\t\tprint_hex_dump(KERN_INFO, "pvr-dump-TQ: ", DUMP_PREFIX_OFFSET, 16, 4,
\t\t\t\t\t       papaui8FWCommand[ui32DumpPrepare],
\t\t\t\t\t       paui32FWCommandSize[ui32DumpPrepare], false);
\t\t}
\t}
"""
    src = src[:j] + dump + src[j:]

P.write_text(src, encoding="utf-8")
print("patched rgxtransfer.c")
