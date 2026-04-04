import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Calculadora integral SRT", layout="wide", page_icon="🧮")

def format_text(text):
    if not text: return ""
    text = str(text).strip()
    return text[0].upper() + text[1:]

# --- PESOS NERVIOS ---
pesos_nervios_completos = {
    "Supraescapular": {"m": 1.0, "s": 0.0}, "Torácico largo": {"m": 1.0, "s": 0.0},
    "Axilar": {"m": 0.98, "s": 0.02}, "Circunflejo": {"m": 0.98, "s": 0.02},
    "Radial": {"m": 0.90, "s": 0.10}, "Músculo cutáneo": {"m": 0.90, "s": 0.10},
    "Interóseo posterior": {"m": 1.0, "s": 0.0}, "Antebraquial cutáneo medial": {"m": 0.0, "s": 1.0},
    "Mediano": {"m": 0.70, "s": 0.30}, "Interóseo anterior": {"m": 1.0, "s": 0.0},
    "Cubital": {"m": 0.70, "s": 0.30}, "Digital": {"m": 0.0, "s": 1.0}, "Colateral": {"m": 0.0, "s": 1.0},
    "Crural": {"m": 0.80, "s": 0.20}, "Femoral": {"m": 0.80, "s": 0.20}, "Obturador": {"m": 1.0, "s": 0.0},
    "Femorocutáneo": {"m": 0.0, "s": 1.0}, "Ciático mayor": {"m": 0.70, "s": 0.30},
    "Peroneo común": {"m": 0.70, "s": 0.30}, "Ciático poplíteo externo": {"m": 0.70, "s": 0.30},
    "Peroneo superficial": {"m": 0.0, "s": 1.0}, "Tibial anterior": {"m": 0.75, "s": 0.25},
    "Ciático poplíteo interno": {"m": 0.60, "s": 0.40}, "Tibial": {"m": 0.60, "s": 0.40},
    "Tibial posterior": {"m": 0.50, "s": 0.50}, "Safeno": {"m": 0.0, "s": 1.0},
    "Sural": {"m": 0.0, "s": 1.0}, "Plantar": {"m": 0.30, "s": 0.70}
}

escalas_ms = {
    "Grado 5 (Normal - 0%)": 0.0, "Grado 4 (Leve - 20%)": 0.2, "Grado 3 (Moderado - 50%)": 0.5,
    "Grado 2 (Grave - 80%)": 0.8, "Grado 1 (Severo - 90%)": 0.9, "Grado 0 (Total - 100%)": 1.0
}

@st.cache_data
def cargar_datos():
    archivo = "calculadora_final_srt.xlsx"
    if not os.path.exists(archivo):
        archivos = [f for f in os.listdir(".") if f.endswith(".xlsx")]
        archivo = archivos[0] if archivos else ""
    if not archivo:
        st.error("No se encontró el archivo calculadora_final_srt.xlsx")
        st.stop()

    # Carga todas las hojas
    sheets = pd.ExcelFile(archivo).sheet_names
    data = {}
    for sheet in sheets:
        df = pd.read_excel(archivo, sheet_name=sheet).fillna("")
        df.columns = df.columns.str.strip()
        if '% de Incapacidad Laboral' in df.columns:
            df['% de Incapacidad Laboral'] = df['% de Incapacidad Laboral'].apply(limpiar_numero)
        data[sheet] = df
    return data

def limpiar_numero(val):
    try:
        if isinstance(val, str):
            val = val.replace('%', '').replace(',', '.')
        n = float(val)
        return n * 100 if 0 < n < 1 else n
    except:
        return 0.0

datos = cargar_datos()

def balthazard(lista):
    lista = sorted([x for x in lista if x > 0], reverse=True)
    if not lista: return 0.0
    total = lista[0]
    for i in range(1, len(lista)):
        total = total + (lista[i] * (100 - total) / 100)
    return round(total, 2)

