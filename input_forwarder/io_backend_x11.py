# io_backend_x11.py

from Xlib import display
from .composer_backend import ComposerBackend

class X11ComposerBackend(ComposerBackend):
    def __init__(self):
        self.disp = display.Display()
        self.screen = self.disp.screen()
        self.root = self.screen.root
        self.composer = "X11"

    def get_pointer_position(self):
        pointer = self.root.query_pointer()
        return (
            pointer.root_x,
            pointer.root_y,
            self.screen.width_in_pixels,
            self.screen.height_in_pixels,
        )

    def set_pointer_position(self, y_ratio: float):
        y_px = int(y_ratio * self.screen.height_in_pixels)
        self.root.warp_pointer(self.screen.width_in_pixels, y_px)
        self.disp.sync()

