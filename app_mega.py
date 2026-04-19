import streamlit as st
import pandas as pd
import os

# 1. Configuración de la aplicación
st.set_page_config(page_title="Calculadora laboral SRT", layout="wide", page_icon="🧮")

@st.cache_resource
def abrir_excel():
    archivo = "calculadora_final_srt.xlsx"
    if not os.path.exists(archivo):
        st.error(f"No se encontró el archivo '{archivo}' en la carpeta.")
        st.stop()
    return pd.ExcelFile(archivo)

def balthazard(lista):
    lista = sorted([x for x in lista if x > 0], reverse=True)
    if not lista: return 0.0
    total = lista[0]
    for i in range(1, len(lista)):
        total = total + (lista[i] * (100 - total) / 100)
    return round(total, 2)

if 'pericia' not in st.session_state:
    st.session_state.pericia = []

st.title("🧮 **Calculadora laboral SRT: Decreto 549/25**")
st.markdown("---")

xls = abrir_excel()

# --- DICCIONARIOS NEUROLÓGICOS (Basados en calculadoraNEURO.xlsx) ---
TABLA_M = {"M0": 1.0, "M1": 0.8, "M2": 0.8, "M3": 0.5, "M4": 0.2, "M5": 0.0}
TABLA_S = {"S0": 1.0, "S1": 0.8, "S2": 0.8, "S3": 0.5, "S4": 0.2, "S5": 0.0}

# Mapeo inicial MSD (Ejemplos extraídos de tu Excel)
NERVIOS_MSD = {
    "Nervio Mediano (Proximal)": {"peso_m": 0.5, "peso_s": 0.5, "max": 0.45},
    "Nervio Mediano (Distal)": {"peso_m": 0.4, "peso_s": 0.6, "max": 0.25},
    "Nervio Cubital (Proximal)": {"peso_m": 0.5, "peso_s": 0.5, "max": 0.35},
    "Nervio Cubital (Distal)": {"peso_m": 0.7, "peso_s": 0.3, "max": 0.25},
    "Nervio Radial": {"peso_m": 0.9, "peso_s": 0.1, "max": 0.45},
    "Nervio Circunflejo": {"peso_m": 1.0, "peso_s": 0.0, "max": 0.05}
}

with st.sidebar:
    st.header("**Carga de hallazgos**")
    tipo_hallazgo = st.radio("**Tipo de lesión**", ["Osteoarticular", "Neurológica Periférica"])
    
    region_sel = st.selectbox("**1. Región Topográfica**", ["Columna", "Miembro Superior", "Miembro Inferior"], index=None)
    
    if region_sel:
        # --- Lógica para lesiones OSTEARTICULARES (Tu código original) ---
        if tipo_hallazgo == "Osteoarticular":
            if region_sel == "Columna":
                sec_col = ["Cervical", "Dorsal", "Lumbar", "Sacrococcigea", "Coxis"]
                sector_val = st.selectbox("**2. Sector**", sec_col, index=None)
                hoja_buscada = sector_val
                lat_sel = None
            else:
                lat_sel = st.selectbox("**2. Lateralidad**", ["Derecho", "Izquierdo"], index=None)
                sectores_m = ["Hombro", "Brazo", "Codo", "Antebrazo", "Muñeca", "Mano", "Dedos"] if "Superior" in region_sel else ["Cadera", "Muslo", "Rodilla", "Pierna", "Tobillo", "Pie", "Dedos"]
                sector_val = st.selectbox("**3. Sector**", sectores_m, index=None)
                hoja_buscada = f"{region_sel} {lat_sel}" if lat_sel else None

            nombre_real_hoja = next((s for s in xls.sheet_names if hoja_buscada and hoja_buscada.lower() == s.lower().strip()), None)
            if nombre_real_hoja and sector_val:
                df = pd.read_excel(xls, sheet_name=nombre_real_hoja).fillna("")
                df_f = df[df[df.columns[0]].astype(str).str.contains(str(sector_val), case=False, na=False)]
                
                opciones = sorted(df_f[df_f.columns[2]].unique().tolist())
                item = st.selectbox(f"**Descripción ({len(opciones)})**", opciones, index=None)
                if item:
                    valor = float(df_f[df_f[df_f.columns[2]] == item][df_f.columns[3]].iloc[0])
                    st.info(f"**Valor baremo: {valor}%**")
                    if st.button("Agregar lesión"):
                        st.session_state.pericia.append({"reg": f"{sector_val} {lat_sel}" if lat_sel else sector_val, "val": valor, "miembro": region_sel, "sector": sector_val, "lado": lat_sel, "desc": item, "tipo": "O"})
                        st.rerun()

        # --- Lógica para lesiones NEUROLÓGICAS (Nueva integración) ---
        else:
            if region_sel == "Miembro Superior":
                lat_sel = st.selectbox("**2. Lateralidad**", ["Derecho", "Izquierdo"], index=None)
                if lat_sel == "Derecho":
                    nervio_sel = st.selectbox("**3. Nervio Periférico**", list(NERVIOS_MSD.keys()), index=None)
                    if nervio_sel:
                        col_m, col_s = st.columns(2)
                        grado_m = col_m.selectbox("Grado M", list(TABLA_M.keys()), index=5) # Default M5 (0%)
                        grado_s = col_s.selectbox("Grado S", list(TABLA_S.keys()), index=5) # Default S5 (0%)
                        
                        # Cálculo según fórmula de tu Excel
                        n_info = NERVIOS_MSD[nervio_sel]
                        def_n = ((TABLA_M[grado_m] * n_info['peso_m']) + (TABLA_S[grado_s] * n_info['peso_s'])) * n_info['max']
                        valor_n = round(def_n * 100, 2)
                        
                        st.warning(f"**Incapacidad calculada: {valor_n}%**")
                        sector_dest = st.selectbox("Asignar al sector (para tope)", ["Hombro", "Codo", "Antebrazo", "Muñeca", "Mano"])
                        
                        if st.button("Agregar Nervio"):
                            st.session_state.pericia.append({"reg": f"Nervio {lat_sel}", "val": valor_n, "miembro": region_sel, "sector": sector_dest, "lado": lat_sel, "desc": f"{nervio_sel} ({grado_m}/{grado_s})", "tipo": "N"})
                            st.rerun()

