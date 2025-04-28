# Wayland protocol paths
WAYLAND_PROTOCOLS_STABLE=/usr/share/wayland-protocols/stable
WLR_PROTOCOLS_DIR=wlr-protocols
WLR_LAYER_SHELL_XML=$(WLR_PROTOCOLS_DIR)/unstable/wlr-layer-shell-unstable-v1.xml

# Output files
XDG_CLIENT_HEADER=xdg-shell-client-protocol.h
XDG_PRIVATE_CODE=xdg-shell-protocol.c
WLR_CLIENT_HEADER=wlr-layer-shell-unstable-v1-client-protocol.h
WLR_PRIVATE_CODE=wlr-layer-shell-unstable-v1-protocol.c

# Compiler
CC=gcc
CFLAGS=-Wall -Wextra -O2
LDFLAGS=-lwayland-client

# Targets
all: hover_surface

hover_surface: hover_surface.c $(XDG_CLIENT_HEADER) $(XDG_PRIVATE_CODE) $(WLR_CLIENT_HEADER) $(WLR_PRIVATE_CODE)
	$(CC) $(CFLAGS) hover_surface.c $(XDG_PRIVATE_CODE) $(WLR_PRIVATE_CODE) -o hover_surface $(LDFLAGS)

# Generate protocol files
$(XDG_CLIENT_HEADER): 
	wayland-scanner client-header $(WAYLAND_PROTOCOLS_STABLE)/xdg-shell/xdg-shell.xml $(XDG_CLIENT_HEADER)

$(XDG_PRIVATE_CODE): 
	wayland-scanner private-code $(WAYLAND_PROTOCOLS_STABLE)/xdg-shell/xdg-shell.xml $(XDG_PRIVATE_CODE)

$(WLR_CLIENT_HEADER):
	wayland-scanner client-header $(WLR_LAYER_SHELL_XML) $(WLR_CLIENT_HEADER)

$(WLR_PRIVATE_CODE):
	wayland-scanner private-code $(WLR_LAYER_SHELL_XML) $(WLR_PRIVATE_CODE)

# Clean
clean:
	rm -f hover_surface *.h *.c

.PHONY: all clean

