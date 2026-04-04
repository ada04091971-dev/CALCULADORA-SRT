import streamlit as st
import pandas as pd
import os

# --- Configuración inicial ---
st.set_page_config(page_title="Calculadora Integral SRT", layout="wide", page_icon="🧮")

def format_text(text):
    if not text: return ""
    text = str(text).strip()
    return text[0].upper() + text[1:]

@st.cache_data
def cargar_hoja(nombre_hoja):
    archivo = "calculadora_final_srt.xlsx"
    try:
        df = pd.read_excel(archivo, sheet_name=nombre_hoja).fillna("")
        df.columns = df.columns.str.strip()
        return df
    except:
        return pd.DataFrame()

def balthazard(lista):
    lista = sorted([x for x in lista if x > 0], reverse=True)
    if not lista: return 0.0
    total = lista[0]
    for i in range(1, len(lista)):
        total = total + (lista[i] * (100 - total) / 100)
    return round(total, 2)

# --- Interfaz principal ---
st.title("🧮 **Mega Calculadora SRT: Edición Profesional Final**")
st.markdown("---")

if 'pericia' not in st.session_state:
    st.session_state.pericia = []

with st.sidebar:
    st.header("**Carga de hallazgos**")
    
    # 1. REGIÓN MADRE
    region_madre = st.selectbox("**1. Región**", ["Columna", "Miembro Superior", "Miembro Inferior"], index=None)
    
    if region_madre:
        # 2. LATERALIDAD (Solo para miembros)
        lat = ""
        if region_madre != "Columna":
            lat = st.selectbox("**2. Lateralidad**", ["Derecho", "Izquierdo"], index=None)
        
        # 3. SECTOR ANATÓMICO (Orden Descendente)
        sectores_map = {
            "Columna": ["Cervical", "Dorsal", "Lumbar", "Sacrococcigea", "Coxis"],
            "Miembro Superior": ["Hombro", "Brazo", "Codo", "Antebrazo", "Muñeca", "Mano", "Dedos"],
            "Miembro Inferior": ["Cadera", "Muslo", "Rodilla", "Pierna", "Tobillo", "Pie", "Dedos"]
        }
        
        sector = st.selectbox("**3. Sector anatómico**", sectores_map[region_madre], index=None)
        
        if sector and (region_madre == "Columna" or lat):
            # 4. TIPO DE HALLAZGO
            hallazgo = st.radio("**4. Tipo de hallazgo**", ["Osteoarticular / Goniometría", "Neurológico / Radicular"])
            
            # Carga de la hoja correcta
            hoja_a_cargar = sector if region_madre == "Columna" else f"{region_madre} {lat}"
            df_final = cargar_hoja("Neurologia" if "Neurológico" in hallazgo else hoja_a_cargar)

            if not df_final.empty:
                # Filtrar Neurología por la región/sector
                if "Neurológico" in hallazgo:
                    kw_neuro = sector if region_madre == "Columna" else ("Superior" if "Superior" in region_madre else "Inferior")
                    df_final = df_final[df_final['Apartado'].str.contains(kw_neuro, case=False, na=False)]
                else:
                    # Filtro anatómico en la hoja de miembros (para reducir las 30 categorías)
                    mask = df_final['Categoría'].str.contains(sector, case=False, na=False) | \
                           df_final['Descripción de lesión'].str.contains(sector, case=False, na=False)
                    df_final = df_final[mask]

                # 5. CATEGORÍA
                categorias = ["Ver todas"] + sorted(df_final['Categoría'].unique().tolist())
                cat_sel = st.selectbox("**5. Categoría**", categorias)
                
                df_items = df_final.copy()
                if cat_sel != "Ver todas":
                    df_items = df_items[df_items['Categoría'] == cat_sel]
                
                # 6. FILTRO DE MOVIMIENTO (Para goniometría)
                if any(x in str(cat_sel) for x in ["Anquilosis", "Limitación", "Goniometría"]):
                    movs_ref = ["Flexión", "Extensión", "Inclinación", "Rotación", "Abducción", "Aducción", "Pronación", "Supinación"]
                    opc_mov = [m for m in movs_ref if df_items['Descripción de lesión'].str.contains(m, case=False).any()]
                    if opc_mov:
                        tipo_mov = st.selectbox("**6. Tipo de movimiento**", opc_mov, index=None)
                        if tipo_mov:
                            df_items = df_items[df_items['Descripción de lesión'].str.contains(tipo_mov, case=False)]

                # 7. SELECCIÓN FINAL
                opciones = sorted(df_items['Descripción de lesión'].unique())
                if opciones:
                    item_sel = st.selectbox(f"**7. Secuela específica ({len(opciones)})**", opciones, format_func=format_text, index=None)
                    
                    if item_sel:
                        fila = df_items[df_items['Descripción de lesión'] == item_sel]
                        valor = fila['% de incapacidad laboral'].iloc[0]
                        
                        st.success(f"**Valor Baremo: {valor}%**")
                        
                        if st.button("**AGREGAR A LA PERICIA**"):
                            st.session_state.pericia.append({
                                "reg": sector if region_madre == "Columna" else f"{sector} {lat}",
                                "desc": item_sel,
                                "val": valor
                            })
                            st.rerun()

