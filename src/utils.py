import unicodedata
import os
import time
import json
import base64
import uuid
import streamlit as st
import streamlit.components.v1 as components

# --- MANEJO DE ARCHIVOS ---
def cargar_json(nombre_archivo):
    ruta = os.path.join("data", nombre_archivo)
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def normalizar_texto(texto):
    if not texto: return ""
    texto = ''.join((c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn'))
    return texto.lower()

def normalizar_nombre_archivo(texto):
    return normalizar_texto(texto).replace(" ", "_") + ".jpg"

def obtener_ruta_imagen(item):
    texto_item = item['text'] if isinstance(item, dict) else item
    
    if 'familia_map' in st.session_state and texto_item in st.session_state.familia_map:
        return st.session_state.familia_map[texto_item]

    nombre_auto = normalizar_nombre_archivo(texto_item)
    ruta_auto = os.path.join("images", nombre_auto)
    if os.path.exists(ruta_auto): return ruta_auto
    
    if isinstance(item, dict) and item.get("image"):
        ruta_json = os.path.join("images", item.get("image"))
        if os.path.exists(ruta_json): return ruta_json
        
    return None

# --- UI UTILS ---
def scroll_to_top():
    ts = int(time.time() * 1000)
    js = f"""<script>
        setTimeout(function() {{ 
            window.scrollTo({{top: 0, behavior: 'instant'}});
            var main = window.parent.document.querySelector(".main");
            if(main) main.scrollTop = 0;
        }}, 50);
    </script><div style="display:none;">{ts}</div>"""
    components.html(js, height=0)

# --- EMAILS ---
def enviar_reporte_progreso(nombre_nino, nombre_padre, email_destino, letra, aciertos, intentos):
    print(f"--- SIMULANDO ENVÍO DE EMAIL A {email_destino} ---")
    return True

def enviar_resumen_padres(nombre_nino, nombre_padre, email_destino, stats, resumen_letras):
    print(f"--- 📧 ENVIANDO RESUMEN A: {email_destino} ---")
    return True

# --- AUDIO INSTANTÁNEO ---
def reproducir_audio_instantaneo(ruta_archivo):
    """
    Reproduce audio sin afectar el layout visual (Cero saltos).
    """
    try:
        if not os.path.exists(ruta_archivo):
            return

        with open(ruta_archivo, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            
            sound_id = f"audio_{uuid.uuid4()}"
            
            # TRUCO ANTISALTO:
            # Envolvemos el audio en un div con height:0 y overflow:hidden
            # Así garantizamos que no ocupe ni un pixel en la pantalla.
            md = f"""
                <div style="width:0; height:0; overflow:hidden; position:absolute; left:-9999px;">
                    <audio id="{sound_id}" autoplay="true">
                        <source src="data:audio/mpeg;base64,{b64}" type="audio/mpeg">
                    </audio>
                </div>
                <script>
                    (function() {{
                        var audio = document.getElementById('{sound_id}');
                        if (audio) {{
                            audio.volume = 1.0;
                            audio.play().catch(e => console.log("Audio play error: " + e));
                        }}
                    }})();
                </script>
            """
            # Usamos un contenedor vacío al final para inyectar esto sin pintar nada
            st.markdown(md, unsafe_allow_html=True)
            
    except Exception as e:
        print(f"Error audio: {e}")