/* Print Vulkan physical device info: name, API version, extensions, limits. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <vulkan/vulkan.h>

static void die(const char *what, VkResult r)
{
    if (r == VK_SUCCESS)
        return;
    fprintf(stderr, "%s failed: %d\n", what, r);
    exit(1);
}

int main(void)
{
    VkApplicationInfo app = {
        .sType = VK_STRUCTURE_TYPE_APPLICATION_INFO,
        .pApplicationName = "vk_info",
        .apiVersion = VK_API_VERSION_1_0,
    };
    VkInstanceCreateInfo ici = {
        .sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO,
        .pApplicationInfo = &app,
    };
    VkInstance inst;
    die("vkCreateInstance", vkCreateInstance(&ici, NULL, &inst));

    uint32_t n = 0;
    die("vkEnumeratePhysicalDevices", vkEnumeratePhysicalDevices(inst, &n, NULL));
    VkPhysicalDevice *pds = calloc(n, sizeof(*pds));
    vkEnumeratePhysicalDevices(inst, &n, pds);

    for (uint32_t i = 0; i < n; i++) {
        VkPhysicalDeviceProperties p;
        vkGetPhysicalDeviceProperties(pds[i], &p);
        printf("device[%u]: %s type=%d api=%u.%u.%u driver=%u\n", i, p.deviceName,
               p.deviceType, VK_VERSION_MAJOR(p.apiVersion),
               VK_VERSION_MINOR(p.apiVersion), VK_VERSION_PATCH(p.apiVersion),
               p.driverVersion);
        printf("  maxImage2D=%ux%u maxFb=%ux%u maxMemAlloc=%u MB\n",
               p.limits.maxImageDimension2D, p.limits.maxImageDimension2D,
               p.limits.maxFramebufferWidth, p.limits.maxFramebufferHeight,
               (unsigned)(p.limits.maxMemoryAllocationCount / 1024));

        uint32_t en = 0;
        vkEnumerateDeviceExtensionProperties(pds[i], NULL, &en, NULL);
        VkExtensionProperties *ex = calloc(en, sizeof(*ex));
        vkEnumerateDeviceExtensionProperties(pds[i], NULL, &en, ex);
        const char *want[] = {
            "VK_KHR_external_memory", "VK_KHR_external_memory_fd",
            "VK_EXT_external_memory_dma_buf", "VK_EXT_image_drm_format_modifier",
            "VK_KHR_image_format_list", "VK_KHR_maintenance1",
            "VK_KHR_display", "VK_KHR_wayland_surface", "VK_KHR_xcb_surface",
            "VK_KHR_swapchain", "VK_KHR_sampler_ycbcr_conversion",
            "VK_EXT_queue_family_foreign", "VK_KHR_dedicated_allocation",
            "VK_KHR_get_memory_requirements2", "VK_KHR_bind_memory2",
            "VK_KHR_copy_commands2", "VK_KHR_synchronization2",
            "VK_KHR_dynamic_rendering", "VK_EXT_descriptor_indexing",
        };
        printf("  extensions (%u):\n", en);
        for (uint32_t k = 0; k < sizeof(want) / sizeof(want[0]); k++) {
            int found = 0;
            for (uint32_t j = 0; j < en; j++)
                if (!strcmp(ex[j].extensionName, want[k]))
                    found = 1;
            printf("    %-40s %s\n", want[k], found ? "yes" : "no");
        }
        printf("  all:\n");
        for (uint32_t j = 0; j < en; j++)
            printf("    %s (rev %u)\n", ex[j].extensionName, ex[j].specVersion);
        free(ex);
    }
    return 0;
}
