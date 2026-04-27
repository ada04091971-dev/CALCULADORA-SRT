import streamlit as st
import pandas as pd
import os

# 1. Configuración de la aplicación
st.set_page_config(page_title="Calculadora Laboral SRT - Integral", layout="wide", page_icon="🧮")

@st.cache_resource
def abrir_excel():
    archivo = "calculadora_final_srt.xlsx"
    if not os.path.exists(archivo):
        st.error(f"No se encontró el archivo '{archivo}' en la carpeta.")
        st.stop()
    return pd.ExcelFile(archivo)

def balthazard(lista):
    """Método de la capacidad restante."""
    lista = sorted([x for x in lista if x > 0], reverse=True)
    if not lista: return 0.0
    total = lista[0]
    for i in range(1, len(lista)):
        total = total + (lista[i] * (100 - total) / 100)
    return round(total, 2)

if 'pericia' not in st.session_state:
    st.session_state.pericia = []

st.title("🧮 **Calculadora Laboral SRT: Baremo Integral 549/25**")
st.markdown("---")

xls = abrir_excel()

# --- Diccionarios Neurológicos (Lógica de fórmulas) ---
TABLA_M = {"M0": 1.0, "M1": 0.8, "M2": 0.8, "M3": 0.5, "M4": 0.2, "M5": 0.0}
TABLA_S = {"S0": 1.0, "S1": 0.8, "S2": 0.8, "S3": 0.5, "S4": 0.2, "S5": 0.0}

NERVIOS_UPPER = {
    "Nervio Mediano Proximal (Brazo/Codo)": {"p_m": 0.7, "p_s": 0.3, "max": 0.40},
    "Nervio Mediano Distal (Muñeca)": {"p_m": 0.4, "p_s": 0.6, "max": 0.25},
    "Nervio Cubital Proximal (Codo)": {"p_m": 0.7, "p_s": 0.3, "max": 0.35},
    "Nervio Cubital Distal (Muñeca)": {"p_m": 0.7, "p_s": 0.3, "max": 0.25},
    "Nervio Radial": {"p_m": 0.9, "p_s": 0.1, "max": 0.30},
    "Nervio Plexo Braquial (Total)": {"p_m": 0.8, "p_s": 0.2, "max": 0.60}
}

NERVIOS_LOWER = {
    "Nervio Ciático Mayor": {"p_m": 0.5, "p_s": 0.5, "max": 0.50},
    "Nervio Peroneo Común (CPE)": {"p_m": 0.7, "p_s": 0.3, "max": 0.25},
    "Nervio Tibial Anterior (Prox)": {"p_m": 0.95, "p_s": 0.05, "max": 0.15}
}

RAICES = {
    "Cervical": {"Raíz C2": 3, "Raíz C3": 3, "Raíz C4": 3, "Raíz C5": 5, "Raíz C6": 9, "Raíz C7": 9, "Raíz C8": 8},
    "Dorsolumbar": {"Raíz D1-D12": 2, "Raíz L1-L5": 3, "Raíz S1-S2": 3, "Raíz S3-S5": 5}
}

