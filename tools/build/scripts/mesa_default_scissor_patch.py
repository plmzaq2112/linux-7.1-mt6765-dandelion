#!/usr/bin/env python3
"""Provide a full-screen ISP scissor table whenever the application did not
set a scissor.

The 1.13 GE8320 firmware defaults to a half-width/half-height scissor when
isp_scissor_base is 0 (observed: 64x64 clears only 32x32, 32x32 only 16x16).
The vendor GLES clear always supplies a valid table at 0x48.
"""
from pathlib import Path

P = Path("/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan/pvr_arch_cmd_buffer.c")
s = P.read_text(encoding="utf-8")

if "pvr_cmd_buffer_fill_default_scissor" in s:
    print("already patched")
    raise SystemExit(0)

# Insert a helper before pvr_cmd_buffer_upload_tables.
anchor = """static VkResult
pvr_cmd_buffer_upload_tables(struct pvr_device *device,
                             struct pvr_cmd_buffer *cmd_buffer,
                             struct pvr_sub_cmd_gfx *const sub_cmd)
{"""
helper = """static void
pvr_cmd_buffer_fill_default_scissor(struct pvr_cmd_buffer *cmd_buffer,
                                    const struct pvr_sub_cmd_gfx *sub_cmd)
{
   const uint32_t width = sub_cmd->rstate->width;
   const uint32_t height = sub_cmd->rstate->height;
   const uint32_t tiles_x = DIV_ROUND_UP(width, 16);
   const uint32_t tiles_y = DIV_ROUND_UP(height, 16);
   const uint32_t count = tiles_x * tiles_y;

   /* One full-screen entry per 16x16 tile; the 1.13 firmware indexes the
    * scissor table per tile/region.
    */
   for (uint32_t i = 0; i < count; i++) {
      struct pvr_scissor_words words;

      pvr_csb_pack (&words.w0, IPF_SCISSOR_WORD_0, word0) {
         word0.scw0_xmin = 0;
         word0.scw0_xmax = width;
      }

      pvr_csb_pack (&words.w1, IPF_SCISSOR_WORD_1, word1) {
         word1.scw1_ymin = 0;
         word1.scw1_ymax = height;
      }

      util_dynarray_append(&cmd_buffer->scissor_array,
                           struct pvr_scissor_words,
                           words);
   }
}

static VkResult
pvr_cmd_buffer_upload_tables(struct pvr_device *device,
                             struct pvr_cmd_buffer *cmd_buffer,
                             struct pvr_sub_cmd_gfx *const sub_cmd)
{"""
assert s.count(anchor) == 1
s = s.replace(anchor, helper, 1)

old = """   if (cmd_buffer->scissor_array.size > 0) {
      result = pvr_gpu_upload(device,
                              device->heaps.general_heap,
                              util_dynarray_begin(&cmd_buffer->scissor_array),
                              cmd_buffer->scissor_array.size,
                              cache_line_size,
                              &sub_cmd->scissor_bo);
"""
new = """   if (cmd_buffer->scissor_array.size == 0)
      pvr_cmd_buffer_fill_default_scissor(cmd_buffer, sub_cmd);

   if (cmd_buffer->scissor_array.size > 0) {
      result = pvr_gpu_upload(device,
                              device->heaps.general_heap,
                              util_dynarray_begin(&cmd_buffer->scissor_array),
                              cmd_buffer->scissor_array.size,
                              cache_line_size,
                              &sub_cmd->scissor_bo);
"""
assert s.count(old) == 1
s = s.replace(old, new, 1)

P.write_text(s, encoding="utf-8")
print("patched default full-screen scissor")
