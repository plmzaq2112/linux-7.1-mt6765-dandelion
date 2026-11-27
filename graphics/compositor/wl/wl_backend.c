/*
 * Minimal Wayland server for the Vulkan/KMS compositor.
 *
 * Protocol subset:
 *   wl_compositor (1..4) - surfaces, regions (regions ignored)
 *   wl_shm             - via wl_display_init_shm(), ARGB8888/XRGB8888
 *   wl_seat    (1..5)  - pointer (touch is forwarded as pointer events)
 *   wl_output  (1..2)  - geometry/mode/scale (clients need it for sizing)
 *   xdg_wm_base (1)    - xdg_surface + xdg_toplevel, popups are placed but
 *                        not constrained
 *
 * Surfaces are composited 1:1 from the client's shm buffer into a linear
 * VkImage that the render pipeline samples.  Client buffers are copied
 * synchronously at commit, so wl_buffer.release is sent immediately.
 */
#define _GNU_SOURCE
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <sys/stat.h>

#include <wayland-server-core.h>
#include <wayland-server.h>
#include <poll.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <linux/input.h>

#include <drm_fourcc.h>

#include "xdg-shell-server-protocol.h"
#include "linux-dmabuf-unstable-v1-server-protocol.h"
#include "xkb_keymap.h"
#include "wl_backend.h"

#ifndef MFD_CLOEXEC
#define MFD_CLOEXEC 0x0001U
#endif

#define MAX_SURF 16

/* A wl_buffer backed by an imported dma-buf (one VkImage per buffer). */
#define WLBUF_MAGIC 0x574c4255u
struct wlbuf {
    uint32_t magic;
    int failed;
    VkImage img;
    VkDeviceMemory mem;
    VkImageView view;
    VkDescriptorSet set;
    int32_t w, h;
    uint32_t drm_format;
    int32_t stride;
    int first_use;
    struct wl_list retired_link;
};

struct wl_rel {
    struct wl_resource *res;
    struct wl_list link;
};

struct wlsurf {
    struct wl_resource *res;          /* wl_surface */
    struct wl_resource *xdg_surface;
    struct wl_resource *toplevel;
    struct wl_resource *popup;
    struct wl_list frame_cbs;         /* struct wl_cb */
    struct wl_list link;

    struct wl_resource *pending_buffer;
    int32_t pending_dx, pending_dy;
    int32_t scale;

    int has_role;
    int configured;
    int acked;
    int mapped;
    int place;                        /* cascade slot */

    float x, y, w, h;                 /* framebuffer pixels */
    int32_t bw, bh;                   /* buffer size */

    VkImage img;
    VkDeviceMemory mem;
    VkImageView view;
    VkDescriptorSet set;
    uint8_t *map;
    size_t map_size;
    uint64_t pitch, offset;
    int tex_w, tex_h;
    int img_owned;                    /* surface owns img/mem/view/set */
    struct wlbuf *dmabuf;             /* current dma-buf buffer, if any */
    int dirty_host;                   /* upload came from the CPU */
    int first_use;
    int dirty;
    int32_t dmg_x0, dmg_y0, dmg_x1, dmg_y1;  /* pending buffer damage */
    int have_damage;
    int tex_written;
};

struct wl_cb {
    struct wl_resource *res;
    struct wl_list link;
};

struct wl_ptr {
    struct wl_resource *res;
    struct wl_list link;
};

struct wl_kbd {
    struct wl_resource *res;
    struct wl_list link;
};

static struct {
    struct wl_display *dpy;
    uint32_t fbw, fbh;
    VkPhysicalDevice pd;
    VkDevice dev;
    VkDescriptorSetLayout dsl;
    VkDescriptorPool dpool;
    VkSampler sampler;
    PFN_vkGetMemoryFdPropertiesKHR get_fd_props;
    struct wl_list surfaces;
    struct wl_list ptrs;
    struct wl_list kbds;
    struct wl_resource *kbd_focus;
    uint32_t mods_depressed, mods_latched, mods_locked, mods_group;
    int kbd_fd;
    struct wl_list retired;           /* wlbuf waiting to be freed */
    struct wl_list release;           /* wl_buffer release deferred one frame */
    int ncreated;
    int ndestroyed;
    struct wlsurf *pointer_focus;
    struct wlsurf *grab;
    float grab_dx, grab_dy;
    float ptr_x, ptr_y;
    int down;
    uint32_t t0;
    int32_t dmg[4];                   /* x0,y0,x1,y1 */
    int dmg_valid;
} B;

/* --- damage -------------------------------------------------------------- */

static void dmg_add(int x0, int y0, int x1, int y1)
{
    if (x0 < 0)
        x0 = 0;
    if (y0 < 0)
        y0 = 0;
    if (x1 > (int)B.fbw)
        x1 = (int)B.fbw;
    if (y1 > (int)B.fbh)
        y1 = (int)B.fbh;
    if (x1 <= x0 || y1 <= y0)
        return;
    if (!B.dmg_valid) {
        B.dmg[0] = x0;
        B.dmg[1] = y0;
        B.dmg[2] = x1;
        B.dmg[3] = y1;
        B.dmg_valid = 1;
        return;
    }
    if (x0 < B.dmg[0])
        B.dmg[0] = x0;
    if (y0 < B.dmg[1])
        B.dmg[1] = y0;
    if (x1 > B.dmg[2])
        B.dmg[2] = x1;
    if (y1 > B.dmg[3])
        B.dmg[3] = y1;
}

static void dmg_surf(struct wlsurf *s)
{
    if (!s->mapped)
        return;
    dmg_add((int)s->x, (int)s->y, (int)(s->x + s->w), (int)(s->y + s->h));
}

static uint32_t now_ms(void)
{
    struct timespec ts;

    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint32_t)(ts.tv_sec * 1000 + ts.tv_nsec / 1000000);
}

/* --- helper lookups ------------------------------------------------------ */

static struct wlsurf *surf_from_resource(struct wl_resource *res)
{
    return res ? wl_resource_get_user_data(res) : NULL;
}

static struct wlsurf *surf_from_xdg(struct wl_resource *xdg_surface)
{
    struct wlsurf *s = surf_from_resource(xdg_surface);

    return s;
}

/* --- Vulkan textures ---------------------------------------------------- */

static void tex_destroy(struct wlsurf *s)
{
    if (!s->img_owned) {
        /* Borrowed from a dma-buf wl_buffer: owned by struct wlbuf. */
        s->img = VK_NULL_HANDLE;
        s->mem = VK_NULL_HANDLE;
        s->view = VK_NULL_HANDLE;
        s->set = VK_NULL_HANDLE;
        s->map = NULL;
        s->tex_w = s->tex_h = 0;
        s->dmabuf = NULL;
        return;
    }
    if (s->set) {
        vkFreeDescriptorSets(B.dev, B.dpool, 1, &s->set);
        s->set = VK_NULL_HANDLE;
    }
    if (s->view) {
        vkDestroyImageView(B.dev, s->view, NULL);
        s->view = VK_NULL_HANDLE;
    }
    if (s->map && s->mem)
        vkUnmapMemory(B.dev, s->mem);
    s->map = NULL;
    if (s->mem) {
        vkFreeMemory(B.dev, s->mem, NULL);
        s->mem = VK_NULL_HANDLE;
    }
    if (s->img) {
        vkDestroyImage(B.dev, s->img, NULL);
        s->img = VK_NULL_HANDLE;
    }
    s->tex_w = s->tex_h = 0;
}

