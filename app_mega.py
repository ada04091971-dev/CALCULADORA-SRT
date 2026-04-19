import streamlit as st
import pandas as pd
import os

# 1. configuración de la aplicación
st.set_page_config(page_title="calculadora laboral srt", layout="wide", page_icon="🧮")

@st.cache_resource
def abrir_excel():
    archivo = "calculadora_final_srt.xlsx"
    if not os.path.exists(archivo):
        st.error(f"no se encontró el archivo '{archivo}' en la carpeta.")
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

st.title("🧮 **calculadora laboral srt: decreto 549/25**")
st.markdown("---")

xls = abrir_excel()

# --- diccionarios neurológicos (datos de calculadoraneuro.xlsx) ---
TABLA_M = {"M0": 1.0, "M1": 0.8, "M2": 0.8, "M3": 0.5, "M4": 0.2, "M5": 0.0}
TABLA_S = {"S0": 1.0, "S1": 0.8, "S2": 0.8, "S3": 0.5, "S4": 0.2, "S5": 0.0}

# miembros superiores (msd/msi)
NERVIOS_SUPERIOR = {
    "nervio mediano proximal": {"p_m": 0.7, "p_s": 0.3, "max": 0.40},
    "nervio mediano distal": {"p_m": 0.4, "p_s": 0.6, "max": 0.25},
    "nervio cubital proximal": {"p_m": 0.7, "p_s": 0.3, "max": 0.35},
    "nervio cubital distal": {"p_m": 0.7, "p_s": 0.3, "max": 0.25},
    "nervio radial": {"p_m": 0.9, "p_s": 0.1, "max": 0.30},
    "nervio músculo cutáneo": {"p_m": 0.9, "p_s": 0.1, "max": 0.20},
    "nervio axilar": {"p_m": 0.98, "p_s": 0.02, "max": 0.20},
    "nervio supraescapular": {"p_m": 1.0, "p_s": 0.0, "max": 0.05},
    "nervio torácico largo": {"p_m": 1.0, "p_s": 0.0, "max": 0.05},
    "nervio interoseo anterior": {"p_m": 1.0, "p_s": 0.0, "max": 0.15},
    "nervio interoseo posterior": {"p_m": 1.0, "p_s": 0.0, "max": 0.10}
}

# miembros inferiores (mid/mii)
NERVIOS_INFERIOR = {
    "nervio ciático": {"p_m": 0.5, "p_s": 0.5, "max": 0.50},
    "nervio femoral": {"p_m": 0.95, "p_s": 0.05, "max": 0.30},
    "nervio peroneo común": {"p_m": 0.7, "p_s": 0.3, "max": 0.25},
    "nervio tibial posterior (prox)": {"p_m": 0.6, "p_s": 0.4, "max": 0.20},
    "nervio tibial anterior (prox)": {"p_m": 0.95, "p_s": 0.05, "max": 0.15},
    "nervio plantar (ext/int)": {"p_m": 0.3, "p_s": 0.7, "max": 0.10},
    "nervio sural": {"p_m": 0.0, "p_s": 1.0, "max": 0.05},
    "nervio safeno": {"p_m": 0.0, "p_s": 1.0, "max": 0.05}
}

# raíces espinales (carga simplificada)
RAICES_ESPINALES = {
    "cervical": {"raíz c2": 3, "raíz c3": 3, "raíz c4": 3, "raíz c5": 5, "raíz c6": 9, "raíz c7": 9, "raíz c8": 8},
    "dorsolumbar": {"raíz d1-d12": 2, "raíz l1-l5": 3, "raíz s1-s2": 3, "raíz s3-s5": 5}
}