with st.sidebar:
    st.header("**Carga de Hallazgos**")
    
    # 1. Selección del Capítulo del Baremo
    capitulos_disponibles = ["Osteoarticular", "Neurológica", "Psiquiatría", "Piel/Quemaduras", "Interna/Otros"]
    cap_sel = st.selectbox("**1. Capítulo del Baremo**", capitulos_disponibles, index=None)
    
    if cap_sel == "Neurológica":
        # Módulo Neurológico (Lógica de Fórmulas)
        region_neuro = st.selectbox("**2. Región**", ["Columna (Raíces)", "Miembro Superior", "Miembro Inferior"], index=None)
        if region_neuro == "Columna (Raíces)":
            sec = st.selectbox("**3. Sector**", ["Cervical", "Dorsolumbar"])
            raiz = st.selectbox("**4. Raíz**", list(RAICES[sec].keys()))
            val = RAICES[sec][raiz]
            if st.button("Agregar Raíz"):
                st.session_state.pericia.append({"cap": "Neuro", "reg": sec, "val": val, "desc": raiz, "tipo": "neuro"})
                st.rerun()
        elif region_neuro:
            lat = st.selectbox("**3. Lateralidad**", ["Derecho", "Izquierdo"])
            dicc = NERVIOS_UPPER if "Superior" in region_neuro else NERVIOS_LOWER
            nervio = st.selectbox("**4. Nervio**", list(dicc.keys()))
            gm = st.selectbox("Grado M", list(TABLA_M.keys()), index=5)
            gs = st.selectbox("Grado S", list(TABLA_S.keys()), index=5)
            n_data = dicc[nervio]
            val = round(((TABLA_M[gm] * n_data['p_m']) + (TABLA_S[gs] * n_data['p_s'])) * n_data['max'] * 100, 2)
            # Asignación a sector para tope regional
            sec_tope = st.selectbox("**5. Sector para Tope**", ["Hombro", "Brazo", "Codo", "Muñeca", "Mano"] if "Superior" in region_neuro else ["Cadera", "Rodilla", "Tobillo", "Pie"])
            if st.button("Agregar Nervio"):
                st.session_state.pericia.append({"cap": "Neuro", "reg": f"{sec_tope} {lat}", "val": val, "desc": f"{nervio} ({gm}/{gs})", "tipo": "neuro"})
                st.rerun()

    elif cap_sel:
        # Lógica General (Lee del Excel según el nombre del capítulo)
        # Si es Osteoarticular, necesita un paso previo para elegir la hoja correcta
        if cap_sel == "Osteoarticular":
            sub_reg = st.selectbox("**2. Región**", ["Columna", "Miembro Superior", "Miembro Inferior"], index=None)
            if sub_reg == "Columna":
                sectores = ["Cervical", "Dorsal", "Lumbar", "Sacrococcigea", "Coxis"]
                sec_val = st.selectbox("**3. Sector**", sectores, index=None)
                hoja_buscada = sec_val
                lado_txt = ""
            elif sub_reg:
                lado = st.selectbox("**3. Lateralidad**", ["Derecho", "Izquierdo"], index=None)
                sectores = ["Hombro", "Codo", "Muñeca", "Mano", "Dedos"] if "Superior" in sub_reg else ["Cadera", "Rodilla", "Tobillo", "Pie"]
                sec_val = st.selectbox("**4. Sector**", sectores, index=None)
                hoja_buscada = f"{sub_reg} {lado}"
                lado_txt = lado
            else:
                sec_val, hoja_buscada = None, None
        else:
            # Para otros capítulos, la solapa se llama igual que el capítulo
            sec_val, hoja_buscada = cap_sel, cap_sel
            lado_txt = ""

        if sec_val and hoja_buscada:
            nombre_real = next((s for s in xls.sheet_names if hoja_buscada.lower() == s.lower().strip()), None)
            if nombre_real:
                df = pd.read_excel(xls, sheet_name=nombre_real).fillna("")
                df.columns = [str(c).strip() for c in df.columns]
                
                # Identificación automática de columnas jerárquicas
                col_cat = next((c for c in df.columns if "categor" in c.lower() and "sub" not in c.lower()), df.columns[1])
                col_sub = next((c for c in df.columns if "sub" in c.lower()), None)
                col_des = next((c for c in df.columns if "descrip" in c.lower()), df.columns[2])
                col_inc = next((c for c in df.columns if "incap" in c.lower() or "%" in c.lower()), df.columns[-1])

                # Filtro por sector si el capítulo es Osteoarticular
                if cap_sel == "Osteoarticular":
                    col_sec = next((c for c in df.columns if "sector" in c.lower()), df.columns[0])
                    df = df[df[col_sec].astype(str).str.contains(str(sec_val), case=False, na=False)]

                # Navegación en cascada
                cat = st.selectbox("**Categoría**", ["Elegir..."] + sorted(df[col_cat].unique().tolist()))
                if cat != "Elegir...":
                    df = df[df[col_cat] == cat]
                    if col_sub:
                        subs = [s for s in df[col_sub].unique().tolist() if str(s).strip() != ""]
                        if subs:
                            sub_sel = st.selectbox("**Subcategoría**", ["Elegir..."] + sorted(subs))
                            if sub_sel != "Elegir...": df = df[df[col_sub] == sub_sel]
                    
                    item = st.selectbox("**Lesión**", sorted(df[col_des].unique().tolist()), index=None)
                    if item:
                        valor = float(df[df[col_des] == item][col_inc].iloc[0])
                        st.info(f"**Valor Baremo: {valor}%**")
                        if st.button("Agregar Hallazgo"):
                            st.session_state.pericia.append({"cap": cap_sel, "reg": f"{sec_val} {lado_txt}".strip(), "val": valor, "desc": f"{cat} - {item}", "tipo": "osteo"})
                            st.rerun()

