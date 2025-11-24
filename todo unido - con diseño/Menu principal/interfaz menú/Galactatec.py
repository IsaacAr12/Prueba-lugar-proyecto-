import pygame
import sys
import json
import os

# Inicializar pygame
pygame.init()

# Configuración de la pantalla en modo fullscreen
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
pygame.display.set_caption("The battle for saturn")

# Colores
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 100, 255)
LIGHT_BLUE = (100, 150, 255)
RED = (255, 50, 50)
GRAY = (100, 100, 100)
GOLD = (255, 215, 0)
GREEN = (50, 255, 50)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)

# Fuentes
title_font = pygame.font.SysFont('arial', 72, bold=True)
menu_font = pygame.font.SysFont('arial', 48)
info_font = pygame.font.SysFont('arial', 24)
config_font = pygame.font.SysFont('arial', 36)
input_font = pygame.font.SysFont('arial', 32)

# Opciones del menú
menu_options = [
    "Iniciar Partida",
    "Editar Perfil", 
    "Salón de la Fama",
    "Configuraciones",
    "Iniciar Jugador 2",
    "Salir"
]

# Configuración de dificultad
DIFFICULTY_LEVELS = {
    0: {"name": "RECLUTA", "color": GREEN, "description": "Fácil"},
    1: {"name": "SARGENTO", "color": YELLOW, "description": "Normal"},
    2: {"name": "COMANDANTE", "color": ORANGE, "description": "Difícil"}
}

# Estados de la aplicación
MAIN_MENU = 0
HALL_OF_FAME = 1
CONFIGURATIONS = 2
SELECT_DIFFICULTY = 3
EDIT_PROFILE = 4
PLAYER2_SETUP = 5

current_state = MAIN_MENU
selected_option = 0
config_selected_option = 0
difficulty_selected_option = 1
profile_input = ""
player2_input = ""
input_active = False
error_message = ""

# Archivo de configuración
CONFIG_FILE = "The battel of saturn_config.json"

# Cargar configuración existente o crear una por defecto
def load_config():
    default_config = {
        "flight_patterns": 1,  # SARGENTO por defecto (normal)
        "player1_name": "PILOTO1",
        "player2_name": "PILOTO2"
    }
    
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        else:
            save_config(default_config)
            return default_config
    except:
        return default_config

# Guardar configuración
def save_config(config):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except:
        return False

# Cargar configuración al inicio
game_config = load_config()
difficulty_selected_option = game_config["flight_patterns"]
profile_input = game_config["player1_name"]

# Función para validar alias
def validate_alias(player1_name, player2_name):
    if not player2_name.strip():
        return "El alias no puede estar vacío"
    if player2_name.upper() == player1_name.upper():
        return "El jugador 2 no puede usar el mismo alias que el jugador 1"
    if len(player2_name) > 10:
        return "El alias no puede tener más de 10 caracteres"
    return ""

# Función para dibujar el fondo
def draw_background():
    screen.fill(BLACK)

