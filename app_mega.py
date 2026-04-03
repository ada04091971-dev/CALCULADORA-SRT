import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Calculadora integral SRT", layout="wide", page_icon="🧮")

def format_text(text):
    if not text: return ""
    text = str(text).strip()
    return text[0].upper() + text[1:]

# --- DICCIONARIO MAESTRO DE PESOS (Nervios) ---
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
            sectores = ["Cadera", "Rodilla", "Tobillo", "Pie", "Pierna", "Muslo", "Pelvis"]
        
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
        
        # === FILTRADO CORREGIDO ===
        df_filtrado = df_maestro.copy()
        
        # Filtro por sector (SOLO se aplica en categorías específicas)
        if sector_sel != "Ver todos":
            if region == "Columna":
                # Para categorías generales (discales, limitación, anquilosis) NO filtramos por sector
                if cat_sel not in ["Lesiones Discales y Ligamentarias", "Limitación Funcional", "Anquilosis"]:
                    sector_map = {
                        "Cervical": r"Cervical|C1|C2|C3|C4|C5|C6|C7|C8|odontoides|apofisis|apófisis|atlas|axis",
                        "Dorsal": r"Dorsal|D1|D2|D3|D4|D5|D6|D7|D8|D9|D10|D11|D12",
                        "Lumbar": r"Lumbar|L1|L2|L3|L4|L5",
                        "Sacro": r"Sacro",
                        "Coccígeo": r"Coxis|Coccígeo|coccigeo"
                    }
                    kw_sector = sector_map.get(sector_sel, sector_sel)
                    df_filtrado = df_filtrado[df_filtrado['Descripción de Lesión'].str.contains(kw_sector, case=False, regex=True)]
            else:  # Extremidades
                sector_map = {
                    "Cadera": r"Cadera|Pelvis|hemipelvis|sínfisis|sacroilíaca|ilíaco|pubis",
                    "Rodilla": r"Rodilla|menisco|rótula|ligamento cruzado",
                    "Tobillo": r"Tobillo|aquiles",
                    "Pie": r"Pie|dedo|metatarso|falange",
                    "Pierna": r"Pierna|tibial|peroneo",
                    "Muslo": r"Muslo|cuádriceps|femur",
                    "Pelvis": r"Pelvis|hemipelvis|sínfisis|sacroilíaca|ilíaco|pubis"
                }
                kw_sector = sector_map.get(sector_sel, sector_sel)
                df_filtrado = df_filtrado[df_filtrado['Descripción de Lesión'].str.contains(kw_sector, case=False, regex=True)]
        
        # Filtro por tipo
        if tipo_hallazgo == "Osteoarticular y Ligamentario":
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
if st.session_state.pericia:
    st.subheader("**Detalle del dictamen médico**")
    st.info("""
    **Regla aplicada según Decreto 549/25**  
    • Dentro de cada **región topográfica / misma lateralidad** → **suma aritmética** + **tope regional**.  
    • Entre regiones diferentes → **Capacidad Restante** (Balthazard).
    """)

    sumas_seg = {}
    for i, p in enumerate(st.session_state.pericia):
        c1, c2, c3 = st.columns([2, 6, 1])
        c1.write(f"**{p['reg']}**")
        c2.write(f"{format_text(p['desc'])} ({p['val']}%)")
        if c3.button("🗑️", key=f"del_{i}"):
            st.session_state.pericia.pop(i)
            st.rerun()

        desc_upper = p['desc'].upper()
        if p['reg'] == "Columna":
            llave = "Columna cervical" if any(x in desc_upper for x in ["CERVICAL", "C1","C2","C3","C4","C5","C6","C7","C8"]) else "Columna dorsolumbar"
        else:
            llave = p['reg']
        sumas_seg[llave] = sumas_seg.get(llave, 0) + p['val']

    topes = {"MSI": 66.0, "MSD": 66.0, "MII": 70.0, "MID": 70.0, 
             "Columna cervical": 40.0, "Columna dorsolumbar": 60.0}

    st.markdown("---")
    st.write("**Análisis de topes por región topográfica**")

    v_bal = []
    for s, suma in sumas_seg.items():
        t = topes.get(s, 100.0)
        v_final = min(suma, t)
        v_bal.append(v_final)
        
        col1, col2, col3 = st.columns([3, 2, 3])
        col1.write(f"**{s}**")
        col2.metric("Suma bruta", f"{suma:.2f}%")
        if suma > t:
            col3.error(f"**Tope aplicado → {v_final:.2f}%** (máx. {t}%)")
        else:
            col3.success(f"Valor final: **{v_final:.2f}%**")

    fis = balthazard(v_bal)

    st.markdown("### **Factores de ponderación**")
    u_edad = st.number_input("**Edad del trabajador**", 14, 99, 17)
    f_e = 0.05 if u_edad <= 20 else 0.04 if u_edad <= 30 else 0.03 if u_edad <= 40 else 0.02
    u_dif = st.selectbox("**Dificultad para tareas habituales**", ["Leve (5%)", "Intermedia (10%)", "Alta (20%)"], index=1)
    f_d = {"Leve (5%)": 0.05, "Intermedia (10%)": 0.10, "Alta (20%)": 0.20}[u_dif]
    
    inc = fis * (f_e + f_d)
    res_f = min(fis + inc, 65.99) if fis < 66.0 else min(fis + inc, 100.0)

    col_l, col_r = st.columns(2)
    with col_l:
        st.metric("**Daño físico residual (Cap. Restante)**", f"{fis}%")
        st.metric("**Incremento por factores**", f"{round(inc, 2)}%")
    with col_r:
        if res_f >= 66.0:
            st.error(f"## **ILP FINAL: {round(res_f, 2)}% (TOTAL)**")
        else:
            st.success(f"## **ILP FINAL: {round(res_f, 2)}% (PARCIAL)**")

    if st.button("🚨 **BORRAR TODO EL DICTAMEN**"):
        st.session_state.pericia = []
        st.rerun()