import streamlit as st
import pandas as pd
import os

# --- configuración inicial ---
st.set_page_config(page_title="calculadora integral SRT", layout="wide", page_icon="🧮")

@st.cache_data
def cargar_datos():
    archivo = "calculadora_final_srt.xlsx"
    if not os.path.exists(archivo):
        archivos_xlsx = [f for f in os.listdir(".") if f.endswith(".xlsx")]
        archivo = archivos_xlsx[0] if archivos_xlsx else ""
    
    if not archivo: raise FileNotFoundError("❌ No hay Excel en el repositorio.")
    
    df = pd.read_excel(archivo, sheet_name="Hoja1").fillna("")
    df.columns = df.columns.str.strip()
    
    def limpiar_numero(val):
        try:
            if isinstance(val, str): val = val.replace('%', '').replace(',', '.')
            n = float(val)
            # Saneador: si Excel guardó 0.02, lo pasamos a 2.0
            return n * 100 if 0 < n < 1 else n
        except: return 0.0

    col_inc = '% de Incapacidad Laboral'
    if col_inc in df.columns:
        df[col_inc] = df[col_inc].apply(limpiar_numero)
    return df

try:
    df_maestro = cargar_datos()
except Exception as e:
    st.error(f"⚠️ Error de base de datos: {e}"); st.stop()

def balthazard(lista):
    lista = sorted([x for x in lista if x > 0], reverse=True)
    if not lista: return 0.0
    total = lista[0]
    for i in range(1, len(lista)):
        total = total + (lista[i] * (100 - total) / 100)
    return round(total, 2)

# --- interfaz ---
st.title("🧮 mega calculadora SRT: edición profesional")
st.markdown("---")

if 'pericia' not in st.session_state:
    st.session_state.pericia = []

with st.sidebar:
    st.header("carga de hallazgos")
    
    region = st.selectbox("1. región topográfica", ["Columna", "MSI", "MSD", "MII", "MID"], index=None, placeholder="Seleccionar")
    
    if region:
        # Filtro inteligente de palabras clave
        if region == "Columna": kw = "Columna|Cervical|Dorsal|Lumbar|Radicular|Medular|S1|S2|S3|S4|S5"
        elif region in ["MSI", "MSD"]: kw = "Superior|Mano|Hombro|Codo|Muñeca|Brazo|Antebrazo|Plexo Braquial"
        else: kw = "Inferior|Cadera|Rodilla|Tobillo|Pie|Pierna|Muslo|Plexo Lumbar"
        
        mask = (df_maestro['Apartado'].str.contains(kw, case=False)) | (df_maestro['Descripción de Lesión'].str.contains(kw, case=False))
        df_region = df_maestro[mask]
        
        grupo = st.radio("2. tipo de hallazgo", ["osteoarticular / goniometría", "neurológico / radicular"])
        cap_busqueda = "Osteoarticular" if "osteo" in grupo else "Sistema Nervioso"
        df_grupo = df_region[df_region['Capítulo'].str.contains(cap_busqueda, case=False)]

        # Categorías y Sectores
        cats = ["ver todas", "amputaciones", "fracturas / luxofracturas", "anquilosis / limitaciones", "prótesis / artroplastias"]
        cat_sel = st.selectbox("3. categoría", cats, index=0)
        
        df_cat = df_grupo.copy()
        if cat_sel != "ver todas":
            kw_cat = cat_sel.split(" ")[0].replace("fracturas", "fractura|consolidación").replace("limitaciones", "limitación")
            df_cat = df_cat[df_cat['Descripción de Lesión'].str.contains(kw_cat, case=False)]

        sectores = ["ver todos"] + (["Cervical", "Dorsal", "Lumbar"] if region == "Columna" else 
                    ["Hombro", "Codo", "Muñeca", "Mano"] if "MS" in region else 
                    ["Cadera", "Rodilla", "Tobillo", "Pie"])
        sector_sel = st.selectbox("4. sector anatómico", sectores, index=0)
        
        df_sector = df_cat.copy()
        if sector_sel != "ver todos":
            df_sector = df_sector[df_sector['Descripción de Lesión'].str.contains(sector_sel, case=False)]

        opciones = sorted(df_sector['Descripción de Lesión'].unique())
        if opciones:
            item = st.selectbox(f"5. secuela específica ({len(opciones)})", opciones, index=None, placeholder="Seleccionar")
            if item:
                valor = df_sector[df_sector['Descripción de Lesión'] == item]['% de Incapacidad Laboral'].iloc[0]
                st.info(f"valor baremo: {valor}%")
                if st.button("AGREGAR"):
                    st.session_state.pericia.append({"reg": region, "desc": item, "val": valor})
                    st.rerun()
        else:
            st.warning("⚠️ Sin coincidencias.")

# --- resultados ---
if st.session_state.pericia:
    st.subheader("📋 detalle del dictamen")
    sumas_seg = {}
    for i, p in enumerate(st.session_state.pericia):
        c1, c2, c3 = st.columns([2, 6, 1])
        c1.write(f"**{p['reg']}**")
        c2.write(f"{p['desc']} ({p['val']}%)")
        if c3.button("🗑️", key=f"del_{i}"):
            st.session_state.pericia.pop(i); st.rerun()
        
        key = f"Columna {'Cervical' if 'Cervical' in p['desc'] else 'Dorsolumbar'}" if p['reg'] == "Columna" else p['reg']
        sumas_seg[key] = sumas_seg.get(key, 0) + p['val']

    # TOPES ACTUALIZADOS SEGÚN DECRETO 549/25
    topes = {
        "MSI": 66.0, "MSD": 66.0, 
        "MII": 70.0, "MID": 70.0, 
        "Columna Cervical": 40.0, "Columna Dorsolumbar": 60.0
    }
    
    st.markdown("---")
    col_l, col_r = st.columns(2)
    with col_l:
        st.write("**análisis de topes regionales:**")
        v_bal = []
        for s, suma in sumas_seg.items():
            t = topes.get(s, 100.0)
            v_f = min(suma, t)
            v_bal.append(v_f)
            if suma > t: st.warning(f"⚠️ {s}: {suma}% excede el tope de {t}%.")
            else: st.write(f"✅ {s}: {suma}% (dentro del límite)")

        st.markdown("### factores de ponderación")
        u_edad = st.number_input("edad del trabajador", 14, 99, 17)
        f_e = 0.05 if u_edad <= 20 else 0.04 if u_edad <= 30 else 0.03 if u_edad <= 40 else 0.02
        u_dif = st.selectbox("dificultad", ["leve (5%)", "intermedia (10%)", "alta (20%)"], index=1)
        f_d = {"leve (5%)": 0.05, "intermedia (10%)": 0.10, "alta (20%)": 0.20}[u_dif]
        
        fis = balthazard(v_bal)
        inc = fis * (f_e + f_d)
        res_pre = fis + inc
        # Regla del 66%: factores no transforman parcial en total
        res_f = min(res_pre, 65.99) if fis < 66.0 else res_pre

    with col_r:
        st.metric("daño físico (residual)", f"{fis}%")
        st.metric("factores de ponderación", f"{round(inc, 2)}%")
        if res_f >= 66.0: st.error(f"## ILP FINAL: {round(res_f, 2)}% (TOTAL)")
        else: st.success(f"## ILP FINAL: {round(res_f, 2)}% (PARCIAL)")
        if st.button("🚨 BORRAR TODO"): st.session_state.pericia = []; st.rerun()