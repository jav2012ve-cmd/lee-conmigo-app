import psycopg2
import streamlit as st
from datetime import datetime

# --- CONEXIÓN A LA NUBE (SUPABASE) ---
def conectar():
    # Busca la URL en tus secretos (.streamlit/secrets.toml o Streamlit Cloud Secrets)
    return psycopg2.connect(st.secrets["supabase"]["url"])

def crear_tablas():
    conn = conectar()
    c = conn.cursor()
    
    # 1. Tabla Estudiantes
    # En Postgres usamos 'SERIAL' en lugar de 'AUTOINCREMENT'
    c.execute('''CREATE TABLE IF NOT EXISTS estudiantes (
        id SERIAL PRIMARY KEY,
        nombre_nino TEXT NOT NULL,
        edad INTEGER,
        nombre_padre TEXT,
        email_padre TEXT,
        documento_facturacion TEXT,
        fecha_registro TEXT,
        pin_secreto TEXT
    )''')
    
    # 2. Tabla Progreso
    c.execute('''CREATE TABLE IF NOT EXISTS progreso (
        id SERIAL PRIMARY KEY,
        estudiante_id INTEGER,
        fecha_hora TIMESTAMP,
        competencia TEXT, 
        item TEXT, 
        resultado TEXT, -- 'acierto' o 'fallo'
        FOREIGN KEY(estudiante_id) REFERENCES estudiantes(id)
    )''')

    # 3. Tabla Familiares
    c.execute('''CREATE TABLE IF NOT EXISTS familiares (
        id SERIAL PRIMARY KEY,
        estudiante_id INTEGER,
        nombre_clave TEXT,
        ruta_imagen TEXT,
        FOREIGN KEY(estudiante_id) REFERENCES estudiantes(id)
    )''')
    
    conn.commit()
    conn.close()

# --- GESTIÓN DE ESTUDIANTES ---
def inscribir_estudiante(nombre_nino, edad, nombre_padre, email, documento, pin_secreto):
    conn = conectar(); c = conn.cursor()
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # En Postgres usamos %s en lugar de ? para los huecos
    c.execute("""
        INSERT INTO estudiantes (nombre_nino, edad, nombre_padre, email_padre, documento_facturacion, fecha_registro, pin_secreto) 
        VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
    """, (nombre_nino, edad, nombre_padre, email, documento, fecha, pin_secreto))
    
    uid = c.fetchone()[0] # Recuperamos el ID del nuevo estudiante
    conn.commit(); conn.close()
    return uid

def obtener_estudiantes():
    conn = conectar(); c = conn.cursor()
    c.execute("SELECT id, nombre_nino, edad, pin_secreto FROM estudiantes")
    data = c.fetchall(); conn.close()
    return data

def obtener_email_padre(estudiante_id):
    conn = conectar(); c = conn.cursor()
    c.execute("SELECT email_padre, nombre_padre FROM estudiantes WHERE id = %s", (estudiante_id,))
    resultado = c.fetchone()
    conn.close()
    return resultado if resultado else (None, None)

# --- GESTIÓN DE PROGRESO ---
def registrar_progreso(estudiante_id, competencia, item, resultado):
    conn = conectar(); c = conn.cursor()
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO progreso (estudiante_id, fecha_hora, competencia, item, resultado) VALUES (%s, %s, %s, %s, %s)", 
              (estudiante_id, fecha, competencia, item, resultado))
    conn.commit(); conn.close()

