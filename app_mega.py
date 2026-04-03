import streamlit as st
import pandas as pd
import os

# --- Configuración inicial ---
st.set_page_config(page_title="Calculadora integral SRT", layout="wide", page_icon="🧮")

# Función para asegurar que solo la primera letra sea mayúscula, respetando siglas
def format_text(text):
    if not text: return ""
    text = str(text).strip()
    # Pone la primera letra en mayúscula y deja el resto intacto (para C1, S1, etc.)
    return text[0].upper() + text[1:]

@st.cache_data
def cargar_datos():
    archivo = "calculadora_final_srt.xlsx"
    if not os.path.exists(archivo):
        archivos_xlsx = [f for f in os.listdir(".") if f.endswith(".xlsx")]
        archivo = archivos_xlsx[0] if archivos_xlsx else ""
    
    if not archivo: raise FileNotFoundError("No se encontró el archivo Excel.")
    
    df = pd.read_excel(archivo, sheet_name="Hoja1").fillna("")
    df.columns = df.columns.str.strip()
    
    def limpiar_numero(val):
        try:
            if isinstance(val, str): val = val.replace('%', '').replace(',', '.')
            n = float(val)
            # Saneador de decimales (0.04 -> 4.0)
            return n * 100 if 0 < n < 1 else n
        except: return 0.0

    col_inc = '% de Incapacidad Laboral'
    if col_inc in df.columns:
        df[col_inc] = df[col_inc].apply(limpiar_numero)
    return df

try:
    df_maestro = cargar_datos()
except Exception as e:
    st.error(f"Error de base de datos: {e}"); st.stop()

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
    
    region = st.selectbox("**1. Región topográfica**", ["Columna", "MSI", "MSD", "MII", "MID"], index=None, placeholder="Seleccionar")
    
    if region:
        # Búsqueda ampliada por región
        if region == "Columna": 
            kw = "Columna|Cervical|Dorsal|Lumbar|Sacro|Radicular|Medular|C1|C2|C3|C4|C5|C6|C7|C8|L1|L2|L3|L4|L5|S1|S2|S3|S4|S5"
        elif region in ["MSI", "MSD"]: 
            kw = "Superior|Mano|Hombro|Codo|Muñeca|Brazo|Antebrazo|Plexo Braquial|C5|C6|C7|C8|T1"
        else: # MII / MID
            kw = "Inferior|Cadera|Rodilla|Tobillo|Pie|Pierna|Muslo|Menisco|Capsulo|Ligamento|S1|L5"
        
        mask = (df_maestro['Apartado'].str.contains(kw, case=False)) | (df_maestro['Descripción de Lesión'].str.contains(kw, case=False))
        df_region = df_maestro[mask]
        
        grupo = st.radio("**2. Tipo de hallazgo**", ["Osteoarticular / Goniometría", "Neurológico / Radicular"])
        cap_busqueda = "Osteoarticular" if "osteo" in grupo.lower() else "Sistema Nervioso"
        df_grupo = df_region[df_region['Capítulo'].str.contains(cap_busqueda, case=False)]

        # Categorías refinadas
        if cap_busqueda == "Osteoarticular":
            cats = ["Ver todas", "Meniscos / Ligamentos", "Fracturas / Luxofracturas", "Anquilosis / Limitaciones", "Amputaciones", "Prótesis"]
        else:
            cats = ["Ver todas", "Raíces y dermatomas", "Nervios periféricos", "Plexos"]
            
        cat_sel = st.selectbox("**3. Categoría**", cats, index=0)
        
        df_cat = df_grupo.copy()
        if cat_sel != "Ver todas":
            map_cat = {
                "Meniscos / Ligamentos": "Menisco|Capsulo|Ligamento|Sutura|Meniscectomía",
                "Raíces y dermatomas": "Radicular|Dermatoma",
                "Nervios periféricos": "Nervio",
                "Amputaciones": "Amputación",
                "Fracturas / Luxofracturas": "Fractura|Luxofractura|Consolidación",
                "Anquilosis / Limitaciones": "Anquilosis|Limitación"
            }
            kw_cat = map_cat.get(cat_sel, cat_sel.split(" ")[0])
            df_cat = df_cat[df_cat['Descripción de Lesión'].str.contains(kw_cat, case=False) | df_cat['Apartado'].str.contains(kw_cat, case=False)]

        # Sectores
        sectores = ["Ver todos"] + (["Cervical", "Dorsal", "Lumbar", "Sacro"] if region == "Columna" else 
                    ["Hombro", "Brazo", "Codo", "Muñeca", "Mano"] if "MS" in region else 
                    ["Cadera", "Muslo", "Rodilla", "Pierna", "Tobillo", "Pie"])
        sector_sel = st.selectbox("**4. Sector anatómico**", sectores, index=0)
        
        df_sector = df_cat.copy()
        if sector_sel != "Ver todos":
            expansion = {
                "Cervical": "Cervical|C1|C2|C3|C4|C5|C6|C7|C8",
                "Rodilla": "Rodilla|Menisco|Capsulo|Ligamento|Cruzado|Rótula",
                "Hombro": "Hombro|Manguito|C5|C6",
                "Mano": "Mano|Pulgar|Dedo|Metacarpo"
            }
            kw_sec = expansion.get(sector_sel, sector_sel)
            df_sector = df_sector[df_sector['Descripción de Lesión'].str.contains(kw_sec, case=False)]

        opciones = sorted(df_sector['Descripción de Lesión'].unique())
        if opciones:
            opciones_fmt = {opt: format_text(opt) for opt in opciones}
            item_sel = st.selectbox(f"**5. Secuela específica ({len(opciones)})**", list(opciones_fmt.keys()), format_func=lambda x: opciones_fmt[x], index=None, placeholder="Seleccionar")
            
            if item_sel:
                valor = df_sector[df_sector['Descripción de Lesión'] == item_sel]['% de Incapacidad Laboral'].iloc[0]
                st.info(f"Valor baremo: {valor}%")
                if st.button("**AGREGAR**"):
                    st.session_state.pericia.append({"reg": region, "desc": item_sel, "val": valor})
                    st.rerun()
        else:
            st.warning("No hay coincidencias.")

