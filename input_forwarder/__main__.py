# __main__.py

import os
import sys
import threading
import subprocess
from evdev import InputDevice, list_devices, ecodes

from .config import (
    IDENTITY_FILE, PI_HOST_KB, REMOTE_COMMAND_KB,
    PI_HOST_M, REMOTE_COMMAND_M, PI_HOST_M1, REMOTE_COMMAND_M1,
    REMOTE_SCREEN_MAX_X, REMOTE_SCREEN_MAX_Y, SCALING_FACTOR
)
from .fsm import TFSM
from .io_backend_x11 import X11ComposerBackend
from .threads import keyboard_thread, mouse_thread, mmabs_thread

print_lock = threading.Lock()

def safe_print(*args, **kwargs):
    with print_lock:
        print(*args, **kwargs)

def is_keyboard(dev):
    try:
        #print(f"Device name is {dev.name.strip()}")
        if os.getenv("KEYBOARD") != dev.name.strip(): 
            return False 

        capabilities = dev.capabilities() 
        #print(f"Name matches") 
        keys         = capabilities.get(ecodes.EV_KEY, []) 
        #print(capabilities) 
        #print(f"Name matches") 
        #print(keys) 
        return ecodes.KEY_A in keys and ecodes.KEY_Z in keys 
    except:
        return False

def is_mouse(dev):
    try:
        #print(f"Device name is {dev.name.strip()}")
        if os.getenv("MOUSE") != dev.name.strip(): 
            return False 
        capabilities = dev.capabilities() 
        rel = capabilities.get(ecodes.EV_REL, [])
        btns = capabilities.get(ecodes.EV_KEY, []) 
        #print(rel,btns) 
        #print(f"Name matches") 
        return ecodes.REL_X in rel and ecodes.BTN_LEFT in btns
        
    except:
        return False

def main():
    devices = [InputDevice(path) for path in list_devices()]
    keyboard = next((d for d in devices if is_keyboard(d)), None)
    mouse = next((d for d in devices if is_mouse(d)), None)

    if not keyboard or not mouse:
        print("Keyboard or mouse not found. Check environment variables.")
        sys.exit(1)

    safe_print(f"Keyboard: {keyboard.name} at {keyboard.path}")
    safe_print(f"Mouse: {mouse.name} at {mouse.path}")

    # Start SSH sessions
    sshkb = subprocess.Popen(["ssh", "-i", IDENTITY_FILE, PI_HOST_KB, REMOTE_COMMAND_KB], stdin=subprocess.PIPE)
    sshm  = subprocess.Popen(["ssh", "-i", IDENTITY_FILE, PI_HOST_M,  REMOTE_COMMAND_M],  stdin=subprocess.PIPE)
    sshm1 = subprocess.Popen(["ssh", "-i", IDENTITY_FILE, PI_HOST_M1, REMOTE_COMMAND_M1], stdin=subprocess.PIPE)

    # Input state and shared memory
    shared_state = {
        "remote_virtual_x": 0,
        "remote_virtual_y": 0,
        "screen_width": 1.0,
        "height_ratio": 0,
        "max_virtual_y": 0,
        "remote_screen_max_x": REMOTE_SCREEN_MAX_X,
        "remote_screen_max_y": REMOTE_SCREEN_MAX_Y,
        "scaling_factor": SCALING_FACTOR,
    }

    # Compose backend and FSM
    composer = X11ComposerBackend()
    pressed_keys = set()

    tfsm = TFSM(
        grab_devices=lambda: (keyboard.grab(), mouse.grab()),
        ungrab_devices=lambda: (keyboard.ungrab(), mouse.ungrab()),
        printer=safe_print
    )

    threads = [
        threading.Thread(target=keyboard_thread, daemon=True, args=(keyboard, tfsm, sshkb, pressed_keys, safe_print)),
        threading.Thread(target=mouse_thread,    daemon=True, args=(mouse, tfsm, sshm,  shared_state, safe_print)),
        threading.Thread(target=mmabs_thread,    daemon=True, args=(tfsm, composer, sshm1, shared_state, safe_print))
    ]

    for t in threads:
        t.start()

    try:
        while True:
            for i, t in enumerate(threads):
                if not t.is_alive():
                    raise RuntimeError(f"[FATAL] Thread {i} has died.")
            threading.Event().wait(1)

    except KeyboardInterrupt:
        for ssh in (sshkb, sshm, sshm1):
            if ssh: ssh.terminate()
        sys.exit(0)

    except BaseException as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