# Función para dibujar el título principal
def draw_title():
    title_text = title_font.render("THE BATTLE FOR SATURN", True, BLUE)
    title_rect = title_text.get_rect(center=(WIDTH//2, HEIGHT//6))
    
    glow_text = title_font.render("THE BATTLE FOR SATURN", True, LIGHT_BLUE)
    glow_rect = glow_text.get_rect(center=(WIDTH//2 + 3, HEIGHT//6 + 3))
    
    screen.blit(glow_text, glow_rect)
    screen.blit(title_text, title_rect)

# Función para dibujar el título del Salón de la Fama
def draw_hall_of_fame_title():
    title_text = title_font.render("SALÓN DE LA FAMA", True, GOLD)
    title_rect = title_text.get_rect(center=(WIDTH//2, HEIGHT//8))
    
    glow_text = title_font.render("SALÓN DE LA FAMA", True, (255, 200, 0))
    glow_rect = glow_text.get_rect(center=(WIDTH//2 + 3, HEIGHT//8 + 3))
    
    screen.blit(glow_text, glow_rect)
    screen.blit(title_text, title_rect)

# Función para dibujar el título de Configuraciones
def draw_config_title():
    title_text = title_font.render("CONFIGURACIONES", True, LIGHT_BLUE)
    title_rect = title_text.get_rect(center=(WIDTH//2, HEIGHT//8))
    
    glow_text = title_font.render("CONFIGURACIONES", True, BLUE)
    glow_rect = glow_text.get_rect(center=(WIDTH//2 + 3, HEIGHT//8 + 3))
    
    screen.blit(glow_text, glow_rect)
    screen.blit(title_text, title_rect)

# Función para dibujar el título de Selección de Dificultad
def draw_difficulty_title():
    title_text = title_font.render("SELECCIONAR DIFICULTAD", True, LIGHT_BLUE)
    title_rect = title_text.get_rect(center=(WIDTH//2, HEIGHT//8))
    
    glow_text = title_font.render("SELECCIONAR DIFICULTAD", True, BLUE)
    glow_rect = glow_text.get_rect(center=(WIDTH//2 + 3, HEIGHT//8 + 3))
    
    screen.blit(glow_text, glow_rect)
    screen.blit(title_text, title_rect)

# Función para dibujar el título de Editar Perfil
def draw_edit_profile_title():
    title_text = title_font.render("EDITAR PERFIL JUGADOR 1", True, LIGHT_BLUE)
    title_rect = title_text.get_rect(center=(WIDTH//2, HEIGHT//8))
    
    glow_text = title_font.render("EDITAR PERFIL JUGADOR 1", True, BLUE)
    glow_rect = glow_text.get_rect(center=(WIDTH//2 + 3, HEIGHT//8 + 3))
    
    screen.blit(glow_text, glow_rect)
    screen.blit(title_text, title_rect)

# Función para dibujar el título de Jugador 2
def draw_player2_title():
    title_text = title_font.render("CONFIGURAR JUGADOR 2", True, LIGHT_BLUE)
    title_rect = title_text.get_rect(center=(WIDTH//2, HEIGHT//8))
    
    glow_text = title_font.render("CONFIGURAR JUGADOR 2", True, BLUE)
    glow_rect = glow_text.get_rect(center=(WIDTH//2 + 3, HEIGHT//8 + 3))
    
    screen.blit(glow_text, glow_rect)
    screen.blit(title_text, title_rect)

# Función para dibujar las opciones del menú principal
def draw_menu():
    for i, option in enumerate(menu_options):
        color = LIGHT_BLUE if i == selected_option else WHITE
        text = menu_font.render(option, True, color)
        rect = text.get_rect(center=(WIDTH//2, HEIGHT//3 + i * 70))
        screen.blit(text, rect)
        
        if i == selected_option:
            pygame.draw.polygon(screen, RED, [
                (rect.left - 30, rect.centery),
                (rect.left - 10, rect.centery - 15),
                (rect.left - 10, rect.centery + 15)
            ])

# Función para dibujar la pantalla del Salón de la Fama (simplificada)
def draw_hall_of_fame():
    draw_hall_of_fame_title()
    
    # Mensaje de que esta función está en desarrollo
    message = config_font.render("Salón de la Fama en desarrollo", True, GOLD)
    message_rect = message.get_rect(center=(WIDTH//2, HEIGHT//2))
    screen.blit(message, message_rect)
    
    # Información de controles
    controls_text = info_font.render("Presiona ESC para volver al menú principal", True, GRAY)
    screen.blit(controls_text, (WIDTH//2 - controls_text.get_width()//2, HEIGHT - 100))

# Función para dibujar la pantalla de Configuraciones (simplificada)
def draw_configurations():
    draw_config_title()
    
    # Mensaje de que esta función está en desarrollo
    message = config_font.render("Configuraciones en desarrollo", True, LIGHT_BLUE)
    message_rect = message.get_rect(center=(WIDTH//2, HEIGHT//2))
    screen.blit(message, message_rect)
    
    # Información de controles
    controls_text = info_font.render("Presiona ESC para volver al menú principal", True, GRAY)
    screen.blit(controls_text, (WIDTH//2 - controls_text.get_width()//2, HEIGHT - 100))

# Función para dibujar la pantalla de Editar Perfil
def draw_edit_profile():
    draw_edit_profile_title()
    
    # Instrucciones
    instructions = config_font.render("Ingresa tu alias (máx. 10 caracteres):", True, WHITE)
    screen.blit(instructions, (WIDTH//2 - instructions.get_width()//2, HEIGHT//3))
    
    # Campo de entrada
    input_rect = pygame.Rect(WIDTH//2 - 200, HEIGHT//2 - 25, 400, 50)
    pygame.draw.rect(screen, LIGHT_BLUE, input_rect, 2)
    
    # Texto del input
    input_text = input_font.render(profile_input, True, WHITE)
    screen.blit(input_text, (input_rect.x + 10, input_rect.y + 10))
    
    # Cursor parpadeante
    if input_active and pygame.time.get_ticks() % 1000 < 500:
        cursor_x = input_rect.x + 10 + input_text.get_width()
        pygame.draw.line(screen, WHITE, (cursor_x, input_rect.y + 10), 
                         (cursor_x, input_rect.y + 40), 2)
    
    # Información de controles
    controls_text = info_font.render("ENTER para guardar, ESC para cancelar", True, GRAY)
    screen.blit(controls_text, (WIDTH//2 - controls_text.get_width()//2, HEIGHT - 100))

# Función para dibujar la pantalla de Configuración de Jugador 2
def draw_player2_setup():
    draw_player2_title()
    
    # Mostrar alias actual del jugador 1
    player1_info = config_font.render(f"Jugador 1: {game_config['player1_name']}", True, LIGHT_BLUE)
    screen.blit(player1_info, (WIDTH//2 - player1_info.get_width()//2, HEIGHT//4))
    
    # Instrucciones
    instructions = config_font.render("Ingresa alias para Jugador 2:", True, WHITE)
    screen.blit(instructions, (WIDTH//2 - instructions.get_width()//2, HEIGHT//3))
    
    # Campo de entrada
    input_rect = pygame.Rect(WIDTH//2 - 200, HEIGHT//2 - 25, 400, 50)
    pygame.draw.rect(screen, LIGHT_BLUE, input_rect, 2)
    
    # Texto del input
    input_text = input_font.render(player2_input, True, WHITE)
    screen.blit(input_text, (input_rect.x + 10, input_rect.y + 10))
    
    # Cursor parpadeante
    if input_active and pygame.time.get_ticks() % 1000 < 500:
        cursor_x = input_rect.x + 10 + input_text.get_width()
        pygame.draw.line(screen, WHITE, (cursor_x, input_rect.y + 10), 
                         (cursor_x, input_rect.y + 40), 2)
    
    # Mostrar mensaje de error si existe
    if error_message:
        error_text = info_font.render(error_message, True, RED)
        screen.blit(error_text, (WIDTH//2 - error_text.get_width()//2, HEIGHT//2 + 50))
    
    # Información de controles
    controls_text = info_font.render("ENTER para confirmar, ESC para cancelar", True, GRAY)
    screen.blit(controls_text, (WIDTH//2 - controls_text.get_width()//2, HEIGHT - 100))

# Función para dibujar la pantalla de Selección de Dificultad
def draw_difficulty_selection():
    draw_difficulty_title()
    
    # Título de la sección de dificultad
    difficulty_title = config_font.render("PATRONES DE VUELO (DIFICULTAD)", True, LIGHT_BLUE)
    screen.blit(difficulty_title, (WIDTH//2 - difficulty_title.get_width()//2, HEIGHT//4))
    
    # Opciones de dificultad
    for i in range(3):
        level = DIFFICULTY_LEVELS[i]
        is_selected = (difficulty_selected_option == i)
        is_current = (game_config["flight_patterns"] == i)
        
        # Color y estilo según el estado
        if is_selected:
            color = RED
            prefix = "> "
        else:
            color = level["color"]
            prefix = "  "
        
        # Texto de la opción
        option_text = f"{prefix}{level['name']} - {level['description']}"
        if is_current:
            option_text += " [ACTUAL]"
        
        text = config_font.render(option_text, True, color)
        y_position = HEIGHT//3 + i * 80
        screen.blit(text, (WIDTH//2 - text.get_width()//2, y_position))
        
        # Descripción adicional de cada dificultad
        desc_y = y_position + 40
        if i == 0:
            desc = "Enemigos lentos, patrones predecibles, daño reducido"
        elif i == 1:
            desc = "Velocidad estándar, patrones variados, daño normal"
        else:
            desc = "Enemigos rápidos, patrones complejos, daño aumentado"
        
        desc_text = info_font.render(desc, True, GRAY)
        screen.blit(desc_text, (WIDTH//2 - desc_text.get_width()//2, desc_y))
    
    # Información de controles
    controls_text = info_font.render("Usa ↑ ↓ para navegar, ENTER para seleccionar y comenzar, ESC para volver", True, GRAY)
    screen.blit(controls_text, (WIDTH//2 - controls_text.get_width()//2, HEIGHT - 100))

# Función para dibujar información en la parte inferior
def draw_footer():
    if current_state == MAIN_MENU:
        text = f"© 2024 The battle for satunr Prototype - Jugador 1: {game_config['player1_name']} - Usa las flechas y ENTER - ESC para salir"
    elif current_state == HALL_OF_FAME:
        text = "Salón de la Fama - Funcionalidad en desarrollo"
    elif current_state == CONFIGURATIONS:
        text = "Configuraciones - Funcionalidad en desarrollo"
    elif current_state == EDIT_PROFILE:
        text = f"Editando perfil de Jugador 1 - Alias actual: {game_config['player1_name']}"
    elif current_state == PLAYER2_SETUP:
        text = f"Configurando Jugador 2 - Jugador 1: {game_config['player1_name']}"
    else:  # SELECT_DIFFICULTY
        text = f"Dificultad actual: {DIFFICULTY_LEVELS[game_config['flight_patterns']]['name']} - {DIFFICULTY_LEVELS[game_config['flight_patterns']]['description']}"
    
    footer_text = info_font.render(text, True, GRAY)
    footer_rect = footer_text.get_rect(center=(WIDTH//2, HEIGHT - 40))
    screen.blit(footer_text, footer_rect)

# Función principal del juego
def main():
    global selected_option, current_state, config_selected_option, difficulty_selected_option
    global game_config, profile_input, player2_input, input_active, error_message
    
    clock = pygame.time.Clock()
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Control del menú con teclado
            if event.type == pygame.KEYDOWN:
                if current_state == MAIN_MENU:
                    if event.key == pygame.K_UP:
                        selected_option = (selected_option - 1) % len(menu_options)
                    elif event.key == pygame.K_DOWN:
                        selected_option = (selected_option + 1) % len(menu_options)
                    elif event.key == pygame.K_RETURN:
                        option = menu_options[selected_option]
                        
                        if option == "Iniciar Partida":
                            current_state = SELECT_DIFFICULTY
                            difficulty_selected_option = game_config["flight_patterns"]
                        elif option == "Editar Perfil":
                            current_state = EDIT_PROFILE
                            profile_input = game_config["player1_name"]
                            input_active = True
                        elif option == "Salón de la Fama":
                            current_state = HALL_OF_FAME
                        elif option == "Configuraciones":
                            current_state = CONFIGURATIONS
                        elif option == "Iniciar Jugador 2":
                            current_state = PLAYER2_SETUP
                            player2_input = game_config["player2_name"]
                            input_active = True
                            error_message = ""
                        elif option == "Salir":
                            running = False
                
                elif current_state == SELECT_DIFFICULTY:
                    if event.key == pygame.K_UP:
                        difficulty_selected_option = (difficulty_selected_option - 1) % 3
                    elif event.key == pygame.K_DOWN:
                        difficulty_selected_option = (difficulty_selected_option + 1) % 3
                    elif event.key == pygame.K_RETURN:
                        # Guardar la nueva dificultad seleccionada e iniciar el juego
                        game_config["flight_patterns"] = difficulty_selected_option
                        if save_config(game_config):
                            print(f"Iniciando partida en dificultad: {DIFFICULTY_LEVELS[difficulty_selected_option]['name']}")
                            # Aquí iría la lógica para iniciar el juego
                            # Por ahora volvemos al menú principal
                            current_state = MAIN_MENU
                        else:
                            print("Error al guardar la configuración")
                
                elif current_state == EDIT_PROFILE:
                    if event.key == pygame.K_RETURN:
                        # Guardar el nuevo alias del jugador 1
                        if profile_input.strip() and len(profile_input) <= 10:
                            game_config["player1_name"] = profile_input.upper()
                            if save_config(game_config):
                                current_state = MAIN_MENU
                                input_active = False
                        else:
                            error_message = "El alias debe tener entre 1 y 10 caracteres"
                    elif event.key == pygame.K_BACKSPACE:
                        profile_input = profile_input[:-1]
                    else:
                        # Agregar caracteres al input (solo letras y números)
                        if len(profile_input) < 10 and event.unicode.isalnum():
                            profile_input += event.unicode.upper()
                
                elif current_state == PLAYER2_SETUP:
                    if event.key == pygame.K_RETURN:
                        # Validar y guardar el alias del jugador 2
                        validation_error = validate_alias(game_config["player1_name"], player2_input)
                        if not validation_error:
                            game_config["player2_name"] = player2_input.upper()
                            if save_config(game_config):
                                print(f"Iniciando partida de 2 jugadores: {game_config['player1_name']} vs {game_config['player2_name']}")
                                current_state = MAIN_MENU
                                input_active = False
                        else:
                            error_message = validation_error
                    elif event.key == pygame.K_BACKSPACE:
                        player2_input = player2_input[:-1]
                        error_message = ""  # Limpiar error al editar
                    else:
                        # Agregar caracteres al input (solo letras y números)
                        if len(player2_input) < 10 and event.unicode.isalnum():
                            player2_input += event.unicode.upper()
                            error_message = ""  # Limpiar error al editar
                
                # Control de la tecla ESC
                if event.key == pygame.K_ESCAPE:
                    if current_state in [HALL_OF_FAME, CONFIGURATIONS, SELECT_DIFFICULTY, EDIT_PROFILE, PLAYER2_SETUP]:
                        # Volver al menú principal desde otras pantallas
                        current_state = MAIN_MENU
                        input_active = False
                        error_message = ""
                    elif current_state == MAIN_MENU:
                        # Salir del juego desde el menú principal
                        running = False
        
        # Dibujar todo
        draw_background()
        
        if current_state == MAIN_MENU:
            draw_title()
            draw_menu()
        elif current_state == HALL_OF_FAME:
            draw_hall_of_fame()
        elif current_state == CONFIGURATIONS:
            draw_configurations()
        elif current_state == SELECT_DIFFICULTY:
            draw_difficulty_selection()
        elif current_state == EDIT_PROFILE:
            draw_edit_profile()
        elif current_state == PLAYER2_SETUP:
            draw_player2_setup()
        
        draw_footer()
        
        # Actualizar pantalla
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()