static int tex_create(struct wlsurf *s, uint32_t tw, uint32_t th)
{
    tex_destroy(s);

    VkImageCreateInfo ci = {
        .sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO,
        .imageType = VK_IMAGE_TYPE_2D,
        .format = VK_FORMAT_R8G8B8A8_UNORM,
        .extent = { tw, th, 1 },
        .mipLevels = 1,
        .arrayLayers = 1,
        .samples = VK_SAMPLE_COUNT_1_BIT,
        .tiling = VK_IMAGE_TILING_LINEAR,
        .usage = VK_IMAGE_USAGE_SAMPLED_BIT,
        .sharingMode = VK_SHARING_MODE_EXCLUSIVE,
        .initialLayout = VK_IMAGE_LAYOUT_UNDEFINED,
    };
    if (vkCreateImage(B.dev, &ci, NULL, &s->img) != VK_SUCCESS) {
        fprintf(stderr, "wl: vkCreateImage(%ux%u) failed\n", tw, th);
        return -1;
    }

    VkMemoryRequirements mr;
    vkGetImageMemoryRequirements(B.dev, s->img, &mr);

    VkPhysicalDeviceMemoryProperties mp;
    vkGetPhysicalDeviceMemoryProperties(B.pd, &mp);

    VkMemoryAllocateInfo mai = {
        .sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
        .allocationSize = mr.size,
    };
    /* memoryTypeBits from a linear host-visible image: pick the first type
     * that supports host-visible+coherent. */
    {
        uint32_t i;

        mai.memoryTypeIndex = UINT32_MAX;
        for (i = 0; i < mp.memoryTypeCount; i++) {
            VkMemoryPropertyFlags f = mp.memoryTypes[i].propertyFlags;

            if ((mr.memoryTypeBits & (1u << i)) &&
                (f & VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT) &&
                (f & VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)) {
                mai.memoryTypeIndex = i;
                break;
            }
        }
        if (mai.memoryTypeIndex == UINT32_MAX) {
            for (i = 0; i < mp.memoryTypeCount; i++) {
                if (mr.memoryTypeBits & (1u << i)) {
                    mai.memoryTypeIndex = i;
                    break;
                }
            }
        }
    }
    if (mai.memoryTypeIndex == UINT32_MAX) {
        fprintf(stderr, "wl: no memory type for surface texture\n");
        return -1;
    }
    if (vkAllocateMemory(B.dev, &mai, NULL, &s->mem) != VK_SUCCESS) {
        fprintf(stderr, "wl: vkAllocateMemory(%llu) failed\n",
                (unsigned long long)mr.size);
        return -1;
    }
    vkBindImageMemory(B.dev, s->img, s->mem, 0);

    if (vkMapMemory(B.dev, s->mem, 0, VK_WHOLE_SIZE, 0, (void **)&s->map) !=
        VK_SUCCESS) {
        fprintf(stderr, "wl: vkMapMemory failed\n");
        s->map = NULL;
        return -1;
    }
    s->map_size = mr.size;

    VkImageSubresource sub = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 0 };
    VkSubresourceLayout lay;
    vkGetImageSubresourceLayout(B.dev, s->img, &sub, &lay);
    s->pitch = lay.rowPitch;
    s->offset = lay.offset;

    VkImageViewCreateInfo vci = {
        .sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO,
        .image = s->img,
        .viewType = VK_IMAGE_VIEW_TYPE_2D,
        .format = VK_FORMAT_R8G8B8A8_UNORM,
        .subresourceRange = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1 },
    };
    if (vkCreateImageView(B.dev, &vci, NULL, &s->view) != VK_SUCCESS) {
        fprintf(stderr, "wl: vkCreateImageView failed\n");
        return -1;
    }

    VkDescriptorSetAllocateInfo ai = {
        .sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO,
        .descriptorPool = B.dpool,
        .descriptorSetCount = 1,
        .pSetLayouts = &B.dsl,
    };
    if (vkAllocateDescriptorSets(B.dev, &ai, &s->set) != VK_SUCCESS) {
        fprintf(stderr, "wl: vkAllocateDescriptorSets failed\n");
        return -1;
    }
    VkDescriptorImageInfo dii = {
        .sampler = B.sampler,
        .imageView = s->view,
        .imageLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
    };
    VkWriteDescriptorSet w = {
        .sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET,
        .dstSet = s->set,
        .dstBinding = 0,
        .descriptorCount = 1,
        .descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,
        .pImageInfo = &dii,
    };
    vkUpdateDescriptorSets(B.dev, 1, &w, 0, NULL);

    s->tex_w = (int)tw;
    s->tex_h = (int)th;
    s->first_use = 1;
    s->img_owned = 1;
    s->dirty_host = 1;
    s->dmabuf = NULL;
    return 0;
}

/* --- dma-buf import ------------------------------------------------------ */

/* DRM fourcc -> Vulkan format for our two single-plane RGB formats.
 * ARGB8888 is B,G,R,A in memory, which B8G8R8A8_UNORM describes exactly, so
 * sampling yields (r,g,b,a) with no swizzle.  XRGB8888 forces alpha to 1. */
static int dmabuf_import(struct wlbuf *b, int fd, int32_t w, int32_t h,
                         uint32_t drm_format, int32_t offset, int32_t stride,
                         uint64_t modifier)
{
    VkFormat fmt = VK_FORMAT_B8G8R8A8_UNORM;
    int xrgb = 0;
    int ifd;

    if (drm_format == DRM_FORMAT_ARGB8888) {
        xrgb = 0;
    } else if (drm_format == DRM_FORMAT_XRGB8888) {
        xrgb = 1;
    } else {
        fprintf(stderr, "dmabuf: unsupported format %08x\n", drm_format);
        return -1;
    }
    if (modifier != DRM_FORMAT_MOD_LINEAR && modifier != DRM_FORMAT_MOD_INVALID) {
        fprintf(stderr, "dmabuf: unsupported modifier %016llx\n",
                (unsigned long long)modifier);
        return -1;
    }
    if (offset != 0) {
        fprintf(stderr, "dmabuf: non-zero plane offset %d unsupported\n", offset);
        return -1;
    }

    VkExternalMemoryImageCreateInfo ext = {
        .sType = VK_STRUCTURE_TYPE_EXTERNAL_MEMORY_IMAGE_CREATE_INFO,
        .handleTypes = VK_EXTERNAL_MEMORY_HANDLE_TYPE_DMA_BUF_BIT_EXT,
    };
    VkImageCreateInfo ci = {
        .sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO,
        .pNext = &ext,
        .imageType = VK_IMAGE_TYPE_2D,
        .format = fmt,
        .extent = { (uint32_t)w, (uint32_t)h, 1 },
        .mipLevels = 1,
        .arrayLayers = 1,
        .samples = VK_SAMPLE_COUNT_1_BIT,
        .tiling = VK_IMAGE_TILING_LINEAR,
        .usage = VK_IMAGE_USAGE_SAMPLED_BIT,
        .sharingMode = VK_SHARING_MODE_EXCLUSIVE,
        .initialLayout = VK_IMAGE_LAYOUT_UNDEFINED,
    };
    if (vkCreateImage(B.dev, &ci, NULL, &b->img) != VK_SUCCESS) {
        fprintf(stderr, "dmabuf: vkCreateImage %dx%d failed\n", w, h);
        return -1;
    }

    VkMemoryRequirements mr;
    vkGetImageMemoryRequirements(B.dev, b->img, &mr);

    uint32_t type_bits = mr.memoryTypeBits;
    if (B.get_fd_props) {
        VkMemoryFdPropertiesKHR fp = {
            .sType = VK_STRUCTURE_TYPE_MEMORY_FD_PROPERTIES_KHR,
        };
        if (B.get_fd_props(B.dev, VK_EXTERNAL_MEMORY_HANDLE_TYPE_DMA_BUF_BIT_EXT,
                           fd, &fp) != VK_SUCCESS) {
            fprintf(stderr, "dmabuf: vkGetMemoryFdPropertiesKHR failed\n");
            return -1;
        }
        type_bits &= fp.memoryTypeBits;
        if (!type_bits) {
            fprintf(stderr, "dmabuf: fd has no usable memory type\n");
            return -1;
        }
    }

    ifd = dup(fd);
    if (ifd < 0) {
        fprintf(stderr, "dmabuf: dup: %s\n", strerror(errno));
        return -1;
    }

    VkImportMemoryFdInfoKHR imp = {
        .sType = VK_STRUCTURE_TYPE_IMPORT_MEMORY_FD_INFO_KHR,
        .handleType = VK_EXTERNAL_MEMORY_HANDLE_TYPE_DMA_BUF_BIT_EXT,
        .fd = ifd,
    };
    VkMemoryDedicatedAllocateInfo ded = {
        .sType = VK_STRUCTURE_TYPE_MEMORY_DEDICATED_ALLOCATE_INFO,
        .pNext = &imp,
        .image = b->img,
    };
    VkMemoryAllocateInfo mai = {
        .sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
        .pNext = &ded,
        .allocationSize = mr.size,
        .memoryTypeIndex = 0,
    };
    uint32_t i;

    mai.memoryTypeIndex = UINT32_MAX;
    {
        VkPhysicalDeviceMemoryProperties mp;

        vkGetPhysicalDeviceMemoryProperties(B.pd, &mp);
        for (i = 0; i < mp.memoryTypeCount; i++) {
            if (type_bits & (1u << i)) {
                mai.memoryTypeIndex = i;
                break;
            }
        }
    }
    if (mai.memoryTypeIndex == UINT32_MAX) {
        close(ifd);
        return -1;
    }
    if (vkAllocateMemory(B.dev, &mai, NULL, &b->mem) != VK_SUCCESS) {
        fprintf(stderr, "dmabuf: vkAllocateMemory failed\n");
        close(ifd);
        return -1;
    }
    if (vkBindImageMemory(B.dev, b->img, b->mem, 0) != VK_SUCCESS) {
        fprintf(stderr, "dmabuf: vkBindImageMemory failed\n");
        return -1;
    }

    VkImageSubresource sub = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 0 };
    VkSubresourceLayout lay;
    vkGetImageSubresourceLayout(B.dev, b->img, &sub, &lay);

    VkComponentMapping swz = {
        .r = VK_COMPONENT_SWIZZLE_IDENTITY,
        .g = VK_COMPONENT_SWIZZLE_IDENTITY,
        .b = VK_COMPONENT_SWIZZLE_IDENTITY,
        .a = xrgb ? VK_COMPONENT_SWIZZLE_ONE : VK_COMPONENT_SWIZZLE_IDENTITY,
    };
    VkImageViewCreateInfo vci = {
        .sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO,
        .image = b->img,
        .viewType = VK_IMAGE_VIEW_TYPE_2D,
        .format = fmt,
        .components = swz,
        .subresourceRange = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1 },
    };
    if (vkCreateImageView(B.dev, &vci, NULL, &b->view) != VK_SUCCESS) {
        fprintf(stderr, "dmabuf: vkCreateImageView failed\n");
        return -1;
    }

    VkDescriptorSetAllocateInfo ai = {
        .sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO,
        .descriptorPool = B.dpool,
        .descriptorSetCount = 1,
        .pSetLayouts = &B.dsl,
    };
    if (vkAllocateDescriptorSets(B.dev, &ai, &b->set) != VK_SUCCESS) {
        fprintf(stderr, "dmabuf: vkAllocateDescriptorSets failed\n");
        return -1;
    }
    VkDescriptorImageInfo dii = {
        .sampler = B.sampler,
        .imageView = b->view,
        .imageLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
    };
    VkWriteDescriptorSet wds = {
        .sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET,
        .dstSet = b->set,
        .dstBinding = 0,
        .descriptorCount = 1,
        .descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,
        .pImageInfo = &dii,
    };
    vkUpdateDescriptorSets(B.dev, 1, &wds, 0, NULL);

    b->w = w;
    b->h = h;
    b->drm_format = drm_format;
    b->stride = stride;
    b->first_use = 1;
    printf("dmabuf: imported %dx%d fmt=%08x stride=%d pitch=%llu size=%llu\n",
           w, h, drm_format, stride, (unsigned long long)lay.rowPitch,
           (unsigned long long)mr.size);
    return 0;
}

