# fsm.py

from enum import Enum
import threading

class TFSM_STATE(Enum):
    IDLE    = 0
    TOGGLE  = 1
    TOGGLEK = 2
    PEN     = 3
    PEN2    = 4
    PEN3    = 5

class TFSM:
    def __init__(self, grab_devices, ungrab_devices, printer=print):
        self._state = TFSM_STATE.IDLE
        self._key1 = False
        self._key2 = False
        self._edge = False
        self._relx = False
        self._release = False
        self._grabbed = False
        self._flag_pos = False
        self._updt_pos = False
        self._lock = threading.Lock()

        self._grab_devices = grab_devices
        self._ungrab_devices = ungrab_devices
        self._print = printer

    @property
    def updt_pos(self):
        if self._updt_pos:
            self._updt_pos = False
            return True
        return False

    @updt_pos.setter
    def updt_pos(self, value):
        self._updt_pos = value

    @property
    def flag_pos(self):
        if self._flag_pos:
            self._flag_pos = False
            return True
        return False

    @flag_pos.setter
    def flag_pos(self, value):
        self._flag_pos = value

    @property
    def relx(self):
        return self._relx

    @relx.setter
    def relx(self, value):
        self._relx = value
        self.fsm()

    @property
    def edge(self):
        return self._edge

    @edge.setter
    def edge(self, value):
        self._edge = value
        self.fsm()

    @property
    def release(self):
        if self._release:
            self._release = False
            return True
        return False

    @release.setter
    def release(self, value):
        self._release = value

    @property
    def grabbed(self):
        return self._grabbed

    @grabbed.setter
    def grabbed(self, value):
        self._grabbed = value

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._state = value

    @property
    def key1(self):
        return self._key1

    @key1.setter
    def key1(self, value):
        self._key1 = value
        self.fsm()

    @property
    def key2(self):
        return self._key2

    @key2.setter
    def key2(self, value):
        self._key2 = value
        self.fsm()

    def fsm(self):
        with self._lock:
            if self.state == TFSM_STATE.IDLE:
                if self.key1 and self.key2:
                    self._print("Keyboard Toggle")
                    self.state = TFSM_STATE.TOGGLEK
                elif self.edge and self.relx:
                    self._print("Edge of screen toggle")
                    self.state = TFSM_STATE.TOGGLE

            elif self.state == TFSM_STATE.TOGGLE:
                if self.grabbed:
                    self._print("Un-grabbing devices: EDGE")
                    self.release = True
                    self.flag_pos = True
                    self.state = TFSM_STATE.PEN2
                else:
                    self._print("Grabbing devices: EDGE")
                    self._grab_devices()
                    self.grabbed = True
                    self.flag_pos = True
                    self.state = TFSM_STATE.PEN

            elif self.state == TFSM_STATE.TOGGLEK:
                if not (self.key1 or self.key2):
                    self._print("KEYBOARD TOGGLE BACK TO IDLE")
                    self.state = TFSM_STATE.IDLE
                    if self.grabbed:
                        self._print("Un-grabbing devices")
                        self._ungrab_devices()
                        self.grabbed = False
                        self.release = True
                    else:
                        self._print("Grabbing devices")
                        self._grab_devices()
                        self.grabbed = True

            elif self.state == TFSM_STATE.PEN:
                if not (self.edge or self.relx):
                    self._print("Back to IDLE from PEN")
                    self.state = TFSM_STATE.IDLE

            elif self.state == TFSM_STATE.PEN2:
                #self._print("State = PEN2")
                if self.updt_pos:
                    self._print("PEN2: State has been updated, back to IDLE")
                    self._ungrab_devices()
                    self.grabbed = False
                    self.state = TFSM_STATE.PEN3

            elif self.state == TFSM_STATE.PEN3: 
                if not (self.edge or self.relx): 
                    self._print("Back to IDLE from PEN3") 
                    self.state = TFSM_STATE.IDLE

