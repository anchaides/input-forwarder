# composer_backend.py 

class ComposerBackend:
    def __init__(self): 
        self._composer = "Undefined"
    def get_pointer_position(self):
        raise NotImplementedError

    def set_pointer_position(self, y_ratio: float):
        raise NotImplementedError

    def shutdown(self): 
        pass 

    @property 
    def composer(self): 
        return self._composer 

    @composer.setter 
    def composer(self, val): 
        self._composer = val
