import streamlit as st
import pandas as pd

# --- configuración y estilos ---
st.set_page_config(page_title="calculadora integral SRT", layout="wide", page_icon="🧮")

def balthazard(lista):
    lista = sorted([x for x in lista if x > 0], reverse=True)
    if not lista: return 0.0
    total = lista[0]
    for i in range(1, len(lista)):
        total = total + (lista[i] * (100 - total) / 100)
    return round(total, 2)

@st.cache_data
def cargar_datos_completos():
    df_maestro = pd.read_excel("calculadora_final_srt.xlsx", sheet_name="Sheet2")
    hojas_reg = ["MSI", "MSD", "MII", "MID", "Columna"]
    dict_reg = {h: pd.read_excel("calculadora_final_srt.xlsx", sheet_name=h) for h in hojas_reg}
    return df_maestro, dict_reg

df_maestro, dict_reg = cargar_datos_completos()

# escalas motoras/sensitivas
escalas_ms = {
    "grado 5 (normal - 0%)": 0.0, "grado 4 (leve - 20%)": 0.2, "grado 3 (moderado - 50%)": 0.5,
    "grado 2 (grave - 80%)": 0.8, "grado 1 (severo - 80%)": 0.8, "grado 0 (total - 100%)": 1.0
}

# --- interfaz principal ---
st.title("🧮 mega calculadora SRT: integración profesional")
st.markdown("---")

if 'pericia' not in st.session_state:
    st.session_state.pericia = []

with st.sidebar:
    st.header("carga de hallazgos")
    region_sel = st.selectbox("1. región topográfica", ["Columna", "MSI", "MSD", "MII", "MID"], index=None, placeholder="Seleccionar")
    
    if region_sel:
        if region_sel == "Columna": keywords = "Columna|Cervical|Dorsal|Lumbar|Sistema Nervioso"
        elif region_sel in ["MSI", "MSD"]: keywords = "Superior|Mano|Hombro|Codo|Muñeca|Brazo|Antebrazo"
        else: keywords = "Inferior|Cadera|Rodilla|Tobillo|Pie|Pierna|Muslo"
        df_contextual = df_maestro[df_maestro['Apartado'].str.contains(keywords, case=False, na=False)]
    
    grupo = st.radio("2. tipo de hallazgo", ["lesiones osteoarticulares", "limitaciones funcionales", "lesiones neurológicas"])
    
    valor_final = 0.0
    descripcion_final = ""

    if region_sel:
        if grupo == "lesiones osteoarticulares":
            df_osteo = df_contextual[df_contextual['Capítulo'] == "Osteoarticular"]
            item = st.selectbox("seleccionar lesión:", df_osteo['Descripción de Lesión'].unique(), index=None, placeholder="Seleccionar")
            if item:
                valor_final = df_osteo[df_osteo['Descripción de Lesión'] == item]['% de Incapacidad Laboral'].iloc[0]
                descripcion_final = item

        elif grupo == "limitaciones funcionales":
            df_gonio = df_contextual[df_contextual['Descripción de Lesión'].str.contains("Limitación", case=False, na=False)]
            art_sel = st.selectbox("articulación:", sorted(df_gonio['Descripción de Lesión'].str.split(' - ').str[0].unique()), index=None, placeholder="Seleccionar")
            if art_sel:
                mov_sel = st.selectbox("rango:", df_gonio[df_gonio['Descripción de Lesión'].str.contains(art_sel)]['Descripción de Lesión'].unique(), index=None, placeholder="Seleccionar")
                if mov_sel:
                    valor_final = df_gonio[df_gonio['Descripción de Lesión'] == mov_sel]['% de Incapacidad Laboral'].iloc[0]
                    descripcion_final = mov_sel

        else: # Lesiones neurológicas
            if region_sel == "Columna":
                cat_neuro = ["Raíces y Dermatomas"]
            else:
                cat_neuro = ["Nervios Periféricos (M/S)", "Raíces y Dermatomas"]
                
            sub_neuro = st.selectbox("categoría neurológica:", cat_neuro, index=None, placeholder="Seleccionar")
            
            if sub_neuro == "Nervios Periféricos (M/S)":
                df_reg = dict_reg[region_sel]
                item = st.selectbox("seleccionar nervio:", df_reg['Estructura anatómica'].unique(), index=None, placeholder="Seleccionar")
                if item:
                    datos = df_reg[df_reg['Estructura anatómica'] == item].iloc[0]
                    # Aquí evitamos el KeyError verificando si existen las columnas
                    m_def = escalas_ms[st.selectbox("déficit motor (m)", list(escalas_ms.keys()))] if 'Peso mot' in datos and datos['Peso mot'] > 0 else 0
                    s_def = escalas_ms[st.selectbox("déficit sensitivo (s)", list(escalas_ms.keys()))] if 'Peso sens' in datos and datos['Peso sens'] > 0 else 0
                    valor_final = datos['Max'] * ((datos.get('Peso mot', 0) * m_def) + (datos.get('Peso sens', 0) * s_def))
                    descripcion_final = item
            elif sub_neuro == "Raíces y Dermatomas":
                df_rad = df_contextual[df_contextual['Apartado'] == "Lesión Radicular"]
                item = st.selectbox("seleccionar dermatoma:", df_rad['Descripción de Lesión'].unique(), index=None, placeholder="Seleccionar")
                if item:
                    valor_final = df_rad[df_rad['Descripción de Lesión'] == item]['% de Incapacidad Laboral'].iloc[0]
                    descripcion_final = item

    if st.button("AGREGAR") and descripcion_final:
        st.session_state.pericia.append({"región": region_sel, "descripción": descripcion_final, "valor": round(valor_final, 2)})
        st.rerun()

