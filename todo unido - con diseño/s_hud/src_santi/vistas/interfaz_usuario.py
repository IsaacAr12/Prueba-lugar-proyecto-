#interfaz_usuario.py
import pygame

import pygame

class InterfazUsuario:
    def __init__(self, pantalla, ancho_pantalla, alto_pantalla):
        self.pantalla = pantalla
        self.ancho_pantalla = ancho_pantalla
        self.alto_pantalla = alto_pantalla
        
        #calcular dimensiones
        self.altura_campo_batalla = int(self.alto_pantalla * 0.85)
        self.altura_hud = self.alto_pantalla - self.altura_campo_batalla
        
        #fuentes escalables
        self.fuente = pygame.font.Font(None, int(self.alto_pantalla * 0.03))
        self.fuente_puntaje = pygame.font.Font(None, int(self.alto_pantalla * 0.045))
        
    def dibujar(self, jugador1, jugador2=None, jugador_activo=None):
        #calcular posiciones
        y_base = self.altura_campo_batalla + 10
        margen = int(self.ancho_pantalla * 0.02)
        
        #jugador 1 se coloca en la izquierda
        self._dibujar_info_jugador(jugador1, margen, y_base)
        
        #jugador 2 (si existe) se coloca en la derecha
        if jugador2:
            self._dibujar_info_jugador(jugador2, self.ancho_pantalla - 250 - margen, y_base)
            
        #vidas del jugador activo
        self._dibujar_vidas(jugador_activo, margen)
        
        #barra de bonos
        self._dibujar_barra_bonos(jugador_activo)
        
    def _dibujar_info_jugador(self, jugador, x, y):
        tamano_foto = int(self.alto_pantalla * 0.06)
        
        #foto del jugador como placeholder
        pygame.draw.rect(self.pantalla, (0, 0, 255), (x, y, tamano_foto, tamano_foto))
        
        #nombre del jugador
        texto_nombre = self.fuente.render(jugador.nombre, True, (255, 255, 255))
        self.pantalla.blit(texto_nombre, (x + tamano_foto + 10, y))
        
        #puntaje visible
        texto_puntaje = self.fuente_puntaje.render(f"{jugador.puntaje}", True, (255, 255, 0))
        self.pantalla.blit(texto_puntaje, (x + tamano_foto + 10, y + 30))
        
    def _dibujar_vidas(self, jugador, margen):
        y_vidas = self.alto_pantalla - 30
        
        #texto de vidas
        texto_vidas = self.fuente.render(f"Vidas: {jugador.vidas}", True, (255, 255, 255))
        self.pantalla.blit(texto_vidas, (margen, y_vidas))
        
        #iconos de vidas
        tamano_vida = int(self.alto_pantalla * 0.025)
        for i in range(jugador.vidas):
            pygame.draw.rect(self.pantalla, (255, 0, 0), 
                           (margen + 100 + (i * (tamano_vida + 10)), y_vidas, tamano_vida, tamano_vida))
            
    def _dibujar_barra_bonos(self, jugador):
        ancho_barra = int(self.ancho_pantalla * 0.6)
        x_barra = (self.ancho_pantalla - ancho_barra) // 2
        y_barra = self.alto_pantalla - 40
        alto_barra = int(self.alto_pantalla * 0.035)
        
        #fondo de la barra
        pygame.draw.rect(self.pantalla, (50, 50, 50), (x_barra, y_barra, ancho_barra, alto_barra))
        
        #bonos disponibles
        tamano_bono = int(alto_barra * 0.7)
        for i, bono in enumerate(jugador.bonos):
            x_bono = x_barra + 10 + (i * (tamano_bono + 20))
            y_bono = y_barra + (alto_barra - tamano_bono) // 2
            
            pygame.draw.rect(self.pantalla, (0, 255, 0), (x_bono, y_bono, tamano_bono, tamano_bono))
            texto_bono = self.fuente.render(bono[0], True, (255, 255, 255))
            self.pantalla.blit(texto_bono, (x_bono + 5, y_bono + 2))