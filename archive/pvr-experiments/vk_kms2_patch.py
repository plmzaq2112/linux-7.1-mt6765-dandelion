#!/usr/bin/env python3
"""vk_kms2: import contiguous DRM dumb buffers into Vulkan instead of exporting"""
from pathlib import Path

p = Path('/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/src/wayland/vk_kms2.c')
s = p.read_text()

# --- 1. swap frame_init for three functions ---------------------------------
start = s.index('static int frame_init(')
end = s.index('static void build_scene(')

new_funcs = r'''static int frame_view_and_fb(struct vk_state *v, struct frame *f, uint32_t w,
                            uint32_t h, VkFormat fmt)
{
    VkImageViewCreateInfo vci = {
        .sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO,
        .image = f->image,
        .viewType = VK_IMAGE_VIEW_TYPE_2D,
        .format = fmt,
        .subresourceRange = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1 },
    };
    CHECK_VK(vkCreateImageView(v->dev, &vci, NULL, &f->view));

    VkFramebufferCreateInfo fbci = {
        .sType = VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO,
        .renderPass = v->rp,
        .attachmentCount = 1,
        .pAttachments = &f->view,
        .width = w,
        .height = h,
        .layers = 1,
    };
    CHECK_VK(vkCreateFramebuffer(v->dev, &fbci, NULL, &f->fb));
    return 0;
}

static VkImageCreateInfo linear_image_ci(uint32_t w, uint32_t h, VkFormat fmt,
                                         const void *pnext)
{
    VkImageCreateInfo ci = {
        .sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO,
        .pNext = pnext,
        .imageType = VK_IMAGE_TYPE_2D,
        .format = fmt,
        .extent = { w, h, 1 },
        .mipLevels = 1,
        .arrayLayers = 1,
        .samples = VK_SAMPLE_COUNT_1_BIT,
        .tiling = VK_IMAGE_TILING_LINEAR,
        .usage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT |
                 VK_IMAGE_USAGE_TRANSFER_SRC_BIT,
        .sharingMode = VK_SHARING_MODE_EXCLUSIVE,
        .initialLayout = VK_IMAGE_LAYOUT_UNDEFINED,
    };
    return ci;
}

/* Import a (contiguous) dma-buf as the render target. */
static int frame_init_import(struct vk_state *v, struct frame *f, uint32_t w,
                             uint32_t h, VkFormat fmt, int fd)
{
    memset(f, 0, sizeof(*f));
    f->dmabuf_fd = fd;

    VkExternalMemoryImageCreateInfo ext = {
        .sType = VK_STRUCTURE_TYPE_EXTERNAL_MEMORY_IMAGE_CREATE_INFO,
        .handleTypes = VK_EXTERNAL_MEMORY_HANDLE_TYPE_DMA_BUF_BIT_EXT,
    };
    VkImageCreateInfo ci = linear_image_ci(w, h, fmt, &ext);
    VkResult r = vkCreateImage(v->dev, &ci, NULL, &f->image);
    if (r != VK_SUCCESS) {
        fprintf(stderr, "import: vkCreateImage -> %d\n", r);
        return -1;
    }

    VkMemoryRequirements mr;
    vkGetImageMemoryRequirements(v->dev, f->image, &mr);

    uint32_t type_bits = mr.memoryTypeBits;
    if (v->get_fd_props) {
        VkMemoryFdPropertiesKHR fp = {
            .sType = VK_STRUCTURE_TYPE_MEMORY_FD_PROPERTIES_KHR,
        };
        r = v->get_fd_props(v->pd,
                           VK_EXTERNAL_MEMORY_HANDLE_TYPE_DMA_BUF_BIT_EXT, fd,
                           &fp);
        if (r != VK_SUCCESS) {
            fprintf(stderr, "import: vkGetMemoryFdPropertiesKHR -> %d\n", r);
            return -1;
        }
        type_bits &= fp.memoryTypeBits;
        if (!type_bits) {
            fprintf(stderr, "import: fd has no usable memory type\n");
            return -1;
        }
    }

    VkImportMemoryFdInfoKHR imp = {
        .sType = VK_STRUCTURE_TYPE_IMPORT_MEMORY_FD_INFO_KHR,
        .handleType = VK_EXTERNAL_MEMORY_HANDLE_TYPE_DMA_BUF_BIT_EXT,
        .fd = fd,
    };
    VkMemoryDedicatedAllocateInfo ded = {
        .sType = VK_STRUCTURE_TYPE_MEMORY_DEDICATED_ALLOCATE_INFO,
        .pNext = &imp,
        .image = f->image,
    };
    VkMemoryAllocateInfo mai = {
        .sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
        .pNext = &ded,
        .allocationSize = mr.size,
        .memoryTypeIndex = find_mem_type(v->pd, type_bits, 0),
    };
    if (mai.memoryTypeIndex == UINT32_MAX) {
        fprintf(stderr, "import: no memory type\n");
        return -1;
    }
    r = vkAllocateMemory(v->dev, &mai, NULL, &f->mem);
    if (r != VK_SUCCESS) {
        fprintf(stderr, "import: vkAllocateMemory -> %d\n", r);
        return -1;
    }
    r = vkBindImageMemory(v->dev, f->image, f->mem, 0);
    if (r != VK_SUCCESS) {
        fprintf(stderr, "import: vkBindImageMemory -> %d\n", r);
        return -1;
    }

    f->size = mr.size;
    VkImageSubresource sub = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 0 };
    VkSubresourceLayout lay;
    vkGetImageSubresourceLayout(v->dev, f->image, &sub, &lay);
    f->pitch = lay.rowPitch;
    printf("import: %ux%u pitch=%llu size=%llu (fd %d)\n", w, h,
           (unsigned long long)lay.rowPitch, (unsigned long long)mr.size, fd);
    return frame_view_and_fb(v, f, w, h, fmt);
}

/* PVR-owned linear image (fallback path). */
static int frame_init_own(struct vk_state *v, struct frame *f, uint32_t w,
                          uint32_t h, VkFormat fmt)
{
    memset(f, 0, sizeof(*f));
    f->dmabuf_fd = -1;

    VkImageCreateInfo ci = linear_image_ci(w, h, fmt, NULL);
    CHECK_VK(vkCreateImage(v->dev, &ci, NULL, &f->image));

    VkMemoryRequirements mr;
    vkGetImageMemoryRequirements(v->dev, f->image, &mr);

    VkMemoryDedicatedAllocateInfo ded = {
        .sType = VK_STRUCTURE_TYPE_MEMORY_DEDICATED_ALLOCATE_INFO,
        .image = f->image,
    };
    VkMemoryAllocateInfo mai = {
        .sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
        .pNext = &ded,
        .allocationSize = mr.size,
        .memoryTypeIndex = find_mem_type(
            v->pd, mr.memoryTypeBits,
            VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT |
                VK_MEMORY_PROPERTY_HOST_COHERENT_BIT),
    };
    if (mai.memoryTypeIndex == UINT32_MAX)
        mai.memoryTypeIndex = find_mem_type(v->pd, mr.memoryTypeBits, 0);
    CHECK_VK(vkAllocateMemory(v->dev, &mai, NULL, &f->mem));
    CHECK_VK(vkBindImageMemory(v->dev, f->image, f->mem, 0));
    f->size = mr.size;
    if (vkMapMemory(v->dev, f->mem, 0, VK_WHOLE_SIZE, 0, &f->host) !=
        VK_SUCCESS)
        f->host = NULL;

    VkImageSubresource sub = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 0 };
    VkSubresourceLayout lay;
    vkGetImageSubresourceLayout(v->dev, f->image, &sub, &lay);
    f->pitch = lay.rowPitch;
    printf("own: %ux%u pitch=%llu size=%llu host=%p\n", w, h,
           (unsigned long long)lay.rowPitch, (unsigned long long)mr.size,
           f->host);
    return frame_view_and_fb(v, f, w, h, fmt);
}

static void frame_fini(struct vk_state *v, struct frame *f)
{
    if (f->fb)
        vkDestroyFramebuffer(v->dev, f->fb, NULL);
    if (f->view)
        vkDestroyImageView(v->dev, f->view, NULL);
    if (f->mem)
        vkFreeMemory(v->dev, f->mem, NULL);
    if (f->image)
        vkDestroyImage(v->dev, f->image, NULL);
    f->fb = VK_NULL_HANDLE;
    f->view = VK_NULL_HANDLE;
    f->mem = VK_NULL_HANDLE;
    f->image = VK_NULL_HANDLE;
}

'''

