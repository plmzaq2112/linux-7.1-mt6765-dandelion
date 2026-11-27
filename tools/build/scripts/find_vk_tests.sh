#!/bin/bash
echo "=== find vk_clear_test ==="
find /home/a12bbb /tmp -maxdepth 6 -name 'vk_clear_test*' 2>/dev/null | head -10
echo "=== find vk_probe ==="
find /home/a12bbb /tmp -maxdepth 6 -name 'vk_probe*' 2>/dev/null | head -10
echo "=== grep for vkCmdClearColorImage in scratch dirs ==="
grep -rl "vkCmdClearColorImage" /home/a12bbb 2>/dev/null | head -10