static int surf_upload(struct wlsurf *s, struct wl_resource *buffer,
                       int32_t dx0, int32_t dy0, int32_t dx1, int32_t dy1)
{
    struct wl_shm_buffer *sb = wl_shm_buffer_get(buffer);
    int32_t bw, bh, stride;
    uint32_t format;
    uint32_t y;
    int full;

    if (!sb) {
        fprintf(stderr, "wl: attach of a non-shm buffer (dma-buf unsupported)\n");
        return -1;
    }
    bw = wl_shm_buffer_get_width(sb);
    bh = wl_shm_buffer_get_height(sb);
    stride = wl_shm_buffer_get_stride(sb);
    format = wl_shm_buffer_get_format(sb);
    if (bw <= 0 || bh <= 0 || bw > 4096 || bh > 4096 || stride < bw * 4) {
        fprintf(stderr, "wl: bad buffer %dx%d stride %d\n", bw, bh, stride);
        return -1;
    }

    full = !s->img || s->tex_w != bw || s->tex_h != bh || !s->tex_written;
    if (full) {
        /* The pipeline may still sample the old image. */
        vkDeviceWaitIdle(B.dev);
        if (!s->img || s->tex_w != bw || s->tex_h != bh) {
            if (tex_create(s, (uint32_t)bw, (uint32_t)bh))
                return -1;
        }
        dx0 = 0;
        dy0 = 0;
        dx1 = bw;
        dy1 = bh;
    } else {
        /* Wait for frames that sample this image before rewriting it. */
        vkDeviceWaitIdle(B.dev);
        if (dx0 < 0) dx0 = 0;
        if (dy0 < 0) dy0 = 0;
        if (dx1 > bw) dx1 = bw;
        if (dy1 > bh) dy1 = bh;
        if (dx1 <= dx0 || dy1 <= dy0) {
            dx0 = dy0 = 0;
            dx1 = bw;
            dy1 = bh;
        }
    }

    wl_shm_buffer_begin_access(sb);
    {
        const uint8_t *src = wl_shm_buffer_get_data(sb);

        for (y = (uint32_t)dy0; y < (uint32_t)dy1; y++) {
            const uint8_t *sp = src + (size_t)y * (size_t)stride +
                                (size_t)dx0 * 4;
            uint8_t *dp = s->map + s->offset + (size_t)y * s->pitch +
                          (size_t)dx0 * 4;
            int32_t x;

            for (x = dx0; x < dx1; x++) {
                uint32_t v;
                uint8_t a;

                memcpy(&v, sp, 4);
                /* wl_shm ARGB8888/XRGB8888 is little-endian BGRA in memory. */
                a = (format == WL_SHM_FORMAT_XRGB8888) ? 255 : (uint8_t)(v >> 24);
                dp[0] = (uint8_t)(v >> 16);
                dp[1] = (uint8_t)(v >> 8);
                dp[2] = (uint8_t)v;
                dp[3] = a;
                sp += 4;
                dp += 4;
            }
        }
    }
    wl_shm_buffer_end_access(sb);

    s->dirty = 1;
    s->tex_written = 1;
    s->bw = bw;
    s->bh = bh;
    printf("wl: surface upload %dx%d rect=(%d,%d)-(%d,%d) %s fmt=%08x\n", bw, bh,
           dx0, dy0, dx1, dy1, full ? "full" : "damage", format);
    return 0;
}

void wl_backend_prepare(VkCommandBuffer cmd)
{
    struct wlsurf *s;

    wl_list_for_each(s, &B.surfaces, link) {
        VkImageMemoryBarrier b = {
            .sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER,
            .srcAccessMask = s->dirty_host ? VK_ACCESS_HOST_WRITE_BIT : 0,
            .dstAccessMask = VK_ACCESS_SHADER_READ_BIT,
            .oldLayout = s->first_use ? VK_IMAGE_LAYOUT_UNDEFINED
                                      : VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
            .newLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
            .srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
            .dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
            .image = s->img,
            .subresourceRange = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1 },
        };

        if (!s->dirty || !s->img)
            continue;
        vkCmdPipelineBarrier(cmd, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT,
                             VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT, 0, 0, NULL,
                             0, NULL, 1, &b);
        s->dirty = 0;
        s->first_use = 0;
        if (s->dmabuf)
            s->dmabuf->first_use = 0;
    }
}

/* --- xdg_surface / surface mapping -------------------------------------- */

static void surf_send_configure(struct wlsurf *s)
{
    if (!s->xdg_surface)
        return;

    if (s->toplevel) {
        struct wl_array states;

        wl_array_init(&states);
        xdg_toplevel_send_configure(s->toplevel, 0, 0, &states);
        wl_array_release(&states);
    } else if (s->popup) {
        xdg_popup_send_configure(s->popup, 0, 0, s->bw, s->bh);
    }
    xdg_surface_send_configure(s->xdg_surface, wl_display_next_serial(B.dpy));
    s->configured = 1;
}

static void kbd_set_focus(struct wlsurf *s, uint32_t serial);

static void surf_map(struct wlsurf *s)
{
    float w = (float)(s->bw / (s->scale > 0 ? s->scale : 1));
    float h = (float)(s->bh / (s->scale > 0 ? s->scale : 1));

    if (!s->mapped) {
        s->place = B.ncreated++;
        s->x = 40.0f + 40.0f * (float)(s->place % 4);
        s->y = 200.0f + 40.0f * (float)(s->place % 4);
        s->mapped = 1;
        printf("wl: mapped surface %d at %.0f,%.0f size %.0fx%.0f\n", s->place,
               s->x, s->y, w, h);
        if (!B.kbd_focus)
            kbd_set_focus(s, wl_display_next_serial(B.dpy));
    }
    s->w = w;
    s->h = h;
}

/* --- wl_surface ---------------------------------------------------------- */

static void srf_destroy(struct wl_client *client, struct wl_resource *res)
{
    wl_resource_destroy(res);
}

static void srf_attach(struct wl_client *client, struct wl_resource *res,
                       struct wl_resource *buffer, int32_t x, int32_t y)
{
    struct wlsurf *s = surf_from_resource(res);

    if (!s)
        return;
    if (s->pending_buffer && s->pending_buffer != buffer)
        wl_buffer_send_release(s->pending_buffer);
    s->pending_buffer = buffer;
    s->pending_dx = x;
    s->pending_dy = y;
}

static void surf_note_damage(struct wlsurf *s, int32_t x, int32_t y, int32_t w,
                             int32_t h)
{
    if (w <= 0 || h <= 0)
        return;
    if (!s->have_damage) {
        s->dmg_x0 = x;
        s->dmg_y0 = y;
        s->dmg_x1 = x + w;
        s->dmg_y1 = y + h;
        s->have_damage = 1;
        return;
    }
    if (x < s->dmg_x0)
        s->dmg_x0 = x;
    if (y < s->dmg_y0)
        s->dmg_y0 = y;
    if (x + w > s->dmg_x1)
        s->dmg_x1 = x + w;
    if (y + h > s->dmg_y1)
        s->dmg_y1 = y + h;
}