s = s[:start] + new_funcs + s[end:]

# --- 2. main(): new buffer setup -------------------------------------------
start = s.index('    struct frame fr[2];')
end = s.index('    /* First frame: render before the initial modeset. */')

new_setup = r'''    struct frame fr[2];
    memset(fr, 0, sizeof(fr));
    int zero_copy = 0;

    if (!force_dumb) {
        int ok = 1;

        for (int i = 0; i < 2 && ok; i++) {
            struct drm_mode_create_dumb cd = {
                .width = w,
                .height = h,
                .bpp = 32,
            };
            int fd = -1;

            if (ioctl(d.fd, DRM_IOCTL_MODE_CREATE_DUMB, &cd)) {
                fprintf(stderr, "CREATE_DUMB: %s\n", strerror(errno));
                ok = 0;
                break;
            }
            fr[i].dumb_handle = cd.handle;
            fr[i].dumb_pitch = cd.pitch;
            fr[i].dumb_size = cd.size;
            if (drmModeAddFB(d.fd, w, h, 24, 32, cd.pitch, cd.handle,
                             &fr[i].drm_fb)) {
                fprintf(stderr, "AddFB: %s\n", strerror(errno));
                ok = 0;
                break;
            }
            if (drmPrimeHandleToFD(d.fd, cd.handle, DRM_CLOEXEC, &fd)) {
                fprintf(stderr, "PrimeHandleToFD: %s\n", strerror(errno));
                ok = 0;
                break;
            }
            if (frame_init_import(&v, &fr[i], w, h, fmt, fd)) {
                ok = 0;
                break;
            }
        }

        if (ok) {
            zero_copy = 1;
            printf("zero-copy: Vulkan renders into the scanout dma-buf\n");
        } else {
            for (int i = 0; i < 2; i++) {
                frame_fini(&v, &fr[i]);
                if (fr[i].drm_fb) {
                    drmModeRmFB(d.fd, fr[i].drm_fb);
                    fr[i].drm_fb = 0;
                }
            }
        }
    }

    if (!zero_copy) {
        printf("fallback: PVR image + CPU copy\n");
        for (int i = 0; i < 2; i++) {
            struct drm_mode_create_dumb cd = {
                .width = w,
                .height = h,
                .bpp = 32,
            };

            if (frame_init_own(&v, &fr[i], w, h, fmt))
                return 1;
            if (!fr[i].host) {
                fprintf(stderr, "image is not host visible, cannot copy\n");
                return 1;
            }
            if (ioctl(d.fd, DRM_IOCTL_MODE_CREATE_DUMB, &cd)) {
                fprintf(stderr, "CREATE_DUMB: %s\n", strerror(errno));
                return 1;
            }
            fr[i].dumb_handle = cd.handle;
            fr[i].dumb_pitch = cd.pitch;
            if (drmModeAddFB(d.fd, w, h, 24, 32, cd.pitch, cd.handle,
                             &fr[i].drm_fb)) {
                fprintf(stderr, "AddFB: %s\n", strerror(errno));
                return 1;
            }
            struct drm_mode_map_dumb md = { .handle = cd.handle };
            if (ioctl(d.fd, DRM_IOCTL_MODE_MAP_DUMB, &md)) {
                fprintf(stderr, "MAP_DUMB: %s\n", strerror(errno));
                return 1;
            }
            fr[i].dumb_ptr = mmap(NULL, cd.size, PROT_READ | PROT_WRITE,
                                  MAP_SHARED, d.fd, md.offset);
            if (fr[i].dumb_ptr == MAP_FAILED) {
                fprintf(stderr, "mmap dumb: %s\n", strerror(errno));
                return 1;
            }
            printf("dumb fb[%d] pitch=%u size=%llu\n", i, cd.pitch,
                   (unsigned long long)cd.size);
        }
    }

'''
s = s[:start] + new_setup + s[end:]

