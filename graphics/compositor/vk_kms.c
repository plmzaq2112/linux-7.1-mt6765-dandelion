/* vk_kms - minimal "compositor core" for the Redmi 9A.
 *
 * Renders an animated scene with Mesa PowerVR Vulkan and presents it straight
 * to the DSI panel through DRM/KMS:
 *   - allocates two linear 720x1600 images with VK_EXT_external_memory_dma_buf
 *   - exports them as dma-buf fds and imports them into DRM as framebuffers
 *   - page-flip loop paced by DRM flip events
 * If dma-buf export is unavailable, falls back to a DRM dumb buffer + CPU copy
 * (VK_KMS_DUMB=1 forces the fallback).
 *
 * Env: VK_KMS_DRM (default /dev/dri/card0), VK_KMS_SECS (default 20),
 *      VK_KMS_DUMB=1, VK_KMS_VERBOSE=1.
 */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <math.h>
#include <poll.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <time.h>
#include <unistd.h>

#include <drm_fourcc.h>
#include <xf86drm.h>
#include <xf86drmMode.h>

#include <vulkan/vulkan.h>

#include "color_vert_spv.h"
#include "color_frag_spv.h"

#define CHECK_VK(x)                                                          \
    do {                                                                     \
        VkResult r_ = (x);                                                   \
        if (r_ != VK_SUCCESS) {                                              \
            fprintf(stderr, "%s -> VkResult %d\n", #x, r_);                  \
            exit(1);                                                         \
        }                                                                    \
    } while (0)

#define CHECK_DRM(x)                                                         \
    do {                                                                     \
        int r_ = (x);                                                        \
        if (r_ < 0) {                                                        \
            fprintf(stderr, "%s -> %d (%s)\n", #x, r_, strerror(errno));     \
            exit(1);                                                         \
        }                                                                    \
    } while (0)

/* ------------------------------------------------------------------ DRM */

struct drm_state {
    int fd;
    drmModeRes *res;
    drmModeConnector *conn;
    drmModeEncoder *enc;
    drmModeCrtc *orig_crtc;
    drmModeModeInfo mode;
    uint32_t crtc_id;
    uint32_t conn_id;
};

static volatile int g_flip_done;

static void flip_handler(int fd, unsigned seq, unsigned sec, unsigned usec,
                         void *data)
{
    (void)fd;
    (void)seq;
    (void)sec;
    (void)usec;
    (void)data;
    g_flip_done = 1;
}

static int wait_flip(int fd)
{
    while (!g_flip_done) {
        drmEventContext ev = {
            .version = 2,
            .page_flip_handler = flip_handler,
        };
        int r = drmHandleEvent(fd, &ev);
        if (r < 0) {
            fprintf(stderr, "drmHandleEvent: %s\n", strerror(errno));
            return -1;
        }
    }
    return 0;
}

static int drm_find_output(struct drm_state *d)
{
    uint32_t i;

    d->res = drmModeGetResources(d->fd);
    if (!d->res) {
        fprintf(stderr, "drmModeGetResources failed\n");
        return -1;
    }

    for (i = 0; i < (uint32_t)d->res->count_connectors; i++) {
        drmModeConnector *c = drmModeGetConnector(d->fd, d->res->connectors[i]);
        if (!c)
            continue;
        if (c->connection == DRM_MODE_CONNECTED && c->count_modes > 0) {
            d->conn = c;
            d->conn_id = c->connector_id;
            break;
        }
        drmModeFreeConnector(c);
    }
    if (!d->conn) {
        fprintf(stderr, "no connected connector with modes\n");
        return -1;
    }

    d->mode = d->conn->modes[0];
    for (i = 0; i < (uint32_t)d->conn->count_modes; i++) {
        if (d->conn->modes[i].type & DRM_MODE_TYPE_PREFERRED) {
            d->mode = d->conn->modes[i];
            break;
        }
    }

    if (d->conn->encoder_id)
        d->enc = drmModeGetEncoder(d->fd, d->conn->encoder_id);
    if (!d->enc && d->conn->count_encoders)
        d->enc = drmModeGetEncoder(d->fd, d->conn->encoders[0]);
    if (!d->enc) {
        fprintf(stderr, "no encoder for connector\n");
        return -1;
    }

    d->crtc_id = d->enc->crtc_id;
    if (!d->crtc_id && d->res->count_crtcs)
        d->crtc_id = d->res->crtcs[0];

    d->orig_crtc = drmModeGetCrtc(d->fd, d->crtc_id);

    printf("drm: connector %u mode \"%s\" %ux%u@%u crtc=%u\n", d->conn_id,
           d->mode.name, d->mode.hdisplay, d->mode.vdisplay, d->mode.vrefresh,
           d->crtc_id);
    return 0;
}

/* ----------------------------------------------------------------- Vulkan */

struct vk_state {
    VkInstance inst;
    VkPhysicalDevice pd;
    VkDevice dev;
    VkQueue queue;
    uint32_t qfam;
    VkCommandPool pool;
    VkCommandBuffer cmd;
    VkFence fence;

    VkShaderModule vs, fs;
    VkPipelineLayout layout;
    VkPipeline pipe;
    VkRenderPass rp;

    VkBuffer vbo;
    VkDeviceMemory vbo_mem;
    void *vbo_ptr;

    PFN_vkGetMemoryFdKHR get_memory_fd;
};

struct frame {
    VkImage image;
    VkDeviceMemory mem;
    VkImageView view;
    VkFramebuffer fb;
    void *host;
    uint64_t size;
    uint64_t pitch;
    int dmabuf_fd;
    uint32_t drm_fb;
    uint32_t dumb_handle;
    uint32_t dumb_pitch;
    void *dumb_ptr;
};

static uint32_t find_mem_type(VkPhysicalDevice pd, uint32_t bits,
                              VkMemoryPropertyFlags want)
{
    VkPhysicalDeviceMemoryProperties mp;
    vkGetPhysicalDeviceMemoryProperties(pd, &mp);
    for (uint32_t i = 0; i < mp.memoryTypeCount; i++)
        if ((bits & (1u << i)) &&
            (mp.memoryTypes[i].propertyFlags & want) == want)
            return i;
    return UINT32_MAX;
}

static int ext_supported(VkPhysicalDevice pd, const char *name)
{
    uint32_t n = 0;
    if (vkEnumerateDeviceExtensionProperties(pd, NULL, &n, NULL) != VK_SUCCESS)
        return 0;
    VkExtensionProperties *ex = calloc(n, sizeof(*ex));
    vkEnumerateDeviceExtensionProperties(pd, NULL, &n, ex);
    int found = 0;
    for (uint32_t i = 0; i < n; i++)
        if (!strcmp(ex[i].extensionName, name))
            found = 1;
    free(ex);
    return found;
}

static VkShaderModule make_shader(VkDevice dev, const unsigned char *code,
                                  unsigned int size)
{
    VkShaderModuleCreateInfo ci = {
        .sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO,
        .codeSize = size,
        .pCode = (const uint32_t *)code,
    };
    VkShaderModule m;
    CHECK_VK(vkCreateShaderModule(dev, &ci, NULL, &m));
    return m;
}

static void vk_init(struct vk_state *v, VkFormat fmt)
{
    VkApplicationInfo app = {
        .sType = VK_STRUCTURE_TYPE_APPLICATION_INFO,
        .pApplicationName = "vk_kms",
        .apiVersion = VK_API_VERSION_1_0,
    };
    VkInstanceCreateInfo ici = {
        .sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO,
        .pApplicationInfo = &app,
    };
    memset(v, 0, sizeof(*v));
    CHECK_VK(vkCreateInstance(&ici, NULL, &v->inst));

    uint32_t n = 0;
    CHECK_VK(vkEnumeratePhysicalDevices(v->inst, &n, NULL));
    if (!n) {
        fprintf(stderr, "no Vulkan device\n");
        exit(1);
    }
    VkPhysicalDevice *pds = calloc(n, sizeof(*pds));
    vkEnumeratePhysicalDevices(v->inst, &n, pds);
    v->pd = pds[0];
    free(pds);

    uint32_t qn = 0;
    vkGetPhysicalDeviceQueueFamilyProperties(v->pd, &qn, NULL);
    VkQueueFamilyProperties *qf = calloc(qn, sizeof(*qf));
    vkGetPhysicalDeviceQueueFamilyProperties(v->pd, &qn, qf);
    for (uint32_t i = 0; i < qn; i++)
        if (qf[i].queueFlags & VK_QUEUE_GRAPHICS_BIT) {
            v->qfam = i;
            break;
        }
    free(qf);

    const char *want[] = {
        "VK_KHR_external_memory",
        "VK_KHR_external_memory_fd",
        "VK_EXT_external_memory_dma_buf",
        "VK_KHR_dedicated_allocation",
        "VK_KHR_get_memory_requirements2",
        "VK_KHR_image_format_list",
        "VK_EXT_image_drm_format_modifier",
    };
    const char *enable[8];
    uint32_t n_enable = 0;
    for (uint32_t i = 0; i < sizeof(want) / sizeof(want[0]); i++)
        if (ext_supported(v->pd, want[i]))
            enable[n_enable++] = want[i];
    printf("vk: enabling %u device extensions\n", n_enable);

    float prio = 1.0f;
    VkDeviceQueueCreateInfo qci = {
        .sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO,
        .queueFamilyIndex = v->qfam,
        .queueCount = 1,
        .pQueuePriorities = &prio,
    };
    VkDeviceCreateInfo dci = {
        .sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO,
        .queueCreateInfoCount = 1,
        .pQueueCreateInfos = &qci,
        .enabledExtensionCount = n_enable,
        .ppEnabledExtensionNames = enable,
    };
    CHECK_VK(vkCreateDevice(v->pd, &dci, NULL, &v->dev));
    vkGetDeviceQueue(v->dev, v->qfam, 0, &v->queue);
    v->get_memory_fd = (PFN_vkGetMemoryFdKHR)vkGetDeviceProcAddr(
        v->dev, "vkGetMemoryFdKHR");

    VkCommandPoolCreateInfo pci = {
        .sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO,
        .queueFamilyIndex = v->qfam,
        .flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT,
    };
    CHECK_VK(vkCreateCommandPool(v->dev, &pci, NULL, &v->pool));
    VkCommandBufferAllocateInfo cbi = {
        .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,
        .commandPool = v->pool,
        .level = VK_COMMAND_BUFFER_LEVEL_PRIMARY,
        .commandBufferCount = 1,
    };
    CHECK_VK(vkAllocateCommandBuffers(v->dev, &cbi, &v->cmd));
    VkFenceCreateInfo fci = { .sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO };
    CHECK_VK(vkCreateFence(v->dev, &fci, NULL, &v->fence));

    v->vs = make_shader(v->dev, color_vert_spv, color_vert_spv_len);
    v->fs = make_shader(v->dev, color_frag_spv, color_frag_spv_len);

    VkAttachmentDescription att = {
        .format = fmt,
        .samples = VK_SAMPLE_COUNT_1_BIT,
        .loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR,
        .storeOp = VK_ATTACHMENT_STORE_OP_STORE,
        .stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE,
        .stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE,
        .initialLayout = VK_IMAGE_LAYOUT_UNDEFINED,
        .finalLayout = VK_IMAGE_LAYOUT_GENERAL,
    };
    VkAttachmentReference ref = { 0, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL };
    VkSubpassDescription sp = {
        .pipelineBindPoint = VK_PIPELINE_BIND_POINT_GRAPHICS,
        .colorAttachmentCount = 1,
        .pColorAttachments = &ref,
    };
    VkRenderPassCreateInfo rpci = {
        .sType = VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO,
        .attachmentCount = 1,
        .pAttachments = &att,
        .subpassCount = 1,
        .pSubpasses = &sp,
    };
    CHECK_VK(vkCreateRenderPass(v->dev, &rpci, NULL, &v->rp));

    VkPipelineShaderStageCreateInfo stages[2] = {
        { .sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO,
          .stage = VK_SHADER_STAGE_VERTEX_BIT, .module = v->vs,
          .pName = "main" },
        { .sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO,
          .stage = VK_SHADER_STAGE_FRAGMENT_BIT, .module = v->fs,
          .pName = "main" },
    };
    VkVertexInputBindingDescription vib = {
        .binding = 0,
        .stride = 5 * sizeof(float),
        .inputRate = VK_VERTEX_INPUT_RATE_VERTEX,
    };
    VkVertexInputAttributeDescription via[2] = {
        { .location = 0, .binding = 0, .format = VK_FORMAT_R32G32_SFLOAT,
          .offset = 0 },
        { .location = 1, .binding = 0, .format = VK_FORMAT_R32G32B32_SFLOAT,
          .offset = 2 * sizeof(float) },
    };
    VkPipelineVertexInputStateCreateInfo vi = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO,
        .vertexBindingDescriptionCount = 1,
        .pVertexBindingDescriptions = &vib,
        .vertexAttributeDescriptionCount = 2,
        .pVertexAttributeDescriptions = via,
    };
    VkPipelineInputAssemblyStateCreateInfo ia = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO,
        .topology = VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST,
    };
    VkPipelineViewportStateCreateInfo vps = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO,
        .viewportCount = 1,
        .scissorCount = 1,
    };
    VkPipelineRasterizationStateCreateInfo rs = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO,
        .polygonMode = VK_POLYGON_MODE_FILL,
        .cullMode = VK_CULL_MODE_NONE,
        .frontFace = VK_FRONT_FACE_COUNTER_CLOCKWISE,
        .lineWidth = 1.0f,
    };
    VkPipelineMultisampleStateCreateInfo ms = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO,
        .rasterizationSamples = VK_SAMPLE_COUNT_1_BIT,
    };
    VkPipelineColorBlendAttachmentState cba = {
        .blendEnable = VK_FALSE,
        .colorWriteMask = 0xf,
    };
    VkPipelineColorBlendStateCreateInfo cb = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO,
        .attachmentCount = 1,
        .pAttachments = &cba,
    };
    VkDynamicState dyn[2] = { VK_DYNAMIC_STATE_VIEWPORT,
                              VK_DYNAMIC_STATE_SCISSOR };
    VkPipelineDynamicStateCreateInfo ds = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_DYNAMIC_STATE_CREATE_INFO,
        .dynamicStateCount = 2,
        .pDynamicStates = dyn,
    };
    VkPipelineLayoutCreateInfo plci = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO,
    };
    CHECK_VK(vkCreatePipelineLayout(v->dev, &plci, NULL, &v->layout));
    VkGraphicsPipelineCreateInfo gpci = {
        .sType = VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO,
        .stageCount = 2,
        .pStages = stages,
        .pVertexInputState = &vi,
        .pInputAssemblyState = &ia,
        .pViewportState = &vps,
        .pRasterizationState = &rs,
        .pMultisampleState = &ms,
        .pColorBlendState = &cb,
        .pDynamicState = &ds,
        .layout = v->layout,
        .renderPass = v->rp,
        .subpass = 0,
    };
    CHECK_VK(vkCreateGraphicsPipelines(v->dev, VK_NULL_HANDLE, 1, &gpci, NULL,
                                       &v->pipe));

    VkBufferCreateInfo bci = {
        .sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO,
        .size = 6 * 5 * sizeof(float),
        .usage = VK_BUFFER_USAGE_VERTEX_BUFFER_BIT,
    };
    CHECK_VK(vkCreateBuffer(v->dev, &bci, NULL, &v->vbo));
    VkMemoryRequirements mr;
    vkGetBufferMemoryRequirements(v->dev, v->vbo, &mr);
    VkMemoryAllocateInfo mai = {
        .sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
        .allocationSize = mr.size,
        .memoryTypeIndex = find_mem_type(
            v->pd, mr.memoryTypeBits,
            VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT |
                VK_MEMORY_PROPERTY_HOST_COHERENT_BIT),
    };
    CHECK_VK(vkAllocateMemory(v->dev, &mai, NULL, &v->vbo_mem));
    CHECK_VK(vkBindBufferMemory(v->dev, v->vbo, v->vbo_mem, 0));
    CHECK_VK(vkMapMemory(v->dev, v->vbo_mem, 0, VK_WHOLE_SIZE, 0, &v->vbo_ptr));
}