# --- Resultados finales ---
if st.session_state.pericia:
    st.subheader("**Detalle del dictamen**")
    sumas_seg = {}
    for i, p in enumerate(st.session_state.pericia):
        c1, c2, c3 = st.columns([2, 6, 1])
        c1.write(f"**{p['reg']}**")
        c2.write(f"{format_text(p['desc'])} ({p['val']}%)")
        if c3.button("🗑️", key=f"del_{i}"):
            st.session_state.pericia.pop(i); st.rerun()
        
        # Lógica de topes segmentales según Decreto 549/25
        desc_upper = p['desc'].upper()
        if p['reg'] == "Columna":
            if any(x in desc_upper for x in ["CERVICAL", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"]):
                llave = "Columna Cervical"
            else:
                llave = "Columna Dorsolumbar"
        else:
            llave = p['reg']
        sumas_seg[llave] = sumas_seg.get(llave, 0) + p['val']

    # Topes legales actualizados
    topes = {"MSI": 66.0, "MSD": 66.0, "MII": 70.0, "MID": 70.0, "Columna Cervical": 40.0, "Columna Dorsolumbar": 60.0}
    
    st.markdown("---")
    col_l, col_r = st.columns(2)
    with col_l:
        st.write("**Análisis de topes regionales:**")
        v_bal = []
        for s, suma in sumas_seg.items():
            t = topes.get(s, 100.0)
            v_f = min(suma, t)
            v_bal.append(v_f)
            if suma > t: st.warning(f"⚠️ {s}: {suma}% excede el tope de {t}%.")
            else: st.write(f"✅ {s}: {suma}% (dentro del límite)")

        st.markdown("### **Factores de ponderación**")
        u_edad = st.number_input("**Edad del trabajador**", 14, 99, 17)
        f_e = 0.05 if u_edad <= 20 else 0.04 if u_edad <= 30 else 0.03 if u_edad <= 40 else 0.02
        u_dif = st.selectbox("**Dificultad para tareas**", ["Leve (5%)", "Intermedia (10%)", "Alta (20%)"], index=1)
        f_d = {"Leve (5%)": 0.05, "Intermedia (10%)": 0.10, "Alta (20%)": 0.20}[u_dif]
        
        fis = balthazard(v_bal)
        inc = fis * (f_e + f_d)
        res = fis + inc
        # Regla del 65.99% para pericias parciales
        res_f = min(res, 65.99) if fis < 66.0 else res

    with col_r:
        st.metric("**Daño físico**", f"{fis}%")
        st.metric("**Factores**", f"{round(inc, 2)}%")
        if res_f >= 66.0: st.error(f"## **ILP FINAL: {round(res_f, 2)}% (TOTAL)**")
        else: st.success(f"## **ILP FINAL: {round(res_f, 2)}% (PARCIAL)**")
        if st.button("🚨 **BORRAR TODO**"):
            st.session_state.pericia = []; st.rerun()