# src/state_manager.py
import streamlit as st

def inicializar_estado():
    # Diccionario con los valores por defecto de todas las variables
    defaults = {
        # Navegación y Usuario
        'modo': "Inicio",
        'login_estado': 'inicio',
        'usuario_actual': None,
        'familia_map': {},
        
        # Lección Actual
        'indice_leccion': 0,
        'id_leccion_actual': None,
        'fase_leccion': "estudio",
        'elemento_activo': None,
        
        # Contenido Dinámico
        'palabras_actuales': [],
        'silabas_actuales': [],
        'frases_actuales': [],
        
        # Estado de Juegos (Taller/Quiz)
        'taller_data': [],
        'taller_idx': 0,
        'taller_construido': [],
        'taller_piezas_pool': [],
        'taller_errores': 0,
        'quiz_preguntas': [],
        'quiz_indice': 0,
        'quiz_estado': "pregunta",
        'ultimo_acierto': None,
        
        # Modo Álbum
        'album_cat': "",
        'album_items': [],
        'album_fase': "lectura",
        'album_taller_data': [],
        'album_taller_idx': 0,
        'album_quiz_idx': 0,
        'juego_target': None,
        
        # Efectos y UI
        'palabra_karaoke': None,
        'audio_pendiente': None,
        'scroll_needed': False,
        'en_celebracion': False,
        
        # Métricas de Sesión
        'sesion_aciertos': 0,
        'sesion_intentos': 0,
        'modo_juego': False,
    }

    # Inicializamos solo las que no existan
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value