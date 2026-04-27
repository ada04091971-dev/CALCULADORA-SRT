import streamlit as st
import pandas as pd
import os

# 1. Configuración de la aplicación
st.set_page_config(page_title="Calculadora Laboral SRT - Decreto 549/25", layout="wide", page_icon="🧮")

@st.cache_resource
def abrir_excel():
    archivo = "calculadora_final_srt.xlsx"
    if not os.path.exists(archivo):
        st.error(f"No se encontró el archivo '{archivo}' en la carpeta de GitHub.")
        st.stop()
    return pd.ExcelFile(archivo)

def balthazard(lista):
    """Método de la capacidad restante (Balthazard)."""
    lista = sorted([x for x in lista if x > 0], reverse=True)
    if not lista: return 0.0
    total = lista[0]
    for i in range(1, len(lista)):
        total = total + (lista[i] * (100 - total) / 100)
    return round(total, 2)

if 'pericia' not in st.session_state:
    st.session_state.pericia = []

st.title("🧮 **Calculadora Laboral SRT: Decreto 549/25**")
st.markdown("---")

xls = abrir_excel()

# --- Diccionarios Neurológicos (Hardcoded según Baremo 549/25) ---
TABLA_M = {"M0": 1.0, "M1": 0.8, "M2": 0.8, "M3": 0.5, "M4": 0.2, "M5": 0.0}
TABLA_S = {"S0": 1.0, "S1": 0.8, "S2": 0.8, "S3": 0.5, "S4": 0.2, "S5": 0.0}

NERVIOS_UPPER = {
    "Nervio Mediano Proximal": {"p_m": 0.7, "p_s": 0.3, "max": 0.40},
    "Nervio Mediano Distal": {"p_m": 0.4, "p_s": 0.6, "max": 0.25},
    "Nervio Cubital Proximal": {"p_m": 0.7, "p_s": 0.3, "max": 0.35},
    "Nervio Cubital Distal": {"p_m": 0.7, "p_s": 0.3, "max": 0.25},
    "Nervio Radial": {"p_m": 0.9, "p_s": 0.1, "max": 0.30},
    "Nervio Plexo Braquial (Total)": {"p_m": 0.8, "p_s": 0.2, "max": 0.60}
}

NERVIOS_LOWER = {
    "Nervio Ciático Mayor": {"p_m": 0.5, "p_s": 0.5, "max": 0.50},
    "Nervio Peroneo Común (CPE)": {"p_m": 0.7, "p_s": 0.3, "max": 0.25},
    "Nervio Tibial Posterior": {"p_m": 0.6, "p_s": 0.4, "max": 0.20}
}

RAICES = {
    "Cervical": {"Raíz C2": 3, "Raíz C3": 3, "Raíz C4": 3, "Raíz C5": 5, "Raíz C6": 9, "Raíz C7": 9, "Raíz C8": 8},
    "Dorsolumbar": {"Raíz D1-D12": 2, "Raíz L1-L5": 3, "Raíz S1-S2": 3, "Raíz S3-S5": 5}
}

