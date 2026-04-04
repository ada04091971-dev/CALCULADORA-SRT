import streamlit as st
import pandas as pd
import os

# configuración de página
st.set_page_config(page_title="Calculadora laboral SRT", layout="wide", page_icon="🧮")

def format_text(text):
    if not text: return ""
    text = str(text).strip()
    return text[0].upper() + text[1:]

@st.cache_resource
def abrir_excel():
    archivo = "calculadora_final_srt.xlsx"
    if not os.path.exists(archivo):
        st.error("no se encontró el archivo excel.")
        st.stop()
    return pd.ExcelFile(archivo)

def balthazard(lista):
    lista = sorted([x for x in lista if x > 0], reverse=True)
    if not lista: return 0.0
    total = lista[0]
    for i in range(1, len(lista)):
        total = total + (lista[i] * (100 - total) / 100)
    return round(total, 2)

# --- interfaz principal ---
st.title("🧮 **calculadora laboral SRT: decreto 549/25**")
st.markdown("---")

if 'pericia' not in st.session_state:
    st.session_state.pericia = []

xls = abrir_excel()

with st.sidebar:
    st.header("**carga de hallazgos**")
    
    region = st.selectbox("**1. región**", ["Columna", "Miembro superior", "Miembro inferior"], index=None)
    
    if region:
        # 2. selección de hoja
        if region == "Columna":
            sector_anat = st.selectbox("**2. nivel vertebral**", ["Cervical", "Dorsal", "Lumbar", "Sacrococcigea", "Coxis"], index=None)
            hoja = sector_anat
        else:
            lat = st.selectbox("**2. lateralidad**", ["Derecho", "Izquierdo"], index=None)
            sectores_m = ["Hombro", "Brazo", "Codo", "Antebrazo", "Muñeca", "Mano", "Dedos"] if "superior" in region.lower() else ["Cadera", "Muslo", "Rodilla", "Pierna", "Tobillo", "Pie", "Dedos"]
            sector_anat = st.selectbox("**3. sector anatómico**", sectores_m, index=None)
            hoja = f"{region} {lat}"

        if sector_anat and (region == "Columna" or (region != "Columna" and lat)):
            try:
                df = pd.read_excel(xls, sheet_name=hoja).fillna("")
                df_f = df.copy()
                
                # REGLA DE POSICIÓN: C(2) Categoría, D(3) Descripción, E(4) %
                # filtro anatómico para miembros
                if region != "Columna":
                    df_f = df_f[df_f.iloc[:, 2].astype(str).str.contains(sector_anat, case=False, na=False) | 
                                df_f.iloc[:, 3].astype(str).str.contains(sector_anat, case=False, na=False)]

                # 4. categoría
                lista_cats = sorted([str(x) for x in df_f.iloc[:, 2].unique() if str(x).strip() != ""])
                categorias = ["ver todas"] + lista_cats
                cat_sel = st.selectbox("**4. categoría**", categorias)
                if cat_sel != "ver todas":
                    df_f = df_f[df_f.iloc[:, 2].astype(str) == cat_sel]
                
                # 5. movimiento (goniometría ampliada)
                if any(x in str(cat_sel).lower() for x in ["anquilosis", "limitación"]):
                    movs = ["Flexión", "Extensión", "Dorsiflexión", "Dorsal", "Inclinación", "Rotación", "Abducción", "Aducción", "Pronación", "Supinación"]
                    opc_mov = [m for m in movs if df_f.iloc[:, 3].astype(str).str.contains(m, case=False).any()]
                    if opc_mov:
                        tipo_mov = st.selectbox("**5. movimiento**", opc_mov, index=None)
                        if tipo_mov:
                            df_f = df_f[df_f.iloc[:, 3].astype(str).str.contains(tipo_mov, case=False)]

                # 6. secuela específica (columna d limpia)
                opciones = sorted(df_f.iloc[:, 3].unique().tolist())
                if opciones:
                    item = st.selectbox(f"**6. secuela ({len(opciones)})**", opciones, format_func=format_text, index=None)
                    
                    if item:
                        fila = df_f[df_f.iloc[:, 3] == item]
                        valor = fila.iloc[0, 4] # Columna E
                        
                        try:
                            val_num = float(str(valor).replace('%', '').replace(',', '.'))
                            if 0 < val_num < 1: val_num *= 100
                        except: val_num = 0.0

                        st.success(f"**valor baremo: {round(val_num, 2)}%**")
                        
                        if st.button("**agregar a la pericia**"):
                            st.session_state.pericia.append({
                                "reg": sector_anat if region == "Columna" else f"{sector_anat} {lat}",
                                "desc": item, 
                                "val": round(val_num, 2)
                            })
                            st.rerun()
            except Exception as e:
                st.error(f"error en hoja {hoja}: {e}")

# --- resultados ---
if st.session_state.pericia:
    st.subheader("**detalle del dictamen (decreto 549/25)**")
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
        elif "SUPERIOR" in r_u:
            llave = "Miembro superior"
        else:
            llave = "Miembro inferior"
        sumas_regionales[llave] = sumas_regionales.get(llave, 0) + p['val']

    topes = {"Miembro superior": 66.0, "Miembro inferior": 70.0}
    st.markdown("---")
    col_izq, col_der = st.columns(2)
    with col_izq:
        st.write("**análisis de topes legales:**")
        v_finales = []
        for reg_nombre, suma in sumas_regionales.items():
            t = topes.get(reg_nombre, 100.0)
            valor_final = min(suma, t)
            v_finales.append(valor_final)
            if suma > t:
                st.warning(f"⚠️ {reg_nombre}: {suma}% (tope aplicado: {t}%)")
            else:
                st.write(f"✅ {reg_nombre}: {suma}%")

        st.markdown("### **factores de ponderación**")
        edad = st.number_input("**edad**", 14, 99, 25)
        f_e = 0.05 if edad <= 20 else 0.04 if edad <= 30 else 0.03 if edad <= 40 else 0.02
        f_d = st.selectbox("**dificultad**", [0.05, 0.10, 0.20], format_func=lambda x: f"{int(x*100)}%")
        
        fis = balthazard(v_finales)
        inc = fis * (f_e + f_d)
        res_f = fis + inc

    with col_der:
        st.metric("**daño físico (balthazard)**", f"{fis}%")
        st.metric("**factores ponderados**", f"{round(inc, 2)}%")
        st.metric("**incapacidad final**", f"{round(res_f, 2)}%")
        if st.button("🚨 **reiniciar**"):
            st.session_state.pericia = []; st.rerun()