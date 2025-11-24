#hud_main.py
import pygame
import sys
from src_santi.motor_juego import MotorJuego

def mostrar_menu_principal():
    #menu simple para que se pruebe el juego
    pygame.init()
    
    #obtener resolución de pantalla
    info_pantalla = pygame.display.Info()
    ancho = info_pantalla.current_w
    alto = info_pantalla.current_h
    
    pantalla = pygame.display.set_mode((ancho, alto), pygame.FULLSCREEN)  #juego en pantalla completa
    pygame.display.set_caption("Galacta - Battle for Saturn")
    
    fuente = pygame.font.Font(None, int(alto * 0.04))  #fuente de manera escalable
    ejecutando = True
    
    while ejecutando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_1:  #presiona 1 para jugar
                    iniciar_partida_galactatec()
                elif evento.key == pygame.K_ESCAPE:
                    ejecutando = False
                elif evento.key == pygame.K_F11:  #F11 también funciona en menú
                    pygame.display.toggle_fullscreen()
        
        #dibujar menú
        pantalla.fill((0, 0, 50))  #fondo azul oscuro
        
        texto_titulo = fuente.render("GALACTATEC - BATTLE FOR SATURN", True, (255, 255, 0))
        texto_instruccion = fuente.render("Presiona 1 para Jugar", True, (255, 255, 255))
        texto_salir = fuente.render("Presiona ESC para Salir", True, (255, 255, 255))
        texto_pantalla = fuente.render("F11: Pantalla Completa", True, (200, 200, 200))
        
        pantalla.blit(texto_titulo, (ancho//2 - texto_titulo.get_width()//2, alto//3))
        pantalla.blit(texto_instruccion, (ancho//2 - texto_instruccion.get_width()//2, alto//2))
        pantalla.blit(texto_salir, (ancho//2 - texto_salir.get_width()//2, alto//2 + 50))
        pantalla.blit(texto_pantalla, (ancho//2 - texto_pantalla.get_width()//2, alto//2 + 100))
        
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()

def iniciar_partida_galactatec():
    #funcion principal de pantalla completa
    info_pantalla = pygame.display.Info()
    ancho = info_pantalla.current_w
    alto = info_pantalla.current_h
    
    pantalla = pygame.display.set_mode((ancho, alto), pygame.FULLSCREEN)  #pantalla completa
    pygame.display.set_caption("GalactaTec - Battle for Saturn")
    
    juego = MotorJuego(pantalla)
    juego.ejecutar()

if __name__ == "__main__":
    mostrar_menu_principal()