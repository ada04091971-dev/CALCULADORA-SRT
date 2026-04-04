import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Calculadora integral SRT", layout="wide", page_icon="🧮")

def format_text(text):
    if not text: return ""
    text = str(text).strip()
    return text[0].upper() + text[1:]

# --- PESOS NERVIOS (sin cambios) ---
pesos_nervios_completos = { ... }  # (mantengo el diccionario completo que ya tenías)

escalas_ms = { ... }  # (mantengo igual)

@st.cache_data
def cargar_datos():
    archivo = "calculadora_final_srt.xlsx"
    if not os.path.exists(archivo):
        archivos = [f for f in os.listdir(".") if f.endswith(".xlsx")]
        archivo = archivos[0] if archivos else ""
    if not archivo:
        st.error("No se encontró el archivo calculadora_final_srt.xlsx")
        st.stop()

    df_main = pd.read_excel(archivo, sheet_name="Lesiones ").fillna("")
    df_mid = pd.read_excel(archivo, sheet_name="Miembro Inferior  Derecho").fillna("")
    df_mii = pd.read_excel(archivo, sheet_name="Miembro Inferior Izquierdo").fillna("")

    for df in [df_main, df_mid, df_mii]:
        df.columns = df.columns.str.strip()
        if '% de Incapacidad Laboral' in df.columns:
            df['% de Incapacidad Laboral'] = df['% de Incapacidad Laboral'].apply(limpiar_numero)

    return df_main, df_mid, df_mii

def limpiar_numero(val):
    try:
        if isinstance(val, str):
            val = val.replace('%', '').replace(',', '.')
        n = float(val)
        return n * 100 if 0 < n < 1 else n
    except:
        return 0.0

df_main, df_mid, df_mii = cargar_datos()

def balthazard(lista):
    lista = sorted([x for x in lista if x > 0], reverse=True)
    if not lista: return 0.0
    total = lista[0]
    for i in range(1, len(lista)):
        total = total + (lista[i] * (100 - total) / 100)
    return round(total, 2)

# =============================================
# ================= INTERFAZ NUEVA =================
# =============================================
st.title("🧮 **Mega Calculadora SRT – Decreto 549/25**")
st.markdown("---")

if 'pericia' not in st.session_state:
    st.session_state.pericia = []

with st.sidebar:
    st.header("**Carga de hallazgos**")
    
    # 1. Capítulo
    capitulo = st.selectbox("**1. Capítulo**", ["Osteoarticular", "Sistema Nervioso"], index=None, placeholder="Seleccionar")
    
    if capitulo:
        # 2. Apartado
        apartados = ["Columna Vertebral", "Miembro Superior", "Miembro Inferior"]
        apartado = st.selectbox("**2. Apartado**", apartados, index=None, placeholder="Seleccionar")
        
        if apartado:
            # 3. Lateralidad (solo para extremidades)
            lateralidad = None
            if apartado in ["Miembro Superior", "Miembro Inferior"]:
                lateralidad = st.radio("**3. Lateralidad**", ["Derecho", "Izquierdo"], horizontal=True)
            
            # 4. Categoría
            if apartado == "Columna Vertebral":
                cats = ["Ver todas", "Fracturas Vertebrales", "Lesiones Discales y Ligamentarias", 
                        "Limitación Funcional", "Anquilosis"]
            else:  # Miembro Superior o Inferior
                cats = ["Ver todas", "Amputaciones", "Fracturas / Luxofracturas", 
                        "Prótesis / Artroplastias", "Lesiones Capsulo-Ligamentarias", 
                        "Lesiones Músculo-Tendinosas", "Limitación Funcional", "Anquilosis"]
            
            cat_sel = st.selectbox("**4. Categoría**", cats, index=0)
            
            # === FILTRADO ===
            if apartado == "Columna Vertebral":
                df_filtrado = df_main[df_main['Apartado'].str.contains("Columna Vertebral", case=False)].copy()
            elif apartado == "Miembro Superior":
                df_filtrado = df_main[df_main['Apartado'].str.contains("Miembro Superior", case=False)].copy()
            elif apartado == "Miembro Inferior":
                df_filtrado = df_mid.copy() if lateralidad == "Derecho" else df_mii.copy()
            
            # Filtro por capítulo
            if capitulo == "Osteoarticular":
                df_filtrado = df_filtrado[df_filtrado['Capítulo'].str.contains("Osteoarticular", case=False)]
            else:
                df_filtrado = df_filtrado[df_filtrado['Capítulo'].str.contains("Sistema Nervioso", case=False)]
            
            # Filtro por categoría
            if cat_sel != "Ver todas":
                map_keywords = {
                    "Fracturas Vertebrales": "Fracturas Vertebrales",
                    "Lesiones Discales y Ligamentarias": "Lesiones Discales Y Ligamentarias",
                    "Limitación Funcional": "Limitación Funcional",
                    "Anquilosis": "Anquilosis",
                    "Amputaciones": "Amputación",
                    "Fracturas / Luxofracturas": "Fractura|Luxofractura",
                    "Prótesis / Artroplastias": "Prótesis",
                    "Lesiones Capsulo-Ligamentarias": "Menisco|Capsulo|Ligamento",
                    "Lesiones Músculo-Tendinosas": "Ruptura|Sección",
                }
                kw = map_keywords.get(cat_sel, cat_sel)
                df_filtrado = df_filtrado[df_filtrado['Descripción de Lesión'].str.contains(kw, case=False)]
            
            opciones = sorted(df_filtrado['Descripción de Lesión'].unique())
            
            if opciones:
                item_sel = st.selectbox(f"**5. Descripción de Lesión ({len(opciones)})**", opciones, 
                                        format_func=format_text, index=None, placeholder="Seleccionar")
                
                if item_sel:
                    v_max = df_filtrado[df_filtrado['Descripción de Lesión'] == item_sel]['% de Incapacidad Laboral'].iloc[0]
                    valor_calculado = v_max
                    
                    # Evaluación M/S para nervios (igual que antes)
                    es_nervio = any(x in item_sel.lower() for x in ["nervio", "neurológico"]) and "dermatoma" not in item_sel.lower()
                    if es_nervio:
                        # (mantengo la misma lógica de déficit motor/sensitivo)
                        ...
                    
                    st.info(f"**Valor a agregar: {round(valor_calculado, 2)}%**")
                    if st.button("**AGREGAR**"):
                        st.session_state.pericia.append({"cap": capitulo, "ap": apartado, "lat": lateralidad or "", "desc": item_sel, "val": round(valor_calculado, 2)})
                        st.rerun()