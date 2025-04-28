# threads.py

import time
import traceback
from evdev import ecodes
from .config import LINUX_TO_HID, MODIFIER_MASK


def keyboard_thread(dev, tfsm, ssh_stream, pressed_keys, printer, shutdown_event):
    modifiers = 0

    #while not shutdown_event.is_set(): 
    for event in dev.read_loop():
        if shutdown_event.is_set(): 
            break 
        if event.type != ecodes.EV_KEY:
            continue
        code = event.code
        value = event.value

        if code in MODIFIER_MASK:
            if value == 1:
                modifiers |= MODIFIER_MASK[code]
                if code == ecodes.KEY_RIGHTSHIFT:
                    tfsm.key1 = True
            elif value == 0:
                modifiers &= ~MODIFIER_MASK[code]
                if code == ecodes.KEY_RIGHTSHIFT:
                    tfsm.key1 = False
        elif code in LINUX_TO_HID:
            hid_code = LINUX_TO_HID[code]
            if value == 1:
                if code == ecodes.KEY_PAUSE:
                    tfsm.key2 = True
                else:
                    pressed_keys.add(hid_code)
            elif value == 0:
                if code == ecodes.KEY_PAUSE:
                    tfsm.key2 = False
                else:
                    pressed_keys.discard(hid_code)
       
        else:
            printer(f"Unknown key code: {code}")

        if modifiers == 0 and all ( key == 0 for key  in pressed_keys):
            tfsm.flagkbi = True 
        else:
            tfsm.flagkbi = False 

        report = bytearray(8)
        if tfsm.release:
            report[0] = 0
            for i in range(2, 8):
                report[i] = 0
            try:
                ssh_stream.stdin.write(report)
                ssh_stream.stdin.flush()
            except Exception as e:
                printer("Keyboard write failed (release):", e)
                raise RuntimeError("Keyboard write error")

        if tfsm.grabbed and ssh_stream.stdin:
            report[0] = modifiers
            for i, key in enumerate(sorted(pressed_keys)[:6]):
                report[2 + i] = key
            try:
                ssh_stream.stdin.write(report)
                ssh_stream.stdin.flush()
            except Exception as e:
                printer("Keyboard write failed (grabbed):", e)
                raise RuntimeError("Keyboard write error")

    print("Exiting Keyboard thread cleanly") 


def mouse_thread(dev, tfsm, composer, ssh_stream, shared_state, printer, shutdown_event):
    buttons = dx = dy = wheel = 0

    #while not shutdown_event.is_set(): 
    for event in dev.read_loop():
        if shutdown_event.is_set(): 
            break 
        if event.type == ecodes.EV_KEY:
            if event.code == ecodes.BTN_LEFT:
                buttons = buttons | 0x01 if event.value else buttons & ~0x01
            elif event.code == ecodes.BTN_RIGHT:
                buttons = buttons | 0x02 if event.value else buttons & ~0x02
            elif event.code == ecodes.BTN_MIDDLE:
                buttons = buttons | 0x04 if event.value else buttons & ~0x04

            if buttons == 0x00: 
                tfsm.flagmi = True 
            else:
                tfsm.flagmi = False 

            if tfsm.grabbed:
                report = bytearray([buttons, 0, 0, 0])
                ssh_stream.stdin.write(report)
                ssh_stream.stdin.flush()

        elif event.type == ecodes.EV_REL:
            if event.code == ecodes.REL_X:
                dx += event.value
            elif event.code == ecodes.REL_Y:
                dy += event.value
            elif event.code == ecodes.REL_WHEEL:
                wheel += event.value

            if composer.composer != "WAYLAND":
                tfsm.relx = (dx > 0 and not tfsm.grabbed) or (dx < 0 and tfsm.grabbed)
            elif tfsm.grabbed: 
                tfsm.relx = dx < 0
            #tfsm.fsm()
            #print(f"tfsm.relx is {tfsm.relx}") 

            if tfsm.grabbed:
                max_vx = int((shared_state['remote_screen_max_x'] * shared_state['scaling_factor']) / shared_state['screen_width'])
                max_vy = int(shared_state['remote_screen_max_y'] * shared_state['scaling_factor'] * 0.60)

                shared_state['max_virtual_y'] = max_vy
                shared_state['remote_virtual_x'] = max(0, min(shared_state['remote_virtual_x'] + dx, max_vx))
                shared_state['remote_virtual_y'] = max(0, min(shared_state['remote_virtual_y'] + dy, max_vy))
                shared_state['height_ratio'] = shared_state['remote_virtual_y'] / max_vy

                report = bytearray([buttons, dx & 0xFF, dy & 0xFF, wheel & 0xFF])
                try:
                    ssh_stream.stdin.write(report)
                    ssh_stream.stdin.flush()
                except Exception as e:
                    printer("Mouse write failed:", e)
                    raise RuntimeError("Mouse thread write error")

            dx = dy = wheel = 0
    print("Exiting Mouse thread cleanly") 


def mmabs_thread(tfsm, composer, ssh_stream, shared_state, printer, shutdown_event):
    try:
        while not shutdown_event.is_set():
            time.sleep(0.001)

            if tfsm.grabbed:
                if shared_state['remote_virtual_x'] > 0:
                    tfsm.edge = False
                else:
                    tfsm.edge = True

                #tfsm.fsm()

                if tfsm.flag_pos:
                    composer.set_pointer_position(shared_state['height_ratio'])
                    printer("Updated local position")
                    #tfsm.updt_pos = True
                    tfsm.flag_pos_ack = True 
            else:
                # if we are on Wayland update the events before quering pointer position 
                #if composer.composer == "WAYLAND":
                    #composer._run_event_loop_once() 

                x, y, sw, sh = composer.get_pointer_position()
                shared_state['screen_width'] = sw / 5120

                #printer(f"x position is {x} screen width is {sw}") 
                if x >= (sw - 1):
                    tfsm.edge = True
                    if composer.composer == "WAYLAND":
                        tfsm.relx = True 

                    print("We should transition here") 

                    scaled_y = int((y / sh) * shared_state['remote_screen_max_y'])

                    tfsm.fsm()

                    if tfsm.flag_pos:
                        print("FSM: flag_position = True") 
                        abs_report = bytearray([0x00, 0x00, 0x00, scaled_y & 0xFF, (scaled_y >> 8) & 0xFF])
                        shared_state['remote_virtual_y'] = int((y / sh) * shared_state['max_virtual_y'])
                        try:
                            ssh_stream.stdin.write(abs_report)
                            ssh_stream.stdin.flush()
                            printer("[Toggle] Sent absolute reset to remote: X=0 Y=", scaled_y)
                            tfsm.flag_pos_ack = True 
                        except Exception as e:
                            print("[Remote Abs Write Error]", e)
                else:
                    tfsm.edge = False
                    
                    if composer.composer == "WAYLAND":
                        tfsm.relx = False 

        print("Mouse absolute thread exited cleanly") 

    except Exception as e:
        printer("mouse absolute thread failed:", e)
        traceback.print_exc()