with st.sidebar:
    st.header("**Carga de Hallazgos**")
    cap_sel = st.selectbox("**1. Capítulo del Baremo**", ["Osteoarticular", "Neurológica", "Psiquiatría"], index=None)
    
    if cap_sel == "Psiquiatría":
        st.subheader("🧠 Salud Mental (D.V.A.)")
        nombre_real = next((s for s in xls.sheet_names if "psiquiatr" in s.lower()), None)
        if nombre_real:
            df_psi = pd.read_excel(xls, sheet_name=nombre_real).fillna("")
            col_cat = next((c for c in df_psi.columns if "categor" in c.lower()), df_psi.columns[0])
            col_des = next((c for c in df_psi.columns if "descrip" in c.lower()), df_psi.columns[1])
            col_inc = next((c for c in df_psi.columns if "incap" in c.lower() or "%" in c.lower()), df_psi.columns[-1])

            denominacion = st.selectbox("**Denominación**", sorted(df_psi[col_cat].unique().tolist()))
            if denominacion:
                df_f = df_psi[df_psi[col_cat] == denominacion]
                grado = st.selectbox("**Grado de la Secuela**", sorted(df_f[col_des].unique().tolist()), index=None)
                if grado:
                    valor = float(df_f[df_f[col_des] == grado][col_inc].iloc[0])
                    st.info(f"**Incapacidad: {valor}%**")
                    if st.button("Adicionar D.V.A."):
                        st.session_state.pericia.append({"cap": "Psiquiatría", "reg": "Salud Mental", "val": valor, "desc": f"{denominacion}: {grado}", "sector": "Psiquiatría"})
                        st.rerun()

    elif cap_sel == "Neurológica":
        reg_n = st.selectbox("**Región**", ["Columna (Raíces)", "Miembro Superior", "Miembro Inferior"], index=None)
        if reg_n == "Columna (Raíces)":
            sec = st.selectbox("Sector", ["Cervical", "Dorsolumbar"])
            raiz = st.selectbox("Raíz", list(RAICES[sec].keys()))
            if st.button("Agregar Raíz"):
                st.session_state.pericia.append({"cap": "Neurológica", "reg": sec, "val": RAICES[sec][raiz], "desc": raiz, "sector": sec})
                st.rerun()
        elif reg_n:
            lat = st.selectbox("Lateralidad", ["Derecho", "Izquierdo"])
            dicc = NERVIOS_UPPER if "Superior" in reg_n else NERVIOS_LOWER
            nervio = st.selectbox("Nervio", list(dicc.keys()))
            gm = st.selectbox("Grado M", list(TABLA_M.keys()), index=5)
            gs = st.selectbox("Grado S", list(TABLA_S.keys()), index=5)
            n_data = dicc[nervio]
            val = round(((TABLA_M[gm] * n_data['p_m']) + (TABLA_S[gs] * n_data['p_s'])) * n_data['max'] * 100, 2)
            sec_tope = st.selectbox("Sector para Tope", ["Hombro", "Brazo", "Codo", "Mano"] if "Superior" in reg_n else ["Cadera", "Rodilla", "Tobillo", "Pie"])
            if st.button("Agregar Nervio"):
                st.session_state.pericia.append({"cap": "Neurológica", "reg": f"{reg_n} {lat}", "val": val, "desc": f"{nervio} ({gm}/{gs})", "sector": sec_tope, "lado": lat})
                st.rerun()

    elif cap_sel == "Osteoarticular":
        # INICIALIZACIÓN CRÍTICA PARA EVITAR NAMEERROR
        sec_val, hoja = None, None
        sub_reg = st.selectbox("**Región**", ["Columna", "Miembro Superior", "Miembro Inferior"], index=None)
        if sub_reg == "Columna":
            sectores = ["Cervical", "Dorsal", "Lumbar", "Sacrococcigea"]
            sec_val = st.selectbox("Sector", sectores, index=None)
            hoja = sec_val
        elif sub_reg:
            lat = st.selectbox("Lateralidad", ["Derecho", "Izquierdo"], index=None)
            sectores = ["Hombro", "Brazo", "Codo", "Antebrazo", "Muñeca", "Mano", "Dedos"] if "Superior" in sub_reg else ["Cadera", "Muslo", "Rodilla", "Pierna", "Tobillo", "Pie", "Dedos"]
            sec_val = st.selectbox("Sector", sectores, index=None)
            hoja = f"{sub_reg} {lat}"
        
        if sec_val and hoja:
            nombre_real = next((s for s in xls.sheet_names if hoja.lower() == s.lower().strip()), None)
            if nombre_real:
                df = pd.read_excel(xls, sheet_name=nombre_real).fillna("")
                col_sector = next((c for c in df.columns if "sector" in c.lower()), df.columns[0])
                df_f = df[df[col_sector].astype(str).str.contains(sec_val, case=False, na=False)]
                
                col_cat = next((c for c in df_f.columns if "categor" in c.lower() and "sub" not in c.lower()), "Categoría")
                cat = st.selectbox("Categoría", ["Elegir..."] + sorted(df_f[col_cat].unique().tolist()))
                if cat != "Elegir...":
                    df_f = df_f[df_f[col_cat] == cat]
                    col_des = next((c for c in df_f.columns if "descrip" in c.lower()), "Descripción")
                    item = st.selectbox("Lesión", sorted(df_f[col_des].unique().tolist()), index=None)
                    if item:
                        col_inc = next((c for c in df_f.columns if "incap" in c.lower() or "%" in c.lower()), "%")
                        valor = float(df_f[df_f[col_des] == item][col_inc].iloc[0])
                        st.info(f"**Valor: {valor}%**")
                        if st.button("Agregar Lesión"):
                            st.session_state.pericia.append({"cap": "Osteoarticular", "reg": hoja, "val": valor, "desc": f"{cat}: {item}", "sector": sec_val, "lado": lat if 'lat' in locals() else None})
                            st.rerun()

