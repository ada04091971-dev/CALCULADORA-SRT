import streamlit as st
import pandas as pd
import os

# --- Configuración inicial ---
st.set_page_config(page_title="Calculadora integral SRT", layout="wide", page_icon="🧮")

def format_text(text):
    if not text: return ""
    text = str(text).strip()
    return text[0].upper() + text[1:]

# --- DICCIONARIO MAESTRO DE PESOS (Nervios) ---
pesos_nervios_completos = {
    "Supraescapular": {"m": 1.0, "s": 0.0}, "Torácico largo": {"m": 1.0, "s": 0.0},
    "Axilar": {"m": 0.98, "s": 0.02}, "Circunflejo": {"m": 0.98, "s": 0.02},
    "Radial": {"m": 0.90, "s": 0.10}, "Músculo cutáneo": {"m": 0.90, "s": 0.10},
    "Interóseo posterior": {"m": 1.0, "s": 0.0}, "Antebraquial cutáneo medial": {"m": 0.0, "s": 1.0},
    "Mediano": {"m": 0.70, "s": 0.30}, "Interóseo anterior": {"m": 1.0, "s": 0.0},
    "Cubital": {"m": 0.70, "s": 0.30}, "Digital": {"m": 0.0, "s": 1.0}, "Colateral": {"m": 0.0, "s": 1.0},
    "Crural": {"m": 0.80, "s": 0.20}, "Femoral": {"m": 0.80, "s": 0.20}, "Obturador": {"m": 1.0, "s": 0.0},
    "Femorocutáneo": {"m": 0.0, "s": 1.0}, "Ciático mayor": {"m": 0.70, "s": 0.30},
    "Peroneo común": {"m": 0.70, "s": 0.30}, "Ciático poplíteo externo": {"m": 0.70, "s": 0.30},
    "Peroneo superficial": {"m": 0.0, "s": 1.0}, "Tibial anterior": {"m": 0.75, "s": 0.25},
    "Ciático poplíteo interno": {"m": 0.60, "s": 0.40}, "Tibial": {"m": 0.60, "s": 0.40},
    "Tibial posterior": {"m": 0.50, "s": 0.50}, "Safeno": {"m": 0.0, "s": 1.0},
    "Sural": {"m": 0.0, "s": 1.0}, "Plantar": {"m": 0.30, "s": 0.70}
}

escalas_ms = {
    "Grado 5 (Normal - 0%)": 0.0, "Grado 4 (Leve - 20%)": 0.2, "Grado 3 (Moderado - 50%)": 0.5,
    "Grado 2 (Grave - 80%)": 0.8, "Grado 1 (Severo - 90%)": 0.9, "Grado 0 (Total - 100%)": 1.0
}

@st.cache_data
def cargar_datos():
    archivo = "calculadora_final_srt.xlsx"
    if not os.path.exists(archivo):
        archivos_xlsx = [f for f in os.listdir(".") if f.endswith(".xlsx")]
        archivo = archivos_xlsx[0] if archivos_xlsx else ""
    if not archivo: 
        st.error("No se encontró el archivo calculadora_final_srt.xlsx")
        st.stop()
    df = pd.read_excel(archivo, sheet_name="Hoja1").fillna("")
    df.columns = df.columns.str.strip()
    
    def limpiar_numero(val):
        try:
            if isinstance(val, str): val = val.replace('%', '').replace(',', '.')
            n = float(val)
            return n * 100 if 0 < n < 1 else n
        except: return 0.0
    if '% de Incapacidad Laboral' in df.columns:
        df['% de Incapacidad Laboral'] = df['% de Incapacidad Laboral'].apply(limpiar_numero)
    return df

df_maestro = cargar_datos()

def balthazard(lista):
    lista = sorted([x for x in lista if x > 0], reverse=True)
    if not lista: return 0.0
    total = lista[0]
    for i in range(1, len(lista)):
        total = total + (lista[i] * (100 - total) / 100)
    return round(total, 2)

# =============================================
# ================= INTERFAZ ==================
# =============================================
st.title("🧮 **Mega Calculadora SRT – Decreto 549/25**")
st.markdown("---")

if 'pericia' not in st.session_state:
    st.session_state.pericia = []

with st.sidebar:
    st.header("**Carga de hallazgos**")
    region = st.selectbox("**1. Región topográfica**", ["Columna", "MSI", "MSD", "MII", "MID"], index=None, placeholder="Seleccionar")
    
    if region:
        if region == "Columna": 
            kw = "Columna|Cervical|Dorsal|Lumbar|Sacro|Radicular|Medular|C1|C2|C3|C4|C5|C