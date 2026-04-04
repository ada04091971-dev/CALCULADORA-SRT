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

# Buscador flexible para Columnas (Prioriza la posición si falla el nombre)
def obtener_datos_columna(df, palabras_clave, indice_fallback):
    for col in df.columns:
        if any(p.lower() in str(col).lower() for p in palabras_clave):
            return col
    return df.columns[indice_fallback]

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
        if region == "Columna":
            sector = st.selectbox("**2. Nivel vertebral**", ["Cervical", "Dorsal", "Lumbar", "Sacrococcigea", "Coxis"], index=None)
            hoja = sector
        else:
            lat = st.selectbox("**2. Lateralidad**", ["Derecho", "Izquierdo"], index=None)
            sectores_m = ["Hombro", "Brazo", "Codo", "Antebrazo", "Muñeca", "Mano", "Dedos"] if "Superior" in region else ["Cadera", "Muslo", "Rodilla", "Pierna", "Tobillo", "Pie", "Dedos"]
            sector = st.selectbox("**3. Sector anatómico**", sectores_m, index=None)
            hoja = f"{region} {lat}"

        if sector and (region == "Columna" or lat):
            df = pd.read_excel(xls, sheet_name=hoja).fillna("")
            df.columns = df.columns.str.strip()
            
            # Identificación de columnas críticas
            c_cat = obtener_datos_columna(df, ["categor", "apartado"], 2)
            c_desc = obtener_datos_columna(df, ["descrip"], 3)
            c_inc = obtener_datos_columna(df, ["incap", "%"], 4) # Columna E (Índice 4)

            # Filtro por sector (solo para miembros)
            df_f = df.copy()
            if region != "Columna":
                df_f = df_f[df_f[c_cat].str.contains(sector, case=False, na=False) | 
                            df_f[c_desc].str.contains(sector, case=False, na=False)]

            # 4. Categoría
            categorias = ["Ver todas"] + sorted(df_f[c_cat].unique().tolist())
            cat_sel = st.selectbox("**4. Categoría**", categorias)
            if cat_sel != "Ver todas":
                df_f = df_f[df_f[c_cat] == cat_sel]
            
            # 5. Movimiento (Goniometría)
            if any(x in str(cat_sel).lower() for x in ["anquilosis", "limitación"]):
                movs = ["Flexión", "Extensión", "Inclinación", "Rotación", "Abducción", "Aducción", "Pronación", "Supinación"]
                opc_mov = [m for m in movs if df_f[c_desc].str.contains(m, case=False).any()]
                if opc_mov:
                    tipo_mov = st.selectbox("**5. Movimiento**", opc_mov, index=None)
                    if tipo_mov:
                        df_f = df_f[df_f[c_desc].str.contains(tipo_mov, case=False)]

            # 6. Selección de Secuela
            opciones = sorted(df_f[c_desc].unique())
            if opciones:
                item = st.selectbox(f"**6. Secuela ({len(opciones)})**", opciones, format_func=format_text, index=None)
                if item:
                    valor = df_f[df_f[c_desc] == item][c_inc].iloc[0]
                    st.success(f"**Valor Baremo: {valor}%**")
                    
                    # BOTÓN DE CARGA
                    if st.button("**AGREGAR A LA PERICIA**"):
                        st.session_state.pericia.append({
                            "reg": sector if region == "Columna" else f"{sector} {lat}",
                            "desc": item, 
                            "val": float(valor)
                        })
                        st.rerun()

# --- PANEL DE RESULTADOS Y TOPES ---
if st.session_state.pericia:
    st.subheader("**Detalle del Dictamen (Decreto 549/25)**")
    sumas_regionales = {}
    for i, p in enumerate(st.session_state.pericia):
        c1, c2, c3 = st.columns([3, 5, 1])
        c1.write(f"**{p['reg']}**")
        c2.write(f"{format_text(p['desc'])} ({p['val']}%)")
        if c3.button("🗑️", key=f"del_{i}"):
            st.session_state.pericia.pop(i); st.rerun()
        
        # Agrupación para aplicación de Topes
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
                st.warning(f"⚠️ {reg_nombre}: {suma}% (Tope aplicado: {t}%)")
            else:
                st.write(f"✅ {reg_nombre}: {suma}%")

        st.markdown("### **Factores de Ponderación**")
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
        if st.button("🚨 **REINICIAR CÁLCULO**"):
            st.session_state.pericia = []; st.rerun()