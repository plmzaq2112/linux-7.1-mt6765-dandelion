#!/usr/bin/env python3
"""vk_ds: separate colour images for the depth pass and the blend pass"""
from pathlib import Path

p = Path('/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/src/wayland/vk_ds.c')
s = p.read_text()

# A. second colour image
old = '''    VkImageViewCreateInfo cvci = {'''
new = '''    VkDeviceMemory cmem2;
    uint64_t csize2;
    VkImage color2 = make_image(dev, pd, W, H, VK_FORMAT_R8G8B8A8_UNORM,
                                VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT |
                                    VK_IMAGE_USAGE_TRANSFER_SRC_BIT,
                                &cmem2, &csize2);

    VkImageViewCreateInfo cvci = {'''
assert s.count(old) == 1, 'cvci anchor'
s = s.replace(old, new, 1)

old = '''    VkImageViewCreateInfo dvci = cvci;'''
new = '''    VkImageViewCreateInfo cvci2 = cvci;
    cvci2.image = color2;
    VkImageView cview2;
    die("vkCreateImageView(color2)", vkCreateImageView(dev, &cvci2, NULL, &cview2));

    VkImageViewCreateInfo dvci = cvci;'''
assert s.count(old) == 1, 'dvci anchor'
s = s.replace(old, new, 1)

# B. fb2 uses the second colour image
old = '''    fbci.renderPass = rp2;
    fbci.attachmentCount = 1;
    fbci.pAttachments = &cview;'''
new = '''    fbci.renderPass = rp2;
    fbci.attachmentCount = 1;
    fbci.pAttachments = &cview2;'''
assert s.count(old) == 1, 'fb2 anchor'
s = s.replace(old, new, 1)

# C. add the blend quad
old = '''    float verts[12][7] = {'''
new = '''    float verts[18][7] = {'''
assert s.count(old) == 1, 'verts decl'
s = s.replace(old, new, 1)

old = '''        { -1.0f,  1.0f, 0.9f, 1, 0, 0, 1 },
    };'''
new = '''        { -1.0f,  1.0f, 0.9f, 1, 0, 0, 1 },
        /* blend quad: red, alpha 0.5 */
        { -1.0f, -1.0f, 0.0f, 1, 0, 0, 0.5f },
        {  1.0f, -1.0f, 0.0f, 1, 0, 0, 0.5f },
        { -1.0f,  1.0f, 0.0f, 1, 0, 0, 0.5f },
        {  1.0f, -1.0f, 0.0f, 1, 0, 0, 0.5f },
        {  1.0f,  1.0f, 0.0f, 1, 0, 0, 0.5f },
        { -1.0f,  1.0f, 0.0f, 1, 0, 0, 0.5f },
    };'''
assert s.count(old) == 1, 'verts rows'
s = s.replace(old, new, 1)

# D. pass 2 draws the blend quad
old = '''    vkCmdBindVertexBuffers(cb, 0, 1, &vbo, &off);
    vkCmdDraw(cb, 6, 1, 0, 0);  /* green z=0.1 quad, now alpha 1 -> opaque */'''
new = '''    vkCmdBindVertexBuffers(cb, 0, 1, &vbo, &off);
    vkCmdDraw(cb, 6, 1, 12, 0);  /* red, alpha 0.5, over blue */'''
assert s.count(old) == 1, 'pass2 draw'
s = s.replace(old, new, 1)

# E. readback of both colour images
old = '''    printf("depth: center=%u corner=%u (D16 raw)\\n",
           d[(H / 2) * W + W / 2], d[0]);
    vkUnmapMemory(dev, cmem);
    vkUnmapMemory(dev, dmem);
    return (green && red) ? 0 : 2;'''
new = '''    printf("depth: center=%u corner=%u (D16 raw)\\n",
           d[(H / 2) * W + W / 2], d[0]);

    void *c2ptr = NULL;
    die("map color2", vkMapMemory(dev, cmem2, 0, VK_WHOLE_SIZE, 0, &c2ptr));
    {
        uint32_t *p2 = c2ptr;
        printf("blend: center=%08x corner=%08x (expect ~80007f80)\\n",
               p2[(H / 2) * W + W / 2], p2[0]);
        vkUnmapMemory(dev, cmem2);
    }

    vkUnmapMemory(dev, cmem);
    vkUnmapMemory(dev, dmem);
    return (green && red) ? 0 : 2;'''
assert s.count(old) == 1, 'readback anchor'
s = s.replace(old, new, 1)

p.write_text(s)
print('vk_ds patched')
