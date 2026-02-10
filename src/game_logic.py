import random
import re
import streamlit as st
from src.utils import normalizar_texto, obtener_ruta_imagen

PALABRAS_CONCRETAS = [
    "mamá", "moto", "mapa", "mula", "mono", "momia", "mesa", "melón", "miel", "mano",
    "papá", "pato", "puma", "pomo", "pipa", "mapa", "pepino", "pelota", "perro", "pie",
    "sapo", "sopa", "suma", "sol", "sal", "sandía", "silla",
    "luna", "lupa", "lima", "loma", "león", "lobo", "lila", "limón",
    "tía", "tío", "tomate", "tuna", "topo", "tapa", "tina", "moto", "auto",
    "prima", "primo", "rojo", "rosa", "azul", "verde"
]

def registrar_intento_sesion(es_acierto):
    if 'sesion_intentos' not in st.session_state:
        st.session_state.sesion_intentos = 0
        st.session_state.sesion_aciertos = 0
    st.session_state.sesion_intentos += 1
    if es_acierto:
        st.session_state.sesion_aciertos += 1

def reset_progresos():
    st.session_state.modo = "Inicio"
    st.session_state.fase_leccion = "estudio"
    st.session_state.taller_idx = 0
    st.session_state.taller_construido = []
    st.session_state.taller_piezas_pool = []
    st.session_state.taller_errores = 0
    st.session_state.quiz_indice = 0
    st.session_state.quiz_preguntas = []
    st.session_state.ultimo_acierto = None
    st.session_state.palabra_karaoke = None 
    st.session_state.album_fase = "lectura" 
    st.session_state.album_taller_idx = 0
    st.session_state.album_taller_data = []
    st.session_state.album_quiz_idx = 0
    st.session_state.sesion_aciertos = 0
    st.session_state.sesion_intentos = 0

def generar_preguntas_leccion(datos_leccion, lecciones_globales):
    preguntas = []
    pool_palabras = datos_leccion.get('word_pool', [])
    if pool_palabras:
        targets_p = random.sample(pool_palabras, min(len(pool_palabras), 6))
        while len(targets_p) < 6 and pool_palabras: targets_p.append(random.choice(pool_palabras))
        for target in targets_p:
            distractores = [p for p in pool_palabras if p['text'] != target['text']]
            if len(distractores) < 2:
                todos = [p for l in lecciones_globales for p in l.get('word_pool', [])]
                distractores += [p for p in todos if p['text'] != target['text']]
            ops = random.sample(distractores, min(len(distractores), 2)); opciones = ops + [target]; random.shuffle(opciones)
            preguntas.append({'tipo': 'palabra', 'target': target, 'opciones': opciones})

    pool_frases_crudo = datos_leccion.get('sentences', [])
    if isinstance(pool_frases_crudo, str): pool_frases_crudo = [pool_frases_crudo]
    
    mapa_roles = {}
    roles_clave = ["mamá", "papá", "abuela", "abuelo", "tía", "tío", "prima", "primo"]
    familia_actual = st.session_state.get('familia_map', {})
    
    for nombre_real in familia_actual.keys():
        for rol in roles_clave:
            if rol in nombre_real.lower(): mapa_roles[rol] = nombre_real; break
    
    pool_frases_procesado = []
    for frase in pool_frases_crudo:
        frase_personalizada = frase
        for rol, nombre_real in mapa_roles.items():
            if rol in frase_personalizada.lower():
                pattern_rol_only = re.compile(re.escape(rol), re.IGNORECASE)
                apellido_sucio = pattern_rol_only.sub("", nombre_real)
                apellido_limpio = apellido_sucio.strip()
                if apellido_limpio:
                     pattern = re.compile(r"\b" + re.escape(rol) + r"\b(?!\s*" + re.escape(apellido_limpio) + r")", re.IGNORECASE)
                else:
                     pattern = re.compile(r"\b" + re.escape(rol) + r"\b", re.IGNORECASE)
                frase_personalizada = pattern.sub(nombre_real, frase_personalizada)
        
        imagen_encontrada = None
        for nombre, archivo_img in familia_actual.items():
            if nombre.lower() in frase_personalizada.lower(): imagen_encontrada = archivo_img; break
        
        if imagen_encontrada: pool_frases_procesado.append({"text": frase_personalizada, "image": imagen_encontrada, "is_sentence": True})
        else: pool_frases_procesado.append(frase_personalizada)

    if pool_frases_procesado:
        targets_f = random.sample(pool_frases_procesado, min(len(pool_frases_procesado), 3))
        while len(targets_f) < 3 and pool_frases_procesado: targets_f.append(random.choice(pool_frases_procesado))
        for target in targets_f:
            target_texto = target['text'] if isinstance(target, dict) else target
            distractores = []
            for f in pool_frases_procesado:
                f_texto = f['text'] if isinstance(f, dict) else f
                if f_texto != target_texto: distractores.append(f)
            if len(distractores) < 2:
                 todos_crudos = [f for l in lecciones_globales for f in l.get('sentences', [])]
                 for f_cruda in todos_crudos: 
                     if f_cruda != target_texto: distractores.append(f_cruda)
            if len(distractores) >= 2:
                ops = random.sample(distractores, 2); opciones = ops + [target]; random.shuffle(opciones)
                preguntas.append({'tipo': 'oracion', 'target': target, 'opciones': opciones})
    return preguntas

