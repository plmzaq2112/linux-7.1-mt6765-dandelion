/* kms_prime_probe - does the display DRM device support PRIME import? */
#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>

#include <xf86drm.h>
#include <xf86drmMode.h>

int main(int argc, char **argv)
{
    const char *path = argc > 1 ? argv[1] : "/dev/dri/card1";
    int fd = open(path, O_RDWR);
    if (fd < 0) {
        printf("%s: open failed: %s\n", path, strerror(errno));
        return 1;
    }

    struct drm_mode_create_dumb cd = { .width = 64, .height = 64, .bpp = 32 };
    if (ioctl(fd, DRM_IOCTL_MODE_CREATE_DUMB, &cd)) {
        printf("CREATE_DUMB failed: %s\n", strerror(errno));
        return 1;
    }
    printf("dumb handle=%u pitch=%u size=%llu\n", cd.handle, cd.pitch,
           (unsigned long long)cd.size);

    int dmabuf_fd = -1;
    int r = drmPrimeHandleToFD(fd, cd.handle, DRM_CLOEXEC, &dmabuf_fd);
    printf("drmPrimeHandleToFD -> %d fd=%d errno=%s\n", r, dmabuf_fd,
           r ? strerror(errno) : "ok");
    if (r)
        return 1;

    uint32_t back = 0;
    errno = 0;
    r = drmPrimeFDToHandle(fd, dmabuf_fd, &back);
    printf("drmPrimeFDToHandle(self) -> %d handle=%u errno=%s\n", r, back,
           r ? strerror(errno) : "ok");

    uint32_t fb = 0;
    errno = 0;
    if (r == 0) {
        uint32_t handles[4] = { back, 0, 0, 0 };
        uint32_t pitches[4] = { cd.pitch, 0, 0, 0 };
        uint32_t offsets[4] = { 0, 0, 0, 0 };
        int r2 = drmModeAddFB2(fd, 64, 64, 0x34325258 /* XRGB8888 */, handles,
                               pitches, offsets, &fb, 0);
        printf("AddFB2(self dmabuf) -> %d fb=%u errno=%s\n", r2, fb,
               r2 ? strerror(errno) : "ok");
    }
    return 0;
}