static void srf_damage(struct wl_client *client, struct wl_resource *res,
                       int32_t x, int32_t y, int32_t w, int32_t h)
{
    (void)client;
    surf_note_damage(surf_from_resource(res), x, y, w, h);
}

static void srf_frame(struct wl_client *client, struct wl_resource *res,
                      uint32_t id)
{
    struct wlsurf *s = surf_from_resource(res);
    struct wl_cb *cb;

    if (!s)
        return;
    cb = calloc(1, sizeof(*cb));
    cb->res = wl_resource_create(client, &wl_callback_interface, 1, id);
    wl_list_insert(s->frame_cbs.prev, &cb->link);
}

static void srf_set_opaque_region(struct wl_client *client,
                                  struct wl_resource *res,
                                  struct wl_resource *region)
{
    (void)client; (void)res; (void)region;
}

static void srf_set_input_region(struct wl_client *client,
                                 struct wl_resource *res,
                                 struct wl_resource *region)
{
    (void)client; (void)res; (void)region;
}

static void srf_commit(struct wl_client *client, struct wl_resource *res)
{
    struct wlsurf *s = surf_from_resource(res);

    (void)client;
    if (!s)
        return;

    if (s->has_role && !s->configured) {
        /* Initial commit: reply with a configure and wait for the buffer. */
        surf_send_configure(s);
        return;
    }

    if (s->pending_buffer) {
        struct wl_resource *buf = s->pending_buffer;
        struct wlbuf *db = NULL;

        s->pending_buffer = NULL;
        /* libwayland's shm buffers also carry user_data, so test shm first. */
        if (!wl_shm_buffer_get(buf)) {
            db = wl_resource_get_user_data(buf);
            if (db && db->magic != WLBUF_MAGIC)
                db = NULL;
        }
        if (db) {
            /* dma-buf: imported once, sampled in place, no copy. */
            if (!db->failed && db->set) {
                struct wl_rel *rel;

                tex_destroy(s);        /* drop any shm texture we owned */
                s->img = db->img;
                s->mem = db->mem;
                s->view = db->view;
                s->set = db->set;
                s->img_owned = 0;
                s->dmabuf = db;
                s->dirty_host = 0;
                s->first_use = db->first_use;
                s->dirty = 1;
                s->bw = db->w;
                s->bh = db->h;
                surf_map(s);
                dmg_surf(s);

                rel = calloc(1, sizeof(*rel));
                rel->res = buf;
                wl_list_insert(B.release.prev, &rel->link);
            } else {
                wl_buffer_send_release(buf);
            }
        } else if (surf_upload(s, buf, s->dmg_x0, s->dmg_y0, s->dmg_x1,
                               s->dmg_y1) == 0) {
            surf_map(s);
            dmg_surf(s);
            /* The pixels were copied synchronously; the client may reuse it. */
            wl_buffer_send_release(buf);
        }
        s->have_damage = 0;
    }
}

static void srf_set_buffer_transform(struct wl_client *client,
                                     struct wl_resource *res, int32_t tf)
{
    (void)client; (void)res; (void)tf;
}

static void srf_set_buffer_scale(struct wl_client *client,
                                 struct wl_resource *res, int32_t scale)
{
    struct wlsurf *s = surf_from_resource(res);

    if (s && scale > 0)
        s->scale = scale;
}

static void srf_damage_buffer(struct wl_client *client, struct wl_resource *res,
                              int32_t x, int32_t y, int32_t w, int32_t h)
{
    (void)client;
    surf_note_damage(surf_from_resource(res), x, y, w, h);
}

static const struct wl_surface_interface surface_impl = {
    .destroy = srf_destroy,
    .attach = srf_attach,
    .damage = srf_damage,
    .frame = srf_frame,
    .set_opaque_region = srf_set_opaque_region,
    .set_input_region = srf_set_input_region,
    .commit = srf_commit,
    .set_buffer_transform = srf_set_buffer_transform,
    .set_buffer_scale = srf_set_buffer_scale,
    .damage_buffer = srf_damage_buffer,
};

static void surf_resource_destroy(struct wl_resource *res)
{
    struct wlsurf *s = surf_from_resource(res);
    struct wl_cb *cb, *tmp;

    if (!s)
        return;

    dmg_surf(s);
    {
        int lost_focus = (B.kbd_focus == s->res);
        if (lost_focus)
            B.kbd_focus = NULL;
        if (B.pointer_focus == s)
            B.pointer_focus = NULL;
        if (B.grab == s)
            B.grab = NULL;
        if (lost_focus) {
            struct wlsurf *it, *pick = NULL;

            wl_list_for_each(it, &B.surfaces, link) {
                if (it != s && it->mapped)
                    pick = it;
            }
            if (pick)
                kbd_set_focus(pick, wl_display_next_serial(B.dpy));
        }
    }

    wl_list_for_each_safe(cb, tmp, &s->frame_cbs, link) {
        wl_resource_destroy(cb->res);
        wl_list_remove(&cb->link);
        free(cb);
    }
    if (s->pending_buffer)
        wl_buffer_send_release(s->pending_buffer);
    tex_destroy(s);
    wl_list_remove(&s->link);
    printf("wl: surface %d destroyed\n", s->place);
    free(s);
    B.ndestroyed++;
}

/* --- wl_compositor ------------------------------------------------------- */

static void comp_create_surface(struct wl_client *client,
                                struct wl_resource *res, uint32_t id)
{
    struct wlsurf *s = calloc(1, sizeof(*s));

    s->res = wl_resource_create(client, &wl_surface_interface,
                                wl_resource_get_version(res), id);
    s->scale = 1;
    s->place = -1;
    wl_list_init(&s->frame_cbs);
    wl_resource_set_implementation(s->res, &surface_impl, s,
                                   surf_resource_destroy);
    wl_list_insert(B.surfaces.prev, &s->link);
}

static void region_destroy(struct wl_client *client, struct wl_resource *res)
{
    wl_resource_destroy(res);
}

static void region_add(struct wl_client *client, struct wl_resource *res,
                       int32_t x, int32_t y, int32_t w, int32_t h)
{
    (void)client; (void)res; (void)x; (void)y; (void)w; (void)h;
}

static void region_subtract(struct wl_client *client, struct wl_resource *res,
                            int32_t x, int32_t y, int32_t w, int32_t h)
{
    (void)client; (void)res; (void)x; (void)y; (void)w; (void)h;
}

static const struct wl_region_interface region_impl = {
    .destroy = region_destroy,
    .add = region_add,
    .subtract = region_subtract,
};

static void comp_create_region(struct wl_client *client,
                               struct wl_resource *res, uint32_t id)
{
    struct wl_resource *r = wl_resource_create(client, &wl_region_interface,
                                               1, id);

    wl_resource_set_implementation(r, &region_impl, NULL, NULL);
}

static const struct wl_compositor_interface compositor_impl = {
    .create_surface = comp_create_surface,
    .create_region = comp_create_region,
};

static void bind_compositor(struct wl_client *client, void *data,
                            uint32_t version, uint32_t id)
{
    struct wl_resource *res = wl_resource_create(
        client, &wl_compositor_interface, version, id);

    wl_resource_set_implementation(res, &compositor_impl, NULL, NULL);
}

/* --- wl_output ----------------------------------------------------------- */

static void output_release(struct wl_client *client, struct wl_resource *res)
{
    wl_resource_destroy(res);
}

static const struct wl_output_interface output_impl = {
    .release = output_release,
};

static void bind_output(struct wl_client *client, void *data, uint32_t version,
                        uint32_t id)
{
    struct wl_resource *res = wl_resource_create(client, &wl_output_interface,
                                                 version, id);

    wl_resource_set_implementation(res, &output_impl, NULL, NULL);
    wl_output_send_geometry(res, 0, 0, 0, 0, WL_OUTPUT_SUBPIXEL_UNKNOWN,
                            "vk", "vk-wl", WL_OUTPUT_TRANSFORM_NORMAL);
    wl_output_send_mode(res, WL_OUTPUT_MODE_CURRENT, B.fbw, B.fbh, 60000);
    if (version >= 2) {
        wl_output_send_scale(res, 1);
        wl_output_send_done(res);
    }
}

/* --- wl_seat / wl_pointer ------------------------------------------------ */

static void ptr_set_cursor(struct wl_client *client, struct wl_resource *res,
                           uint32_t serial, struct wl_resource *surface,
                           int32_t hx, int32_t hy)
{
    (void)client; (void)res; (void)serial; (void)surface; (void)hx; (void)hy;
}

static void ptr_release(struct wl_client *client, struct wl_resource *res)
{
    wl_resource_destroy(res);
}