# --- 3. copy sites + summary use zero_copy ---------------------------------
old_copy = '''        if (!use_dmabuf) {
            for (uint32_t y = 0; y < h; y++)
                memcpy((char *)f->dumb_ptr + (size_t)y * f->dumb_pitch,
                       (const char *)f->host + (size_t)y * f->pitch,
                       (size_t)w * 4);
        }'''
new_copy = '''        if (!zero_copy) {
            for (uint32_t y = 0; y < h; y++)
                memcpy((char *)f->dumb_ptr + (size_t)y * f->dumb_pitch,
                       (const char *)f->host + (size_t)y * f->pitch,
                       (size_t)w * 4);
        }'''
assert s.count(old_copy) == 2, 'copy sites %d' % s.count(old_copy)
s = s.replace(old_copy, new_copy)

old_sum = '           use_dmabuf ? "dmabuf" : "dumb");'
new_sum = '           zero_copy ? "zero-copy" : "cpu-copy");'
assert s.count(old_sum) == 1
s = s.replace(old_sum, new_sum, 1)

# --- 4. get_fd_props member -------------------------------------------------
old_member = '    PFN_vkGetMemoryFdKHR get_memory_fd;'
new_member = ('    PFN_vkGetMemoryFdKHR get_memory_fd;\n'
              '    PFN_vkGetMemoryFdPropertiesKHR get_fd_props;')
assert s.count(old_member) == 1
s = s.replace(old_member, new_member, 1)

old_load = '''    v->get_memory_fd = (PFN_vkGetMemoryFdKHR)vkGetDeviceProcAddr(
        v->dev, "vkGetMemoryFdKHR");'''
new_load = '''    v->get_memory_fd = (PFN_vkGetMemoryFdKHR)vkGetDeviceProcAddr(
        v->dev, "vkGetMemoryFdKHR");
    v->get_fd_props = (PFN_vkGetMemoryFdPropertiesKHR)vkGetDeviceProcAddr(
        v->dev, "vkGetMemoryFdPropertiesKHR");'''
assert s.count(old_load) == 1
s = s.replace(old_load, new_load, 1)

p.write_text(s)
print('vk_kms2 patched')
