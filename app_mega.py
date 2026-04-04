import streamlit as st
import pandas as pd
import os

# --- Configuración inicial ---
st.set_page_config(page_title="Calculadora Laboral SRT", layout="wide", page_icon="🧮")

def format_text(text):
    if not text: return ""
    text = str(text).strip()
    return text[0].upper() + text[1:]

@st.cache_resource
def abrir_excel():
    archivo = "calculadora_final_srt.xlsx"
    if not os.path.exists(archivo):
        st.error("No se encontró el archivo Excel.")
        st.stop()
    return pd.ExcelFile(archivo)

def balthazard(lista):
    lista = sorted([x for x in lista if x > 0], reverse=True)
    if not lista: return 0.0
    total = lista[0]
    for i in range(1, len(lista)):
        total = total + (lista[i] * (100 - total) / 100)
    return round(total, 2)

# --- Interfaz principal ---
st.title("🧮 **Calculadora Laboral SRT: Decreto 549/25**")
st.markdown("---")

if 'pericia' not in st.session_state:
    st.session_state.pericia = []

xls = abrir_excel()

with st.sidebar:
    st.header("**Carga de Hallazgos**")
    
    region = st.selectbox("**1. Región**", ["Columna", "Miembro Superior", "Miembro Inferior"], index=None)
    
    if region:
        # 2. Selección de Hoja
        if region == "Columna":
            sector_anat = st.selectbox("**2. Nivel vertebral**", ["Cervical", "Dorsal", "Lumbar", "Sacrococcigea", "Coxis"], index=None)
            hoja = sector_anat
        else:
            lat = st.selectbox("**2. Lateralidad**", ["Derecho", "Izquierdo"], index=None)
            sectores_m = ["Hombro", "Brazo", "Codo", "Antebrazo", "Muñeca", "Mano", "Dedos"] if "Superior" in region else ["Cadera", "Muslo", "Rodilla", "Pierna", "Tobillo", "Pie", "Dedos"]
            sector_anat = st.selectbox("**3. Sector anatómico**", sectores_m, index=None)
            hoja = f"{region} {lat}"

        if sector_anat and (region == "Columna" or (region != "Columna" and lat)):
            try:
                df = pd.read_excel(xls, sheet_name=hoja).fillna("")
                
                # REGLA DE POSICIÓN: Columna C (2) es Categoría, D (3) es Descripción, E (4) es %
                df_f = df.copy()
                
                # Filtro por sector (solo para Miembros)
                if region != "Columna":
                    # Filtro más permisivo para no perder secuelas que no digan "Tobillo" en el nombre pero sí en la categoría
                    df_f = df_f[df_f.iloc[:, 2].astype(str).str.contains(sector_anat, case=False, na=False) | 
                                df_f.iloc[:, 3].astype(str).str.contains(sector_anat, case=False, na=False)]

                # 4. Categoría (Columna C)
                lista_cats = sorted([str(x) for x in df_f.iloc[:, 2].unique() if str(x).strip() != ""])
                categorias = ["Ver todas"] + lista_cats
                cat_sel = st.selectbox("**4. Categoría**", categorias)
                
                if cat_sel != "Ver todas":
                    df_f = df_f[df_f.iloc[:, 2].astype(str) == cat_sel]
                
                # 5. Movimiento (Goniometría) - LISTA AMPLIADA
                if any(x in str(cat_sel).lower() for x in ["anquilosis", "limitación"]):
                    # Agregamos Dorsiflexión y Dorsal para cubrir Tobillo y Muñeca
                    movs = ["Flexión", "Extensión", "Dorsiflexión", "Dorsal", "Inclinación", "Rotación", "Abducción", "Aducción", "Pronación", "Supinación"]
                    opc_mov = [m for m in movs if df_f.iloc[:, 3].astype(str).str.contains(m, case=False).any()]
                    if opc_mov:
                        tipo_mov = st.selectbox("**5. Movimiento**", opc_mov, index=None)
                        if tipo_mov:
                            df_f = df_f[df_f.iloc[:, 3].astype(str).str.contains(tipo_mov, case=False)]

                # 6. Secuela Específica (Columna D)
                opciones = sorted(df_f.iloc[:, 3].unique().tolist())
                if opciones:
                    item = st.selectbox(f"**6. Secuela ({len(opciones)})**", opciones, format_func=format_text, index=None)
                    
                    if item:
                        fila = df_f[df_f.iloc[:, 3] == item]
                        valor = fila.iloc[0, 4]
                        
                        try:
                            val_num = float(str(valor).replace('%', '').replace(',', '.'))
                            if 0 < val_num < 1: val_num *= 100
                        except: val_num = 0.0

                        st.success(f"**Valor Baremo: {round(val_num, 2)}%**")
                        
                        if st.button("**AGREGAR A LA PERICIA**"):
                            st.session_state.pericia.append({
                                "reg": sector_anat if region == "Columna" else f"{sector_anat} {lat}",
                                "desc": item, 
                                "val": round(val_num, 2)
                            })
                            st.rerun()
            except Exception as e:
                st.error(f"Error en hoja {hoja}: {e}")

# --- PANEL DE RESULTADOS ---
if st.session_state.pericia:
    st.subheader("**Detalle del Dictamen (Decreto 549/25)**")
    sumas_regionales = {}
    for i, p in enumerate(st.session_state.pericia):
        c1, c2, c3 = st.columns([3, 5, 1])
        c1.write(f"**{p['reg']}**")
        c2.write(f"{format_text(p['desc'])} ({p['val']}%)")
        if c3.button("🗑️", key=f"del_{i}"):
            st.session_state.pericia.pop(i); st.rerun()
        
        r_u = p['reg'].upper()
        if any(x in r_u for x in ["CERVICAL", "DORSAL", "LUMBAR", "SACRO", "COXIS"]):
            llave = "Columna"
        elif "SUPERIOR" in r_u or any(x in r_u for x in ["HOMBRO", "CODO", "MANO"]):
            llave = "Miembro Superior"
        else:
            llave = "Miembro Inferior"
        sumas_regionales[llave] = sumas_regionales.get(llave, 0) + p['val']

    topes = {"Miembro Superior": 66.0, "Miembro Inferior": 70.0}
    
    st.markdown("---")
    col_izq, col_der = st.columns(2)
    with col_izq:
        st.write("**Análisis de Topes Legales:**")
        v_finales = []
        for reg_nombre, suma in sumas_regionales.items():
            t = topes.get(reg_nombre, 100.0)
            valor_final = min(suma, t)
            v_finales.append(valor_final)
            if suma > t:
                st.warning(f"⚠️ {reg_nombre}: {suma}% (Tope: {t}%)")
            else:
                st.write(f"✅ {reg_nombre}: {suma}%")

        edad = st.number_input("**Edad**", 14, 99, 25)
        f_e = 0.05 if edad <= 20 else 0.04 if edad <= 30 else 0.03 if edad <= 40 else 0.02
        f_d = st.selectbox("**Dificultad**", [0.05, 0.10, 0.20], format_func=lambda x: f"{int(x*100)}%")
        
        fis = balthazard(v_finales)
        inc = fis * (f_e + f_d)
        res_f = fis + inc

    with col_der:
        st.metric("**Daño Físico (Balthazard)**", f"{fis}%")
        st.metric("**Factores Ponderados**", f"{round(inc, 2)}%")
        st.metric("**Incapacidad Final**", f"{round(res_f, 2)}%")
        if st.button("🚨 **REINICIAR**"):
            st.session_state.pericia = []; st.rerun()