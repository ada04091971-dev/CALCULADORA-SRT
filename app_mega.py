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
pesos_nervios_completos = { ... }  # (mantenés exactamente el mismo que tenías)

escalas_ms = { ... }  # (mantenés exactamente el mismo)

@st.cache_data
def cargar_datos():
    archivo = "calculadora_final_srt.xlsx"
    if not os.path.exists(archivo):
        archivos_xlsx = [f for f in os.listdir(".") if f.endswith(".xlsx")]
        archivo = archivos_xlsx[0] if archivos_xlsx else ""
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

# --- Interfaz ---
st.title("🧮 **Mega Calculadora SRT – Decreto 549/25**")
st.markdown("---")

if 'pericia' not in st.session_state:
    st.session_state.pericia = []

with st.sidebar:
    st.header("**Carga de hallazgos**")
    region = st.selectbox("**1. Región topográfica**", ["Columna", "MSI", "MSD", "MII", "MID"], index=None, placeholder="Seleccionar")
    
    # (mantenés exactamente todo el código de filtrado que ya tenías: región → tipo → categoría → sector → lesión)
    # ... [todo tu código de sidebar se mantiene igual hasta el botón AGREGAR]

# --- RESULTADOS ---
if st.session_state.pericia:
    st.subheader("**Detalle del dictamen médico**")
    
    # === NUEVA EXPLICACIÓN DIDÁCTICA ===
    st.info("""
    **Regla aplicada según Decreto 549/25**  
    • Dentro de cada **región topográfica / misma lateralidad** (MSI, MSD, MII, MID, Columna cervical, Columna dorsolumbar) → **suma aritmética** + **tope regional**.  
    • Entre regiones diferentes → **Capacidad Restante** (método Balthazard).
    """)

    sumas_seg = {}
    for i, p in enumerate(st.session_state.pericia):
        c1, c2, c3 = st.columns([2, 6, 1])
        c1.write(f"**{p['reg']}**")
        c2.write(f"{format_text(p['desc'])} ({p['val']}%)")
        if c3.button("🗑️", key=f"del_{i}"):
            st.session_state.pericia.pop(i)
            st.rerun()

        # Agrupación por región topográfica (suma aritmética dentro de la misma)
        desc_upper = p['desc'].upper()
        if p['reg'] == "Columna":
            llave = "Columna cervical" if any(x in desc_upper for x in ["CERVICAL", "C1","C2","C3","C4","C5","C6","C7","C8"]) else "Columna dorsolumbar"
        else:
            llave = p['reg']   # MSI, MSD, MII, MID
        sumas_seg[llave] = sumas_seg.get(llave, 0) + p['val']

    # Topes oficiales (Decreto 549/25)
    topes = {
        "MSI": 66.0,
        "MSD": 66.0,
        "MII": 70.0,
        "MID": 70.0,
        "Columna cervical": 40.0,
        "Columna dorsolumbar": 60.0
    }

    st.markdown("---")
    st.write("**Análisis de topes por región topográfica**")

    v_bal = []   # valores finales que irán al Balthazard
    for s, suma in sumas_seg.items():
        t = topes.get(s, 100.0)
        v_final = min(suma, t)
        v_bal.append(v_final)
        
        col1, col2, col3 = st.columns([3, 2, 3])
        col1.write(f"**{s}**")
        col2.metric("Suma bruta", f"{suma:.2f}%")
        if suma > t:
            col3.error(f"**Tope aplicado → {v_final:.2f}%** (máx. {t}%)")
        else:
            col3.success(f"Valor final: **{v_final:.2f}%**")

    # Cálculo final
    fis = balthazard(v_bal)   # Capacidad Restante entre regiones

    st.markdown("### **Factores de ponderación**")
    u_edad = st.number_input("**Edad del trabajador**", 14, 99, 17)
    f_e = 0.05 if u_edad <= 20 else 0.04 if u_edad <= 30 else 0.03 if u_edad <= 40 else 0.02
    u_dif = st.selectbox("**Dificultad para tareas habituales**", ["Leve (5%)", "Intermedia (10%)", "Alta (20%)"], index=1)
    f_d = {"Leve (5%)": 0.05, "Intermedia (10%)": 0.10, "Alta (20%)": 0.20}[u_dif]
    
    inc = fis * (f_e + f_d)
    res_f = min(fis + inc, 65.99) if fis < 66.0 else min(fis + inc, 100.0)

    col_l, col_r = st.columns(2)
    with col_l:
        st.metric("**Daño físico residual (Cap. Restante)**", f"{fis}%")
        st.metric("**Incremento por factores**", f"{round(inc, 2)}%")
    with col_r:
        if res_f >= 66.0:
            st.error(f"## **ILP FINAL: {round(res_f, 2)}% (TOTAL)**")
        else:
            st.success(f"## **ILP FINAL: {round(res_f, 2)}% (PARCIAL)**")

    if st.button("🚨 **BORRAR TODO EL DICTAMEN**"):
        st.session_state.pericia = []
        st.rerun()