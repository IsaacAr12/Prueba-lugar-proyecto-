#motor_juego.py
import pygame
import sys
import os
import random

_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

try:
    from vistas.campo_batalla import CampoBatalla
    from vistas.interfaz_usuario import InterfazUsuario
    from modelos.jugador import Jugador
except ImportError as e:
    print(f"Error al importar módulos: {e}")
    CampoBatalla = None
    InterfazUsuario = None
    Jugador = None

_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(_script_dir)))
ASSET_BASE = os.path.join(_project_root, "Jugabilidad/Base")
SOUNDS_DIR = os.path.join(ASSET_BASE, "assets/sounds")
DEFAULT_SPACESHIP_IMAGE = os.path.join(ASSET_BASE, "assets/images/player_ship.png")
DEFAULT_BACKGROUND_MUSIC_MP4 = os.path.join(SOUNDS_DIR, "musica_fondo.mp4")
DEFAULT_BACKGROUND_MUSIC_WAV = os.path.join(SOUNDS_DIR, "musica_fondo.wav")
DEFAULT_BACKGROUND_MUSIC_OGG = os.path.join(SOUNDS_DIR, "musica_fondo.ogg")
FALLBACK_MUSIC = os.path.join(SOUNDS_DIR, "shot.wav")

def _convertir_mp4_a_wav():
    if os.path.isfile(DEFAULT_BACKGROUND_MUSIC_WAV):
        return DEFAULT_BACKGROUND_MUSIC_WAV
    if not os.path.isfile(DEFAULT_BACKGROUND_MUSIC_MP4):
        return None
    import subprocess
    try:
        result = subprocess.run(
            ['ffmpeg', '-i', DEFAULT_BACKGROUND_MUSIC_MP4, '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-y', DEFAULT_BACKGROUND_MUSIC_WAV],
            capture_output=True,
            text=True,
            timeout=120
        )
        if os.path.isfile(DEFAULT_BACKGROUND_MUSIC_WAV):
            print(f"✓ Música MP4 convertida a WAV")
            return DEFAULT_BACKGROUND_MUSIC_WAV
    except:
        pass
    return None

_DEFAULT_BACKGROUND_MUSIC = None
if os.path.isfile(DEFAULT_BACKGROUND_MUSIC_OGG):
    _DEFAULT_BACKGROUND_MUSIC = DEFAULT_BACKGROUND_MUSIC_OGG
elif os.path.isfile(DEFAULT_BACKGROUND_MUSIC_WAV):
    _DEFAULT_BACKGROUND_MUSIC = DEFAULT_BACKGROUND_MUSIC_WAV
else:
    _DEFAULT_BACKGROUND_MUSIC = _convertir_mp4_a_wav() or DEFAULT_BACKGROUND_MUSIC_WAV

DEFAULT_BACKGROUND_MUSIC = _DEFAULT_BACKGROUND_MUSIC

