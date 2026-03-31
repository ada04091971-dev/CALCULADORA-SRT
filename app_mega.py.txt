import streamlit as st
import pandas as pd
import os

# --- configuración inicial ---
st.set_page_config(page_title="calculadora integral SRT", layout="wide", page_icon="🧮")

# --- motor de limpieza de datos ---
@st.cache_data
def cargar_datos():
    archivo = "calculadora_final_srt.xlsx"
    if not os.path.exists(archivo):
        raise FileNotFoundError(f"No se encontró el archivo '{archivo}' en GitHub.")
    
    # Cargamos la Hoja1 que me pasaste
    df = pd.read_excel(archivo, sheet_name="Hoja1")
    
    # Limpieza de columnas y espacios
    df.columns = df.columns.str.strip()
    
    def limpiar_numero(val):
        try:
            if isinstance(val, str):
                val = val.replace('%', '').replace(',', '.')
            n = float(val)
            # Si el Excel guardó 0.02 en vez de 2, lo corregimos
            return n * 100 if 0 < n < 1 else n
        except:
            return 0.0

    if '% de Incapacidad Laboral' in df.columns:
        df['% de Incapacidad Laboral'] = df['% de Incapacidad Laboral'].apply(limpiar_numero)
    
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
    st.error(f"⚠️ Error Crítico: {e}")
    st.stop()

# --- interfaz de usuario ---
st.title("🧮 mega calculadora SRT: edición 549/25")
st.markdown("---")

if 'pericia' not in st.session_state:
    st.session_state.pericia = []

with st.sidebar:
    st.header("carga de hallazgos")
    
    # 1. Selección de Región
    region = st.selectbox("1. región topográfica", ["Columna", "MSI", "MSD", "MII", "MID"], index=None, placeholder="Seleccionar")
    
    # 2. Filtrado dinámico según la región elegida
    if region:
        if region == "Columna": kw = "Columna|Cervical|Dorsal|Lumbar|Sistema Nervioso"
        elif region in ["MSI", "MSD"]: kw = "Superior|Mano|Hombro|Codo|Muñeca|Brazo|Antebrazo"
        else: kw = "Inferior|Cadera|Rodilla|Tobillo|Pie|Pierna|Muslo"
        
        df_filtrado = df_maestro[df_maestro['Apartado'].str.contains(kw, case=False, na=False)]
        
        # 3. Tipo de hallazgo
        grupo = st.radio("2. tipo de hallazgo", ["osteoarticular / goniometría", "neurológico / radicular"])
        
        # Filtrar por capítulo
        if "osteo" in grupo:
            df_final = df_filtrado[df_filtrado['Capítulo'].str.contains("Osteoarticular", case=False, na=False)]
        else:
            df_final = df_filtrado[df_filtrado['Capítulo'].str.contains("Sistema Nervioso", case=False, na=False)]
            
        # 4. Selección de la lesión específica
        opciones = sorted(df_final['Descripción de Lesión'].unique())
        item_sel = st.selectbox("3. seleccionar secuela:", opciones, index=None, placeholder="Seleccionar")
        
        if item_sel:
            valor = df_final[df_final['Descripción de Lesión'] == item_sel]['% de Incapacidad Laboral'].iloc[0]
            st.info(f"valor baremo: {valor}%")
            
            if st.button("AGREGAR A LA PERICIA"):
                st.session_state.pericia.append({"reg": region, "desc": item_sel, "val": valor})
                st.rerun()

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
        
        # Lógica de topes
        llave = f"Columna {'Cervical' if 'Cervical' in p['desc'] else 'Dorsolumbar'}" if p['reg'] == "Columna" else p['reg']
        sumas_segmentales[llave] = sumas_segmentales.get(llave, 0) + p['val']

    # Definición de topes legales
    topes = {"MSI": 60.0, "MSD": 60.0, "MII": 60.0, "MID": 60.0, "Columna Cervical": 40.0, "Columna Dorsolumbar": 60.0}
    
    st.markdown("---")
    col_l, col_r = st.columns(2)
    
    with col_l:
        st.write("**control de topes regionales:**")
        valores_para_balthazard = []
        for s, suma in sumas_segmentales.items():
            t = topes.get(s, 100.0)
            v_final = min(suma, t)
            valores_para_balthazard.append(v_final)
            if suma > t: st.warning(f"⚠️ {s}: {suma}% excede el tope de {t}%.")
            else: st.write(f"✅ {s}: {suma}% (dentro del límite)")

        # Factores de ponderación
        st.markdown("### factores de ponderación")
        u_edad = st.number_input("edad del trabajador", 14, 99, 17)
        f_e = 0.05 if u_edad <= 20 else 0.04 if u_edad <= 30 else 0.03 if u_edad <= 40 else 0.02
        u_dif = st.selectbox("dificultad para tareas", ["leve (5%)", "intermedia (10%)", "alta (20%)"], index=1)
        f_d = {"leve (5%)": 0.05, "intermedia (10%)": 0.10, "alta (20%)": 0.20}[u_dif]
        
        # Cálculo final
        fisf_total = balthazard(valores_para_balthazard)
        incremento = fisf_total * (f_e + f_d)
        total_pre = fisf_total + incremento
        total_final = min(total_pre, 65.99) if fisf_total < 66.0 else total_pre

    with col_r:
        st.metric("daño físico total", f"{fisf_total}%")
        st.metric("incremento factores", f"{round(incremento, 2)}%")
        if total_final >= 66.0:
            st.error(f"## ILP FINAL: {round(total_final, 2)}% (TOTAL)")
        else:
            st.success(f"## ILP FINAL: {round(total_final, 2)}% (PARCIAL)")
        
        if st.button("🚨 BARRAR TODO"):
            st.session_state.pericia = []; st.rerun()