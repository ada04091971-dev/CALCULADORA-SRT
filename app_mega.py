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
    """Fórmula de la capacidad restante."""
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

# --- Diccionarios Neurológicos (Basados en calculadoraNEURO.xlsx) ---
TABLA_M = {"M0": 1.0, "M1": 0.8, "M2": 0.8, "M3": 0.5, "M4": 0.2, "M5": 0.0}
TABLA_S = {"S0": 1.0, "S1": 0.8, "S2": 0.8, "S3": 0.5, "S4": 0.2, "S5": 0.0}

NERVIOS_SUPERIOR = {
    "Nervio Mediano Proximal (Brazo/Codo)": {"p_m": 0.7, "p_s": 0.3, "max": 0.40},
    "Nervio Mediano Distal (Muñeca)": {"p_m": 0.4, "p_s": 0.6, "max": 0.25},
    "Nervio Cubital Proximal (Codo)": {"p_m": 0.7, "p_s": 0.3, "max": 0.35},
    "Nervio Cubital Distal (Muñeca)": {"p_m": 0.7, "p_s": 0.3, "max": 0.25},
    "Nervio Radial": {"p_m": 0.9, "p_s": 0.1, "max": 0.30},
    "Nervio Músculo Cutáneo": {"p_m": 0.9, "p_s": 0.1, "max": 0.20},
    "Nervio Axilar": {"p_m": 0.98, "p_s": 0.02, "max": 0.20},
    "Nervio Plexo Braquial (Total)": {"p_m": 0.8, "p_s": 0.2, "max": 0.60}
}

NERVIOS_INFERIOR = {
    "Nervio Ciático Mayor": {"p_m": 0.5, "p_s": 0.5, "max": 0.50},
    "Nervio Femoral": {"p_m": 0.95, "p_s": 0.05, "max": 0.30},
    "Nervio Peroneo Común (CPE)": {"p_m": 0.7, "p_s": 0.3, "max": 0.25},
    "Nervio Tibial Posterior (Prox)": {"p_m": 0.6, "p_s": 0.4, "max": 0.20},
    "Nervio Tibial Anterior (Prox)": {"p_m": 0.95, "p_s": 0.05, "max": 0.15}
}

RAICES_ESPINALES = {
    "Cervical": {"Raíz C2": 3, "Raíz C3": 3, "Raíz C4": 3, "Raíz C5": 5, "Raíz C6": 9, "Raíz C7": 9, "Raíz C8": 8},
    "Dorsolumbar": {"Raíz D1-D12": 2, "Raíz L1-L5": 3, "Raíz S1-S2": 3, "Raíz S3-S5": 5}
}

