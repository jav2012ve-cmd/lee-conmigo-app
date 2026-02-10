import os
from gtts import gTTS
import hashlib

class SpeechEngine:
    def __init__(self, cache_dir="audio_cache"):
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    def generar_audio(self, texto):
        if not texto: return None
        
        # --- DICCIONARIO DE CORRECCIONES FONÉTICAS ---
        # Aquí forzamos la pronunciación correcta reemplazando el texto
        # justo antes de enviarlo al motor de voz.
        correcciones = {
            "Ne": "Né",   # La tilde evita que diga "Ene E"
            "ne": "né",
            "Cu": "Cú",   # La tilde evita que diga "Ce U"
            "cu": "cú",
            "Se": "Sé",   # A veces pasa con "Se"
            "se": "sé",
            # Agrega aquí cualquier otra sílaba rebelde
        }
        
        # Usamos la corrección si existe, si no, usamos el texto original
        texto_para_audio = correcciones.get(texto, texto)
        
        # Generamos el nombre del archivo basado en el texto YA CORREGIDO.
        # Esto es importante: al cambiar "Ne" por "Né", el sistema generará
        # un archivo de audio nuevo y no usará el antiguo que estaba mal.
        filename = hashlib.md5(texto_para_audio.encode()).hexdigest() + ".mp3"
        filepath = os.path.join(self.cache_dir, filename)

        # Si el archivo no existe, lo creamos
        if not os.path.exists(filepath):
            try:
                tts = gTTS(text=texto_para_audio, lang='es')
                tts.save(filepath)
            except Exception as e:
                print(f"Error generando audio para '{texto}': {e}")
                return None
            
        return filepath