#campo_batalla.py
import pygame
import random
import sys
import os

_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

try:
    from modelos.nave import Nave
    from modelos.bala import Bala
    print("✓ Nave y Bala importadas correctamente")
except ImportError as e:
    print(f"✗ Error al importar Nave/Bala: {e}")
    Nave = None
    Bala = None

class CampoBatalla:
    def __init__(self, pantalla, ancho_pantalla, alto_pantalla):
        self.pantalla = pantalla
        self.ancho_pantalla = ancho_pantalla
        self.alto_campo = int(alto_pantalla * 0.85)
        
        self.estrellas = []
        self._generar_estrellas(150)
        
        self.naves = pygame.sprite.Group()
        self.balas = pygame.sprite.Group()
        self.bounds = pygame.Rect(0, 0, ancho_pantalla, self.alto_campo)
    
    #genera estrellas de manera aleatoria en el espacio
    def _generar_estrellas(self, cantidad):
        for _ in range(cantidad):
            self.estrellas.append({
                'x': random.randint(0, self.ancho_pantalla),
                'y': random.randint(0, self.alto_campo),
                'velocidad': random.uniform(0.1, 0.8),
                'tamaño': random.randint(1, 3)
            })
            
    def agregar_nave(self, x, y, speed=5, image_path=None):
        if Nave:
            nave = Nave(x, y, speed=speed, image_path=image_path or None)
            self.naves.add(nave)
            print(f"✓ Nave creada en ({x}, {y})")
            return nave
        else:
            print("✗ Nave no pudo ser importada")
        return None

    def disparar_desde_nave(self, nave):
        if Bala and nave:
            x, y = nave.get_shot_position()
            bala = Bala(x, y)
            self.balas.add(bala)
            return bala
        return None

    def actualizar(self, pressed_keys=None, joystick=None):
        for estrella in self.estrellas:
            estrella['y'] += estrella['velocidad']
            if estrella['y'] > self.alto_campo:
                estrella['y'] = 0
                estrella['x'] = random.randint(0, self.ancho_pantalla)
    
        # Si se proporciona un joystick, construimos un diccionario simulado
        # de teclas a partir de los ejes del gamepad y lo pasamos a las naves.
        if joystick:
            horiz = 0.0
            vert = 0.0
            try:
                # axis 0 = horizontal, axis 1 = vertical (convención común)
                horiz = joystick.get_axis(0)
                vert = joystick.get_axis(1)
            except Exception:
                pass

            THRESH = 0.4
            simulated = {}
            simulated[pygame.K_LEFT] = horiz < -THRESH
            simulated[pygame.K_RIGHT] = horiz > THRESH
            simulated[pygame.K_UP] = vert < -THRESH
            simulated[pygame.K_DOWN] = vert > THRESH

            for nave in self.naves:
                try:
                    nave.update(simulated, self.bounds)
                except Exception:
                    # En caso de que el método update espere la tupla de pressed_keys,
                    # intentamos pasar la tupla si estaba disponible.
                    if pressed_keys:
                        nave.update(pressed_keys, self.bounds)
        else:
            if pressed_keys:
                for nave in self.naves:
                    nave.update(pressed_keys, self.bounds)
        
        self.balas.update()
                
    def dibujar(self):
        #dibujar estrellas en el fondo
        for estrella in self.estrellas:
            pygame.draw.circle(self.pantalla, (255, 255, 255), 
                             (int(estrella['x']), int(estrella['y'])), estrella['tamaño'])
        
        self.naves.draw(self.pantalla)
        self.balas.draw(self.pantalla)
        
        #linea separadora de las interfaces de usuario
        pygame.draw.line(self.pantalla, (255, 255, 255), 
                        (0, self.alto_campo), (self.ancho_pantalla, self.alto_campo), 2)