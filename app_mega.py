import streamlit as st
import pandas as pd

# --- configuración inicial ---
st.set_page_config(page_title="Calculadora SRT", layout="wide", page_icon="🧮")

def balthazard(lista):
    lista = sorted([x for x in lista if x > 0], reverse=True)
    if not lista: return 0.0
    total = lista[0]
    for i in range(1, len(lista)):
        total = total + (lista[i] * (100 - total) / 100)
    return round(total, 2)

@st.cache_data
def cargar_datos_completos():
    # IMPORTANTE: El archivo en GitHub DEBE llamarse exactamente así
    archivo = "calculadora_final_srt.xlsx"
    df_maestro = pd.read_excel(archivo, sheet_name="Sheet2")
    
    # Limpiamos nombres de columnas y espacios en los datos por seguridad
    df_maestro.columns = df_maestro.columns.str.strip()
    df_maestro['Capítulo'] = df_maestro['Capítulo'].astype(str).str.strip()
    df_maestro['Apartado'] = df_maestro['Apartado'].astype(str).str.strip()
    
    hojas_reg = ["MSI", "MSD", "MII", "MID", "Columna"]
    dict_reg = {h: pd.read_excel(archivo, sheet_name=h) for h in hojas_reg}
    for h in hojas_reg:
        dict_reg[h].columns = dict_reg[h].columns.str.strip()
        
    return df_maestro, dict_reg

try:
    df_maestro, dict_reg = cargar_datos_completos()
except Exception as e:
    st.error(f"❌ Error al cargar el Excel: {e}. Asegúrate de que el archivo se llame 'calculadora_final_srt.xlsx' en GitHub.")
    st.stop()

escalas_ms = {
    "grado 5 (normal - 0%)": 0.0, "grado 4 (leve - 20%)": 0.2, "grado 3 (moderado - 50%)": 0.5,
    "grado 2 (grave - 80%)": 0.8, "grado 1 (severo - 80%)": 0.8, "grado 0 (total - 100%)": 1.0
}

# --- interfaz principal ---
st.title("🧮 Calculadora SRT")
st.markdown("---")

if 'pericia' not in st.session_state:
    st.session_state.pericia = []

with st.sidebar:
    st.header("carga de hallazgos")
    region_sel = st.selectbox("1. región topográfica", ["Columna", "MSI", "MSD", "MII", "MID"], index=None, placeholder="Seleccionar")
    
    if region_sel:
        # Definimos palabras clave para filtrar el Apartado
        if region_sel == "Columna": kw = "Columna|Cervical|Dorsal|Lumbar|Sistema Nervioso"
        elif region_sel in ["MSI", "MSD"]: kw = "Superior|Mano|Hombro|Codo|Muñeca|Brazo|Antebrazo"
        else: kw = "Inferior|Cadera|Rodilla|Tobillo|Pie|Pierna|Muslo"
        
        df_contextual = df_maestro[df_maestro['Apartado'].str.contains(kw, case=False, na=False)]
    
    grupo = st.radio("2. tipo de hallazgo", ["lesiones osteoarticulares", "limitaciones funcionales", "lesiones neurológicas"])
    
    valor_final = 0.0
    descripcion_final = ""

    if region_sel:
        if grupo == "lesiones osteoarticulares":
            df_osteo = df_contextual[df_contextual['Capítulo'].str.contains("Osteoarticular", case=False, na=False)]
            # Quitamos las limitaciones de esta lista para no duplicar
            df_osteo = df_osteo[~df_osteo['Descripción de Lesión'].str.contains("Limitación", case=False, na=False)]
            
            lista_items = df_osteo['Descripción de Lesión'].unique()
            if len(lista_items) > 0:
                item = st.selectbox("seleccionar lesión:", sorted(lista_items), index=None, placeholder="Seleccionar")
                if item:
                    valor_final = df_osteo[df_osteo['Descripción de Lesión'] == item]['% de Incapacidad Laboral'].iloc[0]
                    descripcion_final = item
            else:
                st.info("ℹ️ No se encontraron lesiones puramente osteoarticulares para esta región.")

        elif grupo == "limitaciones funcionales":
            df_gonio = df_contextual[df_contextual['Descripción de Lesión'].str.contains("Limitación", case=False, na=False)]
            articulaciones = sorted(df_gonio['Descripción de Lesión'].str.split(' - ').str[0].unique())
            
            if articulaciones:
                art_sel = st.selectbox("articulación:", articulaciones, index=None, placeholder="Seleccionar")
                if art_sel:
                    df_movs = df_gonio[df_gonio['Descripción de Lesión'].str.contains(art_sel, case=False, na=False)]
                    mov_sel = st.selectbox("rango de movimiento:", df_movs['Descripción de Lesión'].unique(), index=None, placeholder="Seleccionar")
                    if mov_sel:
                        valor_final = df_movs[df_movs['Descripción de Lesión'] == mov_sel]['% de Incapacidad Laboral'].iloc[0]
                        descripcion_final = mov_sel
            else:
                st.info("ℹ️ No se encontraron tablas goniométricas para esta región.")

        else: # Lesiones neurológicas
            cats = ["Raíces y Dermatomas"] if region_sel == "Columna" else ["Nervios Periféricos (M/S)", "Raíces y Dermatomas"]
            sub_neuro = st.selectbox("categoría:", cats, index=None, placeholder="Seleccionar")
            
            if sub_neuro == "Nervios Periféricos (M/S)":
                df_reg = dict_reg[region_sel]
                nervio = st.selectbox("nervio:", df_reg['Estructura anatómica'].unique(), index=None, placeholder="Seleccionar")
                if nervio:
                    d = df_reg[df_reg['Estructura anatómica'] == nervio].iloc[0]
                    m = escalas_ms[st.selectbox("déficit motor", list(escalas_ms.keys()))] if d.get('Peso mot', 0) > 0 else 0
                    s = escalas_ms[st.selectbox("déficit sensitivo", list(escalas_ms.keys()))] if d.get('Peso sens', 0) > 0 else 0
                    valor_final = d['Max'] * ((d.get('Peso mot', 0) * m) + (d.get('Peso sens', 0) * s))
                    descripcion_final = nervio
                    
            elif sub_neuro == "Raíces y Dermatomas":
                df_rad = df_contextual[df_contextual['Apartado'].str.contains("Radicular", case=False, na=False)]
                item = st.selectbox("dermatoma:", df_rad['Descripción de Lesión'].unique(), index=None, placeholder="Seleccionar")
                if item:
                    valor_final = df_rad[df_rad['Descripción de Lesión'] == item]['% de Incapacidad Laboral'].iloc[0]
                    descripcion_final = item

    if st.button("AGREGAR") and descripcion_final:
        st.session_state.pericia.append({"reg": region_sel, "desc": descripcion_final, "val": round(valor_final, 2)})
        st.rerun()