static const struct wl_pointer_interface pointer_impl = {
    .set_cursor = ptr_set_cursor,
    .release = ptr_release,
};

static void ptr_resource_destroy(struct wl_resource *res)
{
    struct wl_ptr *p = wl_resource_get_user_data(res);

    if (!p)
        return;
    wl_list_remove(&p->link);
    free(p);
}

static void ptr_send_enter(struct wlsurf *s, uint32_t serial, float x, float y)
{
    struct wl_ptr *p;

    wl_list_for_each(p, &B.ptrs, link)
        wl_pointer_send_enter(p->res, serial, s->res,
                              wl_fixed_from_double(x),
                              wl_fixed_from_double(y));
}

static void ptr_send_leave(struct wlsurf *s, uint32_t serial)
{
    struct wl_ptr *p;

    wl_list_for_each(p, &B.ptrs, link)
        wl_pointer_send_leave(p->res, serial, s->res);
}

static void ptr_send_motion(uint32_t t, float x, float y)
{
    struct wl_ptr *p;

    wl_list_for_each(p, &B.ptrs, link)
        wl_pointer_send_motion(p->res, t, wl_fixed_from_double(x),
                               wl_fixed_from_double(y));
}

static void ptr_send_button(uint32_t serial, uint32_t t, uint32_t state)
{
    struct wl_ptr *p;

    wl_list_for_each(p, &B.ptrs, link)
        wl_pointer_send_button(p->res, serial, t, 0x110, state);
}

static void ptr_send_frame(void)
{
    struct wl_ptr *p;

    wl_list_for_each(p, &B.ptrs, link) {
        if (wl_resource_get_version(p->res) >= 5)
            wl_pointer_send_frame(p->res);
    }
}

static void touch_release(struct wl_client *client, struct wl_resource *res)
{
    wl_resource_destroy(res);
}

static const struct wl_touch_interface touch_impl = {
    .release = touch_release,
};

/* --- wl_keyboard --------------------------------------------------------- */

static void kbd_send_keymap(struct wl_resource *res)
{
    int fd = memfd_create("xkb-keymap", MFD_CLOEXEC);

    if (fd < 0) {
        fprintf(stderr, "kbd: memfd_create: %s\n", strerror(errno));
        return;
    }
    if (write(fd, xkb_keymap_string, xkb_keymap_size) !=
        (ssize_t)xkb_keymap_size) {
        fprintf(stderr, "kbd: keymap write failed\n");
        close(fd);
        return;
    }
    lseek(fd, 0, SEEK_SET);
    wl_keyboard_send_keymap(res, WL_KEYBOARD_KEYMAP_FORMAT_XKB_V1, fd,
                            xkb_keymap_size);
    close(fd);
}

static void kbd_send_modifiers(uint32_t serial)
{
    struct wl_kbd *k;

    wl_list_for_each(k, &B.kbds, link) {
        wl_keyboard_send_modifiers(k->res, serial, B.mods_depressed,
                                   B.mods_latched, B.mods_locked, B.mods_group);
    }
}

static void kbd_send_enter(struct wlsurf *s, uint32_t serial)
{
    struct wl_array keys;
    struct wl_kbd *k;

    wl_array_init(&keys);
    wl_list_for_each(k, &B.kbds, link)
        wl_keyboard_send_enter(k->res, serial, s->res, &keys);
    wl_array_release(&keys);
}

static void kbd_set_focus(struct wlsurf *s, uint32_t serial)
{
    struct wl_kbd *k;

    if (B.kbd_focus == (s ? s->res : NULL))
        return;
    if (B.kbd_focus) {
        wl_list_for_each(k, &B.kbds, link)
            wl_keyboard_send_leave(k->res, serial, B.kbd_focus);
        printf("kbd: focus lost\n");
    }
    B.kbd_focus = s ? s->res : NULL;
    if (s) {
        kbd_send_enter(s, serial);
        kbd_send_modifiers(serial);
        printf("kbd: focus on surface %d\n", s->place);
    }
}

static void kbd_handle_key(uint32_t code, uint32_t value)
{
    uint32_t keycode = code + 8;         /* evdev -> XKB keycode */
    uint32_t t = now_ms() - B.t0;
    uint32_t serial = wl_display_next_serial(B.dpy);
    struct wl_kbd *k;
    uint32_t bit = 0;
    int changed = 0;

    switch (code) {
    case 42: case 54:                    /* Shift_L / Shift_R */
        bit = 1;
        break;
    case 29: case 97:                    /* Control_L / Control_R */
        bit = 4;
        break;
    case 56: case 100:                   /* Alt_L / Alt_R -> Mod1 */
        bit = 8;
        break;
    case 125: case 126:                  /* Super_L / Super_R -> Mod4 */
        bit = 64;
        break;
    case 58:                             /* Caps_Lock -> Lock */
        if (value == 1) {
            B.mods_locked ^= 2;
            changed = 1;
        }
        break;
    default:
        break;
    }
    if (bit) {
        if (value == 1)
            B.mods_depressed |= bit;
        else if (value == 0)
            B.mods_depressed &= ~bit;
        changed = 1;
    }
    if (value == 2)
        return;                          /* autorepeat is client-side */

    if (B.kbd_focus) {
        wl_list_for_each(k, &B.kbds, link)
            wl_keyboard_send_key(k->res, serial, t, keycode, value);
    }
    if (changed)
        kbd_send_modifiers(serial);
}

static void kbd_poll(void)
{
    struct input_event ev;

    while (B.kbd_fd >= 0 &&
           read(B.kbd_fd, &ev, sizeof(ev)) == (ssize_t)sizeof(ev)) {
        if (ev.type == EV_KEY)
            kbd_handle_key(ev.code, ev.value);
    }
}

static void kbd_release(struct wl_client *client, struct wl_resource *res)
{
    wl_resource_destroy(res);
}

static const struct wl_keyboard_interface keyboard_impl = {
    .release = kbd_release,
};

static void kbd_resource_destroy(struct wl_resource *res)
{
    struct wl_kbd *k = wl_resource_get_user_data(res);

    if (!k)
        return;
    wl_list_remove(&k->link);
    free(k);
}

static void seat_get_pointer(struct wl_client *client, struct wl_resource *res,
                             uint32_t id)
{
    struct wl_ptr *p = calloc(1, sizeof(*p));

    p->res = wl_resource_create(client, &wl_pointer_interface,
                                wl_resource_get_version(res), id);
    wl_resource_set_implementation(p->res, &pointer_impl, p,
                                   ptr_resource_destroy);
    wl_list_insert(B.ptrs.prev, &p->link);
}

static void seat_get_keyboard(struct wl_client *client, struct wl_resource *res,
                              uint32_t id)
{
    struct wl_kbd *k = calloc(1, sizeof(*k));

    k->res = wl_resource_create(client, &wl_keyboard_interface,
                                wl_resource_get_version(res), id);
    wl_resource_set_implementation(k->res, &keyboard_impl, k,
                                   kbd_resource_destroy);
    wl_list_insert(B.kbds.prev, &k->link);
    kbd_send_keymap(k->res);
    wl_keyboard_send_repeat_info(k->res, 25, 600);
    if (B.kbd_focus) {
        struct wlsurf *s;

        wl_list_for_each(s, &B.surfaces, link) {
            if (s->res == B.kbd_focus) {
                kbd_send_enter(s, wl_display_next_serial(B.dpy));
                break;
            }
        }
    }
    kbd_send_modifiers(wl_display_next_serial(B.dpy));
    printf("kbd: client bound (keymap %u bytes)\n", xkb_keymap_size);
}

static void seat_get_touch(struct wl_client *client, struct wl_resource *res,
                           uint32_t id)
{
    struct wl_resource *t = wl_resource_create(client, &wl_touch_interface,
                                               wl_resource_get_version(res), id);

    wl_resource_set_implementation(t, &touch_impl, NULL, NULL);
}

static void seat_release(struct wl_client *client, struct wl_resource *res)
{
    wl_resource_destroy(res);
}

static const struct wl_seat_interface seat_impl = {
    .get_pointer = seat_get_pointer,
    .get_keyboard = seat_get_keyboard,
    .get_touch = seat_get_touch,
    .release = seat_release,
};

static void bind_seat(struct wl_client *client, void *data, uint32_t version,
                      uint32_t id)
{
    struct wl_resource *res = wl_resource_create(client, &wl_seat_interface,
                                                 version, id);

    wl_resource_set_implementation(res, &seat_impl, NULL, NULL);
    wl_seat_send_capabilities(res, WL_SEAT_CAPABILITY_POINTER |
                                       WL_SEAT_CAPABILITY_KEYBOARD);
    if (version >= 2)
        wl_seat_send_name(res, "seat0");
}

/* --- xdg_toplevel -------------------------------------------------------- */