# --- 2. Lógica de Cálculos (Mantiene Aritmética de Columna y Escaleras) ---
if st.session_state.pericia:
    st.subheader("**Detalle de secuelas**")
    
    cervical_arit = 0.0
    dorsolumbar_arit = 0.0
    sacro_arit = 0.0
    miembros_data = {"Superior Derecho": {}, "Superior Izquierdo": {}, "Inferior Derecho": {}, "Inferior Izquierdo": {}}

    for i, p in enumerate(st.session_state.pericia):
        c1, c2, c3 = st.columns([3, 5, 1])
        c1.markdown(f"**{p['reg']}**")
        c2.markdown(f"{p['desc']} (**{p['val']}%**)")
        if c3.button("🗑️", key=f"del_{i}"): st.session_state.pericia.pop(i); st.rerun()

        v, s, m, l = p['val'], p['sector'], p['miembro'], p['lado']
        if m == "Columna":
            if s == "Cervical": cervical_arit += v
            elif s in ["Dorsal", "Lumbar"]: dorsolumbar_arit += v
            else: sacro_arit += v
        else:
            llave = f"{m.replace('Miembro ', '')} {l}"
            if s not in miembros_data[llave]: miembros_data[llave][s] = 0.0
            miembros_data[llave][s] += v

    # (Lógica de topes regionales se mantiene intacta para seguridad)
    cervical_f = min(cervical_arit, 40.0)
    dl_f = min(dorsolumbar_arit, 60.0)
    total_columna = min(cervical_f + dl_f + sacro_arit, 100.0)

    v_regionales = []
    if total_columna > 0: v_regionales.append(total_columna)
    
    for lado in ["Superior Derecho", "Superior Izquierdo"]:
        d = miembros_data[lado]
        if d:
            s1 = min(d.get("Dedos", 0) + d.get("Mano", 0) + d.get("Muñeca", 0), 50.0)
            s2 = min(s1 + d.get("Antebrazo", 0), 55.0)
            s3 = min(s2 + d.get("Codo", 0) + d.get("Brazo", 0), 60.0)
            v_regionales.append(min(s3 + d.get("Hombro", 0), 66.0))

    # --- 3. Resultados Finales (CON RANGOS DE EDAD CORREGIDOS) ---
    st.markdown("---")
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("### **Factores de ponderación**")
        edad = st.number_input("**Edad**", 14, 99, 25)
        
        # AJUSTE SEGÚN DECRETO 549/25 PÁG. 6
        if edad < 21: f_e = 0.05
        elif 21 <= edad <= 35: f_e = 0.04
        elif 36 <= edad <= 45: f_e = 0.03
        else: f_e = 0.02 # 46 años o más
            
        f_d = st.selectbox("**Dificultad**", [0.05, 0.10, 0.20], format_func=lambda x: f"{int(x*100)}%")
        
        fisico = balthazard(v_regionales)
        factores = fisico * (f_e + f_d)
        total_p = fisico + factores
        total_f = min(total_p, 65.99) if fisico < 66.0 else min(total_p, 100.0)

    with col_r:
        st.metric("**Daño físico (Balthazard)**", f"{fisico}%")
        st.metric("**Factores aplicados**", f"{round(factores, 2)}%")
        st.success(f"## **ILP final: ** **{round(total_f, 2)}%**")