# --- RESULTADOS ---
if st.session_state.pericia:
    st.markdown("---")
    st.subheader("📋 detalle de la pericia")
    sumas_seg = {}
    for i, item in enumerate(st.session_state.pericia):
        c1, c2, c3 = st.columns([2, 5, 1])
        c1.write(f"**{item['reg']}**")
        c2.write(f"{item['desc']} ({item['val']}%)")
        if c3.button("🗑️", key=f"d_{i}"):
            st.session_state.pericia.pop(i); st.rerun()
        
        # Agrupación por topes segmentales
        key = f"Columna {'Cervical' if 'Cervical' in item['desc'] else 'Dorsolumbar'}" if item['reg'] == "Columna" else item['reg']
        sumas_seg[key] = sumas_seg.get(key, 0) + item['val']

    topes = {"MSI": 60.0, "MSD": 60.0, "MII": 60.0, "MID": 60.0, "Columna Cervical": 40.0, "Columna Dorsolumbar": 60.0}
    
    st.markdown("---")
    l, r = st.columns(2)
    with l:
        st.write("**análisis de topes:**")
        v_topados = []
        for s, suma in sumas_seg.items():
            t = topes.get(s, 100.0)
            v = min(suma, t)
            v_topados.append(v)
            if suma > t: st.warning(f"⚠️ {s}: {suma}% excede el tope ({t}%).")
            else: st.write(f"✅ {s}: {suma}%")

        u_edad = st.number_input("edad", 14, 99, 25)
        f_e = 0.05 if u_edad <= 20 else 0.04 if u_edad <= 30 else 0.03 if u_edad <= 40 else 0.02
        u_dif = st.selectbox("dificultad", ["leve (5%)", "intermedia (10%)", "alta (20%)"], index=1)
        f_d = {"leve (5%)": 0.05, "intermedia (10%)": 0.10, "alta (20%)": 0.20}[u_dif]
        
        f_tot = balthazard(v_topados)
        inc = f_tot * (f_e + f_d)
        res = f_tot + inc
        res_f = min(res, 65.99) if f_tot < 66.0 else res

    with r:
        st.metric("daño físico", f"{f_tot}%")
        st.metric("factores", f"{round(inc, 2)}%")
        if res_f >= 66.0: st.error(f"## ILP FINAL: {round(res_f, 2)}% (TOTAL)")
        else: st.success(f"## ILP FINAL: {round(res_f, 2)}% (PARCIAL)")
        if st.button("🚨 borrar todo"): st.session_state.pericia = []; st.rerun()