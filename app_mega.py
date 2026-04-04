import streamlit as st
import pandas as pd
import os

# --- Configuración inicial ---
st.set_page_config(page_title="Calculadora integral SRT", layout="wide", page_icon="🧮")

def format_text(text):
    if not text: return ""
    text = str(text).strip()
    return text[0].upper() + text[1:]

# --- Diccionario de Pesos Motor/Sensitivo (Decreto 549/25) ---
pesos_nervios = {
    "Axilar": {"m": 0.98, "s": 0.02}, "Radial": {"m": 0.90, "s": 0.10}, 
    "Mediano": {"m": 0.70, "s": 0.30}, "Cubital": {"m": 0.70, "s": 0.30},
    "Ciático mayor": {"m": 0.70, "s": 0.30}, "Peroneo": {"m": 0.70, "s": 0.30},
    "Tibial": {"m": 0.60, "s": 0.40}, "Femoral": {"m": 0.80, "s": 0.20}
}

escalas_ms = {
    "Grado 5 (Normal - 0%)": 0.0, "Grado 4 (Leve - 20%)": 0.2, "Grado 3 (Moderado - 50%)": 0.5,
    "Grado 2 (Grave - 80%)": 0.8, "Grado 1 (Severo - 90%)": 0.9, "Grado 0 (Total - 100%)": 1.0
}

@st.cache_data
def cargar_hoja(nombre_base):
    archivo = "calculadora_final_srt.xlsx"
    try:
        xls = pd.ExcelFile(archivo)
        # Buscador flexible de hojas (ignora plurales/singulares y espacios)
        nombre_real = next((s for s in xls.sheet_names if nombre_base.lower() in s.lower()), None)
        if not nombre_real: return pd.DataFrame()
        
        df = pd.read_excel(archivo, sheet_name=nombre_real).fillna("")
        df.columns = df.columns.str.strip()
        if '% de Incapacidad Laboral' in df.columns:
            def limpiar(val):
                try:
                    n = float(str(val).replace('%', '').replace(',', '.'))
                    return n * 100 if 0 < n < 1 else n
                except: return 0.0
            df['% de Incapacidad Laboral'] = df['% de Incapacidad Laboral'].apply(limpiar)
        return df
    except: return pd.DataFrame()

def balthazard(lista):
    lista = sorted([x for x in lista if x > 0], reverse=True)
    if not lista: return 0.0
    total = lista[0]
    for i in range(1, len(lista)):
        total = total + (lista[i] * (100 - total) / 100)
    return round(total, 2)

# --- Interfaz principal ---
st.title("🧮 **Mega Calculadora SRT: Edición Profesional**")
st.markdown("---")

if 'pericia' not in st.session_state:
    st.session_state.pericia = []

with st.sidebar:
    st.header("**Carga de hallazgos**")
    
    region_madre = st.selectbox("**1. Región**", ["Columna", "Miembro Superior", "Miembro Inferior"], index=None)
    
    if region_madre:
        # 2. SECTOR / LATERALIDAD
        if region_madre == "Columna":
            sector = st.selectbox("**2. Nivel vertebral**", ["Cervical", "Dorsal", "Lumbar", "Sacrococcigea", "Coxis"], index=None)
            hoja_nombre = sector
        else:
            lat = st.selectbox("**2. Lateralidad**", ["Derecho", "Izquierdo"], index=None)
            sectores_desc = ["Hombro", "Brazo", "Codo", "Antebrazo", "Muñeca", "Mano", "Dedos"] if "Superior" in region_madre else ["Cadera", "Muslo", "Rodilla", "Pierna", "Tobillo", "Pie", "Dedos"]
            sector = st.selectbox("**3. Sector anatómico**", sectores_desc, index=None)
            hoja_nombre = f"{region_madre} {lat}"
            
        if sector:
            hallazgo = st.radio("**Tipo de hallazgo**", ["Osteoarticular / Goniometría", "Neurológico / Radicular"])
            
            if "Neurológico" in hallazgo:
                df_final = cargar_hoja("Neurologia")
                kw_neuro = sector if region_madre == "Columna" else ("Superior" if "Superior" in region_madre else "Inferior")
                df_final = df_final[df_final['Apartado'].str.contains(kw_neuro, case=False, na=False)]
            else:
                df_final = cargar_hoja(hoja_nombre)
                # FILTRO CRÍTICO: Solo mostrar categorías que pertenezcan al sector elegido
                df_final = df_final[df_final['Categorias'].str.contains(sector, case=False, na=False) | df_final['Descripción de Lesión'].str.contains(sector, case=False, na=False)]

            if not df_final.empty:
                col_cat = 'Categorias' if 'Categorias' in df_final.columns else 'Apartado'
                categorias = ["Ver todas"] + sorted(df_final[col_cat].unique().tolist())
                cat_sel = st.selectbox("**Categoría**", categorias)
                
                df_items = df_final.copy()
                if cat_sel != "Ver todas":
                    df_items = df_items[df_items[col_cat] == cat_sel]
                
                # Agrupación por movimiento (Columna y Miembros)
                es_gonio = any(x in cat_sel for x in ["Anquilosis", "Limitación", "Goniometría"])
                if es_gonio:
                    movs = ["Flexión", "Extensión", "Inclinación", "Rotación", "Abducción", "Aducción", "Pronación", "Supinación"]
                    tipo_mov = st.selectbox("**Movimiento**", [m for m in movs if df_items['Descripción de Lesión'].str.contains(m, case=False).any()], index=None)
                    if tipo_mov:
                        df_items = df_items[df_items['Descripción de Lesión'].str.contains(tipo_mov, case=False)]
                
                opciones = sorted(df_items['Descripción de Lesión'].unique())
                if opciones:
                    item_sel = st.selectbox(f"**Secuela específica ({len(opciones)})**", opciones, format_func=format_text, index=None)
                    
                    if item_sel:
                        v_max = df_items[df_items['Descripción de Lesión'] == item_sel]['% de Incapacidad Laboral'].iloc[0]
                        valor_calc = v_max
                        
                        if "Nervio" in item_sel and "Dermatoma" not in item_sel:
                            st.write("**Evaluación M/S**")
                            p_m, p_s = 0.5, 0.5
                            for n, p in pesos_nervios.items():
                                if n.lower() in item_sel.lower(): p_m, p_s = p['m'], p['s']; break
                            m_s = st.selectbox("**M**", list(escalas_ms.keys())); s_s = st.selectbox("**S**", list(escalas_ms.keys()))
                            valor_calc = v_max * ((p_m * escalas_ms[m_s]) + (p_s * escalas_ms[s_s]))

                        st.info(f"Valor: {round(valor_calc, 2)}%")
                        if st.button("**AGREGAR**"):
                            st.session_state.pericia.append({"reg": sector if region_madre == "Columna" else f"{sector} {lat}", "desc": item_sel, "val": round(valor_calc, 2)})
                            st.rerun()

