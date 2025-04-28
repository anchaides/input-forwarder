/* File: hover_layer.c */
#define _GNU_SOURCE

#include <stdio.h>
#include <stdbool.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <signal.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <wayland-client.h>
#include "xdg-shell-client-protocol.h"
#include "wlr-layer-shell-unstable-v1-client-protocol.h"  // NEW include

#define WIDTH 100
#define HEIGHT 1   // will stretch full height by protocol
#define STRIDE (WIDTH * 4)
#define SIZE (STRIDE * HEIGHT)
#define SOCKET_PATH "/tmp/if_socket" 

static int sock_fd = -1;
static int client_fd = -1; 
static volatile bool running = true; 

static struct wl_display *display = NULL;
static struct wl_registry *registry = NULL;
static struct wl_compositor *compositor = NULL;
static struct wl_shm *shm = NULL;
static struct wl_seat *seat = NULL;
static struct wl_pointer *pointer = NULL;
static struct zwlr_layer_shell_v1 *layer_shell = NULL;  // NEW
static struct zwlr_layer_surface_v1 *layer_surface = NULL;  // NEW
static int output_scale = 1; // Default to 1 if compositor doesn't tell us


static struct wl_surface *surface = NULL;
static struct wl_buffer *buffer = NULL;
static void *shm_data = NULL;
static struct wl_output *rightmost_output = NULL;

static int rightmost_output_x = -9999;

static void handle_sigint(int sig) {
    (void)sig; 
    printf("Goodbye!\n"); 
    running = false; 
}

static void cleanup() {
    if (client_fd != -1) close(client_fd);
    if (sock_fd != -1) {
        close(sock_fd);
        unlink(SOCKET_PATH);
    }
    if (display) wl_display_disconnect(display);
}

static void output_geometry(void *data, struct wl_output *wl_output,
                             int32_t x, int32_t y,
                             int32_t physical_width, int32_t physical_height,
                             int32_t subpixel,
                             const char *make, const char *model,
                             int32_t transform) {
    printf("[output_geometry] output=%p x=%d y=%d make=%s model=%s\n",
        wl_output, x, y, make, model);

    if (x > rightmost_output_x) {
        printf("[output_geometry] model=%s\n is the rightmost so far!\n", model);
        rightmost_output = wl_output;
        rightmost_output_x = x;
    } 
}

static void output_mode(void *data, struct wl_output *wl_output,
                        uint32_t flags, int32_t width, int32_t height,
                        int32_t refresh) {
    // ignore for now
}

static void output_done(void *data, struct wl_output *wl_output) {
    // ignore for now
}

static void output_scale_listener(void *data, struct wl_output *wl_output, int32_t factor) {
    printf("[output_scale] %d\n", factor);
    output_scale = factor;
}

static const struct wl_output_listener output_listener = {
    .geometry = output_geometry,
    .mode = output_mode,
    .done = output_done,
    .scale = output_scale_listener,
};

static void draw_color(int r, int g, int b) {
    uint32_t pixel = (255 << 24) | (b << 16) | (g << 8) | r;
    uint32_t *pixels = shm_data;
    for (int i = 0; i < WIDTH * HEIGHT; ++i) {
        pixels[i] = pixel;
    }
}

static void create_shm_buffer(uint32_t width, uint32_t height) {
    //int stride = ((width * 4) + 63) & ~63;  // align stride to 64 bytes
    int stride = width * 4;  // align stride to 64 bytes
    int size = stride * height;

    int fd = memfd_create("hover-layer", MFD_CLOEXEC);
    ftruncate(fd, size);
    shm_data = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    struct wl_shm_pool *pool = wl_shm_create_pool(shm, fd, size);
    buffer = wl_shm_pool_create_buffer(pool, 0, width, height, stride, WL_SHM_FORMAT_ARGB8888);
    wl_shm_pool_destroy(pool);
    close(fd);
}
int setup_socket() {
    struct sockaddr_un addr;
    sock_fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (sock_fd < 0) {
        perror("socket");
        return -1;
    }

    unlink(SOCKET_PATH);  // Remove old socket
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, SOCKET_PATH, sizeof(addr.sun_path) - 1);

    if (bind(sock_fd, (struct sockaddr*)&addr, sizeof(addr)) == -1) {
        perror("bind");
        return -1;
    }

    if (listen(sock_fd, 1) == -1) {
        perror("listen");
        return -1;
    }

    printf("Socket server started at %s\n", SOCKET_PATH);
    return 0;
}

static void send_hover_event(bool hover, int32_t y) {
    if (client_fd == -1) return;

    char buffer[128];
    if (hover) {
        snprintf(buffer, sizeof(buffer), "{\"hover\": true, \"y\": %d}", y);
    } else {
        snprintf(buffer, sizeof(buffer), "{\"hover\": false}");
    }

    write(client_fd, buffer, strlen(buffer));
} 

static void pointer_enter(void *data, struct wl_pointer *pointer, uint32_t serial,
                          struct wl_surface *entered_surface, wl_fixed_t sx, wl_fixed_t sy) {
    if (entered_surface == surface) {
        double y = wl_fixed_to_double(sy);
        //1printf("Pointer entered at Y = %f\n", y);
        send_hover_event(true, y); 
    }
}