with st.sidebar:
    st.header("**Carga de hallazgos**")
    tipo_hallazgo = st.radio("**Tipo de lesión**", ["Osteoarticular", "Neurológica"])
    region_sel = st.selectbox("**1. Región Topográfica**", ["Columna", "Miembro Superior", "Miembro Inferior"], index=None)
    
    if region_sel:
        if tipo_hallazgo == "Osteoarticular":
            # --- Lógica de Carga Osteoarticular Mejorada ---
            if region_sel == "Columna":
                sectores = ["Cervical", "Dorsal", "Lumbar", "Sacrococcigea", "Coxis"]
                sector_val = st.selectbox("**2. Sector**", sectores, index=None)
                hoja_nombre = sector_val
                lat_sel = None
            else:
                lat_sel = st.selectbox("**2. Lateralidad**", ["Derecho", "Izquierdo"], index=None)
                sectores = ["Hombro", "Brazo", "Codo", "Antebrazo", "Muñeca", "Mano", "Dedos"] if "Superior" in region_sel else ["Cadera", "Muslo", "Rodilla", "Pierna", "Tobillo", "Pie", "Dedos"]
                sector_val = st.selectbox("**3. Sector**", sectores, index=None)
                hoja_nombre = f"{region_sel} {lat_sel}"
            
            if sector_val and hoja_nombre:
                nombre_hoja_real = next((s for s in xls.sheet_names if hoja_nombre.lower() == s.lower().strip()), None)
                if nombre_hoja_real:
                    df = pd.read_excel(xls, sheet_name=nombre_hoja_real).fillna("")
                    # Identificación automática de columnas por nombre
                    col_sector = next((c for c in df.columns if "sector" in str(c).lower()), df.columns[0])
                    col_categoria = next((c for c in df.columns if "categor" in str(c).lower()), df.columns[1])
                    col_desc = next((c for c in df.columns if "descrip" in str(c).lower()), df.columns[2])
                    col_incap = next((c for c in df.columns if "incap" in str(c).lower() or "%" in str(c).lower()), df.columns[-1])

                    # Filtro de Sector (con Fallback si no hay coincidencias)
                    df_f = df[df[col_sector].astype(str).str.contains(str(sector_val), case=False, na=False)]
                    if df_f.empty: df_f = df

                    # Filtro de Categoría para facilitar navegación
                    lista_cat = ["Ver todas"] + sorted(df_f[col_categoria].unique().tolist())
                    cat_sel = st.selectbox(f"**Categoría en {sector_val}**", lista_cat)
                    if cat_sel != "Ver todas":
                        df_f = df_f[df_f[col_categoria] == cat_sel]

                    opciones = sorted(df_f[col_desc].unique().tolist())
                    item = st.selectbox(f"**Descripción ({len(opciones)})**", opciones, index=None)
                    if item:
                        valor = float(df_f[df_f[col_desc] == item][col_incap].iloc[0])
                        st.info(f"**Valor Baremo: ** **{valor}%**")
                        if st.button("Agregar Lesión"):
                            st.session_state.pericia.append({"reg": f"{sector_val} {lat_sel}" if lat_sel else sector_val, "val": valor, "miembro": region_sel, "sector": sector_val, "lado": lat_sel, "desc": item})
                            st.rerun()

        else: # Módulo Neurológico
            if region_sel == "Columna":
                cat_root = st.selectbox("**2. Sector de Raíz**", ["Cervical", "Dorsolumbar"], index=None)
                if cat_root:
                    root_sel = st.selectbox("**3. Raíz Espinal**", list(RAICES_ESPINALES[cat_root].keys()), index=None)
                    if root_sel:
                        valor_r = float(RAICES_ESPINALES[cat_root][root_sel])
                        st.warning(f"**Incapacidad Raíz: ** **{valor_r}%**")
                        if st.button("Agregar Raíz"):
                            st.session_state.pericia.append({"reg": f"Raíz {cat_root}", "val": valor_r, "miembro": "Columna", "sector": cat_root, "lado": None, "desc": root_sel})
                            st.rerun()
            else:
                lat_sel = st.selectbox("**2. Lateralidad**", ["Derecho", "Izquierdo"], index=None)
                if lat_sel:
                    dicc = NERVIOS_SUPERIOR if "Superior" in region_sel else NERVIOS_INFERIOR
                    nervio_sel = st.selectbox("**3. Nervio Periférico**", list(dicc.keys()), index=None)
                    if nervio_sel:
                        c1, c2 = st.columns(2)
                        gm = c1.selectbox("Grado M", list(TABLA_M.keys()), index=5)
                        gs = c2.selectbox("Grado S", list(TABLA_S.keys()), index=5)
                        n = dicc[nervio_sel]
                        valor_n = round(((TABLA_M[gm] * n['p_m']) + (TABLA_S[gs] * n['p_s'])) * n['max'] * 100, 2)
                        st.warning(f"**Incapacidad Calculada: ** **{valor_n}%**")
                        sector_dest = st.selectbox("**4. Asignar a Sector (Tope)**", ["Hombro", "Brazo", "Codo", "Antebrazo", "Muñeca", "Mano"] if "Superior" in region_sel else ["Cadera", "Muslo", "Rodilla", "Pierna", "Tobillo", "Pie"])
                        if st.button("Agregar Nervio"):
                            st.session_state.pericia.append({"reg": f"Nervio {lat_sel}", "val": valor_n, "miembro": region_sel, "sector": sector_dest, "lado": lat_sel, "desc": f"{nervio_sel} ({gm}/{gs})"})
                            st.rerun()

