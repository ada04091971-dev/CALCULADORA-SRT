import streamlit as st
import pandas as pd
import os

# configuración de la página
st.set_page_config(page_title="calculadora integral SRT", layout="wide", page_icon="🧮")

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

# interfaz principal
st.title("🧮 **calculadora SRT – edición osteoarticular estable**")
st.markdown("---")

if 'pericia' not in st.session_state:
    st.session_state.pericia = []

xls = abrir_excel()

with st.sidebar:
    st.header("**carga de hallazgos**")
    
    opciones_region = ["columna", "miembro superior", "miembro inferior"]
    region = st.selectbox("**1. región**", opciones_region, index=None)
    
    if region:
        # 2. nivel o lateralidad
        if region == "columna":
            sectores_col = ["cervical", "dorsal", "lumbar", "sacrococcigea", "coxis"]
            sector = st.selectbox("**2. nivel vertebral**", sectores_col, index=None)
            hoja = format_text(sector)
        else:
            lat = st.selectbox("**2. lateralidad**", ["derecho", "izquierdo"], index=None)
            if region == "miembro superior":
                sectores_m = ["hombro", "brazo", "codo", "antebrazo", "muñeca", "mano", "dedos"]
            else:
                sectores_m = ["cadera", "muslo", "rodilla", "pierna", "tobillo", "pie", "dedos"]
            sector = st.selectbox("**3. sector anatómico**", sectores_m, index=None)
            hoja = f"{format_text(region)} {format_text(lat)}"

        if sector and (region == "columna" or lat):
            # carga de datos
            df = pd.read_excel(xls, sheet_name=hoja).fillna("")
            df.columns = df.columns.str.strip()

            # filtro por sector para miembros
            if region != "columna":
                df = df[df['Categoría'].str.contains(sector, case=False, na=False) | 
                        df['Descripción de lesión'].str.contains(sector, case=False, na=False)]

            if not df.empty:
                # 4. categoría
                categorias = ["ver todas"] + sorted(df['Categoría'].unique().tolist())
                cat_sel = st.selectbox("**4. categoría**", categorias)
                df_f = df[df['Categoría'] == cat_sel] if cat_sel != "ver todas" else df
                
                # 5. movimiento (si aplica)
                if any(x in str(cat_sel).lower() for x in ["anquilosis", "limitación"]):
                    movs = ["flexión", "extensión", "inclinación", "rotación", "abducción", "aducción", "pronación", "supinación"]
                    opc_mov = [m for m in movs if df_f['Descripción de lesión'].str.contains(m, case=False).any()]
                    if opc_mov:
                        tipo_mov = st.selectbox("**5. movimiento**", opc_mov, index=None)
                        if tipo_mov:
                            df_f = df_f[df_f['Descripción de lesión'].str.contains(tipo_mov, case=False)]

                # 6. selección final
                opciones = sorted(df_f['Descripción de lesión'].unique())
                if opciones:
                    item = st.selectbox(f"**6. secuela ({len(opciones)})**", opciones, format_func=format_text, index=None)
                    if item:
                        valor = df_f[df_f['Descripción de lesión'] == item]['% de incapacidad laboral'].iloc[0]
                        st.success(f"**valor baremo: {valor}%**")
                        if st.button("**agregar a la pericia**"):
                            st.session_state.pericia.append({
                                "reg": sector if region == "columna" else f"{sector} {lat}",
                                "desc": item, 
                                "val": float(valor)
                            })
                            st.rerun()

# panel de resultados
if st.session_state.pericia:
    st.subheader("**detalle del dictamen médico**")
    sumas_regionales = {}
    for i, p in enumerate(st.session_state.pericia):
        c1, c2, c3 = st.columns([3, 5, 1])
        c1.write(f"**{p['reg']}**")
        c2.write(f"{format_text(p['desc'])} ({p['val']}%)")
        if c3.button("🗑️", key=f"del_{i}"):
            st.session_state.pericia.pop(i)
            st.rerun()
        
        # agrupación para topes
        d_u = p['desc'].upper()
        r_u = p['reg'].upper()
        if "CERVICAL" in r_u or any(x in d_u for x in ["CERVICAL", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"]):
            llave = "columna cervical"
        elif any(x in r_u for x in ["LUMBAR", "DORSAL", "SACRO", "COXIS"]):
            llave = "columna dorsolumbar"
        elif "SUPERIOR" in r_u:
            llave = "miembro superior"
        else:
            llave = "miembro inferior"
        sumas_regionales[llave] = sumas_regionales.get(llave, 0) + p['val']

    topes = {"miembro superior": 66.0, "miembro inferior": 70.0, "columna cervical": 40.0, "columna dorsolumbar": 60.0}
    
    st.markdown("---")
    col_izq, col_der = st.columns(2)
    with col_izq:
        st.write("**análisis de topes regionales:**")
        valores_balthazard = []
        for reg_nombre, suma in sumas_regionales.items():
            t = topes.get(reg_nombre, 100.0)
            valor_final = min(suma, t)
            valores_balthazard.append(valor_final)
            if suma > t:
                st.warning(f"⚠️ {reg_nombre}: {suma}% excede el tope de {t}%.")
            else:
                st.write(f"✅ {reg_nombre}: {suma}%")

        st.markdown("### **factores de ponderación**")
        edad = st.number_input("**edad**", 14, 99, 25)
        f_e = 0.05 if edad <= 20 else 0.04 if edad <= 30 else 0.03 if edad <= 40 else 0.02
        f_d = st.selectbox("**dificultad**", [0.05, 0.10, 0.20], format_func=lambda x: f"{int(x*100)}%")
        
        dano_fisico = balthazard(valores_balthazard)
        factores = dano_fisico * (f_e + f_d)
        ilp_final = min(dano_fisico + factores, 65.99) if dano_fisico < 66.0 else dano_fisico + factores

    with col_der:
        st.metric("**daño físico residual**", f"{dano_fisico}%")
        st.metric("**factores aplicados**", f"{round(factores, 2)}%")
        st.metric("**ILP final**", f"{round(ilp_final, 2)}%")
        if st.button("🚨 **borrar todo**"):
            st.session_state.pericia = []
            st.rerun()