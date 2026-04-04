import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Mega Calculadora SRT", layout="wide")

def format_text(text):
    if not text: return ""
    return str(text).strip().capitalize()

# ====================== CARGA DE DATOS (nombres EXACTOS) ======================
@st.cache_data
def cargar_datos():
    archivo = "calculadora_final_srt.xlsx"
    if not os.path.exists(archivo):
        st.error("No se encontró calculadora_final_srt.xlsx")
        st.stop()

    # Diagnóstico (lo ves en la sidebar)
    with pd.ExcelFile(archivo) as xls:
        st.sidebar.info(f"Hojas detectadas: {xls.sheet_names}")

    sheets = {
        "Cervical": pd.read_excel(archivo, sheet_name="Cervical").fillna(""),
        "Dorsal": pd.read_excel(archivo, sheet_name="Dorsal").fillna(""),
        "Lumbar": pd.read_excel(archivo, sheet_name="Lumbar").fillna(""),
        "Sacrococcigea": pd.read_excel(archivo, sheet_name="Sacrococcigea").fillna(""),
        "Coxis": pd.read_excel(archivo, sheet_name="Coxis").fillna(""),
        "Miembros Superior Derecho": pd.read_excel(archivo, sheet_name="Miembros Superior Derecho").fillna(""),
        "Miembro superior Izquierdo": pd.read_excel(archivo, sheet_name="Miembro superior Izquierdo").fillna(""),
        "Miembro Inferior Derecho": pd.read_excel(archivo, sheet_name="Miembro Inferior Derecho").fillna(""),
        "Miembro Inferior Izquierdo": pd.read_excel(archivo, sheet_name="Miembro Inferior Izquierdo").fillna(""),
        "Neurologia": pd.read_excel(archivo, sheet_name="Neurologia").fillna(""),
    }

    # Limpiar columnas y porcentajes
    def limpiar(val):
        try:
            if isinstance(val, str):
                val = val.replace("%", "").replace(",", ".")
            return float(val)
        except:
            return 0.0

    for df in sheets.values():
        df.columns = df.columns.str.strip()
        if "% de Incapacidad Laboral" in df.columns:
            df["% de Incapacidad Laboral"] = df["% de Incapacidad Laboral"].apply(limpiar)

    return sheets

sheets = cargar_datos()

if 'pericia' not in st.session_state:
    st.session_state.pericia = []

# ====================== SIDEBAR ======================
with st.sidebar:
    st.header("**Carga de hallazgos**")

    capitulo = st.selectbox("**1. Capítulo**", ["Osteoarticular", "Sistema Nervioso"], index=0)

    if capitulo == "Osteoarticular":
        apartado = st.selectbox("**2. Apartado**", ["Columna Vertebral", "Miembro Superior", "Miembro Inferior"])
    else:
        apartado = "Neurologia"

    if apartado in ["Miembro Superior", "Miembro Inferior"]:
        lateralidad = st.radio("**3. Lateralidad**", ["Derecho", "Izquierdo"], horizontal=True)
    else:
        lateralidad = None

    # Categoría
    if apartado == "Columna Vertebral":
        cats = ["Ver todas", "Fracturas Vertebrales", "Lesiones Discales y Ligamentarias", "Limitación Funcional", "Anquilosis"]
    elif apartado == "Miembro Superior":
        cats = ["Ver todas", "Amputaciones", "Fracturas", "Artroplastias", "Inestabilidad Articular", "Lesiones Músculo-Tendinosas", "Limitación Funcional", "Anquilosis"]
    elif apartado == "Miembro Inferior":
        cats = ["Ver todas", "Amputaciones Del Miembro Inferior", "Fracturas Del Miembro Inferior", "Artroplastias Del Miembro Inferior", 
                "Lesiones Capsulo-Ligamentarias Y Meniscales", "Lesiones Músculo-Tendinosas", "Limitación Funcional", "Anquilosis", "Pelvis Inestable"]
    else:
        cats = ["Ver todas"]

    categoria = st.selectbox("**4. Categoría**", cats)

    # Nivel / Parte anatómica
    if apartado == "Columna Vertebral":
        niveles = ["Cervical", "Dorsal", "Lumbar", "Sacrococcigea", "Coxis"]
    elif apartado == "Miembro Superior":
        niveles = ["Hombro/Cintura escapular", "Codo", "Muñeca", "Mano", "Dedos"]
    elif apartado == "Miembro Inferior":
        niveles = ["Cadera", "Rodilla", "Tobillo", "Pie", "Pelvis"]
    else:
        niveles = ["Ver todos"]

    nivel = st.selectbox("**Nivel / Parte anatómica**", niveles)

    # ====================== FILTRADO ======================
    if apartado == "Columna Vertebral":
        sheet_name = nivel
    elif apartado == "Miembro Superior":
        sheet_name = "Miembros Superior Derecho" if lateralidad == "Derecho" else "Miembro superior Izquierdo"
    elif apartado == "Miembro Inferior":
        sheet_name = "Miembro Inferior Derecho" if lateralidad == "Derecho" else "Miembro Inferior Izquierdo"
    else:
        sheet_name = "Neurologia"

    df_fil = sheets.get(sheet_name, pd.DataFrame())

    if categoria != "Ver todas":
        df_fil = df_fil[df_fil['Descripción de Lesión'].str.contains(categoria, case=False, na=False)]

    opciones = sorted(df_fil['Descripción de Lesión'].dropna().unique())

    if opciones:
        lesion = st.selectbox("**Secuela específica**", opciones, format_func=format_text, index=None)
        if lesion:
            valor = df_fil[df_fil['Descripción de Lesión'] == lesion]['% de Incapacidad Laboral'].iloc[0]
            st.success(f"**Valor: {valor}%**")
            if st.button("**AGREGAR A LA PERICIA**"):
                st.session_state.pericia.append({
                    "apartado": apartado,
                    "lateralidad": lateralidad,
                    "categoria": categoria,
                    "nivel": nivel,
                    "lesion": lesion,
                    "valor": valor
                })
                st.rerun()

# ====================== RESULTADOS ======================
st.title("Mega Calculadora SRT – Decreto 549/25")

if st.session_state.pericia:
    st.subheader("Hallazgos cargados")
    for i, item in enumerate(st.session_state.pericia):
        col1, col2, col3 = st.columns([3, 5, 1])
        col1.write(f"**{item['apartado']}** {item.get('lateralidad','')}")
        col2.write(f"{item['lesion']} → **{item['valor']}%**")
        if col3.button("🗑️", key=f"del{i}"):
            st.session_state.pericia.pop(i)
            st.rerun()