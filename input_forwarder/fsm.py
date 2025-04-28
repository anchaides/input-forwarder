# fsm.py

from enum import Enum
import threading

class TFSM_STATE(Enum):
    IDLE                = 0
    TOGGLE              = 1
    TOGGLEK             = 2
    PEN                 = 3
    POST_TOGGLE_UNGRAB  = 4
    PEN3                = 5
    POST_TOGGLE_GRAB    = 6 

class TFSM:
    def __init__(self, grab_devices, ungrab_devices, printer=print):
        self._state = TFSM_STATE.IDLE
        self._key1 = False
        self._key2 = False
        self._flagkbi = True
        self._flagmi = True
        self._edge = False
        self._relx = False
        self._release = False
        self._grabbed = False
        self._flag_pos = False
        self._flag_pos_ack = False
        #self._updt_pos = False
        self._lock = threading.Lock()

        self._grab_devices = grab_devices
        self._ungrab_devices = ungrab_devices
        self._print = printer

    @property
    def flagkbi(self):
        return self._flagkbi

    @flagkbi.setter
    def flagkbi(self, value):
        self._flagkbi = value 

    @property
    def flagmi(self):
        return self._flagmi

    @flagmi.setter
    def flagmi(self, value):
        self._flagmi = value 

    @property
    def flag_pos_ack(self):
        if self._flag_pos_ack:
            self._flag_pos_ack = False
            return True
        return False

    @flag_pos_ack.setter
    def flag_pos_ack(self, value):
        self._flag_pos_ack = value

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
                if self.edge: 
                    print(f"Edge = True, Relx = {self.relx}")
                if self.key1 and self.key2:
                    self._print("Keyboard Toggle")
                    self.state = TFSM_STATE.TOGGLEK
                elif self.edge and self.relx and self.flagkbi and self.flagmi:
                    self._print("Edge of screen toggle")
                    self.state = TFSM_STATE.TOGGLE

            elif self.state == TFSM_STATE.TOGGLE:
                if self.grabbed:
                    self._print("Un-grabbing devices: EDGE")
                    self.release = True
                    self.flag_pos = True
                    self.state = TFSM_STATE.POST_TOGGLE_UNGRAB
                else:
                    self._print("Grabbing devices: EDGE")
                    #self._grab_devices()
                    #self.grabbed = True
                    self.flag_pos = True
                    self.state = TFSM_STATE.POST_TOGGLE_GRAB

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
                self._print(f"PEN, edge = {self.edge} relx = {self.relx}")  
                if not (self.edge or self.relx):
                    self._print("Back to IDLE from PEN")
                    self.state = TFSM_STATE.IDLE

            elif self.state == TFSM_STATE.POST_TOGGLE_UNGRAB:
                #self._print("State = POST_TOGGLE_UNGRAB")
                if self.flag_pos_ack:
                    self._print("POST_TOGGLE_UNGRAB: Updated position has been sent to local pointer, now we can ungrab the devices")
                    self._ungrab_devices()
                    self.grabbed = False
                    self.state = TFSM_STATE.PEN

            elif self.state == TFSM_STATE.POST_TOGGLE_GRAB: 
                self._print("State is TFSM_STATE.POST_TOGGLE_GRAB")
                if self.flag_pos_ack == True: 
                    self._print("POST_TOGGLE_GRAB: Updated position has been sent to device, now we can grab devices") 
                    self._grab_devices() 
                    self.grabbed = True
                    self.state = TFSM_STATE.PEN 

