import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Calculadora integral SRT", layout="wide", page_icon="🧮")

def format_text(text):
    if not text: return ""
    text = str(text).strip()
    return text[0].upper() + text[1:]

# --- DICCIONARIO MAESTRO DE PESOS (Nervios) --- (se mantiene igual)
pesos_nervios_completos = { ... }  # (el mismo que tenías)

escalas_ms = { ... }  # (el mismo)

@st.cache_data
def cargar_datos():
    archivo = "calculadora_final_srt.xlsx"
    if not os.path.exists(archivo):
        archivos_xlsx = [f for f in os.listdir(".") if f.endswith(".xlsx")]
        archivo = archivos_xlsx[0] if archivos_xlsx else ""
    if not archivo: 
        st.error("No se encontró el archivo calculadora_final_srt.xlsx")
        st.stop()
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

df_maestro = cargar_datos()

def balthazard(lista):
    lista = sorted([x for x in lista if x > 0], reverse=True)
    if not lista: return 0.0
    total = lista[0]
    for i in range(1, len(lista)):
        total = total + (lista[i] * (100 - total) / 100)
    return round(total, 2)

# =============================================
# ================= INTERFAZ ==================
# =============================================
st.title("🧮 **Mega Calculadora SRT – Decreto 549/25**")
st.markdown("---")

if 'pericia' not in st.session_state:
    st.session_state.pericia = []

