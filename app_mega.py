import streamlit as st
import pandas as pd

# --- configuración y estilos ---
st.set_page_config(page_title="calculadora integral SRT", layout="wide", page_icon="🧮")

# escalas oficiales según decreto 549/25
escalas_ms = {
    "grado 5 (normal - 0%)": 0.0, "grado 4 (leve - 20%)": 0.2, "grado 3 (moderado - 50%)": 0.5,
    "grado 2 (grave - 80%)": 0.8, "grado 1 (severo - 80%)": 0.8, "grado 0 (total - 100%)": 1.0
}

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
    # carga de sheet2 y hojas regionales
    df_maestro = pd.read_excel("calculadora_final_srt.xlsx", sheet_name="Sheet2")
    hojas_reg = ["MSI", "MSD", "MII", "MID", "Columna"]
    dict_reg = {h: pd.read_excel("calculadora_final_srt.xlsx", sheet_name=h) for h in hojas_reg}
    return df_maestro, dict_reg

df_maestro, dict_reg = cargar_datos_completos()

# --- interfaz principal ---
st.title("🧮 Calculadora SRT")
st.markdown("---")

if 'pericia' not in st.session_state:
    st.session_state.pericia = []

with st.sidebar:
    st.header("carga de hallazgos")
    
    # 1. selección de región
    region_sel = st.selectbox("1. región topográfica", ["Columna", "MSI", "MSD", "MII", "MID"], index=None, placeholder="Seleccionar")
    
    # filtro anatómico base para sheet2
    if region_sel == "Columna":
        keywords = "Columna|Cervical|Dorsal|Lumbar|Sistema Nervioso"
    elif region_sel in ["MSI", "MSD"]:
        keywords = "Superior|Mano|Hombro|Codo|Muñeca|Brazo|Antebrazo"
    elif region_sel in ["MII", "MID"]: # o mii o mid
        keywords = "Inferior|Cadera|Rodilla|Tobillo|Pie|Pierna|Muslo"
    else:
        keywords = "Columna" # valor de resguardo

    df_contextual = df_maestro[df_maestro['Apartado'].str.contains(keywords, case=False, na=False)]
    
    # 2. triple selector de grupo
    grupo = st.radio("2. tipo de hallazgo", 
                     ["lesiones osteoarticulares", "limitaciones funcionales", "lesiones neurológicas"])
    
    valor_final = 0.0
    descripcion_final = ""

    # bloque osteoarticular
    if grupo == "lesiones osteoarticulares" and region_sel:
        df_osteo_base = df_contextual[
            (df_contextual['Capítulo'] == "Osteoarticular") & 
            (~df_contextual['Descripción de Lesión'].str.contains("Limitación", case=False, na=False))
        ].copy()

        subtipo = st.selectbox("seleccionar categoría:", 
                                ["ver todas", "amputaciones", "fracturas", "artroplastias / prótesis", 
                                 "inestabilidad articular", "lesiones musculotendinosas", "anquilosis"], index=None, placeholder="Seleccionar")

        keywords_map = {
            "amputaciones": "Amputación",
            "fracturas": "Fractura|Luxofractura|Consolidación|Pseudoartrosis",
            "artroplastias / prótesis": "Artroplastía|Prótesis|Reemplazo",
            "inestabilidad articular": "Inestabilidad|Luxación|Subluxación",
            "lesiones musculotendinosas": "Tendón|Músculo|Desinserción|Manguito|Ruptura",
            "anquilosis": "Anquilosis"
        }

        if subtipo and subtipo != "ver todas":
            filtro_kw = keywords_map[subtipo.lower()]
            df_filtrado_tipo = df_osteo_base[df_osteo_base['Descripción de Lesión'].str.contains(filtro_kw, case=False, na=False)].copy()
            df_filtrado_tipo['Hueso_Sector'] = df_filtrado_tipo['Descripción de Lesión'].str.split(' - ').str[0]
            
            hueso_lista = sorted(df_filtrado_tipo['Hueso_Sector'].unique())
            hueso_sel = st.selectbox(f"seleccionar hueso/sector ({subtipo.lower()}):", hueso_lista, index=None, placeholder="Seleccionar")
            
            if hueso_sel:
                df_final_osteo = df_filtrado_tipo[df_filtrado_tipo['Hueso_Sector'] == hueso_sel]
            else:
                df_final_osteo = pd.DataFrame()
        else:
            df_final_osteo = df_osteo_base

        if not df_final_osteo.empty:
            item = st.selectbox("seleccionar lesión específica:", df_final_osteo['Descripción de Lesión'].unique(), index=None, placeholder="Seleccionar")
            if item:
                fila_sel = df_final_osteo[df_final_osteo['Descripción de Lesión'] == item].iloc[0]
                valor_final = fila_sel['% de Incapacidad Laboral']
                descripcion_final = item

    # bloque goniometría
    elif grupo == "limitaciones funcionales" and region_sel:
        df_gonio = df_contextual[df_contextual['Descripción de Lesión'].str.contains("Limitación", case=False, na=False)].copy()
        if not df_gonio.empty:
            df_gonio['articulacion'] = df_gonio['Descripción de Lesión'].str.split(' - ').str[0].str.replace('Limitación Funcional de ', '', case=False)
            art_sel = st.selectbox("seleccionar articulación:", sorted(df_gonio['articulacion'].unique()), index=None, placeholder="Seleccionar")
            
            if art_sel:
                df_movs = df_gonio[df_gonio['articulacion'] == art_sel].copy()
                df_movs['movimiento'] = df_movs['Descripción de Lesión'].str.split(' - ').str[1]
                mov_sel = st.selectbox("seleccionar rango de movimiento:", df_movs['movimiento'].unique(), index=None, placeholder="Seleccionar")
                
                if mov_sel:
                    fila_final = df_movs[df_movs['movimiento'] == mov_sel].iloc[0]
                    valor_final = fila_final['% de Incapacidad Laboral']
                    descripcion_final = fila_final['Descripción de Lesión']
        else:
            st.warning("no se encontraron limitaciones para esta región.")

    # bloque neurología (unificado)
    elif grupo == "lesiones neurológicas" and region_sel:
        df_neuro_total = df_maestro[df_maestro['Capítulo'] == "Sistema Nervioso"].copy()
        
        # filtro anatómico estricto
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

        sub_neuro = st.selectbox("categoría neurológica:", opciones_cat, index=None, placeholder="Seleccionar")
        
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

        if lista_final:
            item = st.selectbox("seleccionar diagnóstico:", sorted(lista_final), index=None, placeholder="Seleccionar")
            
            if item:
                if es_calculable:
                    df_reg = dict_reg[region_sel]
                    datos = df_reg[df_reg['Estructura anatómica'] == item].iloc[0]
                    p_m, p_s, v_max = datos.get('Peso mot', 0.0), datos.get('Peso sens', 0.0), datos['Max']
                    
                    m_def, s_def = 0.0, 0.0
                    st.subheader("evaluación de déficit (m/s)")
                    if p_m > 0:
                        m_def_sel = st.selectbox("déficit motor (m)", list(escalas_ms.keys()), index=None, placeholder="Seleccionar")
                        if m_def_sel: m_def = escalas_ms[m_def_sel]
                    if p_s > 0:
                        s_def_sel = st.selectbox("déficit sensitivo (s)", list(escalas_ms.keys()), index=None, placeholder="Seleccionar")
                        if s_def_sel: s_def = escalas_ms[s_def_sel]
                    
                    valor_final = (v_max * ((p_m * m_def) + (p_s * s_def))) * 100
                    descripcion_final = item
                else:
                    fila = df_neuro_filtrado[df_neuro_filtrado['Descripción de Lesión'] == item].iloc[0]
                    valor_final = fila['% de Incapacidad Laboral']
                    descripcion_final = item
                    
                    if pd.isna(valor_final) or isinstance(valor_final, str):
                        st.warning("Asignar este valor manualmente.")
                        valor_final = st.number_input("ingrese % manualmente:", 0.0, 100.0, 0.0)
                    else:
                        if valor_final <= 1: valor_final *= 100
                        st.info(f"porcentaje baremo: {valor_final}%")

    # ajuste final antes de agregar
    if 0 < valor_final <= 1: valor_final *= 100

    if st.button("AGREGAR") and descripcion_final:
        st.session_state.pericia.append({
            "región": region_sel, "tipo": grupo, "descripción": descripcion_final, "valor": round(valor_final, 2)
        })
        st.rerun()

