import streamlit as st
import pandas as pd
import os

# --- Configuración inicial ---
st.set_page_config(page_title="Calculadora integral SRT", layout="wide", page_icon="🧮")

def format_text(text):
    if not text: return ""
    text = str(text).strip()
    return text[0].upper() + text[1:]

# --- DICCIONARIO MAESTRO DE PESOS (Nervios) ---
pesos_nervios_completos = { ... }  # (se mantiene igual)

escalas_ms = { ... }  # (se mantiene igual)

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
        # Filtro por región
        if region == "Columna": 
            kw = ("Columna|Cervical|Dorsal|Lumbar|Sacro|Radicular|Medular|C1|C2|C3|C4|C5|C6|C7|C8|"
                  "L1|L2|L3|L4|L5|S1|S2|S3|S4|S5")
        elif region in ["MSI", "MSD"]: 
            kw = "Superior|Mano|Hombro|Codo|Muñeca|Brazo|Antebrazo|Plexo Braquial"
        else: 
            kw = "Inferior|Cadera|Rodilla|Tobillo|Pie|Pierna|Muslo|Menisco|Capsulo|Ligamento"
        
        mask = (df_maestro['Apartado'].str.contains(kw, case=False)) | (df_maestro['Descripción de Lesión'].str.contains(kw, case=False))
        df_region = df_maestro[mask]
        
        grupo = st.radio("**2. Tipo de hallazgo**", ["Osteoarticular / Goniometría", "Neurológico / Radicular"])
        cap_busqueda = "Osteoarticular" if "osteo" in grupo.lower() else "Sistema Nervioso"
        df_grupo = df_region[df_region['Capítulo'].str.contains(cap_busqueda, case=False)]

        # === CATEGORÍAS DINÁMICAS Y PRECISAS ===
        if region == "Columna":
            if cap_busqueda == "Osteoarticular":
                cats = ["Ver todas", "Fracturas Vertebrales", "Lesiones Discales y Ligamentarias", 
                        "Limitación Funcional", "Anquilosis"]
            else:
                cats = ["Ver todas", "Raíces y dermatomas", "Plexos", "Lesión medular"]
        else:  # Miembros
            if cap_busqueda == "Osteoarticular":
                cats = ["Ver todas", "Meniscos / Ligamentos", "Fracturas / Luxofracturas", 
                        "Anquilosis / Limitaciones", "Amputaciones", "Prótesis"]
            else:
                cats = ["Ver todas", "Nervios periféricos", "Raíces y dermatomas", "Plexos", "Lesión medular"]

        cat_sel = st.selectbox("**3. Categoría**", cats, index=0)
        df_cat = df_grupo.copy()

        if cat_sel != "Ver todas":
            # FILTRO MÁS PRECISO POR CATEGORÍA (para listas cortas)
            map_cat = {
                "Fracturas Vertebrales": "Fracturas Vertebrales",
                "Lesiones Discales y Ligamentarias": "Lesiones Discales Y Ligamentarias",
                "Limitación Funcional": "Limitación Funcional de Columna",
                "Anquilosis": "Anquilosis de Columna",
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
            kw_cat = map_cat.get(cat_sel, cat_sel)
            df_cat = df_cat[(df_cat['Descripción de Lesión'].str.contains(kw_cat, case=False)) | 
                            (df_cat['Apartado'].str.contains(kw_cat, case=False))]

        # Sectores
        sectores = ["Ver todos"] + (["Cervical", "Dorsal", "Lumbar", "Sacro"] if region == "Columna" else 
                                   ["Hombro", "Codo", "Muñeca", "Mano"] if "MS" in region else 
                                   ["Cadera", "Rodilla", "Tobillo", "Pie"])
        sector_sel = st.selectbox("**4. Sector anatómico**", sectores, index=0)
        df_sector = df_cat.copy()
        if sector_sel != "Ver todos":
            expansion = {"Cervical": "Cervical|C1|C2|C3|C4|C5|C6|C7|C8", 
                         "Rodilla": "Rodilla|Menisco|Capsulo|Ligamento", 
                         "Hombro": "Hombro|Manguito|C5|C6", "Mano": "Mano|Pulgar|Dedo"}
            kw_sec = expansion.get(sector_sel, sector_sel)
            df_sector = df_sector[df_sector['Descripción de Lesión'].str.contains(kw_sec, case=False)]

        opciones = sorted(df_sector['Descripción de Lesión'].unique())
        if opciones:
            item_sel = st.selectbox(f"**5. Secuela específica ({len(opciones)} opciones)**", opciones, 
                                    format_func=format_text, index=None, placeholder="Seleccionar")
            if item_sel:
                v_max = df_sector[df_sector['Descripción de Lesión'] == item_sel]['% de Incapacidad Laboral'].iloc[0]
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

    # (el resto del código de resultados se mantiene exactamente igual al anterior)
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