def generar_data_taller(datos_leccion, favoritos):
    letra_actual = datos_leccion['letter'].lower()
    pool_leccion = datos_leccion.get('word_pool', [])
    candidatas = []
    ids_agregados = set()

    for categoria, lista_items in favoritos.items():
        for item in lista_items:
            texto_item = normalizar_texto(item['text'])
            if texto_item.startswith(letra_actual):
                if item.get('syllables') and len(item['syllables']) >= 2:
                    if item['text'] not in ids_agregados:
                        item_copy = item.copy(); item_copy['_origen'] = 'album' 
                        candidatas.append(item_copy); ids_agregados.add(item['text'])

    pool_leccion_filtrado = []
    for p in pool_leccion:
        if p['text'] in ids_agregados: continue
        texto_limpio = normalizar_texto(p['text'])
        if not (p.get('syllables') and len(p['syllables']) >= 2): continue
        es_concreta = texto_limpio in [normalizar_texto(x) for x in PALABRAS_CONCRETAS]
        tiene_foto = obtener_ruta_imagen(p) is not None
        if es_concreta or tiene_foto: pool_leccion_filtrado.append(p)
            
    random.shuffle(pool_leccion_filtrado)
    seleccion_final = candidatas + pool_leccion_filtrado
    
    if len(seleccion_final) > 6:
        num_favoritos = len(candidatas)
        tomar_leccion = 6 - num_favoritos
        if tomar_leccion < 0: tomar_leccion = 0
        seleccion_final = candidatas + pool_leccion_filtrado[:tomar_leccion]
    
    seleccion_final.sort(key=lambda x: (len(x['syllables']), x.get('_origen') != 'album'))
    
    todas_silabas = datos_leccion.get("syllables", [])
    juegos = []
    for palabra in seleccion_final:
        correctas = [s.lower() for s in palabra['syllables']]
        posibles_intrusas = [s for s in todas_silabas if s.lower() not in correctas]
        if not posibles_intrusas: posibles_intrusas = ["ma", "pa", "la", "sa", "to", "mi"]
        intrusa = random.choice(posibles_intrusas).lower()
        piezas = correctas + [intrusa]; random.shuffle(piezas)
        juegos.append({"target_obj": palabra, "target_syllables": correctas, "piezas_mezcladas": piezas})
    return juegos

