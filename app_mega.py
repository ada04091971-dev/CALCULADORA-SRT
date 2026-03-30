import streamlit as st
import pandas as pd

# --- Configuración inicial ---
st.set_page_config(page_title="Calculadora Integral SRT", layout="wide")

# Escalas oficiales según Decreto 549/25
escalas_ms = {
    "Grado 5 (Normal - 0%)": 0.0, "Grado 4 (Leve - 20%)": 0.2, "Grado 3 (Moderado - 50%)": 0.5,
    "Grado 2 (Grave - 80%)": 0.8, "Grado 1 (Severo - 80%)": 0.8, "Grado 0 (Total - 100%)": 1.0
}

# Topes por amputación total del segmento o miembro
topes_amputacion = {
    "MSI": 60.0, "MSD": 60.0, "MII": 60.0, "MID": 60.0, "Columna": 40.0
}

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

# --- Interfaz principal ---
st.title("🛡️ Mega Calculadora SRT: Integración Profesional")
st.markdown("---")

if 'pericia' not in st.session_state:
    st.session_state.pericia = []

with st.sidebar:
    st.header("Carga de hallazgos")
    
    # 1. Selección de región
    region_sel = st.selectbox("1. Región topográfica", ["Columna", "MSI", "MSD", "MII", "MID"])
    
    # Filtro anatómico base para Sheet2
    if region_sel == "Columna":
        keywords = "Columna|Cervical|Dorsal|Lumbar|Sistema Nervioso"
    elif region_sel in ["MSI", "MSD"]:
        keywords = "Superior|Mano|Hombro|Codo|Muñeca|Brazo|Antebrazo"
    else: # MII o MID
        keywords = "Inferior|Cadera|Rodilla|Tobillo|Pie|Pierna|Muslo"

    df_contextual = df_maestro[df_maestro['Apartado'].str.contains(keywords, case=False, na=False)]
    
    # 2. Triple selector de grupo
    grupo = st.radio("2. Tipo de hallazgo", 
                     ["Lesiones osteoarticulares", "Limitaciones funcionales", "Lesiones neurológicas"])
    
    valor_final = 0.0
    descripcion_final = ""

    # --- LÓGICA OSTEOARTICULAR ---
    if grupo == "Lesiones osteoarticulares":
        df_osteo_base = df_contextual[
            (df_contextual['Capítulo'] == "Osteoarticular") & 
            (~df_contextual['Descripción de Lesión'].str.contains("Limitación", case=False, na=False))
        ].copy()

        subtipo = st.selectbox("Seleccionar categoría:", 
                                ["Ver todas", "Amputaciones", "Fracturas", "Artroplastias / Prótesis", 
                                 "Inestabilidad articular", "Lesiones musculotendinosas", "Anquilosis"])

        keywords_map = {
            "amputaciones": "Amputación",
            "fracturas": "Fractura|Luxofractura|Consolidación|Pseudoartrosis",
            "artroplastias / prótesis": "Artroplastía|Prótesis|Reemplazo",
            "inestabilidad articular": "Inestabilidad|Luxación|Subluxación",
            "lesiones musculotendinosas": "Tendón|Músculo|Desinserción|Manguito|Ruptura",
            "anquilosis": "Anquilosis"
        }

        if subtipo != "Ver todas":
            filtro_kw = keywords_map[subtipo.lower()]
            df_filtrado_tipo = df_osteo_base[df_osteo_base['Descripción de Lesión'].str.contains(filtro_kw, case=False, na=False)].copy()
            df_filtrado_tipo['Hueso_Sector'] = df_filtrado_tipo['Descripción de Lesión'].str.split(' - ').str[0]
            
            hueso_lista = sorted(df_filtrado_tipo['Hueso_Sector'].unique())
            hueso_sel = st.selectbox(f"Seleccionar hueso/sector ({subtipo.lower()}):", hueso_lista, index=None)
            
            if hueso_sel:
                df_final_osteo = df_filtrado_tipo[df_filtrado_tipo['Hueso_Sector'] == hueso_sel]
            else:
                df_final_osteo = pd.DataFrame()
        else:
            df_final_osteo = df_osteo_base

        if not df_final_osteo.empty:
            item = st.selectbox("Seleccionar lesión específica:", df_final_osteo['Descripción de Lesión'].unique(), index=None)
            if item:
                fila_sel = df_final_osteo[df_final_osteo['Descripción de Lesión'] == item].iloc[0]
                valor_final = fila_sel['% de Incapacidad Laboral']
                descripcion_final = item

    # --- LÓGICA GONIOMETRÍA ---
    elif grupo == "Limitaciones funcionales":
        df_gonio = df_contextual[df_contextual['Descripción de Lesión'].str.contains("Limitación", case=False, na=False)].copy()
        if not df_gonio.empty:
            df_gonio['articulacion'] = df_gonio['Descripción de Lesión'].str.split(' - ').str[0].str.replace('Limitación Funcional de ', '', case=False)
            art_sel = st.selectbox("Seleccionar articulación:", sorted(df_gonio['articulacion'].unique()), index=None)
            
            if art_sel:
                df_movs = df_gonio[df_gonio['articulacion'] == art_sel].copy()
                df_movs['movimiento'] = df_movs['Descripción de Lesión'].str.split(' - ').str[1]
                mov_sel = st.selectbox("Seleccionar rango de movimiento:", df_movs['movimiento'].unique(), index=None)
                
                if mov_sel:
                    fila_final = df_movs[df_movs['movimiento'] == mov_sel].iloc[0]
                    valor_final = fila_final['% de Incapacidad Laboral']
                    descripcion_final = fila_final['Descripción de Lesión']
        else:
            st.warning("No se encontraron limitaciones para esta región.")

    # --- LÓGICA NEUROLÓGICA ---
    else:
        df_neuro_total = df_maestro[df_maestro['Capítulo'] == "Sistema Nervioso"].copy()
        
        # Filtro anatómico estricto
        if region_sel == "Columna":
            df_neuro_filtrado = df_neuro_total[df_neuro_total['Apartado'].isin([
                "Pares Craneales", "Lesión Radicular", "Lesión Medular", 
                "Traumatismo Craneoencefálico (TEC)", "Otras secuelas neurológicas"
            ])]
            opciones_cat = ["Raíces y Dermatomas", "Pares Craneales", "Lesión Medular", "TEC y Daño Cerebral"]
            
        elif region_sel in ["MSI", "MSD"]:
            df_neuro_filtrado = df_neuro_total[
                (df_neuro_total['Apartado'].isin(["Lesión de Plexo", "Lesión de Nervios Periféricos", "Lesión de Nervio Colateral de Mano"])) &
                (df_neuro_total['Descripción de Lesión'].str.contains("Superior|Braquial|Mano|Cervical|Colateral", case=False, na=False))
            ]
            opciones_cat = ["Nervios (Evaluación M/S)", "Plexos y Lesiones Fijas"]
            
        else: # MII, MID
            df_neuro_filtrado = df_neuro_total[
                (df_neuro_total['Apartado'].isin(["Lesión de Plexo", "Lesión de Nervios Periféricos"])) &
                (df_neuro_total['Descripción de Lesión'].str.contains("Inferior|Lumbar|Sacro|Ciático|Femoral|Peroneo|Tibial|Plantar|Safeno|Sural", case=False, na=False))
            ]
            opciones_cat = ["Nervios (Evaluación M/S)", "Plexos y Lesiones Fijas"]

        sub_neuro = st.selectbox("Categoría neurológica:", opciones_cat)
        
        lista_final = []
        es_calculable = False
        
        if sub_neuro == "Nervios (Evaluación M/S)":
            df_reg = dict_reg[region_sel]
            df_nervios_reg = df_reg[df_reg['Estructura anatómica'].str.contains('Nervio|Raíz', case=False, na=False)]
            lista_final = df_nervios_reg['Estructura anatómica'].dropna().unique().tolist()
            es_calculable = True
        elif sub_neuro == "Plexos y Lesiones Fijas":
            lista_final = df_neuro_filtrado['Descripción de Lesión'].dropna().unique().tolist()
        elif sub_neuro == "Raíces y Dermatomas":
            lista_final = df_neuro_filtrado[df_neuro_filtrado['Apartado'] == "Lesión Radicular"]['Descripción de Lesión'].dropna().unique().tolist()
        elif sub_neuro == "Pares Craneales":
            lista_final = df_neuro_filtrado[df_neuro_filtrado['Apartado'] == "Pares Craneales"]['Descripción de Lesión'].dropna().unique().tolist()
        elif sub_neuro == "Lesión Medular":
            lista_final = df_neuro_filtrado[df_neuro_filtrado['Apartado'] == "Lesión Medular"]['Descripción de Lesión'].dropna().unique().tolist()
        elif sub_neuro == "TEC y Daño Cerebral":
            lista_final = df_neuro_filtrado[df_neuro_filtrado['Apartado'].isin(["Traumatismo Craneoencefálico (TEC)", "Otras secuelas neurológicas"])]['Descripción de Lesión'].dropna().unique().tolist()

        item = st.selectbox("Seleccionar diagnóstico:", sorted(lista_final), index=None)
        
        if item:
            if es_calculable:
                df_reg = dict_reg[region_sel]
                datos = df_reg[df_reg['Estructura anatómica'] == item].iloc[0]
                p_m, p_s, v_max = datos.get('Peso mot', 0.0), datos.get('Peso sens', 0.0), datos['Max']
                
                m_def, s_def = 0.0, 0.0
                st.subheader("Evaluación de déficit (M/S)")
                if p_m > 0:
                    m_def = escalas_ms[st.selectbox("Déficit motor (M)", list(escalas_ms.keys()))]
                if p_s > 0:
                    s_def = escalas_ms[st.selectbox("Déficit sensitivo (S)", list(escalas_ms.keys()))]
                
                valor_final = (v_max * ((p_m * m_def) + (p_s * s_def))) * 100
                descripcion_final = item
            else:
                fila = df_neuro_filtrado[df_neuro_filtrado['Descripción de Lesión'] == item].iloc[0]
                valor_final = fila['% de Incapacidad Laboral']
                descripcion_final = item
                
                if pd.isna(valor_final) or isinstance(valor_final, str):
                    st.warning("El Decreto exige asignar este valor según criterio médico.")
                    valor_final = st.number_input("Ingrese % manualmente:", 0.0, 100.0, 0.0)
                else:
                    if valor_final <= 1: valor_final *= 100
                    st.info(f"Porcentaje Baremo: {valor_final}%")

    # Ajuste final antes de agregar
    if 0 < valor_final <= 1: valor_final *= 100

    if st.button("➕ Agregar a la pericia") and descripcion_final:
        st.session_state.pericia.append({
            "región": region_sel, "tipo": grupo, "descripción": descripcion_final, "valor": round(valor_final, 2)
        })
        st.rerun()

