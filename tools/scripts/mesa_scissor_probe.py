#!/usr/bin/env python3
"""Scissor probes: PVR13_SCISSOR_SWAP=1 swaps the 16-bit halves of the scissor
words (xmin/xmax, ymin/ymax layout guess for 1.13), PVR13_DUMP_SCISSOR=1 prints
the packed words."""
from pathlib import Path

p = Path('/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan/pvr_arch_cmd_buffer.c')
s = p.read_text()

old = '''      if (cmd_buffer->scissor_array.size &&
          cmd_buffer->scissor_words.w0 == scissor_words.w0 &&
          cmd_buffer->scissor_words.w1 == scissor_words.w1) {
         return;
      }'''
new = '''      if (getenv("PVR13_SCISSOR_SWAP")) {
         scissor_words.w0 = (scissor_words.w0 >> 16) | (scissor_words.w0 << 16);
         scissor_words.w1 = (scissor_words.w1 >> 16) | (scissor_words.w1 << 16);
      }
      if (getenv("PVR13_DUMP_SCISSOR")) {
         fprintf(stderr,
                 "pvr-scissor: rect=(%u,%u %ux%u) w0=%08x w1=%08x idx=%u\\n",
                 x, y, width, height, scissor_words.w0, scissor_words.w1,
                 (unsigned)util_dynarray_num_elements(&cmd_buffer->scissor_array,
                                                      struct pvr_scissor_words));
      }

      if (cmd_buffer->scissor_array.size &&
          cmd_buffer->scissor_words.w0 == scissor_words.w0 &&
          cmd_buffer->scissor_words.w1 == scissor_words.w1) {
         return;
      }'''
assert s.count(old) == 1, 'scissor pack anchor'
s = s.replace(old, new, 1)

p.write_text(s)
print('scissor probes added')
