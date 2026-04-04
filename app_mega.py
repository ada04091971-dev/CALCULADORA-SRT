import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Mega Calculadora SRT", layout="wide")

def format_text(text):
    if not text: return ""
    return str(text).strip().capitalize()

# Carga de datos (con nombres exactos de las hojas)
@st.cache_data
def cargar_datos():
    archivo = "calculadora_final_srt.xlsx"
    if not os.path.exists(archivo):
        st.error("No se encontró calculadora_final_srt.xlsx")
        st.stop()

    df_main = pd.read_excel(archivo, sheet_name="Lesiones ").fillna("")
    df_mid = pd.read_excel(archivo, sheet_name="Miembro Inferior  Derecho").fillna("")
    df_mii = pd.read_excel(archivo, sheet_name="Miembro Inferior Izquierdo").fillna("")

    df_main.columns = df_main.columns.str.strip()
    df_mid.columns = df_mid.columns.str.strip()
    df_mii.columns = df_mii.columns.str.strip()

    def limpiar(val):
        try:
            if isinstance(val, str):
                val = val.replace("%", "").replace(",", ".")
            return float(val)
        except:
            return 0.0

    for df in [df_main, df_mid, df_mii]:
        if "% de Incapacidad Laboral" in df.columns:
            df["% de Incapacidad Laboral"] = df["% de Incapacidad Laboral"].apply(limpiar)

    return df_main, df_mid, df_mii

df_main, df_mid, df_mii = cargar_datos()

if 'pericia' not in st.session_state:
    st.session_state.pericia = []

# =============================================
# ================= SIDEBAR ===================
# =============================================
with st.sidebar:
    st.header("**Carga de hallazgos**")

    capitulo = st.selectbox("**1. Capítulo**", ["Osteoarticular", "Sistema Nervioso"], index=0)

    if capitulo == "Osteoarticular":
        apartado_options = ["Columna Vertebral", "Miembro Superior", "Miembro Inferior"]
    else:
        apartado_options = ["Columna Vertebral", "Miembro Superior", "Miembro Inferior"]

    apartado = st.selectbox("**2. Apartado**", apartado_options)

    # Lateralidad (solo para extremidades)
    if apartado in ["Miembro Superior", "Miembro Inferior"]:
        lateralidad = st.radio("**3. Lateralidad**", ["Derecho", "Izquierdo"], horizontal=True)
    else:
        lateralidad = None

    # Categoría dinámica
    if apartado == "Columna Vertebral":
        cats = ["Ver todas", "Fracturas Vertebrales", "Lesiones Discales y Ligamentarias", "Limitación Funcional", "Anquilosis"]
    elif apartado == "Miembro Superior":
        cats = ["Ver todas", "Amputaciones", "Fracturas", "Artroplastias", "Inestabilidad Articular", "Lesiones Músculo-Tendinosas", "Limitación Funcional", "Anquilosis"]
    else:  # Miembro Inferior
        cats = ["Ver todas", "Amputaciones", "Fracturas", "Artroplastias", "Lesiones Capsulo-Ligamentarias Y Meniscales", "Lesiones Músculo-Tendinosas", "Limitación Funcional", "Anquilosis", "Pelvis Inestable"]

    categoria = st.selectbox("**4. Categoría**", cats)

    # Nivel / Parte anatómica (este era el que estaba vacío)
    if apartado == "Miembro Superior":
        niveles = ["Hombro/Cintura escapular", "Codo", "Muñeca", "Mano", "Dedos"]
    elif apartado == "Miembro Inferior":
        niveles = ["Cadera", "Rodilla", "Tobillo", "Pie", "Pelvis"]
    else:
        niveles = ["Ver todos"]

    nivel = st.selectbox("**Nivel / Parte anatómica**", niveles)

    # === FILTRADO FINAL ===
    if apartado == "Columna Vertebral":
        df_fil = df_main[df_main['Apartado'].str.contains("Columna Vertebral", case=False)].copy()
    elif apartado == "Miembro Superior":
        df_fil = df_main[df_main['Apartado'].str.contains("Miembro Superior", case=False)].copy()
    elif apartado == "Miembro Inferior" and lateralidad == "Derecho":
        df_fil = df_mid.copy()
    else:
        df_fil = df_mii.copy()

    # Filtro por categoría
    if categoria != "Ver todas":
        if apartado == "Miembro Inferior":
            # Usamos la columna "Categorias" que creaste en las hojas inferiores
            df_fil = df_fil[df_fil['Categorias'].str.contains(categoria, case=False, na=False)]
        else:
            df_fil = df_fil[df_fil['Descripción de Lesión'].str.contains(categoria, case=False)]

    # Filtro por Nivel / Parte anatómica
    if nivel != "Ver todos":
        if apartado == "Miembro Inferior":
            df_fil = df_fil[df_fil['Categorias'].str.contains(nivel, case=False, na=False)]
        else:
            # Para miembro superior y columna usamos palabras clave en la descripción
            map_nivel = {
                "Hombro/Cintura escapular": "Hombro|escapular|clavícula|escápula|glenohumeral",
                "Codo": "Codo|cúbito|tríceps|bíceps",
                "Muñeca": "Muñeca|carpo|escafoides|semilunar",
                "Mano": "Mano|metacarpiano|dedo|pulgar",
                "Dedos": "Dedos|falange|pulgar|índice|mayor|anular|meñique",
                "Cadera": "Cadera|coxofemoral|fémur",
                "Rodilla": "Rodilla|rótula|tibia|peroné",
                "Tobillo": "Tobillo|astrágalo|cálcaneo",
                "Pie": "Pie|metatarsiano|tarso|dedo del pie",
                "Pelvis": "Pelvis|hemipelvis|iliaco|cotilo"
            }
            kw = map_nivel.get(nivel, nivel)
            df_fil = df_fil[df_fil['Descripción de Lesión'].str.contains(kw, case=False)]

    opciones = sorted(df_fil['Descripción de Lesión'].dropna().unique())

    if opciones:
        lesion = st.selectbox("**Secuela específica**", opciones, format_func=format_text, index=None)
        if lesion:
            valor = df_fil[df_fil['Descripción de Lesión'] == lesion]['% de Incapacidad Laboral'].iloc[0]
            st.success(f"**Valor: {valor}%**")
            if st.button("**AGREGAR A LA PERICIA**"):
                st.session_state.pericia.append({
                    "capitulo": capitulo,
                    "apartado": apartado,
                    "lateralidad": lateralidad,
                    "categoria": categoria,
                    "nivel": nivel,
                    "lesion": lesion,
                    "valor": valor
                })
                st.rerun()

# =============================================
# ================= RESULTADOS =================
# =============================================
st.title("Mega Calculadora SRT – Decreto 549/25")

if st.session_state.pericia:
    st.subheader("Hallazgos cargados")
    for i, item in enumerate(st.session_state.pericia):
        col1, col2, col3 = st.columns([3, 5, 1])
        col1.write(f"**{item['apartado']}** - {item.get('lateralidad','')}")
        col2.write(f"{item['lesion']} → **{item['valor']}%**")
        if col3.button("🗑️", key=f"del{i}"):
            st.session_state.pericia.pop(i)
            st.rerun()