# --- Resultados ---
if st.session_state.pericia:
    st.markdown("---")
    st.subheader("**Detalle del dictamen médico**")
    sumas_seg = {}
    for i, p in enumerate(st.session_state.pericia):
        c1, c2, c3 = st.columns([3, 5, 1])
        c1.write(f"**{p['reg']}**")
        c2.write(f"{format_text(p['desc'])} ({p['val']}%)")
        if c3.button("🗑️", key=f"del_{i}"): st.session_state.pericia.pop(i); st.rerun()
        
        # Agrupación de topes
        desc_u = p['desc'].upper()
        if any(x in p['reg'] or x in desc_u for x in ["CERVICAL", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"]):
            llave = "Columna cervical"
        elif any(x in p['reg'] for x in ["Dorsal", "Lumbar", "Sacro", "Coxis"]):
            llave = "Columna dorsolumbar"
        elif "Hombro" in p['reg'] or "Codo" in p['reg'] or "Mano" in p['reg'] or "Superior" in p['reg']:
            llave = "Miembro superior"
        else:
            llave = "Miembro inferior"
        sumas_seg[llave] = sumas_seg.get(llave, 0) + p['val']

    topes = {"Miembro superior": 66.0, "Miembro inferior": 70.0, "Columna cervical": 40.0, "Columna dorsolumbar": 60.0}
    
    st.markdown("---")
    l, r = st.columns(2)
    with l:
        st.write("**Análisis de topes regionales:**")
        v_bal = []
        for s, suma in sumas_seg.items():
            t = topes.get(s, 100.0)
            v_f = min(suma, t)
            v_bal.append(v_f)
            if suma > t: st.warning(f"⚠️ {s}: {suma}% excede el tope de {t}%.")
            else: st.write(f"✅ {s}: {suma}%")

        st.markdown("### **Factores de ponderación**")
        u_edad = st.number_input("**Edad del trabajador**", 14, 99, 25)
        f_e = 0.05 if u_edad <= 20 else 0.04 if u_edad <= 30 else 0.03 if u_edad <= 40 else 0.02
        f_d = st.selectbox("**Dificultad para tareas**", [0.05, 0.10, 0.20], format_func=lambda x: f"{int(x*100)}%")
        
        fis = balthazard(v_bal)
        inc = fis * (f_e + f_d)
        res_f = min(fis + inc, 65.99) if fis < 66.0 else fis + inc

    with r:
        st.metric("**Daño físico residual**", f"{fis}%")
        st.metric("**Factores aplicados**", f"{round(inc, 2)}%")
        if res_f >= 66.0: st.error(f"## **ILP FINAL: {round(res_f, 2)}% (TOTAL)**")
        else: st.success(f"## **ILP FINAL: {round(res_f, 2)}% (PARCIAL)**")
        if st.button("🚨 **BORRAR TODO**"): st.session_state.pericia = []; st.rerun()