import os
import sys

mp4_file = r"C:\Users\melmo\OneDrive\Documentos\DeepSeekers-Galacta--The-Battle-for-Saturn\Jugabilidad\Base\assets\sounds\musica_fondo.mp4"
ogg_file = mp4_file.replace('.mp4', '.ogg')

try:
    from moviepy.editor import VideoFileClip
    print("Extrayendo audio del MP4...")
    video = VideoFileClip(mp4_file)
    video.audio.write_audiofile(ogg_file, verbose=False, logger=None)
    print(f"✓ Archivo convertido: {ogg_file}")
except Exception as e:
    print(f"Error con moviepy: {e}")
    
    try:
        import subprocess
        print("Intentando con ffmpeg...")
        subprocess.run(['ffmpeg', '-i', mp4_file, '-vn', '-acodec', 'libvorbis', '-q:a', '9', ogg_file], 
                      stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        print(f"✓ Archivo convertido: {ogg_file}")
    except Exception as e:
        print(f"Error con ffmpeg: {e}")
        print("\nAlternativa: Instala ffmpeg o moviepy")
        print("pip install moviepy  (más completo)")
        print("pip install pydub  (alternativa)")