class MotorJuego:
    def __init__(self, pantalla, nombre_jugador1="Jugador1", nombre_jugador2="Jugador2", canciones_favoritas=None, spaceship_image_path=None):
        self.pantalla = pantalla
        self.reloj = pygame.time.Clock()
        self.ejecutando = True
        self.pantalla_completa = True
        # Inicializar joystick (si hay alguno conectado)
        try:
            pygame.joystick.init()
            self.joystick = None
            if pygame.joystick.get_count() > 0:
                joy = pygame.joystick.Joystick(0)
                joy.init()
                self.joystick = joy
                print(f"[MotorJuego] Joystick conectado: {joy.get_name()}, axes={joy.get_numaxes()}, botones={joy.get_numbuttons()}")
        except Exception as e:
            self.joystick = None
            print(f"[MotorJuego] Error inicializando joystick: {e}")
        
        info_pantalla = pygame.display.Info()
        self.ancho_pantalla = info_pantalla.current_w
        self.alto_pantalla = info_pantalla.current_h
        
        self.campo_batalla = CampoBatalla(self.pantalla, self.ancho_pantalla, self.alto_pantalla)
        self.interfaz_usuario = InterfazUsuario(self.pantalla, self.ancho_pantalla, self.alto_pantalla)
        self.spaceship_image_path = self._resolve_spaceship_image_path(spaceship_image_path)
        
        self.jugador1 = Jugador(nombre_jugador1)
        self.jugador2 = Jugador(nombre_jugador2) 
        self.jugador_activo = self.jugador1
        
        self.nave1 = self.campo_batalla.agregar_nave(self.ancho_pantalla // 2, self.alto_pantalla * 0.7, image_path=self.spaceship_image_path)
        
        self.canciones_favoritas = canciones_favoritas or []
        self.volumen_musica = 0.5
        self._init_musica()
        
    def _resolve_spaceship_image_path(self, image_path):
        candidate = (image_path or "").strip()
        if candidate:
            expanded = os.path.expanduser(candidate)
            if not os.path.isabs(expanded):
                expanded = os.path.join(_project_root, expanded)
            if os.path.isfile(expanded):
                return expanded
        if os.path.isfile(DEFAULT_SPACESHIP_IMAGE):
            return DEFAULT_SPACESHIP_IMAGE
        fallback = os.path.join(_project_root, "assets", "images", "player_ship.png")
        if os.path.isfile(fallback):
            return fallback
        return None
    
    def _init_musica(self):
        self.musica_actual = None
        self.lista_reproduccion = self._construir_lista_reproduccion()
        self._reproducir_siguiente_cancion()
    
    def _construir_lista_reproduccion(self):
        if self.canciones_favoritas:
            canciones_validas = [c for c in self.canciones_favoritas if c and os.path.isfile(c)]
            if canciones_validas:
                return canciones_validas
        
        if os.path.isfile(DEFAULT_BACKGROUND_MUSIC):
            return [DEFAULT_BACKGROUND_MUSIC]
        
        base_path = os.path.splitext(DEFAULT_BACKGROUND_MUSIC)[0]
        for ext in ['.wav', '.mp3', '.flac']:
            alt_path = base_path + ext
            if os.path.isfile(alt_path):
                return [alt_path]
        
        if os.path.isfile(FALLBACK_MUSIC):
            return [FALLBACK_MUSIC]
        
        return []
    
    def _cargar_musica(self, ruta_musica):
        try:
            if not os.path.isfile(ruta_musica):
                print(f"✗ Archivo no encontrado: {ruta_musica}")
                return False
            
            try:
                pygame.mixer.music.load(ruta_musica)
                pygame.mixer.music.set_volume(self.volumen_musica)
                pygame.mixer.music.play(-1)
                self.musica_actual = ruta_musica
                print(f"✓ Música cargada: {os.path.basename(ruta_musica)}")
                return True
            except pygame.error as pe:
                print(f"✗ Pygame no puede cargar {os.path.basename(ruta_musica)}: {pe}")
                
                base_path = os.path.splitext(ruta_musica)[0]
                for ext in ['.ogg', '.wav', '.flac', '.mp3']:
                    alt_path = base_path + ext
                    if os.path.isfile(alt_path):
                        try:
                            pygame.mixer.music.load(alt_path)
                            pygame.mixer.music.set_volume(self.volumen_musica)
                            pygame.mixer.music.play(-1)
                            self.musica_actual = alt_path
                            print(f"✓ Usando formato alternativo: {os.path.basename(alt_path)}")
                            return True
                        except:
                            continue
                
                if ruta_musica.lower().endswith('.mp4'):
                    temp_wav = base_path + '_temp.wav'
                    import subprocess
                    try:
                        print(f"Convirtiendo MP4 a WAV con ffmpeg...")
                        result = subprocess.run(
                            ['ffmpeg', '-i', ruta_musica, '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-y', temp_wav],
                            capture_output=True,
                            text=True,
                            timeout=60
                        )
                        if os.path.isfile(temp_wav):
                            pygame.mixer.music.load(temp_wav)
                            pygame.mixer.music.set_volume(self.volumen_musica)
                            pygame.mixer.music.play(-1)
                            self.musica_actual = temp_wav
                            print(f"✓ MP4 convertido con ffmpeg")
                            return True
                    except Exception as e:
                        print(f"ffmpeg no disponible o falló: {e}")
                    
                    try:
                        from pydub import AudioSegment
                        print(f"Convirtiendo MP4 a WAV con pydub...")
                        sound = AudioSegment.from_file(ruta_musica)
                        sound.export(temp_wav, format="wav")
                        pygame.mixer.music.load(temp_wav)
                        pygame.mixer.music.set_volume(self.volumen_musica)
                        pygame.mixer.music.play(-1)
                        self.musica_actual = temp_wav
                        print(f"✓ MP4 convertido con pydub")
                        return True
                    except Exception as e:
                        print(f"pydub no disponible o falló: {e}")
                
                if os.path.isfile(FALLBACK_MUSIC):
                    try:
                        pygame.mixer.music.load(FALLBACK_MUSIC)
                        pygame.mixer.music.set_volume(self.volumen_musica)
                        pygame.mixer.music.play(-1)
                        self.musica_actual = FALLBACK_MUSIC
                        print(f"✓ Usando música de fallback")
                        return True
                    except:
                        pass
                
                return False
        except Exception as e:
            print(f"✗ Error cargando música: {e}")
            return False
    
    def _reproducir_siguiente_cancion(self):
        if not self.lista_reproduccion:
            print("✗ No hay canciones para reproducir")
            return
        cancion = random.choice(self.lista_reproduccion)
        self._cargar_musica(cancion)
    
    def _aumentar_volumen(self):
        self.volumen_musica = min(self.volumen_musica + 0.1, 1.0)
        pygame.mixer.music.set_volume(self.volumen_musica)
        print(f"Volumen: {int(self.volumen_musica * 100)}%")
    
    def _disminuir_volumen(self):
        self.volumen_musica = max(self.volumen_musica - 0.1, 0.0)
        pygame.mixer.music.set_volume(self.volumen_musica)
        print(f"Volumen: {int(self.volumen_musica * 100)}%")
    
    def alternar_pantalla_completa(self):
        self.pantalla_completa = not self.pantalla_completa
        if self.pantalla_completa:
            pantalla = pygame.display.set_mode((self.ancho_pantalla, self.alto_pantalla), pygame.FULLSCREEN)
        else:
            pantalla = pygame.display.set_mode((1200, 800))
        
        self.pantalla = pantalla
        self.campo_batalla.pantalla = pantalla
        self.interfaz_usuario.pantalla = pantalla
        
    def manejar_eventos(self, evento=None):
        if evento is None:
            eventos = pygame.event.get()
        else:
            eventos = [evento] if evento else []
        
        for evento in eventos:
            if evento.type == pygame.QUIT:
                self.ejecutando = False
                return False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    self.ejecutando = False
                    return False
                elif evento.key == pygame.K_SPACE:
                    print("SPACE presionado")
                    if self.nave1:
                        print("Disparando desde nave1")
                        self.campo_batalla.disparar_desde_nave(self.nave1)
                    else:
                        print("Error: nave1 es None")
                elif evento.key == pygame.K_l:
                    self.jugador_activo.perder_vida()
                elif evento.key == pygame.K_b:
                    self.jugador_activo.agregar_bono("Escudo")
                elif evento.key == pygame.K_F11:
                    self.alternar_pantalla_completa()
                elif evento.key == pygame.K_PLUS or evento.key == pygame.K_EQUALS:
                    self._aumentar_volumen()
                elif evento.key == pygame.K_MINUS:
                    self._disminuir_volumen()
            # Soporte para botones de joystick (gamepad)
            elif evento.type == pygame.JOYBUTTONDOWN:
                # botón 0 suele ser el botón principal (A en muchos pads)
                if evento.button == 0:
                    if self.nave1:
                        self.campo_batalla.disparar_desde_nave(self.nave1)
                        try:
                            self.nave1.play_shot_sound()
                        except Exception:
                            pass
            elif evento.type == pygame.JOYHATMOTION:
                # Hat (d-pad) puede manejarse si se desea; actualmente ignorado
                pass
            elif evento.type == pygame.JOYAXISMOTION:
                # Los ejes se procesan en actualizar() para movimiento continuo
                pass
        return True
                    
    def actualizar(self):
        pressed_keys = pygame.key.get_pressed()
        # Obtener el joystick activo (si está conectado) y pasarlo a CampoBatalla
        joystick = self._get_joystick()
        self.campo_batalla.actualizar(pressed_keys, joystick=joystick)
        
    def dibujar(self):
        self.pantalla.fill((0, 0, 0))
        self.campo_batalla.dibujar()
        self.interfaz_usuario.dibujar(self.jugador1, self.jugador2, self.jugador_activo)
        
    def ejecutar(self):
        while self.ejecutando:
            if not self.manejar_eventos():
                break
            self.actualizar()
            self.dibujar()
            self.reloj.tick(60)
        
        return True

    def _get_joystick(self):
        try:
            if pygame.joystick.get_count() > 0:
                joy = pygame.joystick.Joystick(0)
                if not joy.get_init():
                    joy.init()
                return joy
        except Exception:
            pass
        return None