with st.sidebar:
    st.header("**Carga de hallazgos**")
    
    region = st.selectbox("**1. Región topográfica**", ["Columna", "MSI", "MSD", "MII", "MID"], index=None, placeholder="Seleccionar")
    
    if region:
        # 2. Sector anatómico
        if region == "Columna":
            sectores = ["Cervical", "Dorsal", "Lumbar", "Sacro", "Coccígeo"]
        elif region in ["MSI", "MSD"]:
            sectores = ["Hombro", "Codo", "Muñeca", "Mano", "Brazo", "Antebrazo"]
        else:
            sectores = ["Cadera", "Rodilla", "Tobillo", "Pie", "Pierna", "Muslo"]
        
        sector_sel = st.selectbox("**2. Sector anatómico**", ["Ver todos"] + sectores, index=0)
        
        # 3. Tipo de hallazgo
        tipo_hallazgo = st.radio("**3. Tipo de hallazgo**", ["Osteoarticular y Ligamentario", "Neurológico"])
        
        # 4. Categoría
        if tipo_hallazgo == "Osteoarticular y Ligamentario":
            if region == "Columna":
                cats = ["Ver todas", "Fracturas Vertebrales", "Lesiones Discales y Ligamentarias", 
                        "Limitación Funcional", "Anquilosis"]
            else:
                cats = ["Ver todas", "Meniscos / Ligamentos", "Fracturas / Luxofracturas", 
                        "Anquilosis / Limitaciones", "Amputaciones", "Prótesis"]
        else:
            cats = ["Ver todas", "Raíces y dermatomas", "Nervios periféricos", "Plexos", "Lesión medular"]
        
        cat_sel = st.selectbox("**4. Categoría**", cats, index=0)
        
        # === FILTRADO CORREGIDO (ninguna lesión se omite) ===
        df_filtrado = df_maestro.copy()
        
        # Filtro por sector (con mapa ampliado)
        if sector_sel != "Ver todos":
            if region == "Columna":
                sector_map = {
                    "Cervical": r"Cervical|C1|C2|C3|C4|C5|C6|C7|C8|odontoides|apofisis|apófisis|atlas|axis",
                    "Dorsal": r"Dorsal|D1|D2|D3|D4|D5|D6|D7|D8|D9|D10|D11|D12",
                    "Lumbar": r"Lumbar|L1|L2|L3|L4|L5",
                    "Sacro": r"Sacro",
                    "Coccígeo": r"Coxis|Coccígeo|coccigeo"
                }
                kw_sector = sector_map.get(sector_sel, sector_sel)
                df_filtrado = df_filtrado[df_filtrado['Descripción de Lesión'].str.contains(kw_sector, case=False, regex=True)]
            else:
                df_filtrado = df_filtrado[df_filtrado['Descripción de Lesión'].str.contains(sector_sel, case=False)]
        
        # Filtro por tipo
        if tipo_hallazgo == "Osteoarticular y Ligamentario":
            df_filtrado = df_filtrado[df_filtrado['Capítulo'].str.contains("Osteoarticular", case=False)]
        else:
            df_filtrado = df_filtrado[df_filtrado['Capítulo'].str.contains("Sistema Nervioso", case=False)]
        
        # Filtro por categoría (CORREGIDO)
        if cat_sel != "Ver todas":
            map_keywords = {
                "Fracturas Vertebrales": "Fracturas Vertebrales",
                "Lesiones Discales y Ligamentarias": "Lesiones Discales Y Ligamentarias",   # ← clave corregida
                "Limitación Funcional": "Limitación Funcional",
                "Anquilosis": "Anquilosis",
                "Meniscos / Ligamentos": "Menisco|Capsulo|Ligamento",
                "Fracturas / Luxofracturas": "Fractura|Luxofractura",
                "Anquilosis / Limitaciones": "Anquilosis|Limitación",
                "Amputaciones": "Amputación",
                "Prótesis": "Prótesis",
                "Raíces y dermatomas": "Radicular|Dermatoma",
                "Nervios periféricos": "Nervio",
                "Plexos": "Plexo",
                "Lesión medular": "Medular"
            }
            kw = map_keywords.get(cat_sel, cat_sel)
            df_filtrado = df_filtrado[df_filtrado['Descripción de Lesión'].str.contains(kw, case=False)]
        
        opciones = sorted(df_filtrado['Descripción de Lesión'].unique())
        
        if opciones:
            item_sel = st.selectbox(f"**5. Secuela específica ({len(opciones)})**", opciones, 
                                    format_func=format_text, index=None, placeholder="Seleccionar")
            
            if item_sel:
                v_max = df_filtrado[df_filtrado['Descripción de Lesión'] == item_sel]['% de Incapacidad Laboral'].iloc[0]
                valor_calculado = v_max
                
                es_nervio = any(x in item_sel.lower() for x in ["nervio", "neurológico"]) and "dermatoma" not in item_sel.lower()
                if es_nervio:
                    st.markdown("---")
                    st.write("**Evaluación de déficit funcional (M/S)**")
                    p_mot, p_sens = 0.5, 0.5
                    for n, p in pesos_nervios_completos.items():
                        if n.lower() in item_sel.lower():
                            p_mot, p_sens = p['m'], p['s']
                            break
                    m_sel = st.selectbox("**Déficit motor (M)**", list(escalas_ms.keys()), index=0)
                    s_sel = st.selectbox("**Déficit sensitivo (S)**", list(escalas_ms.keys()), index=0)
                    valor_calculado = v_max * ((p_mot * escalas_ms[m_sel]) + (p_sens * escalas_ms[s_sel]))
                    st.caption(f"Ponderación legal: Motor {int(p_mot*100)}% / Sensitivo {int(p_sens*100)}%")
                
                st.info(f"**Valor a agregar: {round(valor_calculado, 2)}%**")
                if st.button("**AGREGAR**"):
                    st.session_state.pericia.append({"reg": region, "desc": item_sel, "val": round(valor_calculado, 2)})
                    st.rerun()

# =============================================
# ================= RESULTADOS =================
# =============================================
# (el bloque de resultados es el mismo que tenías antes - no lo modifico aquí para no alargar)
if st.session_state.pericia:
    # ... (pega aquí el bloque de resultados que ya tenías en la versión anterior)
    pass   # ← reemplaza esto con tu bloque de resultados anterior