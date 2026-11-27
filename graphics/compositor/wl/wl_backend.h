/* Minimal Wayland server backend for the Vulkan KMS compositor. */
#ifndef WL_BACKEND_H
#define WL_BACKEND_H

#include <stdint.h>
#include <vulkan/vulkan.h>

struct wl_backend_cfg {
    uint32_t fb_width, fb_height;
    VkPhysicalDevice pd;
    VkDevice dev;
    VkDescriptorSetLayout dsl;
    VkDescriptorPool dpool;
    VkSampler sampler;
    PFN_vkGetMemoryFdPropertiesKHR get_fd_props;
};

/* One mapped surface, ready to be drawn. */
struct wl_draw_surf {
    float x, y, w, h;      /* framebuffer pixels, top-left origin */
    VkDescriptorSet tex;   /* sampled image, already in SHADER_READ_ONLY */
};

int wl_backend_init(const struct wl_backend_cfg *cfg);

/* Drain client requests without blocking (call once per compositor frame). */
void wl_backend_pump(void);

/* Block up to timeout_ms waiting for client requests (used when idle). */
void wl_backend_wait(int timeout_ms);

/* True when something needs a new frame: damage or pending frame callbacks. */
int wl_backend_needs_frame(void);

/* Take the accumulated damage as x0,y0,x1,y1 (framebuffer pixels). */
int wl_backend_take_damage(int32_t out[4]);

/* Send frame callbacks to every surface. */
void wl_backend_frame(uint32_t time_ms);

/* Record the host->shader barriers for surfaces uploaded since the last call. */
void wl_backend_prepare(VkCommandBuffer cmd);

/* Snapshot of the mapped surfaces in z-order (bottom first). */
int wl_backend_collect(struct wl_draw_surf *out, int max);

/* Forward a touch press/move (down=1) or release (down=0). */
void wl_backend_input(int down, float x, float y);

int wl_backend_client_count(void);

#endif