static void pointer_motion(void *data, struct wl_pointer *pointer,
                           uint32_t time, wl_fixed_t sx, wl_fixed_t sy) {
    // Optionally handle motion
}

static void pointer_leave(void *data, struct wl_pointer *pointer, uint32_t serial,
                          struct wl_surface *left_surface) {
    // Optionally handle leave
}

static void pointer_btn(void *data, struct wl_pointer *pointer, uint32_t serial,
                        uint32_t time, uint32_t button, uint32_t state) {
    printf("Click\n");
}

static void pointer_frame(void *data, struct wl_pointer *pointer) {}

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

static void seat_name(void *data, struct wl_seat *seat, const char *name) {
    printf("[seat_name] %s\n", name);
}

static const struct wl_seat_listener seat_listener = {
    .capabilities = seat_capabilities,
    .name = seat_name
};

static void layer_surface_configure(void *data, struct zwlr_layer_surface_v1 *layer_surface,
uint32_t serial, uint32_t width, uint32_t height) {
    zwlr_layer_surface_v1_ack_configure(layer_surface, serial);

    printf("Layer surface configured: width=%u height=%u\n", width, height);

    int scale = output_scale; 
    int buffer_width = width * scale; 
    int buffer_height = height * scale; 
    //int buffer_height = height; 

    // When compositor tells us dimensions
    create_shm_buffer(buffer_width, buffer_height);
    draw_color(255, 0, 0); // Red
    wl_surface_set_buffer_scale(surface, output_scale); 
    wl_surface_attach(surface, buffer, 0, 0);
    wl_surface_damage_buffer(surface, 0, 0, buffer_width, buffer_height);
    wl_surface_commit(surface);
}

static void layer_surface_closed(void *data, struct zwlr_layer_surface_v1 *surface) {
    printf("Layer surface closed.\n");
    exit(0);
}

static const struct zwlr_layer_surface_v1_listener layer_surface_listener = {
    .configure = layer_surface_configure,
    .closed = layer_surface_closed
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
    } else if (strcmp(interface, zwlr_layer_shell_v1_interface.name) == 0) {
        layer_shell = wl_registry_bind(registry, name, &zwlr_layer_shell_v1_interface, version);
    } else if (strcmp(interface, wl_output_interface.name) == 0) {
        struct wl_output *output = wl_registry_bind(registry, name, &wl_output_interface, 2);
        // Here we would normally inspect output properties (make, model, position)
        // For now just store first one
        //rightmost_output = output;
        wl_output_add_listener(output, &output_listener, NULL);
    }
}

static void registry_global_remove(void *data, struct wl_registry *registry, uint32_t name) {}

static const struct wl_registry_listener registry_listener = {
    .global = registry_global,
    .global_remove = registry_global_remove
};

int main() {
    
    signal(SIGINT, handle_sigint);
    signal(SIGTERM, handle_sigint);

    if (setup_socket() != 0) {
        return EXIT_FAILURE;
    } 

    display = wl_display_connect(NULL);
    if (!display) {
        fprintf(stderr, "Failed to connect to Wayland display.\n");
        return -1;
    }

    registry = wl_display_get_registry(display);
    wl_registry_add_listener(registry, &registry_listener, NULL);
    wl_display_roundtrip(display);
    wl_display_roundtrip(display);

    if (!rightmost_output) {
        fprintf(stderr, "No output available!\n"); 
    }
    surface = wl_compositor_create_surface(compositor);
    wl_surface_set_buffer_scale(surface, output_scale); 

    layer_surface = zwlr_layer_shell_v1_get_layer_surface(
        layer_shell, surface, rightmost_output, ZWLR_LAYER_SHELL_V1_LAYER_OVERLAY, "hover_layer"
    );
    printf("[output_geometry] output=%p\n",rightmost_output); 
    zwlr_layer_surface_v1_add_listener(layer_surface, &layer_surface_listener, NULL);

    zwlr_layer_surface_v1_set_anchor(layer_surface,
        ZWLR_LAYER_SURFACE_V1_ANCHOR_TOP |
        ZWLR_LAYER_SURFACE_V1_ANCHOR_BOTTOM |
        ZWLR_LAYER_SURFACE_V1_ANCHOR_RIGHT);

    zwlr_layer_surface_v1_set_size(layer_surface, 10, 1440);  // 100px width, full height
    zwlr_layer_surface_v1_set_keyboard_interactivity(layer_surface, 0);

    wl_surface_commit(surface);

    printf("Wayland hover daemon ready!\nWaiting for a client to connect...\n");

    client_fd = accept(sock_fd, NULL, NULL);
    if (client_fd < 0) {
        perror("accept");
        cleanup();
        return EXIT_FAILURE;
    }
    printf("Client connected.\n");

    while (running && wl_display_dispatch(display) != -1) {
        // Event loop
    }

    cleanup();
    return EXIT_SUCCESS;
}

