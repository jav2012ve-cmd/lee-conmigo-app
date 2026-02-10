import streamlit as st
import base64
import time
from src.utils import obtener_ruta_imagen

def mostrar_efecto_karaoke_mini(placeholder, palabra_obj):
    silabas = palabra_obj['syllables']
    def obtener_html_bloques(indice_activo):
        bloques_html = ""
        for i, silaba in enumerate(silabas):
            if i == indice_activo:
                bg = "#FFF9C4"; border = "#FBC02D"; color = "#E65100"
                transform = "scale(1.1)"; shadow = "0 4px 8px rgba(0,0,0,0.2)"
                pointer = "<div style='position:absolute; top: 85%; left: 50%; transform: translateX(-50%); font-size: 24px;'>👆</div>"
                z_index = "10"
            else:
                bg = "#FFFFFF"; border = "#E0E0E0"; color = "#757575"
                transform = "scale(1)"; shadow = "none"; pointer = ""
                z_index = "1"
            style_str = (f"position: relative; z-index: {z_index}; display: inline-flex; justify-content: center; align-items: center; "
                         f"width: 45px; height: 45px; background-color: {bg}; border: 2px solid {border}; "
                         f"border-radius: 10px; color: {color}; font-size: 18px; font-weight: bold; font-family: sans-serif; "
                         f"margin: 0 4px; transform: {transform}; box-shadow: {shadow}; transition: all 0.2s;")
            bloques_html += f'<div style="{style_str}">{silaba}{pointer}</div>'
        return f'<div style="display: flex; justify-content: center; align-items: center; height: 180px; background: #FAFAFA; border-radius: 20px;">{bloques_html}</div>'

    placeholder.markdown(obtener_html_bloques(-1), unsafe_allow_html=True)
    time.sleep(0.3)
    for i in range(len(silabas)):
        placeholder.markdown(obtener_html_bloques(i), unsafe_allow_html=True)
        tiempo = 0.6 + (len(silabas[i]) * 0.15)
        time.sleep(tiempo) 
    placeholder.markdown(obtener_html_bloques(-1), unsafe_allow_html=True)
    time.sleep(0.5)

def generar_tarjeta_visual(item, altura=150, ocultar_imagen=False, mostrar_texto=True):
    # 1. Caso: Tarjeta oculta (Signo de interrogación)
    if ocultar_imagen:
        st.markdown(f"""
        <div style="width: 100%; height: {altura}px; border-radius: 15px; background: linear-gradient(135deg, #E0E0E0 0%, #F5F5F5 100%); border: 3px dashed #BDBDBD; display: flex; justify-content: center; align-items: center; font-size: 50px; color: #9E9E9E; box-shadow: inset 0 2px 5px rgba(0,0,0,0.05);">❓</div>""", unsafe_allow_html=True)
        return

    # 2. Caso: Es texto o no tiene imagen
    es_oracion_obj = isinstance(item, dict) and item.get('is_sentence')
    if isinstance(item, str) or (es_oracion_obj and not obtener_ruta_imagen(item)):
        texto = item['text'] if isinstance(item, dict) else item
        font_size = "22px" if len(texto) < 20 else "18px"
        st.markdown(f"""
        <div style="width: 100%; height: {altura}px; border-radius: 15px; background-color: #E3F2FD; border: 3px solid #90CAF9; display: flex; justify-content: center; align-items: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); font-size: {font_size}; padding: 10px; text-align: center; font-weight: bold; color: #1565C0;">{texto}</div>""", unsafe_allow_html=True)
        return

    # 3. Caso: Tiene imagen
    ruta_imagen = obtener_ruta_imagen(item)
    if ruta_imagen:
        with open(ruta_imagen, "rb") as f:
            data = f.read(); encoded = base64.b64encode(data).decode()
        
        texto_html = ""
        
        if mostrar_texto:
             # MODO ESTUDIO: Se ve completa (contain) y texto HTML abajo
             nombre = item['text'] if isinstance(item, dict) else ""
             texto_html = f"<div style='margin-top: 5px; font-weight: bold; color: #555; font-size: 18px;'>{nombre}</div>"
             estilo_img = "max-width: 100%; max-height: 85%; object-fit: contain; border-radius: 10px;"
             padding_box = "5px"
        else:
             # MODO JUEGO: 
             # Forzamos la imagen a llenar todo el cuadro. Al ser 'object-position: top',
             # la parte de abajo (donde suelen estar los nombres en flashcards) se recorta fuera de la vista.
             estilo_img = "width: 100%; height: 100%; object-fit: cover; object-position: top; border-radius: 12px;"
             padding_box = "0px"

        st.markdown(f"""
        <div style="
            width: 100%; 
            height: {altura}px; 
            border-radius: 15px; 
            overflow: hidden; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
            border: 3px solid #FFF; 
            background-color: white; 
            display: flex; 
            flex-direction: column;
            justify-content: center; 
            align-items: center;
            padding: {padding_box}; 
        ">
            <img src="data:image/png;base64,{encoded}" style="{estilo_img}">
            {texto_html}
        </div>""", unsafe_allow_html=True)
    
    # 4. Caso: Emoji
    else:
        colores = ["#FFCDD2", "#F8BBD0", "#E1BEE7", "#BBDEFB", "#B2EBF2", "#DCEDC8", "#FFF9C4"]
        color = colores[hash(item['text']) % len(colores)]
        emoji = item.get('emoji', '⭐')
        st.markdown(f"""
        <div style="width: 100%; height: {altura}px; border-radius: 15px; background-color: {color}; display: flex; justify-content: center; align-items: center; font-size: {int(altura * 0.5)}px; border: 3px solid #FFF; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">{emoji}</div>""", unsafe_allow_html=True)