# --- resultados y cálculos finales ---
if st.session_state.pericia:
    st.markdown("---")
    st.subheader("📋 Detalle de secuelas")
    
    # Creamos una lista para procesar topes específicos
    for i, item in enumerate(st.session_state.pericia):
        col1, col2, col3 = st.columns([2, 5, 1])
        col1.write(f"**{item['región']}**")
        col2.write(f"{item['descripción']} ({item['valor']}%)")
        if col3.button("🗑️", key=f"btn_{i}"):
            st.session_state.pericia.pop(i)
            st.rerun()
    
    # Lógica de topes segmentales y regionales
    sumas_por_segmento = {}
    
    for item in st.session_state.pericia:
        reg = item['región']
        desc = item['descripción']
        
        # Identificación de segmento de columna
        if reg == "Columna":
            if "Cervical" in desc:
                llave = "Columna Cervical"
            else:
                llave = "Columna Dorsolumbar"
        else:
            llave = reg
            
        sumas_por_segmento[llave] = sumas_por_segmento.get(llave, 0) + item['valor']

    # Definición de topes legales (Dec. 549/25)
    topes_legales = {
        "MSI": 60.0, "MSD": 60.0, "MII": 60.0, "MID": 60.0, 
        "Columna Cervical": 40.0, "Columna Dorsolumbar": 60.0
    }

    st.markdown("---")
    c1, col_metrica = st.columns([1, 1])
    
    valores_topados = []
    with c1:
        st.write("**análisis de topes regionales / segmentos:**")
        for seg, suma in sumas_por_segmento.items():
            tope = topes_legales.get(seg, 100.0)
            v_final_seg = min(suma, tope)
            valores_topados.append(v_final_seg)
            
            tipo_tope = "tope de amputación" if "M" in seg else "tope segmental"
            
            if suma > tope:
                st.warning(f"⚠️ {seg}: {suma}% excede el {tipo_tope} ({tope}%). se limita a {tope}%.")
            else:
                st.write(f"✅ {seg}: {suma}% (dentro del límite)")

        st.markdown("### ⚖️ Factores de ponderación (Dec. 549/25)")
        
        u_edad = st.number_input("Edad del trabajador", 14, 100, 25)
        if u_edad <= 20: f_e = 0.05
        elif u_edad <= 30: f_e = 0.04
        elif u_edad <= 40: f_e = 0.03
        else: f_e = 0.02
        
        st.caption(f"factor edad: {int(f_e*100)}% asignado automáticamente.")

        opciones_dif = ["leve (5%)", "intermedia (10%)", "alta (20%)"]
        u_dif = st.selectbox("dificultad para realizar tareas habituales", opciones_dif, index=1)
        map_dif = {"leve (5%)": 0.05, "intermedia (10%)": 0.10, "alta (20%)": 0.20}
        f_d = map_dif[u_dif]
        
        fisico_total = balthazard(valores_topados)
        suma_factores = f_e + f_d
        incremento = fisico_total * suma_factores
        resultado_preliminar = fisico_total + incremento

        if fisico_total < 66.0:
            resultado_final = min(resultado_preliminar, 65.99)
            if resultado_preliminar >= 66.0:
                st.info("💡 se aplicó el tope legal de 65.99% (incapacidad parcial).")
        else:
            resultado_final = resultado_preliminar

    with col_metrica:
        st.metric("daño físico total", f"{fisico_total}%")
        st.metric("incremento factores", f"{round(incremento, 2)}%")
        
        if resultado_final >= 66.0:
            st.error(f"## ILP FINAL: {round(resultado_final, 2)}% (TOTAL)")
        else:
            st.success(f"## ILP FINAL: {round(resultado_final, 2)}% (PARCIAL)")
        
        if st.button("🚨 borrar todo"):
            st.session_state.pericia = []
            st.rerun()

        st.markdown("---")
        if st.button("📄 Generar texto para informe SRT"):
            texto_informe = "detalle de secuelas físicas (decreto 549/25):\n"
            for item in st.session_state.pericia:
                texto_informe += f"- {item['región']}: {item['descripción']} ({item['valor']}%)\n"
            
            texto_informe += f"\nincapacidad física global (fórmula de balthazard): {fisico_total}%\n"
            texto_informe += f"factor edad aplicable: {int(f_e*100)}%\n"
            texto_informe += f"factor dificultad aplicable: {int(f_d*100)}%\n"
            texto_informe += f"incapacidad laboral permanente (ILP) final: {round(resultado_final, 2)}%\n"
            
            st.text_area("copiar y pegar en el dictamen médico:", value=texto_informe, height=250)