static void toplevel_destroy(struct wl_client *client, struct wl_resource *res)
{
    struct wlsurf *s = surf_from_resource(res);

    if (s)
        s->toplevel = NULL;
    wl_resource_destroy(res);
}

static void toplevel_set_parent(struct wl_client *client,
                                struct wl_resource *res,
                                struct wl_resource *parent)
{
    (void)client; (void)res; (void)parent;
}

static void toplevel_set_title(struct wl_client *client,
                               struct wl_resource *res, const char *title)
{
    struct wlsurf *s = surf_from_resource(res);

    printf("wl: toplevel %d title \"%s\"\n", s ? s->place : -1,
           title ? title : "");
}

static void toplevel_set_app_id(struct wl_client *client,
                                struct wl_resource *res, const char *app_id)
{
    struct wlsurf *s = surf_from_resource(res);

    printf("wl: toplevel %d app_id \"%s\"\n", s ? s->place : -1,
           app_id ? app_id : "");
}

static void toplevel_show_menu(struct wl_client *client,
                               struct wl_resource *res, struct wl_resource *seat,
                               uint32_t serial, int32_t x, int32_t y)
{
    (void)client; (void)res; (void)seat; (void)serial; (void)x; (void)y;
}

static void toplevel_move(struct wl_client *client, struct wl_resource *res,
                          struct wl_resource *seat, uint32_t serial)
{
    struct wlsurf *s = surf_from_resource(res);

    if (!s || !B.down)
        return;
    B.grab = s;
    B.grab_dx = B.ptr_x - s->x;
    B.grab_dy = B.ptr_y - s->y;
    printf("wl: toplevel %d interactive move\n", s->place);
}

static void toplevel_resize(struct wl_client *client, struct wl_resource *res,
                            struct wl_resource *seat, uint32_t serial,
                            uint32_t edges)
{
    (void)client; (void)res; (void)seat; (void)serial; (void)edges;
}

static void toplevel_set_size(struct wl_client *client, struct wl_resource *res,
                              int32_t w, int32_t h)
{
    (void)client; (void)res; (void)w; (void)h;
}

static void toplevel_reconfigure(struct wl_client *client,
                                 struct wl_resource *res)
{
    struct wlsurf *s = surf_from_resource(res);

    (void)client;
    if (s)
        surf_send_configure(s);
}

static void toplevel_set_fullscreen(struct wl_client *client,
                                    struct wl_resource *res,
                                    struct wl_resource *output)
{
    (void)output;
    toplevel_reconfigure(client, res);
}

static void toplevel_set_minimized(struct wl_client *client,
                                   struct wl_resource *res)
{
    (void)client; (void)res;
}

static const struct xdg_toplevel_interface toplevel_impl = {
    .destroy = toplevel_destroy,
    .set_parent = toplevel_set_parent,
    .set_title = toplevel_set_title,
    .set_app_id = toplevel_set_app_id,
    .show_window_menu = toplevel_show_menu,
    .move = toplevel_move,
    .resize = toplevel_resize,
    .set_max_size = toplevel_set_size,
    .set_min_size = toplevel_set_size,
    .set_maximized = toplevel_reconfigure,
    .unset_maximized = toplevel_reconfigure,
    .set_fullscreen = toplevel_set_fullscreen,
    .unset_fullscreen = toplevel_reconfigure,
    .set_minimized = toplevel_set_minimized,
};

/* --- xdg_popup ----------------------------------------------------------- */

static void popup_destroy(struct wl_client *client, struct wl_resource *res)
{
    struct wlsurf *s = surf_from_resource(res);

    if (s)
        s->popup = NULL;
    wl_resource_destroy(res);
}

static void popup_grab(struct wl_client *client, struct wl_resource *res,
                       struct wl_resource *seat, uint32_t serial)
{
    (void)client; (void)res; (void)seat; (void)serial;
}

static void popup_reposition(struct wl_client *client, struct wl_resource *res,
                             struct wl_resource *positioner, uint32_t token)
{
    (void)client; (void)res; (void)positioner; (void)token;
}

static const struct xdg_popup_interface popup_impl = {
    .destroy = popup_destroy,
    .grab = popup_grab,
    .reposition = popup_reposition,
};

/* --- xdg_surface --------------------------------------------------------- */

static void xdg_surface_destroy(struct wl_client *client,
                                struct wl_resource *res)
{
    struct wlsurf *s = surf_from_resource(res);

    if (s)
        s->xdg_surface = NULL;
    wl_resource_destroy(res);
}

static void xdg_surface_get_toplevel(struct wl_client *client,
                                     struct wl_resource *res, uint32_t id)
{
    struct wlsurf *s = surf_from_resource(res);
    struct wl_resource *t;

    if (!s)
        return;
    t = wl_resource_create(client, &xdg_toplevel_interface, 1, id);
    wl_resource_set_implementation(t, &toplevel_impl, s, NULL);
    s->toplevel = t;
    s->has_role = 1;
}

static void xdg_surface_get_popup(struct wl_client *client,
                                  struct wl_resource *res, uint32_t id,
                                  struct wl_resource *parent,
                                  struct wl_resource *positioner)
{
    struct wlsurf *s = surf_from_resource(res);
    struct wl_resource *p;

    if (!s)
        return;
    p = wl_resource_create(client, &xdg_popup_interface, 1, id);
    wl_resource_set_implementation(p, &popup_impl, s, NULL);
    s->popup = p;
    s->has_role = 1;
    /* Place popups near the parent; no constraint solving yet. */
    if (parent) {
        struct wlsurf *ps = surf_from_xdg(parent);

        if (ps) {
            s->x = ps->x + 16.0f;
            s->y = ps->y + 16.0f;
        }
    }
}

static void xdg_surface_set_geometry(struct wl_client *client,
                                     struct wl_resource *res, int32_t x,
                                     int32_t y, int32_t w, int32_t h)
{
    (void)client; (void)res; (void)x; (void)y; (void)w; (void)h;
}

static void xdg_surface_ack_configure(struct wl_client *client,
                                      struct wl_resource *res, uint32_t serial)
{
    struct wlsurf *s = surf_from_resource(res);

    if (s)
        s->acked = 1;
    (void)client; (void)serial;
}

static const struct xdg_surface_interface xdg_surface_impl = {
    .destroy = xdg_surface_destroy,
    .get_toplevel = xdg_surface_get_toplevel,
    .get_popup = xdg_surface_get_popup,
    .set_window_geometry = xdg_surface_set_geometry,
    .ack_configure = xdg_surface_ack_configure,
};

/* --- xdg_positioner ------------------------------------------------------ */

static void positioner_destroy(struct wl_client *client,
                               struct wl_resource *res)
{
    wl_resource_destroy(res);
}

static void positioner_noop_i32x2(struct wl_client *client,
                                  struct wl_resource *res, int32_t a, int32_t b)
{
    (void)client; (void)res; (void)a; (void)b;
}

static void positioner_noop_i32x4(struct wl_client *client,
                                  struct wl_resource *res, int32_t a, int32_t b,
                                  int32_t c, int32_t d)
{
    (void)client; (void)res; (void)a; (void)b; (void)c; (void)d;
}

static void positioner_noop_u32(struct wl_client *client,
                                struct wl_resource *res, uint32_t a)
{
    (void)client; (void)res; (void)a;
}

static const struct xdg_positioner_interface positioner_impl = {
    .destroy = positioner_destroy,
    .set_size = positioner_noop_i32x2,
    .set_anchor_rect = positioner_noop_i32x4,
    .set_anchor = positioner_noop_u32,
    .set_gravity = positioner_noop_u32,
    .set_constraint_adjustment = positioner_noop_u32,
    .set_offset = positioner_noop_i32x2,
};

/* --- xdg_wm_base --------------------------------------------------------- */

static void wm_destroy(struct wl_client *client, struct wl_resource *res)
{
    wl_resource_destroy(res);
}

static void wm_create_positioner(struct wl_client *client,
                                 struct wl_resource *res, uint32_t id)
{
    struct wl_resource *p = wl_resource_create(client,
                                               &xdg_positioner_interface, 1, id);

    wl_resource_set_implementation(p, &positioner_impl, NULL, NULL);
}

static void wm_get_xdg_surface(struct wl_client *client,
                               struct wl_resource *res, uint32_t id,
                               struct wl_resource *surface)
{
    struct wlsurf *s = surf_from_resource(surface);
    struct wl_resource *x;

    if (!s)
        return;
    x = wl_resource_create(client, &xdg_surface_interface, 1, id);
    wl_resource_set_implementation(x, &xdg_surface_impl, s, NULL);
    s->xdg_surface = x;
}

static void wm_pong(struct wl_client *client, struct wl_resource *res,
                    uint32_t serial)
{
    (void)client; (void)res; (void)serial;
}