# --- RESULTADOS FINALES ---
if st.session_state.pericia:
    st.markdown("---")
    st.subheader("📋 detalle de la pericia")
    sumas_seg = {}
    for i, item in enumerate(st.session_state.pericia):
        c1, c2, c3 = st.columns([2, 5, 1])
        c1.write(f"**{item['región']}**")
        c2.write(f"{item['descripción']} ({item['valor']}%)")
        if c3.button("🗑️", key=f"del_{i}"):
            st.session_state.pericia.pop(i); st.rerun()
        
        llave = f"Columna {'Cervical' if 'Cervical' in item['descripción'] else 'Dorsolumbar'}" if item['región'] == "Columna" else item['región']
        sumas_seg[llave] = sumas_seg.get(llave, 0) + item['valor']

    topes = {"MSI": 60.0, "MSD": 60.0, "MII": 60.0, "MID": 60.0, "Columna Cervical": 40.0, "Columna Dorsolumbar": 60.0}
    
    st.markdown("---")
    col_left, col_right = st.columns(2)
    with col_left:
        st.write("**análisis de topes regionales / segmentales:**")
        vals_topados = []
        for seg, suma in sumas_seg.items():
            t = topes.get(seg, 100.0)
            v = min(suma, t)
            vals_topados.append(v)
            if suma > t: st.warning(f"⚠️ {seg}: {suma}% excede el tope ({t}%). se limita a {t}%.")
            else: st.write(f"✅ {seg}: {suma}% (dentro del límite)")

        u_edad = st.number_input("edad del trabajador", 14, 99, 25)
        f_e = 0.05 if u_edad <= 20 else 0.04 if u_edad <= 30 else 0.03 if u_edad <= 40 else 0.02
        u_dif = st.selectbox("dificultad para tareas habituales", ["leve (5%)", "intermedia (10%)", "alta (20%)"], index=1)
        f_d = {"leve (5%)": 0.05, "intermedia (10%)": 0.10, "alta (20%)": 0.20}[u_dif]
        
        fisico = balthazard(vals_topados)
        inc = fisico * (f_e + f_d)
        res_pre = fisico + inc
        res_final = min(res_pre, 65.99) if fisico < 66.0 else res_pre

    with col_right:
        st.metric("daño físico total", f"{fisico}%")
        st.metric("incremento factores", f"{round(inc, 2)}%")
        if res_final >= 66.0: st.error(f"## ILP FINAL: {round(res_final, 2)}% (TOTAL)")
        else: st.success(f"## ILP FINAL: {round(res_final, 2)}% (PARCIAL)")
        if st.button("🚨 borrar todo"): st.session_state.pericia = []; st.rerun()