# --- Resultados y cálculos finales ---
if st.session_state.pericia:
    st.markdown("---")
    st.subheader("📋 Detalle de la pericia")
    
    for i, item in enumerate(st.session_state.pericia):
        col1, col2, col3 = st.columns([2, 5, 1])
        col1.write(f"**{item['región']}**")
        col2.write(f"{item['descripción']} ({item['valor']}%)")
        if col3.button("🗑️", key=f"btn_{i}"):
            st.session_state.pericia.pop(i)
            st.rerun()
    
    df_p = pd.DataFrame(st.session_state.pericia)
    sumas_regionales = df_p.groupby('región')['valor'].sum().to_dict()
    valores_topados = []

    st.markdown("---")
    c1, col_metrica = st.columns([1, 1])
    
    with c1:
        st.write("**Análisis de topes por miembro/sector:**")
        for reg, suma in sumas_regionales.items():
            tope = topes_amputacion.get(reg, 100.0)
            v_final_reg = min(suma, tope)
            valores_topados.append(v_final_reg)
            
            if suma > tope:
                st.warning(f"⚠️ {reg}: {suma}% excede el tope de amputación ({tope}%). Se limita a {tope}%.")
            else:
                st.write(f"✅ {reg}: {suma}% (dentro del límite)")

        st.markdown("### ⚖️ Factores de ponderación (Dec. 549/25)")
        
        u_edad = st.number_input("Edad del trabajador", 14, 100, 25)
        if u_edad <= 20: f_e = 0.05
        elif u_edad <= 30: f_e = 0.04
        elif u_edad <= 40: f_e = 0.03
        else: f_e = 0.02
        
        st.caption(f"Factor edad: {int(f_e*100)}% asignado automáticamente.")

        opciones_dif = ["leve (5%)", "intermedia (10%)", "alta (20%)"]
        u_dif = st.selectbox("Dificultad para realizar tareas habituales", opciones_dif, index=1)
        map_dif = {"leve (5%)": 0.05, "intermedia (10%)": 0.10, "alta (20%)": 0.20}
        f_d = map_dif[u_dif]
        
        fisico_total = balthazard(valores_topados)
        suma_factores = f_e + f_d
        incremento = fisico_total * suma_factores
        resultado_preliminar = fisico_total + incremento

        if fisico_total < 66.0:
            resultado_final = min(resultado_preliminar, 65.99)
            if resultado_preliminar >= 66.0:
                st.info("💡 Se aplicó el tope legal de 65.99% (Incapacidad parcial).")
        else:
            resultado_final = resultado_preliminar

    with col_metrica:
        st.metric("Daño físico total", f"{fisico_total}%")
        st.metric("Incremento factores", f"{round(incremento, 2)}%")
        
        if resultado_final >= 66.0:
            st.error(f"## ILP FINAL: {round(resultado_final, 2)}% (TOTAL)")
        else:
            st.success(f"## ILP FINAL: {round(resultado_final, 2)}% (PARCIAL)")
        
        if st.button("🚨 Borrar todo el dictamen"):
            st.session_state.pericia = []
            st.rerun()

        st.markdown("---")
        if st.button("📄 Generar texto para informe SRT"):
            texto_informe = "Detalle de secuelas físicas (Decreto 549/25):\n"
            for item in st.session_state.pericia:
                texto_informe += f"- {item['región']}: {item['descripción']} ({item['valor']}%)\n"
            
            texto_informe += f"\nIncapacidad física global (Fórmula de Balthazard): {fisico_total}%\n"
            texto_informe += f"Factor edad aplicable: {int(f_e*100)}%\n"
            texto_informe += f"Factor dificultad aplicable: {int(f_d*100)}%\n"
            texto_informe += f"Incapacidad Laboral Permanente (ILP) final: {round(resultado_final, 2)}%\n"
            
            st.text_area("Copiar y pegar en el dictamen médico:", value=texto_informe, height=250)