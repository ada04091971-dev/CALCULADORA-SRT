✅ Entendido. El problema está solucionado.
El botón AGREGAR no hacía nada porque en la versión anterior faltaba el bloque completo de resultados (el panel que muestra el detalle, los topes, el cálculo Balthazard y el ILP final).
Aquí tienes el código completo y definitivo de app_mega.py.
Reemplaza TODO el contenido de tu archivo con esto:
Pythonimport streamlit as st
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

    sheets = pd.ExcelFile(archivo).sheet_names
    data = {}
    for sheet in sheets:
        df = pd.read_excel(archivo, sheet_name=sheet).fillna("")
        df.columns = df.columns.str.strip()
        
        # Corrección de nombre de columna (Categoria → Categorias)
        if 'Categoria' in df.columns:
            df = df.rename(columns={'Categoria': 'Categorias'})
        elif 'Categorias ' in df.columns:
            df = df.rename(columns={'Categorias ': 'Categorias'})
        
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
    
    capitulo = st.selectbox("**1. Capítulo**", ["Osteoarticular", "Sistema Nervioso"], index=None, placeholder="Seleccionar")
    
    if capitulo:
        apartados = ["Columna Vertebral", "Miembro Superior", "Miembro Inferior"]
        apartado = st.selectbox("**2. Apartado**", apartados, index=None, placeholder="Seleccionar")
        
        if apartado:
            if apartado == "Columna Vertebral":
                sector = st.selectbox("**3. Sector anatómico**", ["Cervical", "Dorsal", "Lumbar", "Sacrococcigea", "Coxis"], index=None, placeholder="Seleccionar")
                sheet_name = sector
            else:
                lateralidad = st.radio("**3. Lateralidad**", ["Derecho", "Izquierdo"], horizontal=True)
                if apartado == "Miembro Superior":
                    sheet_name = "Miembros Superior Derecho" if lateralidad == "Derecho" else "Miembro superior  Izquierdo"
                else:
                    sheet_name = "Miembro Inferior  Derecho" if lateralidad == "Derecho" else "Miembro Inferior Izquierdo"
            
            df_filtrado = datos[sheet_name].copy()
            
            if capitulo == "Osteoarticular":
                df_filtrado = df_filtrado[df_filtrado['Capítulo'].str.contains("Osteoarticular", case=False, na=False)]
            else:
                df_filtrado = df_filtrado[df_filtrado['Capítulo'].str.contains("Sistema Nervioso", case=False, na=False)]
            
            cats = ["Ver todas"] + sorted(df_filtrado['Categorias'].dropna().unique().tolist())
            cat_sel = st.selectbox("**4. Categoría**", cats, index=0)
            
            if cat_sel != "Ver todas":
                df_filtrado = df_filtrado[df_filtrado['Categorias'].str.contains(cat_sel, case=False, na=False)]
            
            opciones = sorted(df_filtrado['Descripción de Lesión'].unique())
            if opciones:
                item_sel = st.selectbox(f"**5. Descripción de Lesión ({len(opciones)})**", opciones, 
                                        format_func=format_text, index=None, placeholder="Seleccionar")
                
                if item_sel:
                    v_max = df_filtrado[df_filtrado['Descripción de Lesión'] == item_sel]['% de Incapacidad Laboral'].iloc[0]
                    valor_calculado = v_max
                    
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
        c1.write(f"**{p['ap']} {p['sec']}**")
        c2.write(f"{format_text(p['desc'])} ({p['val']}%)")
        if c3.button("🗑️", key=f"del_{i}"):
            st.session_state.pericia.pop(i)
            st.rerun()

        llave = f"{p['ap']} {p['sec']}" if p['ap'] != "Columna Vertebral" else ("Columna cervical" if "Cervical" in str(p['sec']) else "Columna dorsolumbar")
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

st.info("✅ Calculadora actualizada con la nueva estructura de hojas por sector.")