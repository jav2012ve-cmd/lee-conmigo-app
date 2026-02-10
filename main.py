import streamlit as st
import os
import random
import time
import db 

# --- IMPORTACIONES ---
from src.state_manager import inicializar_estado
from src.speech_engine import SpeechEngine
from src.utils import (
    cargar_json, scroll_to_top, normalizar_nombre_archivo, 
    enviar_reporte_progreso, enviar_resumen_padres, 
    reproducir_audio_instantaneo
)
from src.styles import inyectar_css_personalizado
from src.components import generar_tarjeta_visual, mostrar_efecto_karaoke_mini
from src.game_logic import (
    reset_progresos, registrar_intento_sesion, 
    generar_preguntas_leccion, generar_data_taller, 
    preparar_proxima_leccion, preparar_taller_album
)

# Configuración de la página
st.set_page_config(page_title="Lee Conmigo IA", page_icon="📚", layout="centered", initial_sidebar_state="collapsed")

def main():
    inyectar_css_personalizado()
    
    # --- INICIALIZACIÓN DE ESTADO ---
    inicializar_estado()

    if 'pin_ingresado' not in st.session_state: st.session_state.pin_ingresado = []
    if 'temp_registro' not in st.session_state: st.session_state.temp_registro = {}
    if 'temp_usuario' not in st.session_state: st.session_state.temp_usuario = None

    if st.session_state.scroll_needed: 
        scroll_to_top(); st.session_state.scroll_needed = False

    lecciones = cargar_json("lessons.json")
    favoritos = cargar_json("favorites.json")
    motor = SpeechEngine()
    
    if not lecciones: st.error("⚠️ Error: No encuentro 'lessons.json'."); return

    db.crear_tablas()

    # --- REPRODUCTOR GLOBAL ---
    if st.session_state.audio_pendiente:
        texto_o_ruta = st.session_state.audio_pendiente
        if os.path.exists(str(texto_o_ruta)): reproducir_audio_instantaneo(texto_o_ruta)
        else: ruta = motor.generar_audio(texto_o_ruta); reproducir_audio_instantaneo(ruta)
        st.session_state.audio_pendiente = None 

    # ==============================================================================
    # 🔐 SISTEMA DE LOGIN Y REGISTRO
    # ==============================================================================
    if st.session_state.usuario_actual is None:
        st.markdown("<h1 style='text-align:center; color:#E65100;'>🦉 Lee Conmigo IA</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; font-size:18px;'>Aprende a leer con las personas que amas.</p>", unsafe_allow_html=True)
        st.write("")

        if st.session_state.login_estado == 'inicio':
            c1, c2 = st.columns(2, gap="medium")
            with c1:
                st.markdown("""<style>div[data-testid="column"]:nth-of-type(1) button { background: linear-gradient(135deg, #42A5F5 0%, #1565C0 100%) !important; color: white !important; font-size: 24px !important; height: 150px !important; border: 4px solid #0D47A1 !important; }</style>""", unsafe_allow_html=True)
                if st.button("🎓\n\nSoy Alumno", use_container_width=True):
                    st.session_state.login_estado = 'seleccion'; st.rerun()
            with c2:
                st.markdown("""<style>div[data-testid="column"]:nth-of-type(2) button { background: linear-gradient(135deg, #66BB6A 0%, #2E7D32 100%) !important; color: white !important; font-size: 24px !important; height: 150px !important; border: 4px solid #1B5E20 !important; }</style>""", unsafe_allow_html=True)
                if st.button("✨\n\nSoy Nuevo", use_container_width=True):
                    st.session_state.login_estado = 'registro_datos'; st.rerun()

        elif st.session_state.login_estado == 'seleccion':
            st.markdown("### 👤 ¿Quién eres?")
            if st.button("⬅️ Volver", key="back_sel"):
                st.session_state.login_estado = 'inicio'; st.rerun()
            usuarios = db.obtener_estudiantes()
            if usuarios:
                cols = st.columns(4)
                for i, u in enumerate(usuarios):
                    with cols[i % 4]:
                        if st.button(f"👤 {u[1]}", key=f"user_{u[0]}", use_container_width=True):
                            st.session_state.temp_usuario = {"id": u[0], "nombre": u[1], "pin_real": u[3]}
                            st.session_state.pin_ingresado = []
                            st.session_state.login_estado = 'validar_pin'
                            st.rerun()
            else: st.info("No hay alumnos registrados aún.")

        elif st.session_state.login_estado == 'validar_pin':
            u_temp = st.session_state.temp_usuario
            st.markdown(f"<h2 style='text-align:center;'>Hola {u_temp['nombre']} 👋</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align:center; font-size: 20px;'>Ingresa tu clave secreta:</p>", unsafe_allow_html=True)
            
            html_puntos = ""
            for i in range(3):
                color = "#4CAF50" if i < len(st.session_state.pin_ingresado) else "#E0E0E0"
                html_puntos += f"<span style='height: 25px; width: 25px; background-color: {color}; border-radius: 50%; display: inline-block; margin: 10px; border: 2px solid #999;'></span>"
            st.markdown(f"<div style='text-align:center; margin-bottom: 20px;'>{html_puntos}</div>", unsafe_allow_html=True)

            emojis = ["🦁", "🚀", "🍎", "⭐", "⚽", "🐶", "🚗", "🍕", "🐈"]
            cols = st.columns(3)
            for idx, em in enumerate(emojis):
                with cols[idx % 3]:
                    st.markdown("""<style>div[data-testid="column"] button { font-size: 40px !important; height: 80px !important; background: white !important; border: 2px solid #ddd !important; }</style>""", unsafe_allow_html=True)
                    if st.button(em, key=f"pin_log_{idx}", use_container_width=True):
                        st.session_state.pin_ingresado.append(em)
                        if len(st.session_state.pin_ingresado) == 3:
                            pin_str = "-".join(st.session_state.pin_ingresado)
                            pin_correcto = u_temp.get('pin_real')
                            if not pin_correcto or pin_str == pin_correcto:
                                st.balloons()
                                st.session_state.usuario_actual = u_temp
                                st.session_state.familia_map = db.obtener_familia_map(u_temp['id'])
                                st.session_state.login_estado = 'inicio'
                                st.rerun()
                            else:
                                st.toast("❌ Esa no es tu clave", icon="🔒"); time.sleep(1); st.session_state.pin_ingresado = []; st.rerun()
                        else: st.rerun()
            st.write(""); 
            if st.button("⬅️ Soy otra persona"): st.session_state.login_estado = 'seleccion'; st.session_state.temp_usuario = None; st.rerun()

        elif st.session_state.login_estado == 'registro_datos':
            st.markdown("### ✨ Nuevo Alumno (Paso 1/2)")
            if st.button("⬅️ Cancelar"): st.session_state.login_estado = 'inicio'; st.rerun()
            with st.form("reg_form"):
                c1, c2 = st.columns(2)
                with c1: n_nino = st.text_input("Nombre del Niño/a:")
                with c2: edad = st.number_input("Edad:", 3, 12, 6)
                c3, c4 = st.columns(2)
                with c3: n_padre = st.text_input("Nombre Acudiente:")
                with c4: email = st.text_input("Email:")
                doc = st.text_input("Documento (Opcional):")
                if st.form_submit_button("Siguiente ➡️"):
                    if n_nino and n_padre:
                        st.session_state.temp_registro = {"n_nino": n_nino, "edad": edad, "n_padre": n_padre, "email": email, "doc": doc}
                        st.session_state.pin_ingresado = []; st.session_state.login_estado = 'registro_pin'; st.rerun()
                    else: st.error("Faltan nombres.")

        elif st.session_state.login_estado == 'registro_pin':
            datos = st.session_state.temp_registro
            st.markdown(f"<h3 style='text-align:center;'>¡Hola {datos['n_nino']}!</h3>", unsafe_allow_html=True)
            st.markdown("<p style='text-align:center; font-size: 20px; color: #E65100;'>Elige 3 dibujos para tu clave secreta:</p>", unsafe_allow_html=True)
            html_puntos = ""
            for i in range(3):
                color = "#2196F3" if i < len(st.session_state.pin_ingresado) else "#E0E0E0"
                html_puntos += f"<span style='height: 25px; width: 25px; background-color: {color}; border-radius: 50%; display: inline-block; margin: 10px; border: 2px solid #999;'></span>"
            st.markdown(f"<div style='text-align:center; margin-bottom: 20px;'>{html_puntos}</div>", unsafe_allow_html=True)
            emojis = ["🦁", "🚀", "🍎", "⭐", "⚽", "🐶", "🚗", "🍕", "🐈"]
            cols = st.columns(3)
            for idx, em in enumerate(emojis):
                with cols[idx % 3]:
                    st.markdown("""<style>div[data-testid="column"] button { font-size: 40px !important; height: 80px !important; background: white !important; border: 2px solid #ddd !important; }</style>""", unsafe_allow_html=True)
                    if st.button(em, key=f"pin_reg_{idx}", use_container_width=True):
                        st.session_state.pin_ingresado.append(em)
                        if len(st.session_state.pin_ingresado) == 3:
                            pin_final = "-".join(st.session_state.pin_ingresado)
                            uid = db.inscribir_estudiante(datos['n_nino'], datos['edad'], datos['n_padre'], datos['email'], datos['doc'], pin_final)
                            st.success("¡Cuenta Creada!"); st.balloons(); time.sleep(1.5)
                            st.session_state.usuario_actual = {"id": uid, "nombre": datos['n_nino']}; st.session_state.familia_map = {}; st.session_state.login_estado = 'inicio'; st.rerun()
                        else: st.rerun()
            if st.button("🔄 Borrar selección"): st.session_state.pin_ingresado = []; st.rerun()
        return

    # ==============================================================================
    # ⚙️ ZONA DE PADRES
    # ==============================================================================
    if st.session_state.modo == "Configuracion":
        # --- CAMBIO 1: IMAGEN DE BIENVENIDA A PADRES ---
        if os.path.exists("assets/Hola_papas.jpg"):
            st.image("assets/Hola_papas.jpg", use_container_width=True)
            
        st.markdown(f"## ⚙️ Zona de Padres: {st.session_state.usuario_actual['nombre']}")
        if st.button("⬅️ Volver al Inicio"): st.session_state.modo = "Inicio"; st.rerun()
        tab_familia, tab_reporte = st.tabs(["📸 Familia", "📊 Progreso"])
        
        with tab_familia:
            st.info("Sube fotos de la familia para personalizar las lecciones.")
            with st.form("form_familiar", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    rol = st.selectbox("Parentesco", ["Mamá", "Papá", "Abuela", "Abuelo", "Tía", "Tío", "Prima", "Primo", "Mascota", "Yo"])
                    nombre_personal = st.text_input("Nombre completo (Ej: Prima Ana)")
                with col2: foto = st.file_uploader("Subir Foto", type=['jpg', 'png', 'jpeg'])
                if st.form_submit_button("Guardar Familiar"):
                    if foto and nombre_personal:
                        if not os.path.exists("images"): os.makedirs("images")
                        ext = foto.name.split('.')[-1]
                        nombre_clean = normalizar_nombre_archivo(nombre_personal).replace(".jpg", "")
                        filename = f"{st.session_state.usuario_actual['id']}_{nombre_clean}.{ext}"
                        ruta_final = os.path.join("images", filename)
                        with open(ruta_final, "wb") as f: f.write(foto.getbuffer())
                        db.guardar_familiar(st.session_state.usuario_actual['id'], nombre_personal, ruta_final)
                        st.session_state.familia_map = db.obtener_familia_map(st.session_state.usuario_actual['id'])
                        st.success(f"¡Guardado! {nombre_personal}"); time.sleep(1); st.rerun()
            st.markdown("### 📸 Mi Familia")
            familia = st.session_state.familia_map
            if familia:
                cols = st.columns(3)
                for i, (nombre, ruta) in enumerate(familia.items()):
                    with cols[i % 3]:
                        if os.path.exists(ruta): st.image(ruta, caption=nombre, use_container_width=True)
            else: st.caption("Aún no has agregado familiares.")

        with tab_reporte:
            stats = db.obtener_estadisticas(st.session_state.usuario_actual['id'])
            resumen_letras = db.obtener_resumen_letras(st.session_state.usuario_actual['id'])
            st.info(f"📢 **Diagnóstico:** {resumen_letras}")
            st.write("---")
            col_m1, col_m2 = st.columns(2)
            col_m1.metric("Palabras Dominadas", stats['dominadas'])
            col_m2.metric("Palabras Construidas", stats['habilidades'].get('silabica', 0))
            if st.button("📧 Enviar Reporte al Correo", key="btn_send_report", use_container_width=True):
                email_padre, nombre_padre = db.obtener_email_padre(st.session_state.usuario_actual['id'])
                if email_padre and "@" in email_padre:
                    with st.spinner("Enviando correo..."):
                        exito = enviar_resumen_padres(st.session_state.usuario_actual['nombre'], nombre_padre, email_padre, stats, resumen_letras)
                    if exito: st.balloons(); st.success(f"✅ Informe enviado correctamente a {email_padre}"); time.sleep(2)
                else: st.error("⚠️ No se encontró un correo válido registrado.")
            st.write("---")
            st.markdown("### 📜 Últimas Actividades")
            if stats['historial']:
                for h in stats['historial']:
                    icono = "✅" if h[3] == 'acierto' else "❌"
                    st.text(f"{h[0]} | {icono} {h[2]} ({h[1]})")
            else: st.info("Aún no hay actividad registrada.")

    # ==============================================================================
    # 🏠 DASHBOARD PRINCIPAL
    # ==============================================================================
    if st.session_state.modo == "Inicio":
        c_foto, c_txt, c_botones = st.columns([2, 3, 2], gap="medium", vertical_alignment="center")
        with c_foto:
            foto_perfil = None
            if "Yo" in st.session_state.familia_map: foto_perfil = st.session_state.familia_map["Yo"]
            elif st.session_state.usuario_actual['nombre'] in st.session_state.familia_map: foto_perfil = st.session_state.familia_map[st.session_state.usuario_actual['nombre']]
            else:
                posible_path = normalizar_nombre_archivo(st.session_state.usuario_actual['nombre'])
                path_full = os.path.join("images", posible_path)
                if os.path.exists(path_full): foto_perfil = path_full
            
            if foto_perfil and os.path.exists(foto_perfil): st.image(foto_perfil, width=220) 
            else:
                if os.path.exists("assets/placeholder_nino.png"): st.image("assets/placeholder_nino.png", width=220)
                else: st.markdown("<div style='font-size:100px; text-align:center;'>👦</div>", unsafe_allow_html=True)
        
        with c_txt:
            nombre = st.session_state.usuario_actual['nombre']
            st.markdown(f"<h1 style='margin:0; color:#E65100; font-size: 50px;'>¡Hola {nombre}!</h1><p style='margin:0; font-size: 24px;'>¿Listo para jugar?</p>", unsafe_allow_html=True)
        
        with c_botones:
            if st.button("📚 Lecciones", use_container_width=True):
                st.session_state.audio_pendiente = "Vamos a revisar las lecciones"
                st.session_state.modo = "Lecciones"
                st.rerun() 

            if st.button("🖼️ Álbum", use_container_width=True):
                st.session_state.audio_pendiente = "Vamos a ver nuestras palabras favoritas"
                st.session_state.modo = "Álbum"
                st.session_state.album_fase = "lectura"
                st.rerun()
        
        st.write("---")
        letras_dominadas = db.obtener_letras_desbloqueadas(st.session_state.usuario_actual['id'])
        indice_siguiente = 0
        for i, l in enumerate(lecciones):
            if l['letter'].upper() in letras_dominadas: indice_siguiente = i + 1
            else: indice_siguiente = i; break
        if indice_siguiente >= len(lecciones): indice_siguiente = len(lecciones) - 1

        cols = st.columns(4) 
        for i, leccion in enumerate(lecciones):
            letra = leccion['letter']
            estado = "bloqueado"
            if i < indice_siguiente: estado = "dominado"
            elif i == indice_siguiente: estado = "actual"
            with cols[i % 4]:
                if estado == "dominado":
                    st.markdown("""<style>div[data-testid="column"] button.dominado { background: #E8F5E9 !important; border: 2px solid #4CAF50 !important; color: #2E7D32 !important; opacity: 0.8; }</style>""", unsafe_allow_html=True)
                    if st.button(f"⭐ {letra}", key=f"btn_lvl_{i}", use_container_width=True):
                        st.session_state.audio_pendiente = f"¡Vamos a repasar la letra {letra}!"
                        st.session_state.indice_leccion = i
                        st.session_state.modo = "Lecciones"
                        st.rerun()
                elif estado == "actual":
                    st.markdown("""<style>div[data-testid="column"] button.actual { background: linear-gradient(135deg, #42A5F5 0%, #1976D2 100%) !important; border: 4px solid #0D47A1 !important; color: white !important; font-size: 28px !important; transform: scale(1.1); }</style>""", unsafe_allow_html=True)
                    if st.button(f"▶️ {letra}", key=f"btn_lvl_{i}", use_container_width=True):
                        st.session_state.audio_pendiente = f"¡A aprender la letra {letra}!"
                        st.session_state.indice_leccion = i
                        st.session_state.modo = "Lecciones"
                        st.rerun()
                else: st.button(f"🔒 {letra}", key=f"btn_lvl_{i}", disabled=True, use_container_width=True)

        st.write("---")
        c_conf, c_out = st.columns([1, 1])
        with c_conf:
            # --- CAMBIO 2: IMAGEN DINÁMICA DE PADRES ---
            # Buscamos si han subido alguna foto de Papá, Mamá, Padre o Madre
            foto_padres = None
            if 'familia_map' in st.session_state:
                for nombre, ruta in st.session_state.familia_map.items():
                    n_low = nombre.lower()
                    if "papá" in n_low or "mamá" in n_low or "padre" in n_low or "madre" in n_low:
                        if os.path.exists(ruta):
                            foto_padres = ruta; break
            
            # Si hay foto real, la mostramos en un tamaño moderado
            if foto_padres: st.image(foto_padres, width=80)
            
            if st.button("⚙️ Papás", use_container_width=True): st.session_state.modo = "Configuracion"; st.rerun()
        with c_out:
            if foto_padres: st.write("") # Espaciador para alinear con el botón si hay foto
            st.markdown("""<style>div[data-testid="column"]:nth-of-type(2) button { background: #FFEBEE !important; color: #C62828 !important; border: 1px solid #FFCDD2 !important; }</style>""", unsafe_allow_html=True)
            if st.button("🔴 Salir", use_container_width=True): st.session_state.usuario_actual = None; st.session_state.login_estado = 'inicio'; st.rerun()
        return

    # ==============================================================================
    # 📚 MODO LECCIONES
    # ==============================================================================
    if st.session_state.modo == "Lecciones":
        if st.session_state.indice_leccion >= len(lecciones):
            st.success("¡FIN DEL JUEGO! 🏆")
            if st.button("🔄 Empezar otra vez"): st.session_state.indice_leccion = 0; st.rerun()
            return
            
        datos = lecciones[st.session_state.indice_leccion]
        
        # --- SOLUCIÓN AL PROBLEMA DE DOBLE CLIC ---
        if st.session_state.id_leccion_actual != datos['id']:
            with st.spinner("Preparando..."): 
                preparar_proxima_leccion(st.session_state.indice_leccion, lecciones, favoritos, motor)
                st.session_state.modo = "Lecciones"
                st.rerun()
        
        st.progress((st.session_state.indice_leccion + 1) / len(lecciones))
        
        # FASE 1: ESTUDIO
        if st.session_state.fase_leccion == "estudio":
            c_inicio, c_letra, c_silabas = st.columns([1, 1.5, 2.5], gap="medium")
            with c_inicio:
                st.markdown("""<style>div[data-testid="column"]:nth-of-type(1) button { border-radius: 15px !important; height: 60px !important; font-size: 18px !important; background: #FFF9C4 !important; color: #5D4037 !important; border: 2px solid #FBC02D !important; }</style>""", unsafe_allow_html=True)
                if st.button("🏠 Inicio", use_container_width=True): reset_progresos(); st.rerun()
            with c_letra: st.markdown(f"<div style='display:flex; justify-content:center; align-items:center; height: 100%; width: 100%;'><h1 style='color:#FF5252; font-size:90px; margin:0; line-height: 1;'>{datos['letter']} {datos['letter'].lower()}</h1></div>", unsafe_allow_html=True)
            st.markdown("""<style>div[data-testid="column"]:nth-of-type(3) button { background: #FFF9C4 !important; border: 2px solid #FBC02D !important; color: #5D4037 !important; height: 85px !important; width: 85px !important; border-radius: 20px !important; font-size: 28px !important; box-shadow: 0 4px 0px rgba(0,0,0,0.1) !important; margin: 5px !important; }</style>""", unsafe_allow_html=True)
            silabas = st.session_state.silabas_actuales
            with c_silabas:
                r1c1, r1c2, r1c3 = st.columns(3)
                with r1c1: 
                    if st.button(silabas[0], key="s_0"): reproducir_audio_instantaneo(motor.generar_audio(silabas[0]))
                with r1c3: 
                    if st.button(silabas[1], key="s_1"): reproducir_audio_instantaneo(motor.generar_audio(silabas[1]))
                r2c1, r2c2, r2c3 = st.columns(3)
                with r2c2: 
                    if st.button(silabas[2], key="s_2"): reproducir_audio_instantaneo(motor.generar_audio(silabas[2]))
                r3c1, r3c2, r3c3 = st.columns(3)
                with r3c1: 
                    if st.button(silabas[3], key="s_3"): reproducir_audio_instantaneo(motor.generar_audio(silabas[3]))
                with r3c3: 
                    if st.button(silabas[4], key="s_4"): reproducir_audio_instantaneo(motor.generar_audio(silabas[4]))
            st.markdown("---")
            st.markdown("<h3 style='text-align:center;'>📖 Vamos a leer</h3>", unsafe_allow_html=True)
            image_placeholders = {}
            st.markdown("""<style>div[data-testid="column"] button { border-radius: 15px !important; height: auto !important; font-size: 20px !important; width: 100% !important; background: #FFFDE7 !important; color: #3E2723 !important; border: 2px solid #FFD54F !important; }</style>""", unsafe_allow_html=True)
            palabras = st.session_state.palabras_actuales
            if palabras:
                rows = [palabras[i:i+3] for i in range(0, len(palabras), 3)]
                for row in rows:
                    cols = st.columns(len(row))
                    for i, p in enumerate(row):
                        with cols[i]:
                            ph = st.empty(); image_placeholders[p['text']] = ph
                            with ph: generar_tarjeta_visual(p, altura=180)
                            lbl = f"{p['text']}\n({'-'.join(p['syllables'])})"
                            
                            if st.button(lbl, key=f"w_{p['text']}_{i}", use_container_width=True):
                                st.session_state.palabra_karaoke = p
                                # --- CAMBIO 1: LIMPIEZA DE TEXTO PARA AUDIO ---
                                # Aseguramos que el texto vaya limpio al motor de audio
                                st.session_state.audio_pendiente = p['text'].strip()
                                st.rerun() 
            if st.session_state.palabra_karaoke:
                texto_activo = st.session_state.palabra_karaoke['text']
                if texto_activo in image_placeholders: mostrar_efecto_karaoke_mini(image_placeholders[texto_activo], st.session_state.palabra_karaoke)
                st.session_state.palabra_karaoke = None
            st.markdown("<h3 style='text-align:center; margin-top: 30px;'>🌟 Frases Mágicas</h3>", unsafe_allow_html=True)
            frases = st.session_state.frases_actuales 
            for i, f in enumerate(frases):
                if st.button(f'"{f}"', key=f"f_{i}", use_container_width=True):
                    reproducir_audio_instantaneo(motor.generar_audio(f))
                    if i == len(frases) - 1: 
                        st.session_state.elemento_activo = "listo_para_jugar"
                        time.sleep(3.5); st.balloons(); st.rerun()

            if st.session_state.elemento_activo == "listo_para_jugar":
                st.write("---")
                c1, c2, c3 = st.columns([1, 2, 1])
                with c2:
                    st.markdown("""<style>div[data-testid="column"]:nth-of-type(2) button { background: linear-gradient(135deg, #42A5F5 0%, #1565C0 100%) !important; color: white !important; border: 2px solid #0D47A1 !important; height: 80px !important; font-size: 24px !important; }</style>""", unsafe_allow_html=True)
                    if st.button(f"🎮 Jugar con la {datos['letter']}", key="btn_start_quiz", use_container_width=True):
                        st.session_state.fase_leccion = "taller"
                        st.session_state.taller_data = generar_data_taller(datos, favoritos)
                        st.session_state.taller_idx = 0; st.session_state.taller_construido = []; st.session_state.taller_piezas_pool = []; st.session_state.taller_errores = 0
                        st.session_state.audio_pendiente = "¡Vamos a construir palabras!"
                        st.rerun()

        # FASE 2: TALLER (CONSTRUCCIÓN)
        elif st.session_state.fase_leccion == "taller":
            if not st.session_state.taller_data or st.session_state.taller_idx >= len(st.session_state.taller_data):
                st.session_state.fase_leccion = "quiz"; st.session_state.quiz_estado = "pregunta"; st.session_state.quiz_preguntas = generar_preguntas_leccion(datos, lecciones); st.session_state.quiz_indice = 0
                st.session_state.audio_pendiente = "¡Excelente! Ahora escucha con atención"
                st.rerun()

            juego_actual = st.session_state.taller_data[st.session_state.taller_idx]
            target_obj = juego_actual['target_obj']; target_syllables = juego_actual['target_syllables']
            if not st.session_state.taller_piezas_pool and not st.session_state.taller_construido:
                st.session_state.taller_piezas_pool = juego_actual['piezas_mezcladas'].copy(); st.session_state.taller_errores = 0
            
            prog_txt = f"Palabra {st.session_state.taller_idx + 1} de {len(st.session_state.taller_data)}"
            st.markdown(f"<h2 style='text-align:center; color:#E65100; margin-bottom:5px;'>🧩 Arma la palabra</h2>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align:center; color:grey; margin-top:0px; margin-bottom: 20px;'>{prog_txt}</p>", unsafe_allow_html=True)
            st.progress((st.session_state.taller_idx) / len(st.session_state.taller_data))
            st.write("")
            
            col_img, col_juego, col_ctl = st.columns([1.5, 1.5, 1], gap="medium")
            
            with col_img:
                generar_tarjeta_visual(target_obj, altura=300, mostrar_texto=False) # Altura mayor para que luzca
                st.write("") 

            with col_juego:
                st.markdown("<p style='text-align:center; font-size:16px; color:#555; margin-bottom: 5px;'>1. Arrastra aquí:</p>", unsafe_allow_html=True)
                cols_pizarra = st.columns(len(target_syllables))
                for i in range(len(target_syllables)):
                    with cols_pizarra[i]:
                        if i < len(st.session_state.taller_construido):
                            s = st.session_state.taller_construido[i]
                            st.markdown("""<style>div[data-testid="column"] button.css-pizarra { border: 3px solid #4CAF50 !important; background: #E8F5E9 !important; }</style>""", unsafe_allow_html=True)
                            if st.button(s, key=f"pizarra_{i}", use_container_width=True):
                                val = st.session_state.taller_construido.pop(i)
                                st.session_state.taller_piezas_pool.append(val)
                                st.session_state.audio_pendiente = "pop"; st.rerun()
                        else: 
                            st.markdown(f"""<div style="background:#F5F5F5; border:3px dashed #9E9E9E; border-radius:15px; height: 60px; display: flex; align-items: center; justify-content: center; font-size:24px; color:#CCC;">_</div>""", unsafe_allow_html=True)
                
                st.write("---")
                st.markdown("<p style='text-align:center; font-size:16px; color:#555; margin-bottom: 5px;'>2. Elige las sílabas:</p>", unsafe_allow_html=True)
                pool = st.session_state.taller_piezas_pool
                if pool:
                    for i, p in enumerate(pool):
                        if st.button(p, key=f"pool_{i}", use_container_width=True):
                            if len(st.session_state.taller_construido) < len(target_syllables):
                                val = st.session_state.taller_piezas_pool.pop(i)
                                st.session_state.taller_construido.append(val)
                                st.session_state.audio_pendiente = val; st.rerun()
                            else: st.toast("¡Espacios llenos!")
            
            with col_ctl:
                st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
                st.markdown("""<style>div.stButton > button:first-child { background: linear-gradient(135deg, #66BB6A 0%, #43A047 100%) !important; border: none !important; color: white !important; font-weight: bold !important; box-shadow: 0 4px 6px rgba(0,0,0,0.2) !important; font-size: 20px !important; height: 60px !important; }</style>""", unsafe_allow_html=True)
                if st.button("✅ Listo", use_container_width=True):
                    registrar_intento_sesion(False) 
                    if st.session_state.taller_construido == target_syllables:
                        reproducir_audio_instantaneo(motor.generar_audio(f"¡Muy bien! {target_obj['text']}"))
                        if st.session_state.taller_errores == 0: 
                            st.balloons(); registrar_intento_sesion(True) 
                            db.registrar_progreso(st.session_state.usuario_actual['id'], "silabica", target_obj['text'], "acierto")
                        else: st.success("¡Bien hecho!")
                        time.sleep(1.5); st.session_state.taller_idx += 1; st.session_state.taller_construido = []; st.session_state.taller_piezas_pool = []; st.rerun()
                    else:
                        st.session_state.taller_errores += 1
                        db.registrar_progreso(st.session_state.usuario_actual['id'], "silabica", target_obj['text'], "fallo")
                        st.error("Intenta de nuevo"); reproducir_audio_instantaneo(motor.generar_audio("Esa no es"))
                st.write("")
                if st.button("🔄 Borrar", use_container_width=True): st.session_state.taller_construido = []; st.session_state.taller_piezas_pool = juego_actual['piezas_mezcladas'].copy(); st.rerun()
                st.write("")
                if st.button("➡️ Saltar", use_container_width=True):
                    st.session_state.taller_idx += 1; st.session_state.taller_construido = []; st.session_state.taller_piezas_pool = []
                    reproducir_audio_instantaneo(motor.generar_audio("Vamos con la siguiente")); st.rerun()
                st.write("---")
                st.markdown("""<style>div.stButton > button:last-child { background: #CFD8DC !important; border: 1px solid #B0BEC5 !important; color: #455A64 !important; height: 50px !important; font-size: 16px !important; }</style>""", unsafe_allow_html=True)
                if st.button("🏠 Inicio", key="home_taller", use_container_width=True): reset_progresos(); st.rerun()

        # FASE 3: QUIZ
        elif st.session_state.fase_leccion == "quiz":
            if st.session_state.quiz_indice >= len(st.session_state.quiz_preguntas): st.session_state.fase_leccion = "fin"; st.rerun()
            pregunta = st.session_state.quiz_preguntas[st.session_state.quiz_indice]
            if st.session_state.quiz_estado == "pregunta":
                target = pregunta['target']; texto_target = target['text'] if isinstance(target, dict) else target
                c_home, c_title = st.columns([1, 4])
                with c_home:
                    st.markdown("""<style>div[data-testid="column"]:nth-of-type(1) button { border-radius: 15px !important; height: 50px !important; font-size: 16px !important; background: #FFF9C4 !important; color: #5D4037 !important; border: 2px solid #FBC02D !important; }</style>""", unsafe_allow_html=True)
                    if st.button("🏠 Inicio", key="home_quiz", use_container_width=True): reset_progresos(); st.rerun()
                with c_title:
                    st.markdown(f"<h2 style='text-align:center; color:#E65100; margin:0;'>👂 Escucha y Toca</h2>", unsafe_allow_html=True)
                    st.caption(f"Pregunta {st.session_state.quiz_indice + 1} de {len(st.session_state.quiz_preguntas)}")
                st.progress((st.session_state.quiz_indice + 1) / len(st.session_state.quiz_preguntas))
                c_audio = st.columns([1, 1, 1])[1]
                with c_audio:
                    st.markdown("""<style>div[data-testid="column"]:nth-of-type(2) button { background: #FFF3E0 !important; border: 4px solid #FF9800 !important; color: #E65100 !important; height: 100px !important; font-size: 40px !important; border-radius: 50px !important; }</style>""", unsafe_allow_html=True)
                    if st.button("🔊", key=f"btn_listen_{st.session_state.quiz_indice}", use_container_width=True):
                        reproducir_audio_instantaneo(motor.generar_audio(texto_target))
                st.write("")
                cols = st.columns(3)
                for i, opcion in enumerate(pregunta['opciones']):
                    texto_opcion = opcion['text'] if isinstance(opcion, dict) else opcion
                    with cols[i]:
                        st.markdown("""<style>div[data-testid="column"] button { border-radius: 15px !important; height: auto !important; min-height: 60px !important; background: white !important; border: 2px solid #CFD8DC !important; color: #37474F !important; font-weight: bold !important; font-size: 20px !important; }</style>""", unsafe_allow_html=True)
                        generar_tarjeta_visual(opcion, altura=130, ocultar_imagen=True)
                        if st.button(texto_opcion, key=f"q_{st.session_state.quiz_indice}_opt_{i}", use_container_width=True):
                            registrar_intento_sesion(False) 
                            if texto_opcion == texto_target:
                                reproducir_audio_instantaneo(motor.generar_audio("¡Muy bien!"))
                                st.session_state.quiz_estado = "celebracion"; st.session_state.ultimo_acierto = opcion
                                st.balloons(); registrar_intento_sesion(True) 
                                tipo_quiz = "palabra" if "word_pool" in str(pregunta) else "oracion"
                                db.registrar_progreso(st.session_state.usuario_actual['id'], tipo_quiz, texto_target, "acierto")
                                time.sleep(0.5); st.rerun()
                            else: 
                                tipo_quiz = "palabra" if "word_pool" in str(pregunta) else "oracion"
                                db.registrar_progreso(st.session_state.usuario_actual['id'], tipo_quiz, texto_target, "fallo")
                                st.error("¡Intenta de nuevo!"); reproducir_audio_instantaneo(motor.generar_audio("Intenta de nuevo"))
            elif st.session_state.quiz_estado == "celebracion":
                st.markdown(f"<h1 style='text-align:center; color:#4CAF50;'>¡Correcto! 🎉</h1>", unsafe_allow_html=True)
                c_premio = st.columns([1,1,1])[1]
                with c_premio: generar_tarjeta_visual(st.session_state.ultimo_acierto, altura=220, ocultar_imagen=False)
                time.sleep(2.5); st.session_state.quiz_indice += 1; st.session_state.quiz_estado = "pregunta"; st.rerun()

        # FASE 4: FIN DE LECCIÓN
        elif st.session_state.fase_leccion == "fin":
            total_intentos = st.session_state.sesion_intentos
            total_aciertos = st.session_state.sesion_aciertos
            porcentaje = 0
            if total_intentos > 0: porcentaje = total_aciertos / total_intentos
            
            clave_envio = f"reporte_enviado_{st.session_state.id_leccion_actual}_{total_intentos}"
            
            if clave_envio not in st.session_state:
                email_padre, nombre_padre = db.obtener_email_padre(st.session_state.usuario_actual['id'])
                if email_padre and "@" in email_padre:
                    exito = enviar_reporte_progreso(st.session_state.usuario_actual['nombre'], nombre_padre if nombre_padre else "Papá/Mamá", email_padre, datos['letter'], total_aciertos, total_intentos)
                    if exito: st.toast(f"📧 Informe enviado a {nombre_padre}")
                st.session_state[clave_envio] = True

            if porcentaje >= 0.7:
                st.markdown(f"<h1 style='text-align:center; color:#4CAF50; font-size: 60px;'>¡Excelente! 🌟</h1>", unsafe_allow_html=True)
                st.balloons()
            else:
                st.markdown(f"<h1 style='text-align:center; color:#FF9800; font-size: 60px;'>¡Buen Esfuerzo! 💪</h1>", unsafe_allow_html=True)
            
            st.markdown(f"<h3 style='text-align:center;'>Completaste la letra {datos['letter']}</h3>", unsafe_allow_html=True)
            st.write("---"); st.write("")
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("""<style>div[data-testid="column"]:nth-of-type(1) button { background: #FFF9C4 !important; color: #5D4037 !important; border: 2px solid #FBC02D !important; }</style>""", unsafe_allow_html=True)
                if st.button("🏠 Inicio", key="btn_home_end", use_container_width=True): reset_progresos(); st.rerun()
            with c2:
                st.markdown("""<style>div[data-testid="column"]:nth-of-type(2) button { background: #66BB6A !important; color: white !important; border: 2px solid #2E7D32 !important; }</style>""", unsafe_allow_html=True)
                if st.button("➡️ Siguiente Lección", key="btn_next_end", use_container_width=True):
                    nxt = st.session_state.indice_leccion + 1
                    if nxt < len(lecciones):
                        with st.spinner("Preparando..."): preparar_proxima_leccion(nxt, lecciones, favoritos, motor)
                    st.session_state.indice_leccion = nxt; st.rerun()
            

    # --- MODO ÁLBUM ---
    elif st.session_state.modo == "Álbum":
        st.markdown("""<style>div.stButton > button { border-radius: 15px !important; background: #FFF9C4 !important; font-size: 16px !important; border: 2px solid #FBC02D !important; color: #5D4037 !important; }</style>""", unsafe_allow_html=True)
        c_nav, c_sel = st.columns([1, 3], gap="small")
        with c_nav:
            if st.button("🏠 Inicio", use_container_width=True): st.session_state.modo = "Inicio"; st.rerun()
        with c_sel:
            cats = list(favoritos.keys()); opciones_menu = [" -- Selecciona -- "] + cats
            idx_actual = 0
            if st.session_state.album_cat in cats: idx_actual = opciones_menu.index(st.session_state.album_cat)
            seleccion = st.selectbox("Elige una categoría:", opciones_menu, index=idx_actual, label_visibility="collapsed")
            if seleccion != st.session_state.album_cat:
                if seleccion == " -- Selecciona -- ": st.session_state.album_cat = ""; st.session_state.album_items = []
                else:
                    st.session_state.album_cat = seleccion; nuevos_items = favoritos[seleccion].copy()
                    if seleccion != "Números": random.shuffle(nuevos_items)
                    st.session_state.album_items = nuevos_items[:6]
                    st.session_state.album_fase = "lectura" 
                st.rerun()
        
        st.markdown("---")
        if not st.session_state.album_cat: st.info("👆 Selecciona un álbum arriba para empezar."); return 

        st.markdown(f"<h2 style='text-align:center; margin:0;'>📸 {st.session_state.album_cat}</h2>", unsafe_allow_html=True)
        
        # FASE 1: LECTURA
        if st.session_state.album_fase == "lectura":
            col_act, col_next = st.columns([2,1])
            with col_act:
                if st.button("🔄 Nuevas Fichas", use_container_width=True):
                    todos_items = favoritos[st.session_state.album_cat].copy(); random.shuffle(todos_items); st.session_state.album_items = todos_items[:6]; st.rerun()
            with col_next:
                st.markdown("""<style>div[data-testid="column"]:nth-of-type(2) button { background: linear-gradient(135deg, #42A5F5 0%, #1976D2 100%) !important; border: 4px solid #0D47A1 !important; color: white !important; font-weight: bold !important; }</style>""", unsafe_allow_html=True)
                if st.button("🎮 Jugar a Reconocer", use_container_width=True):
                    st.session_state.album_fase = "quiz"; st.session_state.album_quiz_idx = 0; st.session_state.juego_target = None
                    reproducir_audio_instantaneo(motor.generar_audio("¡Encuentra las imágenes!")); time.sleep(1); st.rerun()

            st.write("---")
            image_placeholders_alb = {}
            lista = st.session_state.album_items; rows = [lista[i:i+3] for i in range(0, len(lista), 3)]
            for row in rows:
                cc = st.columns(3)
                for i, item in enumerate(row):
                    with cc[i]:
                        ph = st.empty(); image_placeholders_alb[item['text']] = ph
                        with ph: generar_tarjeta_visual(item, altura=180)
                        label = f"{item['text']}\n({'-'.join(item['syllables'])})"
                        if st.button(label, key=f"alb_{item['text']}_{i}", use_container_width=True):
                            reproducir_audio_instantaneo(motor.generar_audio(item['text'])) 

        # FASE 2: QUIZ
        elif st.session_state.album_fase == "quiz":
            if st.session_state.album_quiz_idx >= len(st.session_state.album_items):
                st.balloons()
                st.success("¡Muy bien! ¡Las encontraste todas!")
                st.markdown("""<style>div.stButton > button { background: linear-gradient(135deg, #66BB6A 0%, #388E3C 100%) !important; border: 4px solid #1B5E20 !important; color: white !important; font-weight: bold !important; font-size: 24px !important; height: 80px !important; }</style>""", unsafe_allow_html=True)
                if st.button("🧩 Ir a Armar Palabras", use_container_width=True):
                    st.session_state.album_fase = "armar"
                    st.session_state.album_taller_data = preparar_taller_album(st.session_state.album_items)
                    st.session_state.album_taller_idx = 0
                    st.session_state.taller_construido = []; st.session_state.taller_piezas_pool = []
                    reproducir_audio_instantaneo(motor.generar_audio("¡Ahora vamos a escribirlas!")); time.sleep(1); st.rerun()
                if st.button("🔄 Repetir Quiz", use_container_width=True):
                    st.session_state.album_quiz_idx = 0; st.rerun()
                return

            col_back, col_status = st.columns([1, 4])
            with col_back:
                if st.button("⬅️", use_container_width=True): st.session_state.album_fase = "lectura"; st.rerun()
            with col_status:
                st.progress((st.session_state.album_quiz_idx) / len(st.session_state.album_items))
                st.caption(f"Encuentra {st.session_state.album_quiz_idx + 1} de {len(st.session_state.album_items)}")

            lista_actual = st.session_state.album_items 
            if st.session_state.juego_target is None:
                target = lista_actual[st.session_state.album_quiz_idx]
                distractores = [x for x in lista_actual if x['text'] != target['text']]
                if len(distractores) > 2: distractores = random.sample(distractores, 2)
                opciones = distractores + [target]; random.shuffle(opciones)
                st.session_state.juego_target = target; st.session_state.juego_opciones = opciones
                reproducir_audio_instantaneo(motor.generar_audio(f"¿Dónde está {target['text']}?")); st.rerun()

            target = st.session_state.juego_target
            if st.session_state.en_celebracion:
                st.balloons()
                st.markdown(f"<h1 style='text-align:center; color:#4CAF50;'>¡Muy bien!</h1>", unsafe_allow_html=True)
                c_cent = st.columns([1,2,1])[1]
                with c_cent: generar_tarjeta_visual(target, altura=250)
                st.markdown(f"<h2 style='text-align:center;'>Es: {target['text']}</h2>", unsafe_allow_html=True)
                time.sleep(4); st.session_state.en_celebracion = False; st.session_state.juego_target = None; st.session_state.album_quiz_idx += 1; st.rerun()

            st.markdown(f"<h1 style='text-align:center; color:#1565C0;'>¿Dónde está...<br>{target['text']}?</h1>", unsafe_allow_html=True)
            cols = st.columns(len(st.session_state.juego_opciones))
            for i, opt in enumerate(st.session_state.juego_opciones):
                with cols[i]:
                    generar_tarjeta_visual(opt, altura=150)
                    if st.button("👆 Aquí está", key=f"juego_{i}", use_container_width=True):
                        if opt['text'] == target['text']:
                            reproducir_audio_instantaneo(motor.generar_audio(f"¡Muy bien! Allí está {target['text']}"))
                            db.registrar_progreso(st.session_state.usuario_actual['id'], "visual", target['text'], "acierto")
                            st.session_state.en_celebracion = True; st.rerun()
                        else:
                            db.registrar_progreso(st.session_state.usuario_actual['id'], "visual", target['text'], "fallo")
                            st.error("¡Ups!"); reproducir_audio_instantaneo(motor.generar_audio("Intenta de nuevo"))

        # FASE 3: ARMAR (ALBUM) (MODIFICADO PARA COLUMNAS LATERALES)
        elif st.session_state.album_fase == "armar":
            if not st.session_state.album_taller_data: st.error("No hay palabras con sílabas para armar en este grupo."); return
            if st.session_state.album_taller_idx >= len(st.session_state.album_taller_data):
                st.balloons(); st.success("¡Terminaste de armar todo!")
                if st.button("🔄 Volver al inicio del álbum"): st.session_state.album_fase = "lectura"; st.rerun()
                return

            juego_actual = st.session_state.album_taller_data[st.session_state.album_taller_idx]
            target_obj = juego_actual['target_obj']; target_syllables = juego_actual['target_syllables']
            
            if not st.session_state.taller_piezas_pool and not st.session_state.taller_construido:
                st.session_state.taller_piezas_pool = juego_actual['piezas_mezcladas'].copy()

            karaoke_ph = st.empty() 
            if st.session_state.palabra_karaoke and st.session_state.palabra_karaoke['text'] == target_obj['text']:
                 mostrar_efecto_karaoke_mini(karaoke_ph, target_obj)
                 st.session_state.palabra_karaoke = None
                 time.sleep(0.5); st.session_state.album_taller_idx += 1; st.session_state.taller_construido = []; st.session_state.taller_piezas_pool = []; st.rerun()
            else:
                 # --- MOSTRAR SOLO EL TITULO SIN TARJETA (LA TARJETA ESTÁ ABAJO) ---
                 st.markdown(f"<h3 style='text-align:center; margin-bottom: 20px;'>Palabra {st.session_state.album_taller_idx + 1} de {len(st.session_state.album_taller_data)}</h3>", unsafe_allow_html=True)

            # --- NUEVA DISPOSICIÓN: IMAGEN (IZQ) - JUEGO (DER) ---
            col_img, col_juego, col_ctl = st.columns([1.5, 1.5, 1], gap="medium")
            
            # COLUMNA IZQUIERDA: IMAGEN
            with col_img:
                generar_tarjeta_visual(target_obj, altura=300, mostrar_texto=False)
                st.write("")

            # COLUMNA CENTRAL: JUEGO
            with col_juego:
                st.markdown("<p style='text-align:center; font-size:16px; color:#555;'>1. Arrastra aquí:</p>", unsafe_allow_html=True)
                
                # A. PIZARRA
                cols_pizarra = st.columns(len(target_syllables))
                for i in range(len(target_syllables)):
                    with cols_pizarra[i]:
                        if i < len(st.session_state.taller_construido):
                            s = st.session_state.taller_construido[i]
                            st.markdown("""<style>div[data-testid="column"] button.css-pizarra { border: 3px solid #4CAF50 !important; background: #E8F5E9 !important; }</style>""", unsafe_allow_html=True)
                            if st.button(s, key=f"piz_alb_{i}", use_container_width=True):
                                val = st.session_state.taller_construido.pop(i)
                                st.session_state.taller_piezas_pool.append(val)
                                st.session_state.audio_pendiente = "pop"; st.rerun()
                        else: 
                            st.markdown(f"""<div style="background:#F5F5F5; border:3px dashed #9E9E9E; border-radius:15px; height: 60px; display: flex; align-items: center; justify-content: center; font-size:24px; color:#CCC;">_</div>""", unsafe_allow_html=True)
                
                st.write("---")
                st.markdown("<p style='text-align:center; font-size:16px; color:#555;'>2. Elige:</p>", unsafe_allow_html=True)

                # B. POOL (VERTICAL)
                pool = st.session_state.taller_piezas_pool
                if pool:
                    for i, p in enumerate(pool):
                        if st.button(p, key=f"pool_alb_{i}", use_container_width=True):
                            if len(st.session_state.taller_construido) < len(target_syllables):
                                val = st.session_state.taller_piezas_pool.pop(i)
                                st.session_state.taller_construido.append(val)
                                st.session_state.audio_pendiente = val; st.rerun()
            
            # COLUMNA DERECHA: CONTROLES
            with col_ctl:
                st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
                if st.button("✅ Listo", key="ok_alb", use_container_width=True):
                    if st.session_state.taller_construido == target_syllables:
                        reproducir_audio_instantaneo(motor.generar_audio(f"¡Muy bien! {target_obj['text']}"))
                        st.success("¡Correcto!")
                        db.registrar_progreso(st.session_state.usuario_actual['id'], "silabica", target_obj['text'], "acierto")
                        st.session_state.palabra_karaoke = target_obj; st.rerun()
                    else:
                        st.error("Nop")
                        db.registrar_progreso(st.session_state.usuario_actual['id'], "silabica", target_obj['text'], "fallo")
                
                st.write("") 
                if st.button("🔄 Borrar", key="retry_alb", use_container_width=True):
                    st.session_state.taller_construido = []
                    st.session_state.taller_piezas_pool = juego_actual['piezas_mezcladas'].copy()
                    st.rerun()

                st.write("")
                if st.button("➡️ Saltar", key="skip_alb", use_container_width=True):
                    st.session_state.album_taller_idx += 1
                    st.session_state.taller_construido = []; st.session_state.taller_piezas_pool = []; st.rerun()

if __name__ == "__main__":
    main()