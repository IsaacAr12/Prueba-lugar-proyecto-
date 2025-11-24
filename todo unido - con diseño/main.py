import sys
import os
import random
from pathlib import Path
from typing import Callable, List, Optional

import pygame
import tkinter as tk
from tkinter import filedialog

from persistence import PlayerRepository
from validators import Validator
from services.player_service import PlayerService
from services.email_sender import EmailSender
from player import Player

MOTOR_JUEGO_AVAILABLE = False
MotorJuego = None

try:
    s_hud_path = str(Path(__file__).parent / "s_hud")
    if s_hud_path not in sys.path:
        sys.path.insert(0, s_hud_path)
    from src_santi.motor_juego import MotorJuego
    MOTOR_JUEGO_AVAILABLE = True
except ImportError as e:
    print(f"Advertencia: No se pudo cargar MotorJuego: {e}")
    MOTOR_JUEGO_AVAILABLE = False

# ================== CONFIGURACIÓN GLOBAL ==================
pygame.init()
pygame.font.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

#Definiciones
WINDOW_WIDTH, WINDOW_HEIGHT = 1000, 700 #Ventana principal
#Paleta de colores retro
BACKGROUND_COLOR = (10, 8, 28)
PANEL_COLOR = (22, 18, 50)
TEXT_COLOR = (229, 227, 255)
ACCENT_COLOR = (255, 64, 129)
ACCENT_HOVER = (255, 149, 0)
ERROR_COLOR = (255, 89, 94)
SUCCESS_COLOR = (67, 255, 190)
BORDER_COLOR = (98, 72, 200)
NEON_GLOW = (58, 255, 254)


def _load_font(size: int, *, bold: bool = False) -> pygame.font.Font:
    font = pygame.font.SysFont("bahnschrift", size, bold=bold)
    if not font:
        font = pygame.font.Font(None, size)
        font.set_bold(bold)
    return font


TITLE_FONT = _load_font(44, bold=True)
FONT = _load_font(24)
SMALL_FONT = _load_font(18)