static const struct xdg_wm_base_interface wm_base_impl = {
    .destroy = wm_destroy,
    .create_positioner = wm_create_positioner,
    .get_xdg_surface = wm_get_xdg_surface,
    .pong = wm_pong,
};

static void bind_wm_base(struct wl_client *client, void *data, uint32_t version,
                         uint32_t id)
{
    struct wl_resource *res = wl_resource_create(client, &xdg_wm_base_interface,
                                                 version, id);

    wl_resource_set_implementation(res, &wm_base_impl, NULL, NULL);
}

/* --- zwp_linux_dmabuf_v1 (v3) -------------------------------------------- */

struct dparams {
    int fd;
    int32_t offset, stride;
    uint64_t modifier;
    int have_plane;
    int used;
};

struct wl_rel {
    struct wl_resource *res;
    struct wl_list link;
};

static void dmabuf_free(struct wlbuf *b)
{
    struct wlsurf *s;

    wl_list_for_each(s, &B.surfaces, link) {
        if (s->dmabuf == b) {
            s->dmabuf = NULL;
            s->img = VK_NULL_HANDLE;
            s->mem = VK_NULL_HANDLE;
            s->view = VK_NULL_HANDLE;
            s->set = VK_NULL_HANDLE;
            s->img_owned = 0;
            s->tex_w = s->tex_h = 0;
        }
    }
    if (b->mem)
        vkFreeMemory(B.dev, b->mem, NULL);
    if (b->view)
        vkDestroyImageView(B.dev, b->view, NULL);
    if (b->img)
        vkDestroyImage(B.dev, b->img, NULL);
    if (b->set)
        vkFreeDescriptorSets(B.dev, B.dpool, 1, &b->set);
    free(b);
}

static void buffer_impl_destroy(struct wl_client *client,
                                struct wl_resource *res)
{
    wl_resource_destroy(res);
}

static const struct wl_buffer_interface buffer_impl = {
    .destroy = buffer_impl_destroy,
};

static void buffer_resource_destroy(struct wl_resource *res)
{
    struct wlbuf *b = wl_resource_get_user_data(res);

    if (!b)
        return;
    /* The compositor may still sample it this frame. */
    wl_list_insert(B.retired.prev, &b->retired_link);
}

static void params_destroy(struct wl_client *client, struct wl_resource *res)
{
    wl_resource_destroy(res);
}

static void params_resource_destroy(struct wl_resource *res)
{
    struct dparams *p = wl_resource_get_user_data(res);

    if (!p)
        return;
    if (p->fd >= 0)
        close(p->fd);
    free(p);
}

static void params_add(struct wl_client *client, struct wl_resource *res,
                       int32_t fd, uint32_t plane_idx, uint32_t offset,
                       uint32_t stride, uint32_t mod_hi, uint32_t mod_lo)
{
    struct dparams *p = wl_resource_get_user_data(res);

    if (p->used) {
        close(fd);
        wl_resource_post_error(res, ZWP_LINUX_BUFFER_PARAMS_V1_ERROR_ALREADY_USED,
                               "params already used");
        return;
    }
    if (plane_idx != 0) {
        close(fd);
        wl_resource_post_error(res, ZWP_LINUX_BUFFER_PARAMS_V1_ERROR_PLANE_IDX,
                               "only single-plane formats are supported");
        return;
    }
    if (p->have_plane) {
        close(fd);
        wl_resource_post_error(res, ZWP_LINUX_BUFFER_PARAMS_V1_ERROR_PLANE_SET,
                               "plane 0 already set");
        return;
    }
    p->fd = fd;
    p->offset = offset;
    p->stride = stride;
    p->modifier = ((uint64_t)mod_hi << 32) | mod_lo;
    p->have_plane = 1;
}

static void params_create_common(struct wl_client *client,
                                 struct wl_resource *res, int immed,
                                 uint32_t id, int32_t w, int32_t h,
                                 uint32_t format, uint32_t flags)
{
    struct dparams *p = wl_resource_get_user_data(res);
    struct wlbuf *b;
    struct wl_resource *buf;

    if (!p || p->used) {
        wl_resource_post_error(res, ZWP_LINUX_BUFFER_PARAMS_V1_ERROR_ALREADY_USED,
                               "params already used");
        return;
    }
    if (!p->have_plane) {
        wl_resource_post_error(res, ZWP_LINUX_BUFFER_PARAMS_V1_ERROR_INCOMPLETE,
                               "no plane added");
        return;
    }
    if (w <= 0 || h <= 0) {
        wl_resource_post_error(res,
                               ZWP_LINUX_BUFFER_PARAMS_V1_ERROR_INVALID_DIMENSIONS,
                               "invalid size %dx%d", w, h);
        return;
    }
    if (flags != 0) {
        wl_resource_post_error(res,
                               ZWP_LINUX_BUFFER_PARAMS_V1_ERROR_INVALID_FORMAT,
                               "unsupported flags 0x%x", flags);
        return;
    }

    b = calloc(1, sizeof(*b));
    b->magic = WLBUF_MAGIC;
    wl_list_init(&b->retired_link);
    if (dmabuf_import(b, p->fd, w, h, format, p->offset, p->stride,
                      p->modifier)) {
        b->failed = 1;
        if (!immed) {
            zwp_linux_buffer_params_v1_send_failed(res);
            p->used = 1;
            free(b);
            return;
        }
        /* create_immed: hand out an inert wl_buffer, like wlroots does. */
        buf = wl_resource_create(client, &wl_buffer_interface, 1, id);
        wl_resource_set_implementation(buf, &buffer_impl, b,
                                       buffer_resource_destroy);
        p->used = 1;
        return;
    }

    buf = wl_resource_create(client, &wl_buffer_interface, 1,
                             immed ? id : 0);
    wl_resource_set_implementation(buf, &buffer_impl, b,
                                   buffer_resource_destroy);
    if (!immed)
        zwp_linux_buffer_params_v1_send_created(res, buf);
    p->used = 1;
    printf("dmabuf: wl_buffer %s %dx%d\n", immed ? "create_immed" : "created",
           w, h);
}

static void params_create(struct wl_client *client, struct wl_resource *res,
                          int32_t w, int32_t h, uint32_t format, uint32_t flags)
{
    params_create_common(client, res, 0, 0, w, h, format, flags);
}

static void params_create_immed(struct wl_client *client,
                                struct wl_resource *res, uint32_t id,
                                int32_t w, int32_t h, uint32_t format,
                                uint32_t flags)
{
    params_create_common(client, res, 1, id, w, h, format, flags);
}

static const struct zwp_linux_buffer_params_v1_interface params_impl = {
    .destroy = params_destroy,
    .add = params_add,
    .create = params_create,
    .create_immed = params_create_immed,
};

static void dmabuf_create_params(struct wl_client *client,
                                 struct wl_resource *res, uint32_t id)
{
    struct dparams *p = calloc(1, sizeof(*p));
    struct wl_resource *r;

    p->fd = -1;
    r = wl_resource_create(client, &zwp_linux_buffer_params_v1_interface,
                           wl_resource_get_version(res), id);
    wl_resource_set_implementation(r, &params_impl, p, params_resource_destroy);
}

static void dmabuf_destroy(struct wl_client *client, struct wl_resource *res)
{
    wl_resource_destroy(res);
}

static const struct zwp_linux_dmabuf_v1_interface dmabuf_impl = {
    .destroy = dmabuf_destroy,
    .create_params = dmabuf_create_params,
};

static void bind_dmabuf(struct wl_client *client, void *data, uint32_t version,
                        uint32_t id)
{
    struct wl_resource *res = wl_resource_create(
        client, &zwp_linux_dmabuf_v1_interface, version, id);

    wl_resource_set_implementation(res, &dmabuf_impl, NULL, NULL);

    /* v4+ replaced these with feedback objects; we cap at v3. */
    zwp_linux_dmabuf_v1_send_format(res, DRM_FORMAT_ARGB8888);
    zwp_linux_dmabuf_v1_send_format(res, DRM_FORMAT_XRGB8888);
    if (version >= 3) {
        const uint32_t formats[2] = { DRM_FORMAT_ARGB8888, DRM_FORMAT_XRGB8888 };
        const uint64_t mods[2] = { DRM_FORMAT_MOD_LINEAR,
                                   DRM_FORMAT_MOD_INVALID };

        for (unsigned f = 0; f < 2; f++)
            for (unsigned m = 0; m < 2; m++)
                zwp_linux_dmabuf_v1_send_modifier(res, formats[f],
                                                  (uint32_t)(mods[m] >> 32),
                                                  (uint32_t)mods[m]);
    }
}

/* --- input forwarding ---------------------------------------------------- */

