from halo import Halo

class Spinner:
    _instance = None  # Atributo de clase para almacenar la única instancia

    def __new__(cls, *args, **kwargs):
        # Si no existe una instancia, la creamos
        if not cls._instance:
            cls._instance = super(Spinner, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):  # Solo inicializamos una vez
            self.initialized = True
            self.halo = Halo(text="", spinner='dots')
            self.prefix = ""  # Inicializamos el prefijo vacío

    def start(self, prefixText=""):
        self.prefix = prefixText
        self.halo.start(f'{self.prefix} Loading...')

    def resume(self, text, emoji="", color="white"):
        self.halo.start("")
        self.log(text, emoji, color)

    def stop(self, text="", emoji="", color="white", persist=True):
        if text:
            self.log(text, emoji, color)

        if persist:
            self.halo.stop_and_persist()
        else:
            self.halo.stop()

    def warn(self, text, emoji="⚠️", color="yellow"):
        self.log(text, emoji, color)

    def error(self, text, emoji="❌", color="red"):
        self.log(text, emoji, color)
        self.stop()

    def log(self, text, emoji="", color="white"):
        self.halo.color = color
        self.halo.text = f'{emoji}{"  " if emoji else ""}{self.prefix}. {text}'

    def set_prefix(self, prefixText):
        self.prefix = prefixText  # Permite actualizar el prefijo sin iniciar el spinner
