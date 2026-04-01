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
    
    if not archivo: raise FileNotFoundError("❌ No hay Excel.")
    
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

try:
    df_maestro = cargar_datos()
except Exception as e:
    st.error(f"⚠️ Error: {e}"); st.stop()

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
        # MAPEO INTELIGENTE DE KEYWORDS
        # Esto asegura que C6 aparezca tanto en Columna como en Miembro Superior
        if region == "Columna": 
            kw = "Columna|Cervical|Dorsal|Lumbar|Sacro|Radicular|Medular|C1|C2|C3|C4|C5|C6|C7|C8|L1|L2|L3|L4|L5|S1|S2|S3|S4|S5"
        elif region in ["MSI", "MSD"]: 
            kw = "Superior|Mano|Hombro|Codo|Muñeca|Brazo|Antebrazo|Plexo Braquial|C5|C6|C7|C8|T1"
        else: # MII / MID
            kw = "Inferior|Cadera|Rodilla|Tobillo|Pie|Pierna|Muslo|Plexo Lumbar|L1|L2|L3|L4|L5|S1|S2|S3|S4|S5"
        
        mask = (df_maestro['Apartado'].str.contains(kw, case=False)) | (df_maestro['Descripción de Lesión'].str.contains(kw, case=False))
        df_region = df_maestro[mask]
        
        grupo = st.radio("2. tipo de hallazgo", ["osteoarticular / goniometría", "neurológico / radicular"])
        cap_busqueda = "Osteoarticular" if "osteo" in grupo else "Sistema Nervioso"
        df_grupo = df_region[df_region['Capítulo'].str.contains(cap_busqueda, case=False)]

        # CATEGORÍAS
        if cap_busqueda == "Osteoarticular":
            cats = ["ver todas", "amputaciones", "fracturas / luxofracturas", "anquilosis / limitaciones", "prótesis / artroplastias"]
        else:
            cats = ["ver todas", "raíces y dermatomas", "nervios periféricos", "plexos", "lesión medular"]
            
        cat_sel = st.selectbox("3. categoría", cats, index=0)
        
        df_cat = df_grupo.copy()
        if cat_sel != "ver todas":
            # Mapeo de búsqueda por categoría
            map_cat = {
                "raíces y dermatomas": "Radicular|Dermatoma",
                "nervios periféricos": "Nervio",
                "plexos": "Plexo",
                "amputaciones": "Amputación",
                "fracturas / luxofracturas": "Fractura|Luxofractura|Consolidación",
                "anquilosis / limitaciones": "Anquilosis|Limitación",
                "prótesis / artroplastias": "Prótesis|Artroplastía"
            }
            kw_cat = map_cat.get(cat_sel, cat_sel.split(" ")[0])
            df_cat = df_cat[df_cat['Descripción de Lesión'].str.contains(kw_cat, case=False) | df_cat['Apartado'].str.contains(kw_cat, case=False)]

        # SECTORES (Mapeo dinámico para que C6 aparezca al elegir 'Cervical' o 'Hombro')
        if region == "Columna":
            sectores = ["ver todos", "Cervical", "Dorsal", "Lumbar", "Sacro"]
        elif region in ["MSI", "MSD"]:
            sectores = ["ver todos", "Hombro", "Brazo", "Codo", "Muñeca", "Mano"]
        else:
            sectores = ["ver todos", "Cadera", "Muslo", "Rodilla", "Pierna", "Tobillo", "Pie"]
            
        sector_sel = st.selectbox("4. sector anatómico", sectores, index=0)
        
        df_sector = df_cat.copy()
        if sector_sel != "ver todos":
            # Diccionario de expansión de búsqueda (Cervical busca C1-C8, Hombro busca C5-C6, etc)
            expansion = {
                "Cervical": "Cervical|C1|C2|C3|C4|C5|C6|C7|C8",
                "Lumbar": "Lumbar|L1|L2|L3|L4|L5",
                "Sacro": "Sacro|S1|S2|S3|S4|S5",
                "Hombro": "Hombro|C5|C6|Circunflejo|Axilar",
                "Mano": "Mano|C8|T1|Mediano|Cubital",
                "Pie": "Pie|L5|S1|S2|Ciático"
            }
            kw_sec = expansion.get(sector_sel, sector_sel)
            df_sector = df_sector[df_sector['Descripción de Lesión'].str.contains(kw_sec, case=False)]

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
            st.warning("⚠️ No hay coincidencias con estos filtros.")

# --- resultados finales ---
if st.session_state.pericia:
    st.subheader("📋 detalle del dictamen")
    sumas_seg = {}
    for i, p in enumerate(st.session_state.pericia):
        c1, c2, c3 = st.columns([2, 6, 1])
        c1.write(f"**{p['reg']}**")
        c2.write(f"{p['desc']} ({p['val']}%)")
        if c3.button("🗑️", key=f"del_{i}"):
            st.session_state.pericia.pop(i); st.rerun()
        
        # Lógica de topes segmentales según el Decreto 549/25
        # Buscamos palabras clave en la descripción para asignar el tope correcto
        desc_upper = p['desc'].upper()
        if p['reg'] == "Columna":
            # Si la descripción contiene C1 a C8 o la palabra Cervical, va a tope de 40
            if any(x in desc_upper for x in ["CERVICAL", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"]):
                llave = "Columna Cervical"
            else:
                llave = "Columna Dorsolumbar"
        else:
            llave = p['reg']
            
        sumas_seg[llave] = sumas_seg.get(llave, 0) + p['val']

    topes = {"MSI": 66.0, "MSD": 66.0, "MII": 70.0, "MID": 70.0, "Columna Cervical": 40.0, "Columna Dorsolumbar": 60.0}
    
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
        u_edad = st.number_input("edad", 14, 99, 17)
        f_e = 0.05 if u_edad <= 20 else 0.04 if u_edad <= 30 else 0.03 if u_edad <= 40 else 0.02
        u_dif = st.selectbox("dificultad", ["leve (5%)", "intermedia (10%)", "alta (20%)"], index=1)
        f_d = {"leve (5%)": 0.05, "intermedia (10%)": 0.10, "alta (20%)": 0.20}[u_dif]
        
        fis = balthazard(v_bal)
        inc = fis * (f_e + f_d)
        res = fis + inc
        res_f = min(res, 65.99) if fis < 66.0 else res

    with col_r:
        st.metric("daño físico", f"{fis}%")
        st.metric("factores", f"{round(inc, 2)}%")
        if res_f >= 66.0: st.error(f"## ILP FINAL: {round(res_f, 2)}% (TOTAL)")
        else: st.success(f"## ILP FINAL: {round(res_f, 2)}% (PARCIAL)")
        if st.button("🚨 BORRAR TODO"): st.session_state.pericia = []; st.rerun()