#jugador.py
class Jugador:
    def __init__(self, nombre, ruta_foto=None):
        self.nombre = nombre
        self.ruta_foto = ruta_foto
        self.puntaje = 0
        self.vidas = 3
        self.bonos = []
        self.esta_activo = False
    
    #se actualiza el puntaje
    def actualizar_puntaje(self, puntos):
        self.puntaje += puntos
    
    #funcion para perder vidas
    def perder_vida(self):
        if self.vidas > 0:
            self.vidas -= 1
            return True
        return False
    
    #función para agregar bonos
    def agregar_bono(self, tipo_bono):
        if tipo_bono not in self.bonos:
            self.bonos.append(tipo_bono)