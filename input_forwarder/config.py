# config.py

from evdev import ecodes
import os

IDENTITY_FILE = os.path.expanduser("~/.ssh/id_rsa")

PI_HOST_KB = "hidk@pi-hid"
REMOTE_COMMAND_KB = "cat > /dev/hidg0"
PI_HOST_M = "hidm@pi-hid"
REMOTE_COMMAND_M = "cat > /dev/hidg1"
PI_HOST_M1 = "hidm1@pi-hid"
REMOTE_COMMAND_M1 = "cat > /dev/hidg2"

REMOTE_SCREEN_MAX_X = 32767
REMOTE_SCREEN_MAX_Y = 32767
SCALING_FACTOR = 0.062

LINUX_TO_HID = {
    ecodes.KEY_A: 0x04, ecodes.KEY_B: 0x05, ecodes.KEY_C: 0x06, ecodes.KEY_D: 0x07,
    ecodes.KEY_E: 0x08, ecodes.KEY_F: 0x09, ecodes.KEY_G: 0x0A, ecodes.KEY_H: 0x0B,
    ecodes.KEY_I: 0x0C, ecodes.KEY_J: 0x0D, ecodes.KEY_K: 0x0E, ecodes.KEY_L: 0x0F,
    ecodes.KEY_M: 0x10, ecodes.KEY_N: 0x11, ecodes.KEY_O: 0x12, ecodes.KEY_P: 0x13,
    ecodes.KEY_Q: 0x14, ecodes.KEY_R: 0x15, ecodes.KEY_S: 0x16, ecodes.KEY_T: 0x17,
    ecodes.KEY_U: 0x18, ecodes.KEY_V: 0x19, ecodes.KEY_W: 0x1A, ecodes.KEY_X: 0x1B,
    ecodes.KEY_Y: 0x1C, ecodes.KEY_Z: 0x1D, ecodes.KEY_1: 0x1E, ecodes.KEY_2: 0x1F,
    ecodes.KEY_3: 0x20, ecodes.KEY_4: 0x21, ecodes.KEY_5: 0x22, ecodes.KEY_6: 0x23,
    ecodes.KEY_7: 0x24, ecodes.KEY_8: 0x25, ecodes.KEY_9: 0x26, ecodes.KEY_0: 0x27,
    ecodes.KEY_ENTER: 0x28, ecodes.KEY_ESC: 0x29, ecodes.KEY_BACKSPACE: 0x2A,
    ecodes.KEY_TAB: 0x2B, ecodes.KEY_SPACE: 0x2C, ecodes.KEY_MINUS: 0x2D,
    ecodes.KEY_EQUAL: 0x2E, ecodes.KEY_LEFTBRACE: 0x2F, ecodes.KEY_RIGHTBRACE: 0x30,
    ecodes.KEY_BACKSLASH: 0x31, ecodes.KEY_SEMICOLON: 0x33, ecodes.KEY_APOSTROPHE: 0x34,
    ecodes.KEY_GRAVE: 0x35, ecodes.KEY_COMMA: 0x36, ecodes.KEY_DOT: 0x37,
    ecodes.KEY_SLASH: 0x38, ecodes.KEY_CAPSLOCK: 0x39, ecodes.KEY_F1: 0x3A,
    ecodes.KEY_F2: 0x3B, ecodes.KEY_F3: 0x3C, ecodes.KEY_F4: 0x3D, ecodes.KEY_F5: 0x3E,
    ecodes.KEY_F6: 0x3F, ecodes.KEY_F7: 0x40, ecodes.KEY_F8: 0x41, ecodes.KEY_F9: 0x42,
    ecodes.KEY_F10: 0x43, ecodes.KEY_F11: 0x44, ecodes.KEY_F12: 0x45,
    ecodes.KEY_PAUSE: 0x48,
    ecodes.KEY_LEFTCTRL: 0xE0, ecodes.KEY_LEFTSHIFT:  0xE1, ecodes.KEY_LEFTALT:    0xE2,
    ecodes.KEY_LEFTMETA: 0xE3, ecodes.KEY_RIGHTCTRL:  0xE4, ecodes.KEY_RIGHTSHIFT: 0xE5,
    ecodes.KEY_RIGHTALT: 0xE6, ecodes.KEY_RIGHTMETA:  0xE7, ecodes.KEY_COMPOSE:    0x65,
    ecodes.KEY_SYSRQ:    0x46, ecodes.KEY_SCROLLLOCK: 0x47, ecodes.KEY_DELETE:     0x4C,
    ecodes.KEY_END:      0x4D, ecodes.KEY_INSERT:     0x49, ecodes.KEY_HOME:       0x4A,
    ecodes.KEY_PAGEUP:   0x4B, ecodes.KEY_PAGEDOWN:   0x4E, ecodes.KEY_LEFT:       0x50,
    ecodes.KEY_DOWN:     0x51, ecodes.KEY_UP:         0x52, ecodes.KEY_RIGHT:      0x4F,
    ecodes.KEY_NUMLOCK:  0x53, ecodes.KEY_KPSLASH:    0x54, ecodes.KEY_KPASTERISK: 0x55,
    ecodes.KEY_KPMINUS:  0x56, ecodes.KEY_KPPLUS:     0x57, ecodes.KEY_KPENTER:    0x58,
    ecodes.KEY_KP1:      0x59, ecodes.KEY_KP2:        0x5A, ecodes.KEY_KP3:        0x5B,
    ecodes.KEY_KP4:      0x5C, ecodes.KEY_KP5:        0x5D, ecodes.KEY_KP6:        0x5E,
    ecodes.KEY_KP7:      0x5F, ecodes.KEY_KP8:        0x60, ecodes.KEY_KP9:        0x61,
    ecodes.KEY_KP0:      0x62, ecodes.KEY_KPDOT:      0x63,
}

MODIFIER_MASK = {
    ecodes.KEY_LEFTCTRL: 0x01, ecodes.KEY_LEFTSHIFT: 0x02, ecodes.KEY_LEFTALT: 0x04,
    ecodes.KEY_LEFTMETA: 0x08, ecodes.KEY_RIGHTCTRL: 0x10, ecodes.KEY_RIGHTSHIFT: 0x20,
    ecodes.KEY_RIGHTALT: 0x40, ecodes.KEY_RIGHTMETA: 0x80,
}