# --- 2. Cálculos y Visualización ---
if st.session_state.pericia:
    st.subheader("**Detalle de la Pericia Médica**")
    
    acum_cervical, acum_dorsolumbar, acum_sacro = 0.0, 0.0, 0.0
    miembros = {"superior derecho": {}, "superior izquierdo": {}, "inferior derecho": {}, "inferior izquierdo": {}}
    otros_capitulos = []

    for i, p in enumerate(st.session_state.pericia):
        c1, c2, c3 = st.columns([2, 6, 1])
        cap = p.get('cap', 'Osteoarticular')
        reg = p.get('reg', 'N/A')
        val = p.get('val', 0.0)
        desc = p.get('desc', 'Sin descripción')
        sector = p.get('sector', '').lower()
        lado = p.get('lado', '').lower() if p.get('lado') else ""

        c1.markdown(f"**{cap} - {reg}**")
        c2.write(f"{desc} (**{val}%**)")
        if c3.button("🗑️", key=f"del_{i}"): st.session_state.pericia.pop(i); st.rerun()

        if cap == "Psiquiatría":
            otros_capitulos.append(val)
        elif "cervical" in sector or "cervical" in reg.lower(): acum_cervical += val
        elif any(x in sector or x in reg.lower() for x in ["dorsal", "lumbar"]): acum_dorsolumbar += val
        elif any(x in sector or x in reg.lower() for x in ["sacro", "coxis"]): acum_sacro += val
        elif lado:
            m_llave = f"{'superior' if 'superior' in reg.lower() else 'inferior'} {lado}"
            if m_llave in miembros: miembros[m_llave][sector] = miembros[m_llave].get(sector, 0.0) + val

    v_balthazard = []
    # Columna: Tope Cervical (40%) + Dorsolumbar (60%)
    col_final = min(min(acum_cervical, 40.0) + min(acum_dorsolumbar, 60.0) + acum_sacro, 100.0)
    if col_final > 0: v_balthazard.append(col_final)
    
    # Miembros (Lógica de Escalera Infranqueable)
    for m, datos in miembros.items():
        if datos:
            if "superior" in m:
                s1 = min(datos.get("dedos",0) + datos.get("mano",0) + datos.get("muñeca",0), 50.0)
                s2 = min(s1 + datos.get("antebrazo",0), 55.0)
                s3 = min(s2 + datos.get("codo",0) + datos.get("brazo",0), 60.0)
                v_balthazard.append(min(s3 + datos.get("hombro",0), 66.0))
            else:
                s1 = min(datos.get("dedos",0) + datos.get("pie",0) + datos.get("tobillo",0), 35.0)
                s2 = min(s1 + datos.get("pierna",0), 40.0)
                s3 = min(s2 + datos.get("rodilla",0), 55.0)
                v_balthazard.append(min(s3 + datos.get("muslo",0) + datos.get("cadera",0), 70.0))
    
    # Salud Mental (D.V.A.)
    for v in otros_capitulos: v_balthazard.append(v)

    st.markdown("---")
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("### **Factores de Ponderación (Decreto 549/25)**")
        edad = st.number_input("**Edad al momento de la consolidación**", 14, 99, 54)
        # Rangos página 6: <21, 21-35, 36-45, >45
        f_e = 0.05 if edad < 21 else 0.04 if edad <= 35 else 0.03 if edad <= 45 else 0.02
        
        dif_map = {"Leve (5%)": 0.05, "Intermedia (10%)": 0.10, "Alta (20%)": 0.20}
        f_d = dif_map[st.selectbox("**Dificultad para tareas habituales**", list(dif_map.keys()))]
        
        fisico = balthazard(v_balthazard)
        factores = fisico * (f_e + f_d)
        
        # Barrera de incapacidad total: si físico < 66%, el final NO toca 66%
        total_f = min(fisico + factores, 65.99) if fisico < 66.0 else min(fisico + factores, 100.0)

    with col_r:
        st.metric("**Daño Físico Global (Balthazard)**", f"{fisico}%")
        st.metric("**Suma de Factores**", f"{round(factores, 2)}%")
        st.success(f"## **ILP FINAL: {round(total_f, 2)}%**")
        if st.button("🚨 Reiniciar Pericia"): st.session_state.pericia = []; st.rerun()