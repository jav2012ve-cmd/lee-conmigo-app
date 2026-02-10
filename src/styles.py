import streamlit as st

def inyectar_css_personalizado():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@400;700&display=swap');
        
        /* 1. ESTABILIDAD VISUAL: Evita saltos horizontales forzando el scrollbar */
        html {
            overflow-y: scroll; 
        }
        
        html, body, [class*="css"] {
            font-family: 'Fredoka', sans-serif !important;
        }

        /* 2. LIMPIEZA: Ocultar menú de hamburguesa, footer y bordes de carga */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;} 
        .stDeployButton {display: none;}
        
        /* Ocultar la animación de carga superior (el "running man") */
        .stApp > header {display: none !important;}
        
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 5rem !important;
            max-width: 800px !important; /* Ancho fijo para evitar estiramientos raros */
            margin: 0 auto !important;
        }

        /* --- BOTONES COMPACTOS Y ESTABLES --- */
        div.stButton > button {
            width: 100%;
            border: none !important;
            border-radius: 15px !important;
            height: 60px !important; 
            min-height: 60px !important; /* Fuerza la altura para evitar colapsos */
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            color: white !important;
            background: linear-gradient(145deg, #42A5F5, #1E88E5);
            box-shadow: 0px 4px 0px #1565C0, 0px 5px 10px rgba(0,0,0,0.1) !important;
            transition: transform 0.1s, box-shadow 0.1s !important; /* Animación suave */
            position: relative;
            top: 0;
        }

        div.stButton > button p, 
        div.stButton > button div {
            font-size: 25px !important; 
            font-weight: 700 !important;
            margin: 0 !important;
            line-height: 1.2 !important;
        }

        /* Efecto de presión real */
        div.stButton > button:active {
            top: 4px !important;
            box-shadow: 0px 0px 0px #1565C0, inset 0px 2px 5px rgba(0,0,0,0.2) !important;
        }

        /* Estilos específicos columnas (Botones amarillos) */
        div[data-testid="column"] div.stButton > button {
            background: #FFF59D !important;
            color: #5D4037 !important;
            box-shadow: 0px 4px 0px #FBC02D, 0px 5px 5px rgba(0,0,0,0.1) !important;
            border: 2px solid #FFF176 !important;
        }
        
        div[data-testid="column"] div.stButton > button:active {
            box-shadow: 0px 0px 0px #FBC02D, inset 0px 2px 5px rgba(0,0,0,0.2) !important;
        }

        div.stButton > button:disabled {
            background: #ECEFF1 !important;
            color: #B0BEC5 !important;
            box-shadow: none !important;
            border: 2px dashed #CFD8DC !important;
            cursor: not-allowed;
            pointer-events: none;
        }
        
        /* FOTO DE PERFIL */
        div[data-testid="stImage"] img {
            border-radius: 20px !important;
            border: 3px solid #fff;
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            object-fit: cover;
        }
        
        /* Ocultar reproductor de audio completamente del flujo visual */
        .stAudio { display: none; }
        
        /* Ajuste de contenedores horizontales para que no bailen */
        div[data-testid="stHorizontalBlock"] { 
            align-items: center !important; 
            gap: 1rem !important;
        }
    </style>
    """, unsafe_allow_html=True)