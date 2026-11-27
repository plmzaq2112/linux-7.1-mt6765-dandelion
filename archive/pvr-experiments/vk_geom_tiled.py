#!/usr/bin/env python3
"""vk_geom: VK_GEOM_TILED=1 renders into an OPTIMAL (tiled) image"""
from pathlib import Path

p = Path('/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/src/wayland/vk_geom.c')
s = p.read_text()

old = '''    VkQueue q;
    vkGetDeviceQueue(dev, qi, 0, &q);

    VkImageCreateInfo img = {'''
new = '''    VkQueue q;
    vkGetDeviceQueue(dev, qi, 0, &q);

    const int tiled = getenv("VK_GEOM_TILED") != NULL;

    VkImageCreateInfo img = {'''
assert s.count(old) == 1, 'queue anchor'
s = s.replace(old, new, 1)

old = '        .tiling = VK_IMAGE_TILING_LINEAR,'
new = '        .tiling = VK_IMAGE_TILING_LINEAR, /* overridden below when tiled */'
assert s.count(old) == 1, 'tiling anchor'
s = s.replace(old, new, 1)

old = '''    VkImage image;
    r = vkCreateImage(dev, &img, NULL, &image);'''
new = '''    if (tiled)
        img.tiling = VK_IMAGE_TILING_OPTIMAL;

    VkImage image;
    r = vkCreateImage(dev, &img, NULL, &image);'''
assert s.count(old) == 1, 'image create anchor'
s = s.replace(old, new, 1)

old = '''            mt = i; break;
        }
    }
    fprintf(stderr, "image mem: size=%llu type=%u\\n",
            (unsigned long long)mr.size, mt);'''
new = '''            mt = i; break;
        }
    }
    if (tiled &&
        !(mp.memoryTypes[mt].propertyFlags & VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT)) {
        for (uint32_t i = 0; i < mp.memoryTypeCount; i++) {
            if (mr.memoryTypeBits & (1u << i)) {
                mt = i;
                break;
            }
        }
    }
    fprintf(stderr, "image mem: size=%llu type=%u tiled=%d\\n",
            (unsigned long long)mr.size, mt, tiled);'''
assert s.count(old) == 1, 'memtype anchor'
s = s.replace(old, new, 1)

old = '''    void *ptr = NULL;
    r = vkMapMemory(dev, mem, 0, VK_WHOLE_SIZE, 0, &ptr);
    die("vkMapMemory", r);
'''
new = '''    if (tiled) {
        printf("tiled: readback skipped\\n");
        return 0;
    }

    void *ptr = NULL;
    r = vkMapMemory(dev, mem, 0, VK_WHOLE_SIZE, 0, &ptr);
    die("vkMapMemory", r);
'''
assert s.count(old) == 1, 'readback anchor'
s = s.replace(old, new, 1)

p.write_text(s)
print('tiled knob added')
