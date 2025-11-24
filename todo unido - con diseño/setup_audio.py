#!/usr/bin/env python3
import subprocess
import os
import sys
import shutil

mp4_file = r"C:\Users\melmo\OneDrive\Documentos\DeepSeekers-Galacta--The-Battle-for-Saturn\Jugabilidad\Base\assets\sounds\musica_fondo.mp4"
ogg_file = mp4_file.replace('.mp4', '.ogg')
wav_file = mp4_file.replace('.mp4', '.wav')

if not os.path.exists(mp4_file):
    print(f"✗ No se encontró: {mp4_file}")
    sys.exit(1)

if os.path.exists(ogg_file) or os.path.exists(wav_file):
    print("✓ El archivo de música ya está en formato compatible")
    sys.exit(0)

print("Convirtiendo musica_fondo.mp4 a formato compatible...")
print("(Esta operación puede tomar unos minutos)\n")

conversión_exitosa = False

try:
    print("Intentando con ffmpeg...")
    if not shutil.which('ffmpeg'):
        raise FileNotFoundError("ffmpeg no está instalado")
    
    result = subprocess.run(
        ['ffmpeg', '-i', mp4_file, '-vn', '-acodec', 'libvorbis', '-q:a', '9', '-y', ogg_file],
        capture_output=True,
        text=True,
        timeout=120
    )
    if result.returncode == 0 and os.path.exists(ogg_file):
        print(f"✓ Conversión exitosa con ffmpeg: {ogg_file}\n")
        conversión_exitosa = True
    else:
        print(f"ffmpeg retornó error: {result.stderr[:200]}")
except Exception as e:
    print(f"ffmpeg no disponible: {e}\n")

if not conversión_exitosa:
    try:
        print("Intentando con moviepy...")
        from moviepy.editor import VideoFileClip
        print("Extrayendo audio (esto toma tiempo)...")
        video = VideoFileClip(mp4_file)
        audio = video.audio
        print(f"Audio extraído. Guardando como OGG...")
        audio.write_audiofile(ogg_file, verbose=False, logger=None)
        print(f"✓ Conversión exitosa con moviepy: {ogg_file}\n")
        conversión_exitosa = True
    except Exception as e:
        print(f"moviepy no disponible: {e}\n")

if not conversión_exitosa:
    try:
        print("Intentando con pydub...")
        from pydub import AudioSegment
        sound = AudioSegment.from_file(mp4_file)
        sound.export(ogg_file, format="ogg")
        print(f"✓ Conversión exitosa con pydub: {ogg_file}\n")
        conversión_exitosa = True
    except Exception as e:
        print(f"pydub no disponible: {e}\n")

if not conversión_exitosa:
    print("=" * 60)
    print("¡No se pudo convertir automáticamente!")
    print("=" * 60)
    print("\nPara reproducir música, instala una de estas librerías:")
    print("\n1. OPCIÓN RECOMENDADA: ffmpeg (más rápido)")
    print("   Descargar desde: https://ffmpeg.org/download.html")
    print("   O en Windows con chocolatey: choco install ffmpeg")
    print("\n2. OPCIÓN 2: moviepy")
    print("   Instalar con: pip install moviepy")
    print("\n3. OPCIÓN 3: pydub")
    print("   Instalar con: pip install pydub")
    print("\nDespués ejecuta este script de nuevo.")
    sys.exit(1)

print("=" * 60)
print("✓ Setup completado exitosamente!")
print("=" * 60)
print("\nAhora la música debería reproducirse correctamente en el juego.")
print("Usa +/- para ajustar el volumen durante el gameplay.")
