#include <errno.h>
#include <fcntl.h>
#include <linux/uinput.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>

static void emit(int fd, unsigned type, unsigned code, int value)
{
    struct input_event ev = { 0 };

    ev.type = type;
    ev.code = code;
    ev.value = value;
    if (write(fd, &ev, sizeof(ev)) < 0)
        perror("write");
}

static void key(int fd, unsigned code)
{
    emit(fd, EV_KEY, code, 1);
    emit(fd, EV_SYN, SYN_REPORT, 0);
    usleep(50000);
    emit(fd, EV_KEY, code, 0);
    emit(fd, EV_SYN, SYN_REPORT, 0);
    usleep(50000);
}

int main(int argc, char **argv)
{
    int delay_ms = argc > 1 ? atoi(argv[1]) : 3000;
    int fd = open("/dev/uinput", O_WRONLY | O_NONBLOCK);
    struct uinput_setup us = { 0 };
    int i;

    if (fd < 0) {
        perror("open /dev/uinput");
        return 1;
    }

    ioctl(fd, UI_SET_EVBIT, EV_KEY);
    for (i = 1; i < 128; i++)
        ioctl(fd, UI_SET_KEYBIT, i);

    snprintf(us.name, UINPUT_MAX_NAME_SIZE, "vk-wl-test-kbd");
    us.id.bustype = BUS_USB;
    us.id.vendor = 0x1234;
    us.id.product = 0x5678;
    ioctl(fd, UI_DEV_SETUP, &us);
    ioctl(fd, UI_DEV_CREATE);

    /* Give the compositor time to open the new event node. */
    usleep(500000);
    printf("uinput: ready\n");
    fflush(stdout);

    usleep((useconds_t)delay_ms * 1000);
    printf("uinput: injecting keys\n");
    fflush(stdout);
    key(fd, KEY_A);
    key(fd, KEY_B);
    key(fd, KEY_C);
    key(fd, KEY_ENTER);
    usleep(500000);

    ioctl(fd, UI_DEV_DESTROY);
    close(fd);
    printf("uinput: done\n");
    return 0;
}