class SpaceBackground:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self._base_image = self._load_image()
        self._scaled_image: Optional[pygame.Surface] = None
        self._overlay: Optional[pygame.Surface] = None
        self._stars: List[dict] = []
        self._ensure_scaled_image()
        self._refresh_overlay()
        self._generate_stars()

    def _load_image(self) -> Optional[pygame.Surface]:
        base_path = Path(__file__).parent
        candidates = [
            base_path / "Jugabilidad" / "Base" / "assets" / "images" / "space_background.png",
            base_path / "s_hud" / "assets" / "images" / "space_background.png",
        ]
        for candidate in candidates:
            if candidate.exists():
                try:
                    return pygame.image.load(str(candidate)).convert()
                except pygame.error:
                    continue
        return None

    def _ensure_scaled_image(self):
        if self._base_image:
            self._scaled_image = pygame.transform.smoothscale(self._base_image, (self.width, self.height))
        else:
            self._scaled_image = None

    def _refresh_overlay(self):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((10, 20, 40, 90))
        self._overlay = overlay

    def _generate_stars(self):
        self._stars.clear()
        total = max(140, (self.width * self.height) // 9000)
        palette = [(255, 255, 255), (198, 220, 255), (255, 204, 153), (180, 190, 255)]
        for _ in range(total):
            self._stars.append(
                {
                    "x": random.uniform(0, self.width),
                    "y": random.uniform(0, self.height),
                    "speed": random.uniform(40, 120),
                    "size": random.randint(1, 3),
                    "color": random.choice(palette),
                }
            )

    def update(self, dt: float):
        if not self._stars:
            return
        for star in self._stars:
            star["y"] += star["speed"] * dt
            if star["y"] >= self.height:
                star["y"] -= self.height
                star["x"] = random.uniform(0, self.width)

    def draw(self, surface: pygame.Surface):
        width, height = surface.get_size()
        if width != self.width or height != self.height:
            self.width = width
            self.height = height
            self._ensure_scaled_image()
            self._refresh_overlay()
            self._generate_stars()
        if self._scaled_image:
            surface.blit(self._scaled_image, (0, 0))
        else:
            surface.fill((5, 7, 22))
        for star in self._stars:
            pygame.draw.circle(surface, star["color"], (int(star["x"]), int(star["y"])), star["size"])
        if self._overlay:
            surface.blit(self._overlay, (0, 0))


# ================== UTILIDADES DE UI ==================
class MessageBanner:
    """Muestra mensajes temporales en pantalla."""

    def __init__(self):
        self.message: str = ""
        self.color = TEXT_COLOR
        self.expire_at: int = 0

    def show(self, message: str, color=TEXT_COLOR, duration_ms: int = 3500):
        """Configura y activa el banner con un mensaje, color y duración."""
        self.message = message
        self.color = color
        self.expire_at = pygame.time.get_ticks() + duration_ms

    def draw(self, surface: pygame.Surface):
        """Dibuja el banner si está activo y comprueba si debe expirar."""
        if not self.message:
            return
        if pygame.time.get_ticks() > self.expire_at:
            self.message = ""
            return
        banner_rect = pygame.Rect(0, WINDOW_HEIGHT - 64, WINDOW_WIDTH, 64)
        overlay = pygame.Surface(banner_rect.size, pygame.SRCALPHA)
        overlay.fill((18, 10, 40, 220))
        surface.blit(overlay, banner_rect)
        pygame.draw.rect(surface, NEON_GLOW, banner_rect, width=2)
        text_surface = SMALL_FONT.render(self.message, True, self.color)
        surface.blit(text_surface, (24, WINDOW_HEIGHT - 44))


class InputBox:
    """Campo de texto simple (menja entrada, activación y dibujo)."""

    def __init__(self, x: int, y: int, w: int, h: int, *, placeholder: str = "", text: str = "", password: bool = False):
        self.rect = pygame.Rect(x, y, w, h)
        self.placeholder = placeholder
        self.text = text
        self.password = password
        self.active = False
        self.color_inactive = BORDER_COLOR
        self.color_active = ACCENT_COLOR
        self.color = self.color_inactive
        self.min_width = w
        self.min_height = h
        self.padding_x = 12
        self.padding_y = 10
        self.display_text = ""
        self.rect.width = self.min_width
        self.rect.height = self.min_height
        self._render_text()

    def _display_text(self) -> str:
        """Devuelve el texto a mostrar (contraseña, texto normal o placeholder)."""
        if self.text:
            return "*" * len(self.text) if self.password else self.text
        return self.placeholder

    def _text_color(self) -> pygame.Color:
        if self.text:
            return TEXT_COLOR
        return pygame.Color(160, 172, 210)

    def _render_text(self):
        display = self._display_text()
        available_width = self.min_width - self.padding_x * 2
        if available_width <= 0:
            available_width = 10
        self.display_text = display
        if FONT.size(display)[0] > available_width:
            truncated = display
            while truncated and FONT.size(truncated + "…")[0] > available_width:
                truncated = truncated[:-1]
            self.display_text = f"{truncated}…" if truncated else "…"
        self.txt_surface = FONT.render(self.display_text, True, self._text_color())
        self.rect.width = self.min_width
        height_needed = self.txt_surface.get_height() + self.padding_y * 2
        self.rect.height = max(self.min_height, height_needed)

    def set_text(self, value: str):
        """Establece el valor del texto y lo vuelve a renderizar."""
        self.text = value
        self._render_text()

    def set_active(self, active: bool):
        """Cambia el estado de enfoque y actualiza el color del borde."""
        self.active = active
        self.color = self.color_active if self.active else self.color_inactive

    def handle_event(self, event: pygame.event.EventType) -> Optional[str]:
        """Procesa eventos de ratón y teclado para la InputBox."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Detecta clic para activar/desactivar el foco
            self.set_active(self.rect.collidepoint(event.pos))
            return None
        if event.type == pygame.KEYDOWN and self.active:
            # Comportamiento especial para teclas
            if event.key == pygame.K_RETURN:
                return "SUBMIT" # Señal para el envío del formulario
            if event.key == pygame.K_TAB:
                return "TAB" # Señal para mover el foco al siguiente campo
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1] # Elimina el último caracter
            elif event.key == pygame.K_ESCAPE:
                self.set_active(False) # Pierde el foco
            else:
                #(soporte para acentos y caracteres especiales)
                if event.unicode:
                    self.text += event.unicode
            self._render_text()
        return None

    def update(self):
        """Método de actualización (vacío, solo para consistencia con BaseScreen)."""
        pass

    def draw(self, surface: pygame.Surface):
        """Dibuja la caja de texto y el texto en la superficie."""
        outer_rect = self.rect.inflate(12, 12)
        pygame.draw.rect(surface, BORDER_COLOR, outer_rect, width=2, border_radius=8)
        pygame.draw.rect(surface, PANEL_COLOR, self.rect, border_radius=8)
        text_x = self.rect.x + self.padding_x
        text_y = self.rect.y + (self.rect.height - self.txt_surface.get_height()) // 2
        surface.blit(self.txt_surface, (text_x, text_y))
        pygame.draw.rect(surface, self.color, self.rect, 2, border_radius=8)


class Button:
    """Botón básico con callback."""

    def __init__(self, rect: pygame.Rect, text: str, callback: Callable[[], None], *, bg_color=ACCENT_COLOR, text_color=TEXT_COLOR, hover_text_color=NEON_GLOW):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.bg_color = bg_color
        self.text_normal_color = text_color
        self.text_hover_color = hover_text_color
        self.hover = False
        self.padding_x = 26
        self.padding_y = 14
        self._update_text_surface()

    def _update_text_surface(self):
        self.text_surface = FONT.render(self.text, True, self.text_normal_color)
        self._resize_to_text()

    def _resize_to_text(self):
        width = self.text_surface.get_width() + self.padding_x * 2
        height = self.text_surface.get_height() + self.padding_y * 2
        self.rect.width = width
        self.rect.height = height

    def set_text(self, new_text: str):
        if self.text != new_text:
            self.text = new_text
            self._update_text_surface()

    def handle_event(self, event: pygame.event.EventType):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()

    def draw(self, surface: pygame.Surface):
        glow_rect = self.rect.inflate(20, 12)
        border_rect = self.rect.inflate(10, 6)
        pygame.draw.rect(surface, NEON_GLOW if self.hover else BORDER_COLOR, glow_rect, width=2, border_radius=10)
        pygame.draw.rect(surface, BORDER_COLOR, border_rect, width=3, border_radius=10)
        color = ACCENT_HOVER if self.hover else self.bg_color
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        text_surface = FONT.render(self.text, True, self.text_hover_color if self.hover else self.text_normal_color)
        text_pos = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_pos)


class FileDialogHelperMixin:
    """Mixin que provee utilidades para abrir selectores de archivos y actualizar campos."""

    _file_dialog_root: Optional[tk.Tk] = None

    def _init_upload_helpers(self) -> tk.Tk:
        if FileDialogHelperMixin._file_dialog_root is None:
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            FileDialogHelperMixin._file_dialog_root = root
        FileDialogHelperMixin._file_dialog_root.update()
        return FileDialogHelperMixin._file_dialog_root

    def _create_upload_rect(self, index: int) -> pygame.Rect:
        width, height = self.upload_button_size
        input_rect = self.inputs[index].rect
        x = input_rect.right + self.upload_margin
        y = input_rect.y + (input_rect.height - height) // 2
        return pygame.Rect(x, y, width, height)

    def _open_file_dialog(self, input_index: int, *filetypes):
        """Abre un diálogo para seleccionar un solo archivo y actualiza el InputBox."""
        root = self._init_upload_helpers()
        selected = filedialog.askopenfilename(
            parent=root,
            title="Seleccionar archivo",
            filetypes=filetypes or [("Todos", "*.*")],
        )
        if selected:
            self.inputs[input_index].set_text(selected)

    def _open_file_dialog_multiple(self, input_index: int, *filetypes):
        """Abre un diálogo para seleccionar múltiples archivos y actualiza el InputBox."""
        root = self._init_upload_helpers()
        selected = filedialog.askopenfilenames(
            parent=root,
            title="Seleccionar archivos",
            filetypes=filetypes or [("Todos", "*.*")],
        )
        if selected:
            joined = ", ".join(selected)
            self.inputs[input_index].set_text(joined)


# ================== CLASES DE PANTALLA ==================
class BaseScreen:
    def __init__(self, app: "GameApp"):
        self.app = app

    def draw_background(self, surface: pygame.Surface):
        background = getattr(self.app, "space_background", None)
        if background:
            background.draw(surface)

    def handle_event(self, event: pygame.event.EventType):
        raise NotImplementedError

    def update(self):
        pass

    def draw(self, surface: pygame.Surface):
        raise NotImplementedError


class MainMenuScreen(BaseScreen):
    def __init__(self, app: "GameApp"):
        super().__init__(app)
        button_width, button_height = 260, 60
        x = (WINDOW_WIDTH - button_width) // 2
        start_y = 260
        spacing = 80
        # Lista de botones con callbacks lambda para cambiar de pantalla
        self.buttons = [
            Button(pygame.Rect(x, start_y, button_width, button_height), "Iniciar sesión", lambda: app.set_screen(LoginScreen(app))),
            Button(pygame.Rect(x, start_y + spacing, button_width, button_height), "Registrarse", lambda: app.set_screen(RegisterScreen(app))),
            Button(pygame.Rect(x, start_y + spacing * 2, button_width, button_height), "Salir", self.exit_app),
        ]
        app.stop_background_music()

    def exit_app(self):
        self.app.running = False

    def handle_event(self, event: pygame.event.EventType):
        # Soporte básico de gamepad: botón 0 como "confirmar/seleccionar" en menús
        if event.type == pygame.JOYBUTTONDOWN:
            try:
                if event.button == 0:
                    # Ejecuta callback del primer botón (Iniciar sesión)
                    if self.buttons:
                        self.buttons[0].callback()
                    return
            except Exception as e:
                print(f"Error manejando JOYBUTTONDOWN en MainMenu: {e}")

        for button in self.buttons:
            button.handle_event(event)

    def draw(self, surface: pygame.Surface):
        self.draw_background(surface)
        title = TITLE_FONT.render("¡Bienvenido!", True, TEXT_COLOR)
        subtitle = SMALL_FONT.render("Menu", True, TEXT_COLOR)
        surface.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 150)))
        surface.blit(subtitle, subtitle.get_rect(center=(WINDOW_WIDTH // 2, 200)))
        for button in self.buttons:
            button.draw(surface)


class LoginScreen(BaseScreen):
    def __init__(self, app: "GameApp"):
        super().__init__(app)
        center_x = WINDOW_WIDTH // 2
        self.inputs: List[InputBox] = [
            InputBox(center_x - 180, 220, 360, 48, placeholder="Alias o correo"),
            InputBox(center_x - 180, 300, 360, 48, placeholder="Contraseña", password=True),
        ]
        for idx, box in enumerate(self.inputs):
            box.set_active(idx == 0)

        self.buttons = [
            Button(pygame.Rect(center_x - 150, 380, 160, 50), "Ingresar", self.attempt_login),
            Button(pygame.Rect(center_x + 10, 380, 200, 50), "Recuperar contraseña", self.request_password_reset),
            Button(pygame.Rect(center_x - 150, 450, 160, 45), "Regresar", lambda: app.set_screen(MainMenuScreen(app))),
        ]

        self.recovery_modal: Optional[RecoveryModal] = None
        self.recovery_code_sent = False

    def _focus_next(self, current: InputBox):
        if current not in self.inputs:
            return
        idx = self.inputs.index(current)
        next_idx = (idx + 1) % len(self.inputs)
        # Desactiva todos y activa el siguiente
        for box in self.inputs:
            box.set_active(False)
        self.inputs[next_idx].set_active(True)

    def attempt_login(self):
        alias_email = self.inputs[0].text.strip()
        password = self.inputs[1].text.strip()

        if not alias_email or not password:
            self.app.banner.show("Debes ingresar alias/email y contraseña.", ERROR_COLOR)
            return

        self.app.repo.reload_players()
        # Busca al jugador por alias O por email
        player = self.app.repo.get_player_by_alias(alias_email) or self.app.repo.get_player_by_email(alias_email)
        if not player:
            self.app.banner.show("Usuario no registrado.", ERROR_COLOR)
            return
        # Verifica la contraseña (asume uso de hashing)
        if not player.verify_password(password):
            self.app.banner.show("Contraseña incorrecta.", ERROR_COLOR)
            return
        # Login exitoso: Muestra banner y cambia a la pantalla de juego
        self.app.banner.show(f"¡Hola {player.alias}!", SUCCESS_COLOR)
        self.app.set_screen(GameScreen(self.app, player))

    def request_password_reset(self):
        """Inicializa el modal de recuperación de contraseña."""
        # Desactiva los campos de login para enfocarse en el modal
        for box in self.inputs:
            box.set_active(False)
        self.recovery_modal = RecoveryModal(self.app, self)

    def handle_event(self, event: pygame.event.EventType):
        """Maneja eventos, priorizando el modal si está activo."""
        if self.recovery_modal:
            self.recovery_modal.handle_event(event)
            return
        # Manejo de eventos de los InputBox
        for box in self.inputs:
            result = box.handle_event(event)
            if result == "TAB":
                self._focus_next(box) #logica de foco
            elif result == "SUBMIT":
                self.attempt_login() #envio de formulario
        for button in self.buttons:
            button.handle_event(event)

    def update(self):
        """Actualiza el modal o los InputBox (si el modal no está activo)."""
        if self.recovery_modal:
            self.recovery_modal.update()
        else:
            for box in self.inputs:
                box.update()

    def draw(self, surface: pygame.Surface):
        self.draw_background(surface)
        title = TITLE_FONT.render("Iniciar sesión", True, TEXT_COLOR)
        surface.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 140)))

        labels = ["Alias o correo", "Contraseña"]
        for idx, label in enumerate(labels):
            text = SMALL_FONT.render(label, True, TEXT_COLOR)
            surface.blit(text, (self.inputs[idx].rect.x, self.inputs[idx].rect.y - 28))

        for box in self.inputs:
            box.draw(surface)
        for button in self.buttons:
            button.draw(surface)

        if self.recovery_modal:
            self.recovery_modal.draw(surface)


class RecoveryModal:
    """Modal de múltiples etapas para recuperar la contraseña (EMAIL -> CODE -> PASSWORD)."""
    def __init__(self, app: "GameApp", login_screen: "LoginScreen"):
        self.app = app
        self.login_screen = login_screen
        self.stage = "EMAIL"  # EMAIL -> CODE -> PASSWORD
        self.email_input = InputBox((WINDOW_WIDTH // 2) - 200, 250, 400, 48, placeholder="Correo registrado")
        self.code_input = InputBox((WINDOW_WIDTH // 2) - 150, 250, 300, 48, placeholder="Código de recuperación")
        self.password_input = InputBox((WINDOW_WIDTH // 2) - 200, 250, 400, 48, placeholder="Nueva contraseña", password=True)
        self.confirm_password_input = InputBox((WINDOW_WIDTH // 2) - 200, 320, 400, 48, placeholder="Confirmar contraseña", password=True)
        self.inputs = [
            self.email_input,
            self.code_input,
            self.password_input,
            self.confirm_password_input,
        ]
        self.visible = True
        self.sent_code: Optional[str] = None
        self.code_expires_at: Optional[int] = None

        self.email_input.set_active(True)

        self.buttons = [
            Button(pygame.Rect((WINDOW_WIDTH // 2) - 150, 420, 160, 48), "Enviar código", self.send_code),
            Button(pygame.Rect((WINDOW_WIDTH // 2) + 10, 420, 160, 48), "Cancelar", self.close),
        ]

    def close(self):
        """Cierra el modal y restablece el estado."""
        self._reset_state()
        self.visible = False
        self.login_screen.recovery_modal = None
        self.login_screen.recovery_code_sent = False

    def _generate_code(self) -> str:
        """Genera un código aleatorio de 6 dígitos."""
        return f"{random.randint(0, 999999):06d}"

    def _reset_state(self):
        self.stage = "EMAIL"
        self.sent_code = None
        self.code_expires_at = None
        self.email_input.text = ""
        self.code_input.text = ""
        self.password_input.text = ""
        self.confirm_password_input.text = ""
        for box in self.inputs:
            box._render_text()
            box.set_active(False)
        self.email_input.set_active(True)
        # Restablece el botón de acción a "Enviar código"
        self.buttons[0] = Button(pygame.Rect((WINDOW_WIDTH // 2) - 150, 420, 160, 48), "Enviar código", self.send_code)

    def send_code(self):
        """Busca el correo del jugador y envía el código de recuperación."""
        email = self.email_input.text.strip()
        if not email:
            self.app.banner.show("Ingresa el correo registrado.", ERROR_COLOR)
            return

        player = self.app.repo.get_player_by_email(email)
        if not player:
            self.app.banner.show("Correo no encontrado.", ERROR_COLOR)
            return

        self.sent_code = f"{random.randint(0, 999999):06d}"
        self.code_expires_at = pygame.time.get_ticks() + 5 * 60 * 1000
        try:
            self.app.email_sender.enviar_codigo_recuperacion(email, self.sent_code)
        except Exception as error:
            self.app.banner.show(f"No se pudo enviar el código: {error}", ERROR_COLOR)
            return

        self.app.banner.show("Código enviado. Revisa tu correo.", SUCCESS_COLOR)
        self.stage = "CODE"
        self.login_screen.recovery_code_sent = True
        self.email_input.set_active(False)
        self.code_input.set_active(True)
        self.buttons[0] = Button(pygame.Rect((WINDOW_WIDTH // 2) - 150, 420, 160, 48), "Validar código", self.validate_code)

    def validate_code(self):
        if not self.sent_code or not self.code_expires_at:
            self.app.banner.show("Primero solicita un código.", ERROR_COLOR)
            return
        
        if pygame.time.get_ticks() > self.code_expires_at:
            self.app.banner.show("El código ha expirado, solicita uno nuevo.", ERROR_COLOR)
            self.stage = "EMAIL"
            self.code_input.set_active(False)
            self.email_input.set_active(True)
            self.buttons[0] = Button(pygame.Rect((WINDOW_WIDTH // 2) - 150, 420, 160, 48), "Enviar código", self.send_code)
            return

        code = self.code_input.text.strip()
        if code != self.sent_code:
            self.app.banner.show("Código incorrecto.", ERROR_COLOR)
            return

        self.app.banner.show("Código validado. Ingresa la nueva contraseña.", SUCCESS_COLOR)
        self.stage = "PASSWORD"
        self.code_input.set_active(False)
        self.password_input.set_active(True)
        self.buttons[0] = Button(pygame.Rect((WINDOW_WIDTH // 2) - 150, 420, 160, 48), "Guardar", self.save_new_password)

    def save_new_password(self):
        """Valida la nueva contraseña y la guarda en el repositorio."""
        new_password = self.password_input.text.strip()
        confirm_password = self.confirm_password_input.text.strip()

        if new_password != confirm_password:
            self.app.banner.show("Las contraseñas no coinciden.", ERROR_COLOR)
            return

        email = self.email_input.text.strip()

        try:
            Validator.validate_password_strength(new_password)
        except ValueError as error:
            self.app.banner.show(str(error), ERROR_COLOR)
            return
        
        self.app.repo.reload_players()
        player = self.app.repo.get_player_by_email(email)
        if player:
            player.set_password(new_password)
            self.app.repo.update_player_info(player)
            self.app.banner.show("Contraseña actualizada.", SUCCESS_COLOR)
            self.close()
        else:
            self.app.banner.show("No se pudo actualizar la contraseña. Verifica el correo.", ERROR_COLOR)

    def handle_event(self, event: pygame.event.EventType):
        if not self.visible:
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
            return

        if self.stage == "EMAIL":
            result = self.email_input.handle_event(event)
            if result == "SUBMIT":
                self.send_code()
        elif self.stage == "CODE":
            result = self.code_input.handle_event(event)
            if result == "SUBMIT":
                self.validate_code()
        elif self.stage == "PASSWORD":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                self.password_input.set_active(not self.password_input.active)
                self.confirm_password_input.set_active(not self.confirm_password_input.active)
            else:
                result1 = self.password_input.handle_event(event)
                result2 = self.confirm_password_input.handle_event(event)
                if result1 == "SUBMIT" or result2 == "SUBMIT":
                    self.save_new_password()

        for button in self.buttons:
            button.handle_event(event)

    def update(self):
        if not self.visible:
            return

        for input_box in self.inputs:
            input_box.update()

        if self.stage == "CODE" and self.code_expires_at and pygame.time.get_ticks() > self.code_expires_at:
            self.stage = "EMAIL"
            self.app.banner.show("El código expiró.", ERROR_COLOR)
            self.buttons[0] = Button(pygame.Rect((WINDOW_WIDTH // 2) - 150, 420, 160, 48), "Enviar código", self.send_code)

    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return

        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        modal_rect = pygame.Rect((WINDOW_WIDTH // 2) - 250, 180, 500, 360)
        pygame.draw.rect(surface, PANEL_COLOR, modal_rect, border_radius=12)
        pygame.draw.rect(surface, BORDER_COLOR, modal_rect, 2, border_radius=12)

        if self.stage == "EMAIL":
            title = TITLE_FONT.render("Recuperar contraseña", True, TEXT_COLOR)
            surface.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 210)))
            info = SMALL_FONT.render("Ingresa tu correo para recibir un código.", True, TEXT_COLOR)
            surface.blit(info, info.get_rect(center=(WINDOW_WIDTH // 2, 260)))
            self.email_input.draw(surface)
        elif self.stage == "CODE":
            title = TITLE_FONT.render("Validar código", True, TEXT_COLOR)
            surface.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 210)))
            info = SMALL_FONT.render("Revisa tu correo e ingresa el código.", True, TEXT_COLOR)
            surface.blit(info, info.get_rect(center=(WINDOW_WIDTH // 2, 260)))
            self.code_input.draw(surface)
        elif self.stage == "PASSWORD":
            title = TITLE_FONT.render("Nueva contraseña", True, TEXT_COLOR)
            surface.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 210)))
            info = SMALL_FONT.render("Ingresa y confirma tu nueva contraseña.", True, TEXT_COLOR)
            surface.blit(info, info.get_rect(center=(WINDOW_WIDTH // 2, 260)))
            self.password_input.draw(surface)
            self.confirm_password_input.draw(surface)

        for button in self.buttons:
            button.draw(surface)


class RegisterScreen(BaseScreen, FileDialogHelperMixin):
    """Pantalla para el registro de nuevos jugadores (usa el Mixin para subir archivos)."""
    def __init__(self, app: "GameApp"):
        super().__init__(app)
        center_x = WINDOW_WIDTH // 2
        start_y = 150
        field_height = 48
        spacing = 70

        placeholders = [
            ("Alias", ""),
            ("Nombre completo", ""),
            ("Correo", ""),
            ("Contraseña", "", True),
            ("Imagen de perfil", "Ruta opcional"),
            ("Imagen de nave", "Ruta opcional"),
            ("Música favorita", "Separar por coma"),
        ]

        self.inputs: List[InputBox] = []
        for idx, data in enumerate(placeholders):
            placeholder, initial = data[0], data[1]
            password = data[2] if len(data) > 2 else False
            box = InputBox(center_x - 220, start_y + idx * spacing, 440, field_height, placeholder=placeholder, text=initial, password=password)
            self.inputs.append(box)
        self.inputs[0].set_active(True)

        self.upload_margin = 18
        self.upload_button_size = (170, 42)
        self.upload_buttons: List[Button] = []

        self.buttons = [
            Button(pygame.Rect(center_x - 220, start_y + len(self.inputs) * spacing, 200, 52), "Registrarse", self.register_player),
            Button(pygame.Rect(center_x + 20, start_y + len(self.inputs) * spacing, 200, 52), "Cancelar", lambda: app.set_screen(MainMenuScreen(app))),
        ]

        self.upload_buttons.extend(
            [
                Button(self._create_upload_rect(4), "Cargar imagen", lambda: self._open_file_dialog(4, ("Archivos PNG", "*.png"), ("Archivos JPG", "*.jpg;*.jpeg"), ("Todos", "*.*"))),
                Button(self._create_upload_rect(5), "Cargar nave", lambda: self._open_file_dialog(5, ("Archivos PNG", "*.png"), ("Archivos JPG", "*.jpg;*.jpeg"), ("Todos", "*.*"))),
                Button(self._create_upload_rect(6), "Cargar música", lambda: self._open_file_dialog_multiple(6, ("Archivos de audio", "*.mp3;*.wav;*.ogg"), ("Todos", "*.*"))),
            ]
        )

        self.buttons.extend(self.upload_buttons)

    def _focus_next(self, current: InputBox):
        if current not in self.inputs:
            return
        idx = self.inputs.index(current)
        next_idx = (idx + 1) % len(self.inputs)
        for box in self.inputs:
            box.set_active(False)
        self.inputs[next_idx].set_active(True)

    def register_player(self):
        """Recoge los datos del formulario y llama al PlayerService para registrarlos."""
        values = [box.text.strip() for box in self.inputs]
        alias, full_name, email, password, profile_picture, spaceship_image, favorite_music = values
        music_list = [m.strip() for m in favorite_music.split(",") if m.strip()]

        try:
            jugador = self.app.service.registrar_jugador(
                alias=alias,
                full_name=full_name,
                email=email,
                password=password,
                profile_picture=profile_picture,
                spaceship_image=spaceship_image,
                favorite_music=music_list,
            )
        except ValueError as error:
            self.app.banner.show(str(error), ERROR_COLOR)
            return
        except Exception as error:  # Captura errores externos (como envío de correo)
            self.app.banner.show(f"Error al registrar: {error}", ERROR_COLOR)
            return

        self.app.banner.show(f"Registro exitoso. Confirma tu correo: {jugador['email']}", SUCCESS_COLOR)
        self.app.set_screen(MainMenuScreen(self.app))

    def handle_event(self, event: pygame.event.EventType):
        for box in self.inputs:
            result = box.handle_event(event)
            if result == "TAB":
                self._focus_next(box)
            elif result == "SUBMIT":
                self.register_player()
        for button in self.buttons:
            button.handle_event(event)

    def update(self):
        for box in self.inputs:
            box.update()

    def draw(self, surface: pygame.Surface):
        self.draw_background(surface)
        title = TITLE_FONT.render("Registro de jugador", True, TEXT_COLOR)
        surface.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 90)))

        for box in self.inputs:
            label_text = SMALL_FONT.render(box.placeholder, True, TEXT_COLOR)
            surface.blit(label_text, (box.rect.x, box.rect.y - 28))
            box.draw(surface)

        helper_text = SMALL_FONT.render("Puedes cargar archivos o escribir rutas manualmente.", True, (180, 180, 180))
        surface.blit(helper_text, (WINDOW_WIDTH // 2 - helper_text.get_width() // 2, self.inputs[-1].rect.bottom + 16))

        for button in self.buttons:
            button.draw(surface)


class GameScreen(BaseScreen):
    """área de juego después del login exitoso."""
    def __init__(self, app: "GameApp", player: Player):
        super().__init__(app)
        self.player = player
        center_x = WINDOW_WIDTH // 2
        start_y = 240
        spacing = 70
        self.buttons = [
            Button(pygame.Rect(center_x - 170, start_y, 340, 55), "Jugar", lambda: app.set_screen(GameMenuScreen(app, self.player))),
            Button(pygame.Rect(center_x - 170, start_y + spacing, 340, 55), "Ver perfil", lambda: app.set_screen(ProfileScreen(app, self.player))),
            Button(pygame.Rect(center_x - 170, start_y + spacing * 2, 340, 55), "Editar perfil", lambda: app.set_screen(EditProfileScreen(app, self.player))),
            Button(pygame.Rect(center_x - 170, start_y + spacing * 3, 340, 55), "Cerrar sesión", lambda: app.set_screen(MainMenuScreen(app))),
        ]

    def handle_event(self, event: pygame.event.EventType):
        for button in self.buttons:
            button.handle_event(event)

    def draw(self, surface: pygame.Surface):
        self.draw_background(surface)
        title = TITLE_FONT.render("Área de juego", True, TEXT_COLOR)
        welcome = FONT.render(f"Bienvenido {self.player.alias}!", True, TEXT_COLOR)
        surface.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 150)))
        surface.blit(welcome, welcome.get_rect(center=(WINDOW_WIDTH // 2, 210)))
        for button in self.buttons:
            button.draw(surface)


class GameMenuScreen(BaseScreen):
    def __init__(self, app: "GameApp", player: Player):
        super().__init__(app)
        self.player = player
        center_x = WINDOW_WIDTH // 2
        start_y = 260
        spacing = 70
        self.buttons = [
            Button(pygame.Rect(center_x - 170, start_y, 340, 55), "Iniciar Partida", lambda: app.set_screen(SelectDifficultyScreen(app, self.player))),
            Button(pygame.Rect(center_x - 170, start_y + spacing, 340, 55), "Salón de la Fama", lambda: app.set_screen(HallOfFameScreen(app, self.player))),
            Button(pygame.Rect(center_x - 170, start_y + spacing * 2, 340, 55), "Configuraciones", lambda: app.set_screen(ConfigurationsScreen(app, self.player))),
            Button(pygame.Rect(center_x - 170, start_y + spacing * 3, 340, 55), "Iniciar Jugador 2", lambda: app.set_screen(Player2SetupScreen(app, self.player))),
            Button(pygame.Rect(center_x - 170, start_y + spacing * 4, 340, 55), "Volver", lambda: app.set_screen(GameScreen(app, self.player))),
        ]

    def handle_event(self, event: pygame.event.EventType):
        for button in self.buttons:
            button.handle_event(event)

    def draw(self, surface: pygame.Surface):
        self.draw_background(surface)
        title = TITLE_FONT.render("Menú de juego", True, TEXT_COLOR)
        surface.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 150)))
        for button in self.buttons:
            button.draw(surface)
class SelectDifficultyScreen(BaseScreen):
    def __init__(self, app: "GameApp", player: Player):
        super().__init__(app)
        self.player = player
        center_x = WINDOW_WIDTH // 2
        start_y = 260
        spacing = 100
        self.difficulty_names = ["RECLUTA (Fácil)", "SARGENTO (Normal)", "COMANDANTE (Difícil)"]
        self.selected = 1
        self.buttons = [
            Button(pygame.Rect(center_x - 170, start_y + spacing * 3, 340, 55), "Confirmar", self.start_game),
            Button(pygame.Rect(center_x - 170, start_y + spacing * 4, 340, 55), "Volver", lambda: app.set_screen(GameMenuScreen(app, self.player))),
        ]
    def start_game(self):
        if MOTOR_JUEGO_AVAILABLE:
            self.app.set_screen(GamePlayScreen(self.app, self.player, self.selected))
        else:
            self.app.banner.show("Error: Motor del juego no disponible", ERROR_COLOR)
    def handle_event(self, event: pygame.event.EventType):
        # Soporte de teclado y joystick: cambiar selección con flechas/WASD y confirmar con botón 0
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.difficulty_names)
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.difficulty_names)
        elif event.type == pygame.JOYBUTTONDOWN:
            # botón 0 = confirmar selección
            try:
                if event.button == 0:
                    self.start_game()
                    return
            except Exception as e:
                print(f"Error manejando JOYBUTTONDOWN en SelectDifficulty: {e}")

        for button in self.buttons:
            button.handle_event(event)
    def draw(self, surface: pygame.Surface):
        self.draw_background(surface)
        title = TITLE_FONT.render("Seleccionar Dificultad", True, TEXT_COLOR)
        surface.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 100)))

        colors = [SUCCESS_COLOR, (255, 255, 100), ERROR_COLOR]
        descriptions = ["Enemigos lentos, patrones predecibles", "Velocidad estándar, patrones variados", "Enemigos rápidos, patrones complejos"]

        for i, name in enumerate(self.difficulty_names):
            color = ACCENT_HOVER if i == self.selected else TEXT_COLOR
            text = FONT.render(name, True, color)
            surface.blit(text, text.get_rect(center=(WINDOW_WIDTH // 2, 220 + i * 60)))
            
            desc = SMALL_FONT.render(descriptions[i], True, (180, 180, 180))
            surface.blit(desc, desc.get_rect(center=(WINDOW_WIDTH // 2, 250 + i * 60)))

        for button in self.buttons:
            button.draw(surface)
class HallOfFameScreen(BaseScreen):
    def __init__(self, app: "GameApp", player: Player):
        super().__init__(app)
        self.player = player
        self.back_button = Button(pygame.Rect((WINDOW_WIDTH // 2) - 170, 600, 340, 55), "Volver", lambda: app.set_screen(GameMenuScreen(app, self.player)))

    def handle_event(self, event: pygame.event.EventType):
        self.back_button.handle_event(event)

    def draw(self, surface: pygame.Surface):
        self.draw_background(surface)
        title = TITLE_FONT.render("Salón de la Fama", True, TEXT_COLOR)
        surface.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 150)))

        message = FONT.render("Salón de la Fama en desarrollo", True, (255, 215, 0))
        surface.blit(message, message.get_rect(center=(WINDOW_WIDTH // 2, 350)))

        self.back_button.draw(surface)
class ConfigurationsScreen(BaseScreen):
    def __init__(self, app: "GameApp", player: Player):
        super().__init__(app)
        self.player = player
        self.back_button = Button(pygame.Rect((WINDOW_WIDTH // 2) - 170, 600, 340, 55), "Volver", lambda: app.set_screen(GameMenuScreen(app, self.player)))

    def handle_event(self, event: pygame.event.EventType):
        self.back_button.handle_event(event)

    def draw(self, surface: pygame.Surface):
        self.draw_background(surface)
        title = TITLE_FONT.render("Configuraciones", True, TEXT_COLOR)
        surface.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 150)))

        message = FONT.render("Configuraciones en desarrollo", True, ACCENT_HOVER)
        surface.blit(message, message.get_rect(center=(WINDOW_WIDTH // 2, 350)))

        self.back_button.draw(surface)

class Player2SetupScreen(BaseScreen):
    def __init__(self, app: "GameApp", player: Player):
        super().__init__(app)
        self.player = player
        center_x = WINDOW_WIDTH // 2
        self.player2_input = InputBox(center_x - 180, 350, 360, 48, placeholder="Alias del Jugador 2")
        self.player2_input.set_active(True)
        self.error_message = ""
        
        self.buttons = [
            Button(pygame.Rect(center_x - 150, 450, 160, 45), "Confirmar", self.confirm_player2),
            Button(pygame.Rect(center_x + 10, 450, 160, 45), "Volver", lambda: app.set_screen(GameMenuScreen(app, self.player))),
        ]

    def confirm_player2(self):
        player2_name = self.player2_input.text.strip()
        if not player2_name:
            self.error_message = "El alias no puede estar vacío"
            return
        if player2_name.upper() == self.player.alias.upper():
            self.error_message = "No puede ser igual al alias del Jugador 1"
            return
        if len(player2_name) > 10:
            self.error_message = "El alias no puede exceder 10 caracteres"
            return
        
        self.app.player2_alias = player2_name
        self.app.banner.show(f"Jugador 2 configurado: {player2_name}", SUCCESS_COLOR)
        self.app.set_screen(GameMenuScreen(self.app, self.player))

    def handle_event(self, event: pygame.event.EventType):
        self.player2_input.handle_event(event)
        for button in self.buttons:
            button.handle_event(event)

    def update(self):
        self.player2_input.update()

    def draw(self, surface: pygame.Surface):
        self.draw_background(surface)
        title = TITLE_FONT.render("Configurar Jugador 2", True, TEXT_COLOR)
        surface.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 100)))

        player1_info = SMALL_FONT.render(f"Jugador 1: {self.player.alias}", True, TEXT_COLOR)
        surface.blit(player1_info, (WINDOW_WIDTH // 2 - player1_info.get_width() // 2, 220))

        label = SMALL_FONT.render("Ingresa alias para Jugador 2:", True, TEXT_COLOR)
        surface.blit(label, (self.player2_input.rect.x, self.player2_input.rect.y - 28))

        self.player2_input.draw(surface)

        if self.error_message:
            error_text = SMALL_FONT.render(self.error_message, True, ERROR_COLOR)
            surface.blit(error_text, (WINDOW_WIDTH // 2 - error_text.get_width() // 2, 420))

        for button in self.buttons:
            button.draw(surface)


class GamePlayScreen(BaseScreen):
    def __init__(self, app: "GameApp", player: Player, difficulty: int):
        super().__init__(app)
        self.player = player
        self.difficulty = difficulty
        self.game_engine = None
        self.original_surface = app.screen
        self.original_size = (WINDOW_WIDTH, WINDOW_HEIGHT)
        self.fullscreen_surface = None
        self.initialized = False
        self.error_message = ""
        self.exit_button = None
        self.config_button: Optional[Button] = None
        self.menu_exit_button: Optional[Button] = None
        self.pause_button: Optional[Button] = None
        self.volume_down_button: Optional[Button] = None
        self.volume_up_button: Optional[Button] = None
        self.menu_buttons: List[Button] = []
        self.menu_rect = pygame.Rect(0, 0, 0, 0)
        self.show_menu = False
        self.paused = False
        self._init_game()
        self._setup_exit_button()
        self._setup_menu_controls()
        self._setup_config_button()
        self._position_menu_elements()

    def _setup_config_button(self):
        if not self.initialized:
            return
        self.config_button = Button(pygame.Rect(0, 0, 0, 0), "Menú", self.toggle_menu)
        self.config_button.rect.topleft = (40, 40)

    def _init_game(self):
        if not MOTOR_JUEGO_AVAILABLE:
            self.error_message = "Motor del juego no disponible"
            return
        
        try:
            fullscreen_width = pygame.display.Info().current_w
            fullscreen_height = pygame.display.Info().current_h
            self.fullscreen_surface = pygame.display.set_mode((fullscreen_width, fullscreen_height), pygame.FULLSCREEN)
            
            nombre_j1 = self.player.alias
            nombre_j2 = self.app.player2_alias or "Jugador2"
            canciones = self.player._favorite_music or []
            spaceship_image = getattr(self.player, "_spaceship_image", "")
            
            self.game_engine = MotorJuego(self.fullscreen_surface, nombre_j1, nombre_j2, canciones, spaceship_image_path=spaceship_image)
            self.app.screen = self.fullscreen_surface
            self.initialized = True
            
            pygame.mixer.stop()
            self.app.play_background_music(self.player)
        except Exception as e:
            self.error_message = f"Error al iniciar juego: {str(e)}"
            print(f"Error al iniciar MotorJuego: {e}")
            import traceback
            traceback.print_exc()

    def _setup_exit_button(self):
        self.exit_button = None

    def _setup_menu_controls(self):
        info = pygame.display.Info()
        menu_width = 480
        menu_height = 360
        center_x = info.current_w // 2
        center_y = info.current_h // 2
        self.menu_rect = pygame.Rect(center_x - menu_width // 2, center_y - menu_height // 2, menu_width, menu_height)
        self.pause_button = Button(pygame.Rect(0, 0, 0, 0), "Pausar", self.toggle_pause)
        self.volume_down_button = Button(pygame.Rect(0, 0, 0, 0), "Vol -", self.decrease_volume)
        self.volume_up_button = Button(pygame.Rect(0, 0, 0, 0), "Vol +", self.increase_volume)
        self.menu_exit_button = Button(pygame.Rect(0, 0, 0, 0), "Salir", self.exit_game)
        self.menu_buttons = [
            self.pause_button,
            self.volume_down_button,
            self.volume_up_button,
            self.menu_exit_button,
        ]
        self._position_menu_elements()

    def _position_menu_elements(self):
        if not self.menu_rect.width:
            return
        top = self.menu_rect.y + 90
        if self.pause_button:
            self.pause_button.rect.centerx = self.menu_rect.centerx
            self.pause_button.rect.y = top
        if self.volume_down_button and self.volume_up_button:
            volume_center_y = self.menu_rect.y + 220
            self.volume_down_button.rect.centery = volume_center_y
            self.volume_down_button.rect.right = self.menu_rect.centerx - 120
            self.volume_up_button.rect.centery = volume_center_y
            self.volume_up_button.rect.left = self.menu_rect.centerx + 120
        if self.menu_exit_button:
            self.menu_exit_button.rect.centerx = self.menu_rect.centerx
            self.menu_exit_button.rect.y = self.menu_rect.y + self.menu_rect.height - self.menu_exit_button.rect.height - 70

    def toggle_menu(self):
        self.show_menu = not self.show_menu
        self._position_menu_elements()

    def toggle_pause(self):
        self.paused = not self.paused
        if self.pause_button:
            self.pause_button.set_text("Reanudar" if self.paused else "Pausar")
            self._position_menu_elements()
        if self.paused:
            self.app.pause_background_music()
        else:
            self.app.resume_background_music()

    def increase_volume(self):
        self.app.set_music_volume(self.app.music_volume + 0.1)

    def decrease_volume(self):
        self.app.set_music_volume(self.app.music_volume - 0.1)

    def handle_event(self, event: pygame.event.EventType):
        if not self.initialized or not self.game_engine:
            return

        # Soporte de gamepad: botón 7 (Start) para alternar menú/pausa
        if event.type == pygame.JOYBUTTONDOWN:
            try:
                if event.button == 7:
                    self.toggle_menu()
                    return
            except Exception:
                pass

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.toggle_menu()
            return

        if self.config_button:
            self.config_button.handle_event(event)

        if self.show_menu:
            for button in self.menu_buttons:
                if button:
                    button.handle_event(event)
            return

        if self.exit_button:
            self.exit_button.handle_event(event)

        if self.paused or self.app.music_paused:
            return

        if not self.game_engine.manejar_eventos(event):
            self.exit_game()

    def update(self):
        if not self.initialized or not self.game_engine:
            return

        if self.paused or self.show_menu or self.app.music_paused:
            return

        self.game_engine.actualizar()

    def draw(self, surface: pygame.Surface):
        if not self.initialized:
            self.draw_background(surface)
            error_text = FONT.render(self.error_message or "Iniciando juego...", True, ERROR_COLOR if self.error_message else TEXT_COLOR)
            surface.blit(error_text, error_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)))
            return
        
        if self.game_engine:
            self.game_engine.dibujar()
            
            if self.exit_button:
                self.exit_button.draw(surface)
            if self.config_button:
                self.config_button.draw(surface)
            if self.show_menu:
                self._draw_menu(surface)

    def _draw_menu(self, surface: pygame.Surface):
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        surface.blit(overlay, (0, 0))
        pygame.draw.rect(surface, PANEL_COLOR, self.menu_rect, border_radius=12)
        pygame.draw.rect(surface, ACCENT_COLOR, self.menu_rect, width=3, border_radius=12)
        title = FONT.render("Configuración", True, TEXT_COLOR)
        surface.blit(title, title.get_rect(center=(self.menu_rect.centerx, self.menu_rect.y + 50)))
        volume_label = SMALL_FONT.render(f"Volumen: {int(self.app.music_volume * 100)}%", True, TEXT_COLOR)
        surface.blit(volume_label, volume_label.get_rect(center=(self.menu_rect.centerx, self.menu_rect.y + 160)))
        for button in self.menu_buttons:
            if button:
                button.draw(surface)

    def exit_game(self):
        try:
            self.app.screen = pygame.display.set_mode(self.original_size)
            pygame.display.set_caption("Mi Juego - Pygame")
        except Exception as e:
            print(f"Error al restaurar pantalla: {e}")
        self.app.set_screen(GameMenuScreen(self.app, self.player))
        self.app.play_background_music(self.player)


class ProfileScreen(BaseScreen):
    def __init__(self, app: "GameApp", player: Player):
        super().__init__(app)
        self.player = player
        self.back_button = Button(pygame.Rect(60, 600, 180, 48), "Volver", lambda: app.set_screen(GameScreen(app, self.player)))

    def handle_event(self, event: pygame.event.EventType):
        self.back_button.handle_event(event)

    def draw(self, surface: pygame.Surface):
        self.draw_background(surface)
        title = TITLE_FONT.render("Mi perfil", True, TEXT_COLOR)
        surface.blit(title, (60, 60))

        info_lines = [
            f"ID: {self.player._id}",
            f"Alias: {self.player.alias}",
            f"Nombre completo: {self.player._full_name}",
            f"Correo: {self.player.email}",
            f"Imagen de perfil: {self.player._profile_picture or 'No configurada'}",
            f"Imagen de nave: {self.player._spaceship_image or 'No configurada'}",
        ]

        if self.player._favorite_music:
            info_lines.append("Música favorita:")
            info_lines.extend([f" - {music}" for music in self.player._favorite_music])
        else:
            info_lines.append("Música favorita: No configurada")

        y = 140
        for line in info_lines:
            text = SMALL_FONT.render(line, True, TEXT_COLOR)
            surface.blit(text, (20, y))
            y += 32

        self.back_button.draw(surface)


class EditProfileScreen(BaseScreen, FileDialogHelperMixin):
    def __init__(self, app: "GameApp", player: Player):
        super().__init__(app)
        self.player = player
        center_x = WINDOW_WIDTH // 2
        start_y = 140
        spacing = 68

        field_data = [
            ("Alias", self.player.alias),
            ("Nombre completo", self.player._full_name),
            ("Correo", self.player.email),
            ("Imagen de perfil", self.player._profile_picture),
            ("Imagen de nave", self.player._spaceship_image),
            ("Música favorita", ", ".join(self.player._favorite_music)),
        ]

        self.inputs: List[InputBox] = []
        for idx, (placeholder, initial) in enumerate(field_data):
            box = InputBox(center_x - 220, start_y + spacing * idx, 440, 48, placeholder=placeholder, text=initial)
            self.inputs.append(box)
        self.inputs[0].set_active(True)

        self.upload_margin = 18
        self.upload_button_size = (170, 42)
        self.upload_buttons: List[Button] = []

        self.buttons = [
            Button(pygame.Rect(center_x - 220, start_y + spacing * len(self.inputs), 200, 52), "Guardar", self.save_changes),
            Button(pygame.Rect(center_x + 20, start_y + spacing * len(self.inputs), 200, 52), "Cancelar", lambda: app.set_screen(GameScreen(app, self.player))),
        ]

        self.upload_buttons.extend(
            [
                Button(self._create_upload_rect(3), "Cargar imagen", lambda: self._open_file_dialog(3, ("Archivos PNG", "*.png"), ("Archivos JPG", "*.jpg;*.jpeg"), ("Todos", "*.*"))),
                Button(self._create_upload_rect(4), "Cargar nave", lambda: self._open_file_dialog(4, ("Archivos PNG", "*.png"), ("Archivos JPG", "*.jpg;*.jpeg"), ("Todos", "*.*"))),
                Button(self._create_upload_rect(5), "Cargar música", lambda: self._open_file_dialog_multiple(5, ("Archivos de audio", "*.mp3;*.wav;*.ogg"), ("Todos", "*.*"))),
            ]
        )

        self.buttons.extend(self.upload_buttons)

    def _focus_next(self, current: InputBox):
        if current not in self.inputs:
            return
        idx = self.inputs.index(current)
        next_idx = (idx + 1) % len(self.inputs)
        for box in self.inputs:
            box.set_active(False)
        self.inputs[next_idx].set_active(True)

    def save_changes(self):
        alias = self.inputs[0].text.strip()
        full_name = self.inputs[1].text.strip()
        email = self.inputs[2].text.strip()
        profile_picture = self.inputs[3].text.strip()
        spaceship_image = self.inputs[4].text.strip()
        favorite_music = [m.strip() for m in self.inputs[5].text.split(",") if m.strip()]

        try:
            updated_player = self.app.service.actualizar_jugador(
                player_id=self.player._id,
                alias=alias,
                full_name=full_name,
                email=email,
                profile_picture=profile_picture,
                spaceship_image=spaceship_image,
                favorite_music=favorite_music,
            )
        except ValueError as error:
            self.app.banner.show(str(error), ERROR_COLOR)
            return
        except Exception as error:
            self.app.banner.show(f"Error al actualizar: {error}", ERROR_COLOR)
            return

        self.app.banner.show("Información actualizada correctamente.", SUCCESS_COLOR)
        self.app.set_screen(GameScreen(self.app, updated_player))

    def handle_event(self, event: pygame.event.EventType):
        for box in self.inputs:
            result = box.handle_event(event)
            if result == "TAB":
                self._focus_next(box)
            elif result == "SUBMIT":
                self.save_changes()
        for button in self.buttons:
            button.handle_event(event)

    def update(self):
        for box in self.inputs:
            box.update()

    def draw(self, surface: pygame.Surface):
        self.draw_background(surface)
        title = TITLE_FONT.render("Editar perfil", True, TEXT_COLOR)
        surface.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 80)))

        for box in self.inputs:
            label_text = SMALL_FONT.render(box.placeholder, True, TEXT_COLOR)
            surface.blit(label_text, (box.rect.x, box.rect.y - 28))
            box.draw(surface)

        for button in self.buttons:
            button.draw(surface)

# ================== APLICACIÓN PRINCIPAL ==================
class GameApp:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Mi Juego - Pygame")
        self.space_background = SpaceBackground(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.clock = pygame.time.Clock()
        self.running = True

        # Inicialización de repositorio y servicios 
        self.repo = PlayerRepository("data/players.json")
        self.email_sender = EmailSender(
            api_key="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",
            remitente={"email": "melmontoya245@gmail.com", "name": "Mi Juego"},
        )
        self.service = PlayerService(self.repo, self.email_sender)

        self.banner = MessageBanner()
        self.current_screen: BaseScreen = MainMenuScreen(self)
        self.player2_alias: Optional[str] = None
        self.current_music_path: Optional[str] = None
        self.current_music_channel: Optional[pygame.mixer.Channel] = None
        self.music_volume: float = 0.6
        self.music_paused: bool = False

    def _get_default_music_path(self) -> Optional[str]:
        base_path = Path(__file__).parent
        possible_paths = [
            base_path / "Jugabilidad" / "Base" / "assets" / "sounds" / "musica_fondo.mp3",
            base_path / "Jugabilidad" / "Base" / "assets" / "sounds" / "musica_fondo.ogg",
            base_path / "Jugabilidad" / "Base" / "assets" / "sounds" / "musica_fondo.wav",
            base_path / "Jugabilidad" / "Base" / "assets" / "sounds" / "musica_fondo.mp4",
        ]
        for path in possible_paths:
            if path.exists():
                print(f"[Música] Encontrado: {path.name}")
                if str(path).lower().endswith('.mp4'):
                    converted = self._convert_mp4_to_mp3(str(path))
                    if converted:
                        print(f"[Música] Usando convertido: {converted}")
                        return converted
                else:
                    print(f"[Música] Usando: {path}")
                    return str(path)
        print("[Música] No se encontró archivo de música por defecto")
        return None

    def _convert_mp4_to_mp3(self, mp4_path: str) -> Optional[str]:
        mp3_path = mp4_path.replace('.mp4', '.mp3').replace('.MP4', '.mp3')
        if Path(mp3_path).exists():
            return mp3_path
        
        try:
            import subprocess
            import shutil
            if shutil.which('ffmpeg'):
                result = subprocess.run(
                    ['ffmpeg', '-i', mp4_path, '-q:a', '5', '-y', mp3_path],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                if result.returncode == 0 and Path(mp3_path).exists():
                    print(f"✓ Convertido: {Path(mp3_path).name}")
                    return mp3_path
        except:
            pass
        
        return None

    def _convert_mp4_to_ogg(self, mp4_path: str) -> Optional[str]:
        ogg_path = mp4_path.replace('.mp4', '.ogg').replace('.MP4', '.ogg')
        if Path(ogg_path).exists():
            return ogg_path
        
        try:
            from moviepy.editor import VideoFileClip
            print(f"Convirtiendo {mp4_path} a OGG con moviepy...")
            video = VideoFileClip(mp4_path)
            audio = video.audio
            audio.write_audiofile(ogg_path, verbose=False, logger=None)
            video.close()
            print(f"✓ Conversión completada: {ogg_path}")
            return ogg_path
        except Exception as e:
            print(f"moviepy no disponible: {e}")
        
        try:
            import subprocess
            import shutil
            if shutil.which('ffmpeg'):
                print(f"Convirtiendo {mp4_path} a OGG con ffmpeg...")
                result = subprocess.run(
                    ['ffmpeg', '-i', mp4_path, '-vn', '-acodec', 'libvorbis', '-q:a', '9', '-y', ogg_path],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if result.returncode == 0 and Path(ogg_path).exists():
                    print(f"✓ Conversión completada con ffmpeg: {ogg_path}")
                    return ogg_path
        except Exception as e:
            print(f"ffmpeg no disponible: {e}")
        
        print(f"⚠ No se pudo convertir {mp4_path}. Instala: pip install moviepy")
        return None

    def play_background_music(self, player: Optional[Player] = None):
        try:
            pygame.mixer.music.stop()
            self.music_paused = False
            
            music_path = None
            supported_formats = ('.mp3', '.ogg', '.wav')
            
            if player and player._favorite_music:
                print(f"[Música] Buscando música favorita: {player._favorite_music}")
                for music_file in player._favorite_music:
                    if Path(music_file).exists() and music_file.lower().endswith(supported_formats):
                        music_path = music_file
                        print(f"[Música] Usando música favorita: {music_file}")
                        break
            
            if not music_path:
                print("[Música] Buscando música por defecto...")
                music_path = self._get_default_music_path()
            
            if music_path:
                print(f"[Música] Ruta final: {music_path}")
                print(f"[Música] Existe: {Path(music_path).exists()}")
                print(f"[Música] Formato válido: {music_path.lower().endswith(supported_formats)}")
            
            if music_path and Path(music_path).exists() and music_path.lower().endswith(supported_formats):
                current_path = getattr(self, 'current_music_path', None)
                if current_path != music_path:
                    try:
                        print(f"[Música] Cargando: {music_path}")
                        pygame.mixer.music.load(music_path)
                        pygame.mixer.music.set_volume(getattr(self, 'music_volume', 1.0))
                        pygame.mixer.music.play(-1)
                        self.music_paused = False
                        self.current_music_path = music_path
                        print(f"✓ Música reproduciendo: {Path(music_path).name}")
                    except Exception as e:
                        print(f"[Música] Error al reproducir: {e}")
            else:
                print("[Música] No hay música para reproducir")
        except Exception as e:
            print(f"[Música] Error general: {e}")

    def stop_background_music(self):
        try:
            if hasattr(self, 'current_music_channel') and self.current_music_channel:
                self.current_music_channel.stop()
                self.current_music_channel = None
            pygame.mixer.music.stop()
            self.music_paused = False
            if hasattr(self, 'current_music_path'):
                self.current_music_path = None
        except Exception as e:
            print(f"Error al detener música: {e}")

    def pause_background_music(self):
        try:
            pygame.mixer.music.pause()
            self.music_paused = True
        except Exception as e:
            print(f"[Música] Error al pausar: {e}")

    def resume_background_music(self):
        try:
            pygame.mixer.music.unpause()
            pygame.mixer.music.set_volume(self.music_volume)
            self.music_paused = False
        except Exception as e:
            print(f"[Música] Error al reanudar: {e}")

    def set_music_volume(self, volume: float):
        try:
            clamped = max(0.0, min(1.0, volume))
            self.music_volume = clamped
            pygame.mixer.music.set_volume(self.music_volume)
            print(f"[Música] Volumen: {int(self.music_volume * 100)}%")
        except Exception as e:
            print(f"[Música] Error volumen: {e}")

    def set_screen(self, screen: BaseScreen):
        self.current_screen = screen

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.current_screen.handle_event(event)

            self.space_background.update(dt)
            self.current_screen.update()
            self.current_screen.draw(self.screen)
            self.banner.draw(self.screen)

            pygame.display.flip()

        pygame.quit()
        sys.exit()
def main():
    """Función principal que inicia la aplicación."""
    app = GameApp()
    app.set_screen(LoginScreen(app))
    app.run()


if __name__ == "__main__":
    main()