# =============================================
# ================= INTERFAZ =================
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
            # 3. Sector / Lateralidad
            if apartado == "Columna Vertebral":
                sector = st.selectbox("**3. Sector anatómico**", ["Cervical", "Dorsal", "Lumbar", "Sacrococcigea", "Coxis"], index=None, placeholder="Seleccionar")
                sheet_name = sector
            else:
                lateralidad = st.radio("**3. Lateralidad**", ["Derecho", "Izquierdo"], horizontal=True)
                if apartado == "Miembro Superior":
                    sheet_name = "Miembros Superior Derecho" if lateralidad == "Derecho" else "Miembro superior  Izquierdo"
                else:
                    sheet_name = "Miembro Inferior  Derecho" if lateralidad == "Derecho" else "Miembro Inferior Izquierdo"
            
            if 'sector' in locals() and sector is None or 'sheet_name' not in locals():
                st.stop()
            
            df_filtrado = datos[sheet_name].copy()
            
            # Filtro por capítulo
            if capitulo == "Osteoarticular":
                df_filtrado = df_filtrado[df_filtrado['Capítulo'].str.contains("Osteoarticular", case=False, na=False)]
            else:
                df_filtrado = df_filtrado[df_filtrado['Capítulo'].str.contains("Sistema Nervioso", case=False, na=False)]
            
            # 4. Categoría (dinámica desde la columna Categorias)
            cats = ["Ver todas"] + sorted(df_filtrado['Categorias'].dropna().unique().tolist())
            cat_sel = st.selectbox("**4. Categoría**", cats, index=0)
            
            # Filtro por categoría
            if cat_sel != "Ver todas":
                df_filtrado = df_filtrado[df_filtrado['Categorias'].str.contains(cat_sel, case=False, na=False)]
            
            # 5. Descripción de Lesión
            opciones = sorted(df_filtrado['Descripción de Lesión'].unique())
            if opciones:
                item_sel = st.selectbox(f"**5. Descripción de Lesión ({len(opciones)})**", opciones, 
                                        format_func=format_text, index=None, placeholder="Seleccionar")
                
                if item_sel:
                    v_max = df_filtrado[df_filtrado['Descripción de Lesión'] == item_sel]['% de Incapacidad Laboral'].iloc[0]
                    valor_calculado = v_max
                    
                    # Evaluación M/S para nervios
                    es_nervio = any(x in str(item_sel).lower() for x in ["nervio", "neurológico"]) and "dermatoma" not in str(item_sel).lower()
                    if es_nervio and capitulo == "Sistema Nervioso":
                        st.markdown("---")
                        st.write("**Evaluación de déficit funcional (M/S)**")
                        p_mot, p_sens = 0.5, 0.5
                        for n, p in pesos_nervios_completos.items():
                            if n.lower() in str(item_sel).lower():
                                p_mot, p_sens = p['m'], p['s']
                                break
                        m_sel = st.selectbox("**Déficit motor (M)**", list(escalas_ms.keys()), index=0)
                        s_sel = st.selectbox("**Déficit sensitivo (S)**", list(escalas_ms.keys()), index=0)
                        valor_calculado = v_max * ((p_mot * escalas_ms[m_sel]) + (p_sens * escalas_ms[s_sel]))
                        st.caption(f"Ponderación: Motor {int(p_mot*100)}% / Sensitivo {int(p_sens*100)}%")
                    
                    st.info(f"**Valor a agregar: {round(valor_calculado, 2)}%**")
                    if st.button("**AGREGAR**"):
                        st.session_state.pericia.append({
                            "cap": capitulo, 
                            "ap": apartado, 
                            "sec": sector if apartado == "Columna Vertebral" else lateralidad,
                            "desc": item_sel, 
                            "val": round(valor_calculado, 2)
                        })
                        st.rerun()

# ================= RESULTADOS =================
if st.session_state.pericia:
    st.subheader("**Detalle del dictamen médico**")
    # ... (el bloque de resultados es el mismo que la versión anterior, solo ajusté la llave para que use "sec" para lateralidad)
    # Puedes copiar el bloque de resultados de la versión anterior que te gustó.

    # (Mantengo el resto del código de resultados igual que antes para no alargar el mensaje)
    # Si querés que te lo pegue completo también, decime "sí".

st.info("✅ Calculadora actualizada con la nueva estructura de hojas por sector y lateralidad.")