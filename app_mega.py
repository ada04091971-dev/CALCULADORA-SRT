import streamlit as st
import pandas as pd
import os

# --- configuración inicial ---
st.set_page_config(page_title="calculadora integral SRT", layout="wide", page_icon="🧮")

# --- motor de limpieza de datos ---
@st.cache_data
def cargar_datos():
    # Buscamos el archivo. Si no lo renombraste, el código lo busca igual
    archivo = "calculadora_final_srt.xlsx"
    if not os.path.exists(archivo):
        # Si no existe, buscamos cualquier archivo Excel en la carpeta
        archivos_xlsx = [f for f in os.listdir(".") if f.endswith(".xlsx")]
        if archivos_xlsx:
            archivo = archivos_xlsx[0]
        else:
            raise FileNotFoundError("❌ No encontré el archivo Excel en GitHub.")
    
    # Cargamos Hoja1
    df = pd.read_excel(archivo, sheet_name="Hoja1")
    df.columns = df.columns.str.strip()
    
    # Saneador de porcentajes (0.02 -> 2.0)
    def limpiar_numero(val):
        try:
            if isinstance(val, str):
                val = val.replace('%', '').replace(',', '.')
            n = float(val)
            return n * 100 if 0 < n < 1 else n
        except:
            return 0.0

    col_inc = '% de Incapacidad Laboral'
    if col_inc in df.columns:
        df[col_inc] = df[col_inc].apply(limpiar_numero)
    
    # Rellenamos celdas vacías para que no falle el buscador
    df = df.fillna("")
    return df

# --- lógica actuarial ---
def balthazard(lista):
    lista = sorted([x for x in lista if x > 0], reverse=True)
    if not lista: return 0.0
    total = lista[0]
    for i in range(1, len(lista)):
        total = total + (lista[i] * (100 - total) / 100)
    return round(total, 2)

# --- carga de datos ---
try:
    df_maestro = cargar_datos()
except Exception as e:
    st.error(f"⚠️ Error de Archivo: {e}")
    st.stop()

# --- interfaz de usuario ---
st.title("🧮 mega calculadora SRT: edición 549/25")
st.markdown("---")

if 'pericia' not in st.session_state:
    st.session_state.pericia = []

with st.sidebar:
    st.header("carga de hallazgos")
    
    region = st.selectbox("1. región topográfica", ["Columna", "MSI", "MSD", "MII", "MID"], index=None, placeholder="Seleccionar")
    
    if region:
        # Definimos el motor de búsqueda inteligente
        if region == "Columna": kw = "Columna|Cervical|Dorsal|Lumbar|Radicular|Medular|S1|S2|S3|S4|S5"
        elif region in ["MSI", "MSD"]: kw = "Superior|Mano|Hombro|Codo|Muñeca|Brazo|Antebrazo|Plexo Braquial"
        else: kw = "Inferior|Cadera|Rodilla|Tobillo|Pie|Pierna|Muslo|Plexo Lumbar"
        
        # Filtramos buscando en Apartado Y en Descripción de Lesión (esto arregla tu error)
        mask = (df_maestro['Apartado'].str.contains(kw, case=False, na=False)) | \
               (df_maestro['Descripción de Lesión'].str.contains(kw, case=False, na=False))
        df_filtrado = df_maestro[mask]
        
        grupo = st.radio("2. tipo de hallazgo", ["osteoarticular / goniometría", "neurológico / radicular"])
        
        if "osteo" in grupo:
            df_final = df_filtrado[df_filtrado['Capítulo'].str.contains("Osteoarticular", case=False, na=False)]
        else:
            df_final = df_filtrado[df_filtrado['Capítulo'].str.contains("Sistema Nervioso", case=False, na=False)]
            
        opciones = sorted(df_final['Descripción de Lesión'].unique())
        
        if len(opciones) > 0:
            item_sel = st.selectbox(f"3. seleccionar secuela ({len(opciones)} hallazgos):", opciones, index=None, placeholder="Seleccionar")
            
            if item_sel:
                valor = df_final[df_final['Descripción de Lesión'] == item_sel]['% de Incapacidad Laboral'].iloc[0]
                st.info(f"valor baremo: {valor}%")
                
                if st.button("AGREGAR A LA PERICIA"):
                    st.session_state.pericia.append({"reg": region, "desc": item_sel, "val": valor})
                    st.rerun()
        else:
            st.warning("⚠️ No se encontraron lesiones. Probá cambiando el tipo de hallazgo.")

# --- resultados finales ---
if st.session_state.pericia:
    st.subheader("📋 detalle del dictamen")
    sumas_segmentales = {}
    
    for i, p in enumerate(st.session_state.pericia):
        c1, c2, c3 = st.columns([2, 6, 1])
        c1.write(f"**{p['reg']}**")
        c2.write(f"{p['desc']} ({p['val']}%)")
        if c3.button("🗑️", key=f"del_{i}"):
            st.session_state.pericia.pop(i); st.rerun()
        
        llave = f"Columna {'Cervical' if 'Cervical' in p['desc'] else 'Dorsolumbar'}" if p['reg'] == "Columna" else p['reg']
        sumas_segmentales[llave] = sumas_segmentales.get(llave, 0) + p['val']

    topes = {"MSI": 60.0, "MSD": 60.0, "MII": 60.0, "MID": 60.0, "Columna Cervical": 40.0, "Columna Dorsolumbar": 60.0}
    
    st.markdown("---")
    col_l, col_r = st.columns(2)
    
    with col_l:
        st.write("**control de topes regionales:**")
        v_balthazard = []
        for s, suma in sumas_segmentales.items():
            t = topes.get(s, 100.0)
            v_final = min(suma, t)
            v_balthazard.append(v_final)
            if suma > t: st.warning(f"⚠️ {s}: {suma}% excede el tope de {t}%.")
            else: st.write(f"✅ {s}: {suma}%")

        st.markdown("### factores de ponderación")
        u_edad = st.number_input("edad del trabajador", 14, 99, 17)
        f_e = 0.05 if u_edad <= 20 else 0.04 if u_edad <= 30 else 0.03 if u_edad <= 40 else 0.02
        u_dif = st.selectbox("dificultad para tareas", ["leve (5%)", "intermedia (10%)", "alta (20%)"], index=1)
        f_d = {"leve (5%)": 0.05, "intermedia (10%)": 0.10, "alta (20%)": 0.20}[u_dif]
        
        fisf_total = balthazard(v_balthazard)
        inc = fisf_total * (f_e + f_d)
        res_pre = fisf_total + inc
        res_final = min(res_pre, 65.99) if fisf_total < 66.0 else res_pre

    with col_r:
        st.metric("daño físico total", f"{fisf_total}%")
        st.metric("incremento factores", f"{round(inc, 2)}%")
        if res_final >= 66.0:
            st.error(f"## ILP FINAL: {round(res_final, 2)}% (TOTAL)")
        else:
            st.success(f"## ILP FINAL: {round(res_final, 2)}% (PARCIAL)")
        
        if st.button("🚨 BORRAR TODO"):
            st.session_state.pericia = []; st.rerun()