# --- 2. Cálculos y Visualización ---
if st.session_state.pericia:
    st.subheader("**Detalle de secuelas**")
    conteos = { (p['miembro'], p['lado'], p['sector'], p['desc']): 0 for p in st.session_state.pericia }
    for p in st.session_state.pericia:
        conteos[(p['miembro'], p['lado'], p['sector'], p['desc'])] += 1

    cervical_arit, dorsolumbar_arit, sacro_arit = 0.0, 0.0, 0.0
    miembros_data = {"superior derecho": {}, "superior izquierdo": {}, "inferior derecho": {}, "inferior izquierdo": {}}

    for i, p in enumerate(st.session_state.pericia):
        c1, c2, c3 = st.columns([3, 5, 1])
        dup = conteos[(p['miembro'], p['lado'], p['sector'], p['desc'])] > 1
        txt_r, txt_d = f"**{p['reg']}**", f"{p['desc']} (**{p['val']}%**)"
        if dup:
            c1.markdown(f":red[{txt_r}]"); c2.markdown(f":red[{txt_d}]")
        else:
            c1.markdown(txt_r); c2.markdown(txt_d)
        if c3.button("🗑️", key=f"d_{i}"): st.session_state.pericia.pop(i); st.rerun()

        v, s, m, l = p['val'], p['sector'], p['miembro'].lower(), p['lado'].lower() if p['lado'] else ""
        if "columna" in m:
            if "cervical" in s: cervical_arit += v
            elif s in ["dorsal", "lumbar", "dorsolumbar"]: dorsolumbar_arit += v
            else: sacro_arit += v
        else:
            llave = f"{m.replace('miembro ', '')} {l}"
            miembros_data[llave][s] = miembros_data[llave].get(s, 0) + v

    v_regionales = []
    total_col = min(min(cervical_arit, 40.0) + min(dorsolumbar_arit, 60.0) + sacro_arit, 100.0)
    if total_col > 0: v_regionales.append(total_col)

    for l in ["superior derecho", "superior izquierdo"]:
        d = miembros_data[l]; s1 = min(d.get("dedos", 0) + d.get("mano", 0) + d.get("muñeca", 0), 50.0)
        s2 = min(s1 + d.get("antebrazo", 0), 55.0); s3 = min(s2 + d.get("codo", 0) + d.get("brazo", 0), 60.0)
        if d: v_regionales.append(min(s3 + d.get("hombro", 0), 66.0))
            
    for l in ["inferior derecho", "inferior izquierdo"]:
        d = miembros_data[l]; s1 = min(d.get("dedos", 0) + d.get("pie", 0) + d.get("tobillo", 0), 35.0)
        s2 = min(s1 + d.get("pierna", 0), 40.0); s3 = min(s2 + d.get("rodilla", 0), 55.0)
        if d: v_regionales.append(min(s3 + d.get("muslo", 0) + d.get("cadera", 0), 70.0))

    st.markdown("---")
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("### **Factores de ponderación**")
        edad = st.number_input("**Edad**", 14, 99, 54) 
        if edad < 21: f_e = 0.05
        elif 21 <= edad <= 35: f_e = 0.04
        elif 36 <= edad <= 45: f_e = 0.03
        else: f_e = 0.02 
            
        f_d = st.selectbox("**Dificultad**", [0.05, 0.10, 0.20], format_func=lambda x: f"{int(x*100)}%")
        
        fisico = balthazard(v_regionales)
        factores = fisico * (f_e + f_d)
        total_f = min(fisico + factores, 65.99) if fisico < 66.0 else min(fisico + factores, 100.0)

    with col_r:
        st.metric("**Daño físico (Balthazard)**", f"{fisico}%")
        st.metric("**Factores aplicados**", f"{round(factores, 2)}%")
        st.success(f"## **ILP FINAL: ** **{round(total_f, 2)}%**")
        if st.button("🚨 Reiniciar"): st.session_state.pericia = []; st.rerun()