static int frame_init(struct vk_state *v, struct frame *f, uint32_t w,
                      uint32_t h, VkFormat fmt, int want_export)
{
    memset(f, 0, sizeof(*f));
    f->dmabuf_fd = -1;

    VkExternalMemoryImageCreateInfo ext = {
        .sType = VK_STRUCTURE_TYPE_EXTERNAL_MEMORY_IMAGE_CREATE_INFO,
        .handleTypes = VK_EXTERNAL_MEMORY_HANDLE_TYPE_DMA_BUF_BIT_EXT,
    };
    VkImageCreateInfo ci = {
        .sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO,
        .pNext = want_export ? &ext : NULL,
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
    CHECK_VK(vkCreateImage(v->dev, &ci, NULL, &f->image));

    VkMemoryRequirements mr;
    vkGetImageMemoryRequirements(v->dev, f->image, &mr);

    VkMemoryDedicatedAllocateInfo ded = {
        .sType = VK_STRUCTURE_TYPE_MEMORY_DEDICATED_ALLOCATE_INFO,
        .image = f->image,
    };
    VkExportMemoryAllocateInfo export_info = {
        .sType = VK_STRUCTURE_TYPE_EXPORT_MEMORY_ALLOCATE_INFO,
        .pNext = &ded,
        .handleTypes = VK_EXTERNAL_MEMORY_HANDLE_TYPE_DMA_BUF_BIT_EXT,
    };
    VkMemoryAllocateInfo mai = {
        .sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
        .pNext = want_export ? &export_info : (void *)&ded,
        .allocationSize = mr.size,
        .memoryTypeIndex = find_mem_type(
            v->pd, mr.memoryTypeBits,
            VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT |
                VK_MEMORY_PROPERTY_HOST_COHERENT_BIT),
    };
    if (mai.memoryTypeIndex == UINT32_MAX)
        mai.memoryTypeIndex = find_mem_type(v->pd, mr.memoryTypeBits, 0);
    VkResult r = vkAllocateMemory(v->dev, &mai, NULL, &f->mem);
    if (r != VK_SUCCESS) {
        fprintf(stderr, "image memory alloc failed: %d\n", r);
        return -1;
    }
    CHECK_VK(vkBindImageMemory(v->dev, f->image, f->mem, 0));
    f->size = mr.size;
    r = vkMapMemory(v->dev, f->mem, 0, VK_WHOLE_SIZE, 0, &f->host);
    if (r != VK_SUCCESS) {
        fprintf(stderr, "image map failed: %d\n", r);
        f->host = NULL;
    }

    VkImageSubresource sub = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 0 };
    VkSubresourceLayout lay;
    vkGetImageSubresourceLayout(v->dev, f->image, &sub, &lay);
    f->pitch = lay.rowPitch;
    printf("frame: %ux%u pitch=%llu offset=%llu size=%llu host=%p\n", w, h,
           (unsigned long long)lay.rowPitch, (unsigned long long)lay.offset,
           (unsigned long long)mr.size, f->host);

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

static void build_scene(struct vk_state *v, float t)
{
    float verts[6][5];
    const float quad[4][2] = { { -0.7f, -0.7f }, { 0.7f, -0.7f },
                               { -0.7f, 0.7f }, { 0.7f, 0.7f } };
    const float col[4][3] = {
        { 1, 0, 0 }, { 0, 1, 0 }, { 0, 0, 1 }, { 1, 1, 0 }
    };
    const int idx[6] = { 0, 1, 2, 3, 2, 1 };
    float c = cosf(t), s = sinf(t);

    for (int i = 0; i < 6; i++) {
        int k = idx[i];
        verts[i][0] = quad[k][0] * c - quad[k][1] * s;
        verts[i][1] = quad[k][0] * s + quad[k][1] * c;
        verts[i][2] = col[k][0];
        verts[i][3] = col[k][1];
        verts[i][4] = col[k][2];
    }
    memcpy(v->vbo_ptr, verts, sizeof(verts));
}

int main(void)
{
    const char *drm_path =
        getenv("VK_KMS_DRM") ? getenv("VK_KMS_DRM") : "/dev/dri/card0";
    int seconds = getenv("VK_KMS_SECS") ? atoi(getenv("VK_KMS_SECS")) : 20;
    int force_dumb = getenv("VK_KMS_DUMB") != NULL;

    struct drm_state d;
    memset(&d, 0, sizeof(d));
    d.fd = open(drm_path, O_RDWR);
    if (d.fd < 0) {
        fprintf(stderr, "open %s: %s\n", drm_path, strerror(errno));
        return 1;
    }
    if (drm_find_output(&d))
        return 1;
    if (drmSetMaster(d.fd))
        fprintf(stderr, "drmSetMaster: %s (continuing)\n", strerror(errno));

    uint32_t w = d.mode.hdisplay, h = d.mode.vdisplay;

    struct vk_state v;
    VkFormat fmt = VK_FORMAT_B8G8R8A8_UNORM;
    vk_init(&v, fmt);

    struct frame fr[2];
    int use_dmabuf = force_dumb ? 0 : 1;
    if (frame_init(&v, &fr[0], w, h, fmt, use_dmabuf) ||
        frame_init(&v, &fr[1], w, h, fmt, use_dmabuf))
        return 1;

    if (use_dmabuf && !v.get_memory_fd) {
        fprintf(stderr, "vkGetMemoryFdKHR unavailable\n");
        use_dmabuf = 0;
    }

    for (int i = 0; i < 2 && use_dmabuf; i++) {
        VkMemoryGetFdInfoKHR gi = {
            .sType = VK_STRUCTURE_TYPE_MEMORY_GET_FD_INFO_KHR,
            .memory = fr[i].mem,
            .handleType = VK_EXTERNAL_MEMORY_HANDLE_TYPE_DMA_BUF_BIT_EXT,
        };
        VkResult r = v.get_memory_fd(v.dev, &gi, &fr[i].dmabuf_fd);
        if (r != VK_SUCCESS) {
            fprintf(stderr, "vkGetMemoryFdKHR: %d\n", r);
            use_dmabuf = 0;
            break;
        }
        uint32_t handle = 0;
        if (drmPrimeFDToHandle(d.fd, fr[i].dmabuf_fd, &handle)) {
            fprintf(stderr, "drmPrimeFDToHandle: %s\n", strerror(errno));
            use_dmabuf = 0;
            break;
        }
        uint32_t handles[4] = { handle, 0, 0, 0 };
        uint32_t pitches[4] = { (uint32_t)fr[i].pitch, 0, 0, 0 };
        uint32_t offsets[4] = { 0, 0, 0, 0 };
        uint32_t fourccs[3] = { DRM_FORMAT_ARGB8888, DRM_FORMAT_XRGB8888,
                                DRM_FORMAT_ABGR8888 };
        int ok = 0;
        for (int k = 0; k < 3; k++) {
            if (drmModeAddFB2(d.fd, w, h, fourccs[k], handles, pitches,
                              offsets, &fr[i].drm_fb, 0) == 0) {
                printf("dmabuf fb[%d] ok fourcc=%08x pitch=%u fd=%d\n", i,
                       fourccs[k], (uint32_t)fr[i].pitch, fr[i].dmabuf_fd);
                ok = 1;
                break;
            }
        }
        if (!ok) {
            fprintf(stderr, "drmModeAddFB2 failed on dma-buf\n");
            use_dmabuf = 0;
        }
    }

    if (!use_dmabuf) {
        printf("using dumb buffers + CPU copy\n");
        for (int i = 0; i < 2; i++) {
            struct drm_mode_create_dumb cd = {
                .width = w,
                .height = h,
                .bpp = 32,
            };
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
        if (!fr[0].host || !fr[1].host) {
            fprintf(stderr, "images are not host visible, cannot copy\n");
            return 1;
        }
    }

    /* First frame: render before the initial modeset. */
    {
        struct frame *f = &fr[0];
        build_scene(&v, 0.0f);
        VkCommandBufferBeginInfo bi = {
            .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO,
        };
        CHECK_VK(vkBeginCommandBuffer(v.cmd, &bi));
        VkClearValue cv = { .color = { { 0.05f, 0.05f, 0.1f, 1.0f } } };
        VkRenderPassBeginInfo rbi = {
            .sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO,
            .renderPass = v.rp,
            .framebuffer = f->fb,
            .renderArea = { { 0, 0 }, { w, h } },
            .clearValueCount = 1,
            .pClearValues = &cv,
        };
        vkCmdBeginRenderPass(v.cmd, &rbi, VK_SUBPASS_CONTENTS_INLINE);
        vkCmdBindPipeline(v.cmd, VK_PIPELINE_BIND_POINT_GRAPHICS, v.pipe);
        VkViewport vp = { 0, 0, (float)w, (float)h, 0, 1 };
        VkRect2D sc = { { 0, 0 }, { w, h } };
        vkCmdSetViewport(v.cmd, 0, 1, &vp);
        vkCmdSetScissor(v.cmd, 0, 1, &sc);
        VkDeviceSize off = 0;
        vkCmdBindVertexBuffers(v.cmd, 0, 1, &v.vbo, &off);
        vkCmdDraw(v.cmd, 6, 1, 0, 0);
        vkCmdEndRenderPass(v.cmd);
        CHECK_VK(vkEndCommandBuffer(v.cmd));
        VkSubmitInfo si = {
            .sType = VK_STRUCTURE_TYPE_SUBMIT_INFO,
            .commandBufferCount = 1,
            .pCommandBuffers = &v.cmd,
        };
        CHECK_VK(vkResetFences(v.dev, 1, &v.fence));
        CHECK_VK(vkQueueSubmit(v.queue, 1, &si, v.fence));
        CHECK_VK(vkWaitForFences(v.dev, 1, &v.fence, VK_TRUE, 2000000000ull));
        if (!use_dmabuf) {
            for (uint32_t y = 0; y < h; y++)
                memcpy((char *)f->dumb_ptr + (size_t)y * f->dumb_pitch,
                       (const char *)f->host + (size_t)y * f->pitch,
                       (size_t)w * 4);
        }
    }

    CHECK_DRM(drmModeSetCrtc(d.fd, d.crtc_id, fr[0].drm_fb, 0, 0, &d.conn_id, 1,
                             &d.mode));

    struct timespec t0;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    uint64_t frames = 0;
    int cur = 1;

    while (1) {
        struct timespec now;
        clock_gettime(CLOCK_MONOTONIC, &now);
        double elapsed = (now.tv_sec - t0.tv_sec) +
                         (now.tv_nsec - t0.tv_nsec) / 1e9;
        if (elapsed >= seconds)
            break;

        struct frame *f = &fr[cur];
        build_scene(&v, (float)elapsed * 0.8f);

        VkCommandBufferBeginInfo bi = {
            .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO,
        };
        CHECK_VK(vkBeginCommandBuffer(v.cmd, &bi));
        VkClearValue cv = { .color = { { 0.05f, 0.05f, 0.1f, 1.0f } } };
        VkRenderPassBeginInfo rbi = {
            .sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO,
            .renderPass = v.rp,
            .framebuffer = f->fb,
            .renderArea = { { 0, 0 }, { w, h } },
            .clearValueCount = 1,
            .pClearValues = &cv,
        };
        vkCmdBeginRenderPass(v.cmd, &rbi, VK_SUBPASS_CONTENTS_INLINE);
        vkCmdBindPipeline(v.cmd, VK_PIPELINE_BIND_POINT_GRAPHICS, v.pipe);
        VkViewport vp = { 0, 0, (float)w, (float)h, 0, 1 };
        VkRect2D sc = { { 0, 0 }, { w, h } };
        vkCmdSetViewport(v.cmd, 0, 1, &vp);
        vkCmdSetScissor(v.cmd, 0, 1, &sc);
        VkDeviceSize off = 0;
        vkCmdBindVertexBuffers(v.cmd, 0, 1, &v.vbo, &off);
        vkCmdDraw(v.cmd, 6, 1, 0, 0);
        vkCmdEndRenderPass(v.cmd);
        CHECK_VK(vkEndCommandBuffer(v.cmd));

        VkSubmitInfo si = {
            .sType = VK_STRUCTURE_TYPE_SUBMIT_INFO,
            .commandBufferCount = 1,
            .pCommandBuffers = &v.cmd,
        };
        CHECK_VK(vkResetFences(v.dev, 1, &v.fence));
        CHECK_VK(vkQueueSubmit(v.queue, 1, &si, v.fence));
        CHECK_VK(vkWaitForFences(v.dev, 1, &v.fence, VK_TRUE, 2000000000ull));

        if (!use_dmabuf) {
            for (uint32_t y = 0; y < h; y++)
                memcpy((char *)f->dumb_ptr + (size_t)y * f->dumb_pitch,
                       (const char *)f->host + (size_t)y * f->pitch,
                       (size_t)w * 4);
        }

        g_flip_done = 0;
        if (drmModePageFlip(d.fd, d.crtc_id, f->drm_fb,
                            DRM_MODE_PAGE_FLIP_EVENT, NULL)) {
            fprintf(stderr, "page flip failed: %s\n", strerror(errno));
            break;
        }
        if (wait_flip(d.fd))
            break;

        frames++;
        cur ^= 1;
    }

    struct timespec t1;
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double total =
        (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;
    printf("presented %llu frames in %.2fs (%.1f fps), mode=%s\n",
           (unsigned long long)frames, total, frames / total,
           use_dmabuf ? "dmabuf" : "dumb");

    if (d.orig_crtc && d.orig_crtc->mode_valid)
        drmModeSetCrtc(d.fd, d.crtc_id, d.orig_crtc->buffer_id,
                       d.orig_crtc->x, d.orig_crtc->y, &d.conn_id, 1,
                       &d.orig_crtc->mode);
    return frames ? 0 : 2;
}
