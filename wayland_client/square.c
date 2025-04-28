/* File: hover_square.c */
#define _GNU_SOURCE

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <wayland-client.h>
#include "xdg-shell-client-protocol.h"

#define WIDTH 200
#define HEIGHT 200
#define STRIDE (WIDTH * 4)
#define SIZE (STRIDE * HEIGHT)

static struct wl_display *display = NULL;
static struct wl_registry *registry = NULL;
static struct wl_compositor *compositor = NULL;
static struct wl_shm *shm = NULL;
static struct wl_seat *seat = NULL;
static struct wl_pointer *pointer = NULL;
static struct xdg_wm_base *wm_base = NULL;

static struct wl_surface *surface = NULL;
static struct xdg_surface *xdg_surface = NULL;
static struct xdg_toplevel *xdg_toplevel = NULL;
static struct wl_buffer *buffer = NULL;
static void *shm_data = NULL;
static int color_state = 0; // 0 = red, 1 = blue

static void draw_color(int r, int g, int b) {
    uint32_t pixel = (255 << 24) | (b << 16) | (g << 8) | r;
    uint32_t *pixels = shm_data;
    for (int i = 0; i < WIDTH * HEIGHT; ++i) {
        pixels[i] = pixel;
    }
}

static void create_shm_buffer() {
    int fd = memfd_create("hover-square", MFD_CLOEXEC);
    ftruncate(fd, SIZE);
    shm_data = mmap(NULL, SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    struct wl_shm_pool *pool = wl_shm_create_pool(shm, fd, SIZE);
    buffer = wl_shm_pool_create_buffer(pool, 0, WIDTH, HEIGHT, STRIDE, WL_SHM_FORMAT_ARGB8888);
    wl_shm_pool_destroy(pool);
    close(fd);
}

static void pointer_enter(void *data, struct wl_pointer *pointer, uint32_t serial,
                          struct wl_surface *surface, wl_fixed_t sx, wl_fixed_t sy) {
    if (color_state != 1) {
        draw_color(0, 0, 255); // Blue
        wl_surface_attach(surface, buffer, 0, 0);
        wl_surface_commit(surface);
        color_state = 1;
    }
}

static void pointer_motion(void *data, struct wl_pointer *pointer,
                           uint32_t time, wl_fixed_t sx, wl_fixed_t sy)
{
    // You can print the coordinates if you want
    printf("Pointer moved to: %f, %f\n", wl_fixed_to_double(sx), wl_fixed_to_double(sy));
}

static void pointer_leave(void *data, struct wl_pointer *pointer, uint32_t serial,
                          struct wl_surface *surface) {
    if (color_state != 0) {
        draw_color(255, 0, 0); // Red
        wl_surface_attach(surface, buffer, 0, 0);
        wl_surface_commit(surface);
        color_state = 0;
    }
}

static void pointer_btn(void *data, struct wl_pointer *, uint32_t arg1,  uint32_t arg2,  uint32_t arg3,  uint32_t arg4)
{
    printf("Click\n");
}

static void pointer_frame(void *data, struct wl_pointer *pointer)
{
    // Do nothing for now
}

static const struct wl_pointer_listener pointer_listener = {
    .enter = pointer_enter,
    .leave = pointer_leave,
    .motion = pointer_motion,
    .button = pointer_btn,
    .axis = NULL,
    .frame = pointer_frame,
    .axis_source = NULL,
    .axis_stop = NULL,
    .axis_discrete = NULL
};

static void seat_capabilities(void *data, struct wl_seat *seat, uint32_t caps) {
    if ((caps & WL_SEAT_CAPABILITY_POINTER) && !pointer) {
        pointer = wl_seat_get_pointer(seat);
        wl_pointer_add_listener(pointer, &pointer_listener, NULL);
    } else if (!(caps & WL_SEAT_CAPABILITY_POINTER) && pointer) {
        wl_pointer_destroy(pointer);
        pointer = NULL;
    }
}

static void seat_name(void *data, struct wl_seat *seat, const char *name)
{
    // Just ignore or print if you want
    printf("[seat_name] seat name is %s\n", name);
}

static const struct wl_seat_listener seat_listener = {
    .capabilities = seat_capabilities,
    .name = seat_name
};

static void xdg_surface_configure(void *data, struct xdg_surface *xdg_surface, uint32_t serial) {
    xdg_surface_ack_configure(xdg_surface, serial);

    create_shm_buffer();
    draw_color(255, 0, 0); // Red initially
    wl_surface_attach(surface, buffer, 0, 0);
    wl_surface_commit(surface);
}

static const struct xdg_surface_listener xdg_surface_listener = {
    .configure = xdg_surface_configure
};

static void xdg_wm_base_ping(void *data, struct xdg_wm_base *xdg_wm_base, uint32_t serial) {
    xdg_wm_base_pong(xdg_wm_base, serial);
}

static const struct xdg_wm_base_listener wm_base_listener = {
    .ping = xdg_wm_base_ping
};

static void registry_global(void *data, struct wl_registry *registry, uint32_t name,
                             const char *interface, uint32_t version) {
    if (strcmp(interface, wl_compositor_interface.name) == 0) {
        compositor = wl_registry_bind(registry, name, &wl_compositor_interface, 4);
    } else if (strcmp(interface, wl_shm_interface.name) == 0) {
        shm = wl_registry_bind(registry, name, &wl_shm_interface, 1);
    } else if (strcmp(interface, wl_seat_interface.name) == 0) {
        seat = wl_registry_bind(registry, name, &wl_seat_interface, 5);
        wl_seat_add_listener(seat, &seat_listener, NULL);
    } else if (strcmp(interface, xdg_wm_base_interface.name) == 0) {
        wm_base = wl_registry_bind(registry, name, &xdg_wm_base_interface, 1);
        xdg_wm_base_add_listener(wm_base, &wm_base_listener, NULL);
    }
}

static void registry_global_remove(void *data, struct wl_registry *registry, uint32_t name) {}

static const struct wl_registry_listener registry_listener = {
    .global = registry_global,
    .global_remove = registry_global_remove
};

int main() {
    display = wl_display_connect(NULL);
    if (!display) {
        fprintf(stderr, "Failed to connect to Wayland display.\n");
        return -1;
    }

    registry = wl_display_get_registry(display);
    wl_registry_add_listener(registry, &registry_listener, NULL);
    wl_display_roundtrip(display);

    surface = wl_compositor_create_surface(compositor);
    xdg_surface = xdg_wm_base_get_xdg_surface(wm_base, surface);
    xdg_surface_add_listener(xdg_surface, &xdg_surface_listener, NULL);

    xdg_toplevel = xdg_surface_get_toplevel(xdg_surface);
    xdg_toplevel_set_title(xdg_toplevel, "Hover Square");
    wl_surface_commit(surface);

    while (wl_display_dispatch(display) != -1) {}

    return 0;
}