void wl_backend_input(int down, float x, float y)
{
    struct wl_list *l;
    struct wlsurf *hit = NULL;
    uint32_t serial = wl_display_next_serial(B.dpy);
    uint32_t t = now_ms() - B.t0;

    B.ptr_x = x;
    B.ptr_y = y;

    if (B.down && B.grab) {
        /* Keep the pointer on the surface being dragged, even if it moves
         * out from under the finger. */
        hit = B.grab;
    } else {
        for (l = B.surfaces.prev; l != &B.surfaces; l = l->prev) {
            struct wlsurf *s = wl_container_of(l, s, link);

            if (s->mapped && x >= s->x && x < s->x + s->w && y >= s->y &&
                y < s->y + s->h) {
                hit = s;
                break;
            }
        }
    }

    if (down && !hit)
        return;

    if (hit != B.pointer_focus) {
        if (B.pointer_focus)
            ptr_send_leave(B.pointer_focus, serial);
        B.pointer_focus = hit;
        if (hit) {
            ptr_send_enter(hit, serial, x - hit->x, y - hit->y);
            printf("wl: pointer enter surface %d\n", hit->place);
        }
    }

    if (!B.pointer_focus)
        return;

    ptr_send_motion(t, x - B.pointer_focus->x, y - B.pointer_focus->y);

    if (down && !B.down) {
        ptr_send_button(serial, t, WL_POINTER_BUTTON_STATE_PRESSED);
        B.grab = B.pointer_focus;
        B.grab_dx = x - B.grab->x;
        B.grab_dy = y - B.grab->y;
        /* Click-to-focus for the keyboard. */
        kbd_set_focus(B.pointer_focus, serial);
        printf("wl: pointer button down on surface %d\n", B.grab->place);
    } else if (down && B.down) {
        if (B.grab) {
            dmg_surf(B.grab);
            B.grab->x = x - B.grab_dx;
            B.grab->y = y - B.grab_dy;
            if (B.grab->x < 0)
                B.grab->x = 0;
            if (B.grab->y < 0)
                B.grab->y = 0;
            if (B.grab->x + B.grab->w > (float)B.fbw)
                B.grab->x = (float)B.fbw - B.grab->w;
            if (B.grab->y + B.grab->h > (float)B.fbh)
                B.grab->y = (float)B.fbh - B.grab->h;
            dmg_surf(B.grab);
        }
    } else if (!down && B.down) {
        ptr_send_button(serial, t, WL_POINTER_BUTTON_STATE_RELEASED);
        printf("wl: pointer button up\n");
        B.grab = NULL;
    }

    ptr_send_frame();

    B.down = down;
}

/* --- init / pump / frame / collect --------------------------------------- */

/* Any evdev node with a full alphabet is treated as a keyboard. */
static int kbd_open(void)
{
    const char *forced = getenv("VK_WL_KBD");
    char path[64];
    int i;

    for (i = 0; i < 32; i++) {
        unsigned long keys[(KEY_MAX / (8 * sizeof(unsigned long))) + 1] = { 0 };
        int fd;

        if (forced)
            snprintf(path, sizeof(path), "%s", forced);
        else
            snprintf(path, sizeof(path), "/dev/input/event%d", i);

        fd = open(path, O_RDONLY | O_NONBLOCK);
        if (fd < 0) {
            if (forced)
                return -1;
            continue;
        }
        if (ioctl(fd, EVIOCGBIT(EV_KEY, sizeof(keys)), keys) < 0 ||
            !(keys[KEY_A / (8 * sizeof(unsigned long))] &
              (1UL << (KEY_A % (8 * sizeof(unsigned long))))) ||
            !(keys[KEY_Z / (8 * sizeof(unsigned long))] &
              (1UL << (KEY_Z % (8 * sizeof(unsigned long)))))) {
            close(fd);
            if (forced)
                return -1;
            continue;
        }
        printf("kbd: using %s\n", path);
        return fd;
    }
    return -1;
}

int wl_backend_init(const struct wl_backend_cfg *cfg)
{
    const char *sock = getenv("VK_WL_SOCKET");
    const char *rt = getenv("XDG_RUNTIME_DIR");
    char dir[256];

    memset(&B, 0, sizeof(B));
    B.fbw = cfg->fb_width;
    B.fbh = cfg->fb_height;
    B.pd = cfg->pd;
    B.dev = cfg->dev;
    B.dsl = cfg->dsl;
    B.dpool = cfg->dpool;
    B.sampler = cfg->sampler;
    B.get_fd_props = cfg->get_fd_props;
    B.t0 = now_ms();
    wl_list_init(&B.surfaces);
    wl_list_init(&B.ptrs);
    wl_list_init(&B.kbds);
    wl_list_init(&B.retired);
    wl_list_init(&B.release);

    if (!rt) {
        snprintf(dir, sizeof(dir), "/tmp/vk-wl-%u", (unsigned)getuid());
        mkdir(dir, 0700);
        setenv("XDG_RUNTIME_DIR", dir, 1);
    }

    B.dpy = wl_display_create();
    if (!B.dpy) {
        fprintf(stderr, "wl: wl_display_create failed\n");
        return -1;
    }
    if (wl_display_add_socket(B.dpy, sock ? sock : "wayland-vk")) {
        fprintf(stderr, "wl: add_socket(%s) failed: %s\n",
                sock ? sock : "wayland-vk", strerror(errno));
        return -1;
    }
    if (wl_display_init_shm(B.dpy)) {
        fprintf(stderr, "wl: init_shm failed\n");
        return -1;
    }

    wl_global_create(B.dpy, &wl_compositor_interface, 4, NULL,
                     bind_compositor);
    wl_global_create(B.dpy, &wl_seat_interface, 5, NULL, bind_seat);
    wl_global_create(B.dpy, &wl_output_interface, 2, NULL, bind_output);
    wl_global_create(B.dpy, &xdg_wm_base_interface, 1, NULL, bind_wm_base);
    wl_global_create(B.dpy, &zwp_linux_dmabuf_v1_interface, 3, NULL,
                     bind_dmabuf);

    printf("wl: listening on %s/%s (%ux%u)\n", getenv("XDG_RUNTIME_DIR"),
           sock ? sock : "wayland-vk", B.fbw, B.fbh);

    B.kbd_fd = kbd_open();
    if (B.kbd_fd < 0)
        printf("kbd: no keyboard device found\n");
    return 0;
}

void wl_backend_pump(void)
{
    struct wl_event_loop *loop = wl_display_get_event_loop(B.dpy);

    kbd_poll();
    wl_event_loop_dispatch(loop, 0);
    wl_display_flush_clients(B.dpy);
}

void wl_backend_wait(int timeout_ms)
{
    struct wl_event_loop *loop = wl_display_get_event_loop(B.dpy);

    kbd_poll();
    wl_event_loop_dispatch(loop, timeout_ms);
    wl_display_flush_clients(B.dpy);
}

static int surf_has_callbacks(void)
{
    struct wlsurf *s;

    wl_list_for_each(s, &B.surfaces, link) {
        if (!wl_list_empty(&s->frame_cbs))
            return 1;
    }
    return 0;
}

int wl_backend_needs_frame(void)
{
    return B.dmg_valid || surf_has_callbacks();
}

int wl_backend_take_damage(int32_t out[4])
{
    if (!B.dmg_valid)
        return 0;
    out[0] = B.dmg[0];
    out[1] = B.dmg[1];
    out[2] = B.dmg[2];
    out[3] = B.dmg[3];
    B.dmg_valid = 0;
    return 1;
}

void wl_backend_frame(uint32_t time_ms)
{
    struct wlsurf *s;
    struct wl_rel *rel, *rtmp;
    struct wlbuf *b, *btmp;

    wl_list_for_each(s, &B.surfaces, link) {
        struct wl_cb *cb, *tmp;

        wl_list_for_each_safe(cb, tmp, &s->frame_cbs, link) {
            wl_callback_send_done(cb->res, time_ms);
            wl_resource_destroy(cb->res);
            wl_list_remove(&cb->link);
            free(cb);
        }
    }

    /* One full frame has been recorded with these buffers. */
    wl_list_for_each_safe(rel, rtmp, &B.release, link) {
        wl_buffer_send_release(rel->res);
        wl_list_remove(&rel->link);
        free(rel);
    }
    wl_list_for_each_safe(b, btmp, &B.retired, retired_link) {
        wl_list_remove(&b->retired_link);
        dmabuf_free(b);
    }
    /* Push callbacks out now: waiting for the next pump would cost a vblank. */
    wl_display_flush_clients(B.dpy);
}

int wl_backend_collect(struct wl_draw_surf *out, int max)
{
    struct wlsurf *s;
    int n = 0;

    wl_list_for_each(s, &B.surfaces, link) {
        if (!s->mapped || !s->img || !s->set || n >= max)
            continue;
        out[n].x = s->x;
        out[n].y = s->y;
        out[n].w = s->w;
        out[n].h = s->h;
        out[n].tex = s->set;
        n++;
    }
    return n;
}

int wl_backend_client_count(void)
{
    return B.ncreated - B.ndestroyed;
}