def obtener_estadisticas(estudiante_id):
    conn = conectar(); c = conn.cursor()
    
    # Contamos palabras únicas dominadas
    c.execute("SELECT count(DISTINCT item) FROM progreso WHERE estudiante_id = %s AND resultado = 'acierto'", (estudiante_id,))
    res_count = c.fetchone()
    palabras_dominadas = res_count[0] if res_count else 0
    
    # Habilidades por competencia
    c.execute("SELECT competencia, count(*) FROM progreso WHERE estudiante_id = %s AND resultado = 'acierto' GROUP BY competencia", (estudiante_id,))
    habilidades = dict(c.fetchall())
    
    # Historial reciente (Postgres usa TO_CHAR para formatear fechas, pero aquí lo simplificamos)
    # Nota: Simplificamos la query para evitar problemas de formato de fecha por ahora
    c.execute("SELECT fecha_hora, competencia, item, resultado FROM progreso WHERE estudiante_id = %s ORDER BY id DESC LIMIT 5", (estudiante_id,))
    raw_historial = c.fetchall()
    
    # Formateamos la fecha en Python para asegurar compatibilidad
    historial = []
    for h in raw_historial:
        fecha_str = str(h[0])[:16] # Cortamos para que se vea bonita "2024-02-10 14:30"
        historial.append((fecha_str, h[1], h[2], h[3]))

    conn.close()
    return {"dominadas": palabras_dominadas, "habilidades": habilidades, "historial": historial}

def obtener_resumen_letras(estudiante_id):
    conn = conectar(); c = conn.cursor()
    c.execute("SELECT item, resultado FROM progreso WHERE estudiante_id = %s AND competencia != 'visual'", (estudiante_id,))
    registros = c.fetchall(); conn.close()
    
    stats_letras = {}
    for item, resultado in registros:
        if not item: continue
        letra = item[0].upper()
        if not letra.isalpha(): continue
        if letra not in stats_letras: stats_letras[letra] = {'aciertos': 0, 'fallos': 0}
        if resultado == 'acierto': stats_letras[letra]['aciertos'] += 1
        elif resultado == 'fallo': stats_letras[letra]['fallos'] += 1
    
    dominadas = []; en_progreso = []
    for letra, s in stats_letras.items():
        total = s['aciertos'] + s['fallos']
        if total < 3: en_progreso.append(letra); continue
        if (s['aciertos'] / total) >= 0.70: dominadas.append(letra)
        else: en_progreso.append(letra)
            
    msg_partes = []
    if dominadas: msg_partes.append(f"🏆 Dominadas: {', '.join(sorted(dominadas))}")
    if en_progreso: msg_partes.append(f"💪 Practicando: {', '.join(sorted(en_progreso))}")
    return " | ".join(msg_partes) if msg_partes else "Aún no hay suficientes datos."

def obtener_letras_desbloqueadas(estudiante_id):
    conn = conectar(); c = conn.cursor()
    c.execute("SELECT item, resultado FROM progreso WHERE estudiante_id = %s AND competencia != 'visual'", (estudiante_id,))
    data = c.fetchall(); conn.close()
    stats = {}
    for item, res in data:
        l = item[0].upper()
        if not l.isalpha(): continue
        if l not in stats: stats[l] = {'a':0, 'f':0}
        if res == 'acierto': stats[l]['a']+=1
        else: stats[l]['f']+=1
    return {l for l, s in stats.items() if (s['a']+s['f'])>=3 and (s['a']/(s['a']+s['f']) >= 0.7)}

# --- GESTIÓN DE FAMILIARES ---
def guardar_familiar(estudiante_id, nombre_clave, ruta_imagen):
    conn = conectar(); c = conn.cursor()
    c.execute("SELECT id FROM familiares WHERE estudiante_id = %s AND nombre_clave = %s", (estudiante_id, nombre_clave))
    existe = c.fetchone()
    if existe: c.execute("UPDATE familiares SET ruta_imagen = %s WHERE id = %s", (ruta_imagen, existe[0]))
    else: c.execute("INSERT INTO familiares (estudiante_id, nombre_clave, ruta_imagen) VALUES (%s, %s, %s)", (estudiante_id, nombre_clave, ruta_imagen))
    conn.commit(); conn.close()

def obtener_familia_map(estudiante_id):
    conn = conectar(); c = conn.cursor()
    c.execute("SELECT nombre_clave, ruta_imagen FROM familiares WHERE estudiante_id = %s", (estudiante_id,))
    data = c.fetchall(); conn.close()
    return {item[0]: item[1] for item in data}