def preparar_taller_album(items_seleccionados):
    juegos = []
    pool_silabas_extra = ["ma", "pa", "la", "sa", "to", "mi", "le", "ro", "ca"]
    
    for item in items_seleccionados:
        if not (isinstance(item, dict) and item.get('syllables') and len(item['syllables']) >= 2):
            continue
        correctas = [s.lower() for s in item['syllables']]
        intrusa = random.choice(pool_silabas_extra)
        piezas = correctas + [intrusa]
        random.shuffle(piezas)
        juegos.append({"target_obj": item, "target_syllables": correctas, "piezas_mezcladas": piezas})
    return juegos

def preparar_proxima_leccion(indice_nuevo, lecciones, favoritos, motor):
    datos_proxima = lecciones[indice_nuevo]
    letra_proxima = datos_proxima['letter'].lower()
    
    reset_progresos()
    
    mis_silabas = datos_proxima["syllables"].copy(); random.shuffle(mis_silabas)
    for s in mis_silabas: t = "Né" if s == "Ne" else s; motor.generar_audio(t)
    
    prioritarios = []
    familia_actual = st.session_state.get('familia_map', {})
    for nombre in familia_actual.keys():
        if nombre.lower().startswith(letra_proxima): prioritarios.append(nombre)

    letras_vistas = [l['letter'].lower() for l in lecciones[:indice_nuevo + 1]]
    pool_leccion = [p for p in datos_proxima.get('word_pool', []) if p['text'][0].lower() in letras_vistas]
    
    pool_favoritos = []
    for fam_nombre in prioritarios:
        # --- CORRECCIÓN: DETECCIÓN AUTOMÁTICA DE SÍLABAS SEGÚN EL ROL ---
        n_low = fam_nombre.lower()
        silabas_auto = [fam_nombre] # Default fallback
        
        if "papá" in n_low: silabas_auto = ["Pa", "pá"]
        elif "mamá" in n_low: silabas_auto = ["Ma", "má"]
        elif "prima" in n_low: silabas_auto = ["Pri", "ma"]
        elif "primo" in n_low: silabas_auto = ["Pri", "mo"]
        elif "tía" in n_low: silabas_auto = ["Tí", "a"]
        elif "tío" in n_low: silabas_auto = ["Tí", "o"]
        elif "abuela" in n_low: silabas_auto = ["A", "bue", "la"]
        elif "abuelo" in n_low: silabas_auto = ["A", "bue", "lo"]
        
        pool_favoritos.append({
            "text": fam_nombre, 
            "image": familia_actual[fam_nombre], 
            "syllables": silabas_auto
        })

    for cat, lista in favoritos.items():
        for p in lista:
            if p.get('text', '').lower().startswith(letra_proxima): pool_favoritos.append(p)
            
    seleccion_final = []; nombres_ya_agregados = set()
    for p in pool_favoritos:
        if p['text'] not in nombres_ya_agregados: seleccion_final.append(p); nombres_ya_agregados.add(p['text'])
    for p in pool_leccion:
        if p['text'] not in nombres_ya_agregados: seleccion_final.append(p); nombres_ya_agregados.add(p['text'])
            
    if len(seleccion_final) > 6:
        familia_len = len(prioritarios)
        resto = seleccion_final[familia_len:]
        random.shuffle(resto)
        seleccion_final = seleccion_final[:familia_len] + resto
        seleccion_final = seleccion_final[:6]

    for p in seleccion_final: motor.generar_audio(p['text'])
    frases_pool = datos_proxima.get('sentences', [])
    if isinstance(frases_pool, str): frases_pool = [frases_pool]
    random.shuffle(frases_pool); seleccion_frases = frases_pool[:3]
    for f in seleccion_frases: motor.generar_audio(f)
    st.session_state.silabas_actuales = mis_silabas
    st.session_state.palabras_actuales = seleccion_final
    st.session_state.frases_actuales = seleccion_frases
    st.session_state.id_leccion_actual = datos_proxima['id']
    st.session_state.scroll_needed = True