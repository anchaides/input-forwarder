from pydbus import SessionBus
import os
import time
import mmap 
import socket
import uinput 
import json 
import tempfile 
import subprocess
import selectors, threading 

from .composer_backend import ComposerBackend
from pywayland.protocol.xdg_shell import XdgWmBase, XdgSurface, XdgToplevel
#from pywayland.protocol.wayland   import WlOutput

from pywayland.protocol.wayland   import (
    WlCompositor, 
    WlSurface, 
    WlSeat, 
    WlPointer, 
    WlRegistry, 
    WlShm,
    WlShmPool,
    WlOutput
)

from pywayland.client import Display 
import re

from pydbus import SessionBus 

WL_SEAT_CAPABILITY_POINTER = 1

class VirtualMouse:
    def __init__(self, width, height):
        self.device = uinput.Device([
            uinput.ABS_X + (0, width, 0, 0),   # min=0, max=screen_width
            uinput.ABS_Y + (0, height, 0, 0),   # min=0, max=screen_height
            uinput.BTN_LEFT,
            uinput.BTN_RIGHT,
        ])
        print("✅ Virtual Mouse Created")

    def move_absolute(self, x, y):
        self.device.emit(uinput.ABS_X, x, syn=False)
        self.device.emit(uinput.ABS_Y, y)
        print(f"🖱️ Moved to absolute: {x}, {y}")

    def click_left(self):
        self.device.emit_click(uinput.BTN_LEFT)

    def click_right(self):
        self.device.emit_click(uinput.BTN_RIGHT)

class WaylandComposerBackend(ComposerBackend):
    def __init__(self):
        super().__init__()
        self.hover_socket_path = "/tmp/if_socket"
        self.hover_daemon_path = "hover_surface"  # Path to your compiled daemon
        self.hover_sock = None
        self._composer = "WAYLAND"
        self.last_hover_data = {"hover": False, "y": 0}
        self.screen_width, self.screen_height = self._get_screen_dimensions() 
        self.vmouse = VirtualMouse(self.screen_width, self.screen_height)  
        self._ensure_hover_daemon_running()
        self._connect_hover_socket()

    def _get_screen_dimensions(self):
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        raw_out = subprocess.check_output(["kscreen-doctor", "--outputs"]).decode()
        out = ansi_escape.sub('', raw_out)

        screen_blocks = out.split("Output:")[1:]  # skip the first empty split
        total_width = 0
        height_set = set()

        mode_regex = re.compile(r"\d+:(\d+)x(\d+)@\d+\S+[*]")  # Matches refresh rate and finds '*' or '*!'
        geom_regex = re.compile(r"Geometry:\s+\d+,\d+\s+(\d+)x(\d+)")

        for block in screen_blocks:
            #print(f" Read block is \n {block}")
            block_lines = block.strip().splitlines()

            # Check if the mode is selected in this block
            mode_line = next((line for line in block_lines if "Modes:" in line), "")

            #for line in block_lines:
            #    print(line)
            #mode_regex.search(line)

            for token in mode_line.split():
                if "*" in token:
                    print(f"a token matched {token}")
                    mode_match = mode_regex.match(token)
                    if mode_match:
                        print(f"regex matched")
                        width  = int(mode_match.group(1))
                        height = int(mode_match.group(2))
                        total_width += width
                        height_set.add(height)


        if not total_width or len(height_set) != 1:
            raise RuntimeError("Unable to parse consistent screen resolution from kscreen-doctor")

        total_height = height_set.pop()
        return total_width, total_height
        raise RuntimeError("Could not determine screen resolution.")

    def _ensure_hover_daemon_running(self):
        if os.path.exists(self.hover_socket_path):
            print("✅ Hover daemon already running.")
            os.unlink(self.hover_socket_path)
            print("🧹 Stale socket deleted")
            #return

        print("🚀 Launching hover_surface daemon...")
        # Start the daemon
        self.hover_daemon_proc = subprocess.Popen(
            [self.hover_daemon_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Give it a moment to create the socket
        for _ in range(40):  # wait up to 2 seconds
            if os.path.exists(self.hover_socket_path):
                print("✅ Hover socket available.")
                return
            time.sleep(0.1)

        raise RuntimeError("Hover daemon did not start properly!")

    def _connect_hover_socket(self):
        retry = 0
        max_retries = 5
        wait_time = 0.5  # seconds

        self.hover_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.hover_sock.connect(self.hover_socket_path)
        self.hover_sock.setblocking(False)

    def get_pointer_position(self):
        try:
            data = self.hover_sock.recv(1024)
            if data:
                hover_data = json.loads(data.decode())
                self.last_hover_data.update(hover_data)
        except BlockingIOError:
            self.last_hover_data = {"hover": False, "y": 0}
            # No new data, reuse old
            pass

        if self.last_hover_data.get("hover"):
            return (self.screen_width, self.last_hover_data["y"],
                    self.screen_width, self.screen_height)
        else:
            return (0, 0, self.screen_width, self.screen_height)

    def shutdown(self):
        super().shutdown()
        print("🛑 Composer shutdown entered:")
        if self.hover_sock:
            self.hover_sock.close()
        # Optionally, kill the hover_surface daemon when exiting
        if hasattr(self, 'hover_daemon_proc'):
            print("🛑 Terminating hover daemon")
            self.hover_daemon_proc.kill() 
            self.hover_daemon_proc.wait()
            print("🛑 Hover daemon terminated.")

    def set_pointer_position(self, y_ratio: float):
        print(f"Attempting to set local position to {y_ratio}") 
        y_px = int(y_ratio * self.screen_height)
        x_px = self.screen_width - 1  # Rightmost edge, for example
        self.vmouse.move_absolute(x_px, y_px) 