# --- Resultados ---
if st.session_state.pericia:
    st.subheader("**Detalle del dictamen médico**")
    sumas_seg = {}
    for i, p in enumerate(st.session_state.pericia):
        c1, c2, c3 = st.columns([3, 5, 1])
        c1.write(f"**{p['reg']}**")
        c2.write(f"{format_text(p['desc'])} ({p['val']}%)")
        if c3.button("🗑️", key=f"del_{i}"): st.session_state.pericia.pop(i); st.rerun()
        
        # Lógica de topes
        desc_u = p['desc'].upper()
        if any(x in p['reg'] or x in desc_u for x in ["CERVICAL", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"]): llave = "Columna Cervical"
        elif any(x in p['reg'] for x in ["Dorsal", "Lumbar", "Sacro"]): llave = "Columna Dorsolumbar"
        elif "Superior" in p['reg'] or any(x in p['reg'] for x in ["Hombro", "Codo", "Muñeca", "Mano"]): llave = "Miembro Superior"
        else: llave = "Miembro Inferior"
        sumas_seg[llave] = sumas_seg.get(llave, 0) + p['val']

    topes = {"Miembro Superior": 66.0, "Miembro Inferior": 70.0, "Columna Cervical": 40.0, "Columna Dorsolumbar": 60.0}
    
    st.markdown("---")
    l, r = st.columns(2)
    with l:
        st.write("**Análisis de topes:**")
        v_bal = []
        for s, suma in sumas_seg.items():
            t = topes.get(s, 100.0)
            v_f = min(suma, t)
            v_bal.append(v_f)
            if suma > t: st.warning(f"⚠️ {s}: {suma}% excede tope ({t}%).")
            else: st.write(f"✅ {s}: {suma}%")

        u_edad = st.number_input("**Edad**", 14, 99, 25)
        f_e = 0.05 if u_edad <= 20 else 0.04 if u_edad <= 30 else 0.03 if u_edad <= 40 else 0.02
        f_d = st.selectbox("**Dificultad**", [0.05, 0.10, 0.20], format_func=lambda x: f"{int(x*100)}%")
        
        fis = balthazard(v_bal)
        inc = fis * (f_e + f_d)
        res_f = min(fis + inc, 65.99) if fis < 66.0 else fis + inc

    with r:
        st.metric("**Daño físico**", f"{fis}%")
        st.metric("**Factores**", f"{round(inc, 2)}%")
        if res_f >= 66.0: st.error(f"## **ILP FINAL: {round(res_f, 2)}% (TOTAL)**")
        else: st.success(f"## **ILP FINAL: {round(res_f, 2)}% (PARCIAL)**")
        if st.button("🚨 **BORRAR TODO**"): st.session_state.pericia = []; st.rerun()