with st.sidebar:
    st.header("**carga de hallazgos**")
    tipo_hallazgo = st.radio("**tipo de lesión**", ["osteoarticular", "neurológica"])
    region_sel = st.selectbox("**1. región topográfica**", ["columna", "miembro superior", "miembro inferior"], index=None)
    
    if region_sel:
        if tipo_hallazgo == "osteoarticular":
            # [bloque osteoarticular original]
            if region_sel == "columna":
                sectores = ["cervical", "dorsal", "lumbar", "sacrococcigea", "coxis"]
                sector_val = st.selectbox("**2. sector**", sectores, index=None)
                hoja = sector_val
                lat_sel = None
            else:
                lat_sel = st.selectbox("**2. lateralidad**", ["derecho", "izquierdo"], index=None)
                sectores = ["hombro", "brazo", "codo", "antebrazo", "muñeca", "mano", "dedos"] if "superior" in region_sel else ["cadera", "muslo", "rodilla", "pierna", "tobillo", "pie", "dedos"]
                sector_val = st.selectbox("**3. sector**", sectores, index=None)
                hoja = f"{region_sel} {lat_sel}"
            
            if sector_val and hoja:
                nombre_hoja = next((s for s in xls.sheet_names if hoja.lower() == s.lower().strip()), None)
                if nombre_hoja:
                    df = pd.read_excel(xls, sheet_name=nombre_hoja).fillna("")
                    df_f = df[df[df.columns[0]].astype(str).str.contains(str(sector_val), case=False, na=False)]
                    opciones = sorted(df_f[df_f.columns[2]].unique().tolist())
                    item = st.selectbox(f"**descripción ({len(opciones)})**", opciones, index=None)
                    if item:
                        valor = float(df_f[df_f[df_f.columns[2]] == item][df_f.columns[3]].iloc[0])
                        st.info(f"**valor baremo: ** **{valor}%**")
                        if st.button("agregar"):
                            st.session_state.pericia.append({"reg": f"{sector_val} {lat_sel}" if lat_sel else sector_val, "val": valor, "miembro": region_sel, "sector": sector_val, "lado": lat_sel, "desc": item})
                            st.rerun()

        else: # neurológica
            if region_sel == "columna":
                cat_root = st.selectbox("**2. sector de raíz**", ["cervical", "dorsolumbar"], index=None)
                if cat_root:
                    root_sel = st.selectbox("**3. raíz espinal**", list(RAICES_ESPINALES[cat_root].keys()), index=None)
                    if root_sel:
                        valor_r = float(RAICES_ESPINALES[cat_root][root_sel])
                        st.warning(f"**incapacidad raíz: ** **{valor_r}%**")
                        if st.button("agregar raíz"):
                            st.session_state.pericia.append({"reg": f"raíz {cat_root}", "val": valor_r, "miembro": "columna", "sector": cat_root, "lado": None, "desc": root_sel})
                            st.rerun()
            else:
                lat_sel = st.selectbox("**2. lateralidad**", ["derecho", "izquierdo"], index=None)
                if lat_sel:
                    dicc = NERVIOS_SUPERIOR if "superior" in region_sel else NERVIOS_INFERIOR
                    nervio_sel = st.selectbox("**3. nervio periférico**", list(dicc.keys()), index=None)
                    if nervio_sel:
                        c1, c2 = st.columns(2)
                        gm = c1.selectbox("grado m", list(TABLA_M.keys()), index=5)
                        gs = c2.selectbox("grado s", list(TABLA_S.keys()), index=5)
                        n = dicc[nervio_sel]
                        valor_n = round(((TABLA_M[gm] * n['p_m']) + (TABLA_S[gs] * n['p_s'])) * n['max'] * 100, 2)
                        st.warning(f"**incapacidad calculada: ** **{valor_n}%**")
                        sector_dest = st.selectbox("**4. sector (para tope)**", ["hombro", "brazo", "codo", "antebrazo", "muñeca", "mano"] if "superior" in region_sel else ["cadera", "muslo", "rodilla", "pierna", "tobillo", "pie"])
                        if st.button("agregar nervio"):
                            st.session_state.pericia.append({"reg": f"nervio {lat_sel}", "val": valor_n, "miembro": region_sel, "sector": sector_dest, "lado": lat_sel, "desc": f"{nervio_sel} ({gm}/{gs})"})
                            st.rerun()

# --- 2. visualización y cálculos (bold y duplicados) ---
if st.session_state.pericia:
    st.subheader("**detalle de secuelas**")
    conteos = {}
    for p in st.session_state.pericia:
        clave = (p['miembro'], p['lado'], p['sector'], p['desc'])
        conteos[clave] = conteos.get(clave, 0) + 1

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
    # columna aritmética
    total_col = min(min(cervical_arit, 40.0) + min(dorsolumbar_arit, 60.0) + sacro_arit, 100.0)
    if total_col > 0: v_regionales.append(total_col)

    # escaleras miembros
    for l in ["superior derecho", "superior izquierdo"]:
        d = miembros_data[l]
        if d:
            s1 = min(d.get("dedos", 0) + d.get("mano", 0) + d.get("muñeca", 0), 50.0)
            s2 = min(s1 + d.get("antebrazo", 0), 55.0)
            s3 = min(s2 + d.get("codo", 0) + d.get("brazo", 0), 60.0)
            v_regionales.append(min(s3 + d.get("hombro", 0), 66.0))
            
    for l in ["inferior derecho", "inferior izquierdo"]:
        d = miembros_data[l]
        if d:
            s1 = min(d.get("dedos", 0) + d.get("pie", 0) + d.get("tobillo", 0), 35.0)
            s2 = min(s1 + d.get("pierna", 0), 40.0)
            s3 = min(s2 + d.get("rodilla", 0), 55.0)
            v_regionales.append(min(s3 + d.get("muslo", 0) + d.get("cadera", 0), 70.0))

    st.markdown("---")
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("### **factores de ponderación**")
        edad = st.number_input("**edad**", 14, 99, 25)
        if edad < 21: f_e = 0.05
        elif 21 <= edad <= 35: f_e = 0.04
        elif 36 <= edad <= 45: f_e = 0.03
        else: f_e = 0.02
        f_d = st.selectbox("**dificultad**", [0.05, 0.10, 0.20], format_func=lambda x: f"{int(x*100)}%")
        fisico = balthazard(v_regionales)
        factores = fisico * (f_e + f_d)
        total_f = min(fisico + factores, 65.99) if fisico < 66.0 else min(fisico + factores, 100.0)

    with col_r:
        st.metric("**daño físico (balthazard)**", f"{fisico}%")
        st.metric("**factores aplicados**", f"{round(factores, 2)}%")
        st.success(f"## **ilp final: ** **{round(total_f, 2)}%**")
        if st.button("🚨 reiniciar"): st.session_state.pericia = []; st.rerun()