# --- 2. Cálculos y Visualización ---
if st.session_state.pericia:
    st.subheader("**Resumen de la Pericia**")
    
    acumuladores = {"cervical": 0.0, "dorsolumbar": 0.0, "sacro": 0.0, "msd": {}, "msi": {}, "mid": {}, "mii": {}, "otros": []}

    for i, p in enumerate(st.session_state.pericia):
        c1, c2, c3 = st.columns([2, 6, 1])
        c1.markdown(f"**{p['cap']} - {p['reg']}**")
        c2.write(f"{p['desc']} (**{p['val']}%**)")
        if c3.button("🗑️", key=f"del_{i}"): st.session_state.pericia.pop(i); st.rerun()

        # Distribución de valores para aplicación de topes
        v, r, c = p['val'], p['reg'].lower(), p['cap']
        if "cervical" in r: acumuladores["cervical"] += v
        elif any(x in r for x in ["dorsal", "lumbar"]): acumuladores["dorsolumbar"] += v
        elif "sacro" in r or "coxis" in r: acumuladores["sacro"] += v
        elif "superior derecho" in r or "superior derecho" in r: # Lógica para miembros
            # Aquí iría la lógica de escalera para MS/MI similar a la anterior
            pass 
        else:
            acumuladores["otros"].append(v)

    # --- Aplicación de Topes (Regla de Oro) ---
    v_finales = []
    # Columna
    final_col = min(min(acumuladores["cervical"], 40.0) + min(acumuladores["dorsolumbar"], 60.0) + acumuladores["sacro"], 100.0)
    if final_col > 0: v_finales.append(final_col)
    # Otros Capítulos
    for v in acumuladores["otros"]: v_finales.append(v)

    st.markdown("---")
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("### **Factores de Ponderación**")
        edad = st.number_input("**Edad**", 14, 99, 54)
        f_e = 0.05 if edad < 21 else 0.04 if edad <= 35 else 0.03 if edad <= 45 else 0.02
        dif_map = {"Leve (5%)": 0.05, "Intermedia (10%)": 0.10, "Alta (20%)": 0.20}
        f_d = dif_map[st.selectbox("**Dificultad**", list(dif_map.keys()))]
        
        fisico = balthazard(v_finales)
        factores = fisico * (f_e + f_d)
        total_f = min(fisico + factores, 65.99) if fisico < 66.0 else min(fisico + factores, 100.0)

    with col_r:
        st.metric("**Daño Físico (Balthazard)**", f"{fisico}%")
        st.metric("**Factores de Ponderación**", f"{round(factores, 2)}%")
        st.success(f"## **ILP FINAL: {round(total_f, 2)}%**")
        if st.button("🚨 Reiniciar"): st.session_state.pericia = []; st.rerun()