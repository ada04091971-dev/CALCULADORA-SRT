import streamlit as st
import pandas as pd
import os

# --- Configuración inicial ---
st.set_page_config(page_title="Mega Calculadora SRT", layout="wide", page_icon="🧮")

def format_text(text):
    if not text: return ""
    return str(text).strip()

@st.cache_data
def cargar_datos():
    archivo = "calculadora_final_srt.xlsx"
    if not os.path.exists(archivo):
        st.error("No se encontró el archivo Excel.")
        st.stop()
    return pd.ExcelFile(archivo)

try:
    xls = cargar_datos()
except Exception as e:
    st.error(f"Error al abrir el Excel: {e}")
    st.stop()

def balthazard(lista):
    lista = sorted([x for x in lista if x > 0], reverse=True)
    if not lista: return 0.0
    total = lista[0]
    for i in range(1, len(lista)):
        total = total + (lista[i] * (100 - total) / 100)
    return round(total, 2)

# --- Interfaz ---
st.title("🧮 **Mega Calculadora SRT: Edición Estable**")
st.markdown("---")

if 'pericia' not in st.session_state:
    st.session_state.pericia = []

with st.sidebar:
    st.header("**Carga de hallazgos**")
    
    region = st.selectbox("**1. Región**", ["Columna", "Miembro Superior", "Miembro Inferior"], index=None)
    
    if region:
        # 2. Selección de Hoja
        if region == "Columna":
            sub = st.selectbox("**2. Nivel vertebral**", ["Cervical", "Dorsal", "Lumbar", "Sacrococcigea", "Coxis"], index=None)
            hoja_nombre = sub
        else:
            lat = st.selectbox("**2. Lateralidad**", ["Derecho", "Izquierdo"], index=None)
            hoja_nombre = f"{region} {lat}"
            
        if hoja_nombre in xls.sheet_names:
            df_hoja = pd.read_excel(xls, sheet_name=hoja_nombre).fillna("")
            # Limpiamos nombres de columnas para evitar el KeyError
            df_hoja.columns = df_hoja.columns.str.strip()
            
            # 3. Tipo de Hallazgo
            hallazgo = st.radio("**3. Tipo de hallazgo**", ["Osteoarticular / Goniometría", "Neurológico / Radicular"])
            
            if "Neurológico" in hallazgo:
                df_fil = pd.read_excel(xls, sheet_name="Neurologia").fillna("")
                df_fil.columns = df_fil.columns.str.strip()
                kw = hoja_nombre if region == "Columna" else region.split(" ")[1]
                df_fil = df_fil[df_fil['Apartado'].str.contains(kw, case=False, na=False)]
            else:
                df_fil = df_hoja

            if not df_fil.empty:
                # 4. CATEGORÍA (Usando el nombre exacto de tu Excel: 'Categorias')
                # Si la columna no existe, avisamos para no romper la app
                col_cat = "Categorias" if "Categorias" in df_fil.columns else "Apartado"
                
                lista_cats = ["Ver todas"] + sorted(df_fil[col_cat].unique().tolist())
                cat_sel = st.selectbox("**4. Categoría**", lista_cats)
                
                df_cat = df_fil.copy()
                if cat_sel != "Ver todas":
                    df_cat = df_cat[df_cat[col_cat] == cat_sel]
                
                # 5. MOVIMIENTO (Para achicar la lista de 45 ítems)
                if any(x in str(cat_sel) for x in ["Anquilosis", "Limitación"]):
                    movs = ["Flexión", "Extensión", "Inclinación", "Rotación", "Abducción", "Aducción"]
                    opc_mov = [m for m in movs if df_cat['Descripción de Lesión'].str.contains(m, case=False).any()]
                    if opc_mov:
                        tipo_mov = st.selectbox("**5. Tipo de movimiento**", opc_mov, index=None)
                        if tipo_mov:
                            df_cat = df_cat[df_cat['Descripción de Lesión'].str.contains(tipo_mov, case=False)]

                # 6. SECUELA ESPECÍFICA
                opciones = sorted(df_cat['Descripción de Lesión'].unique())
                if opciones:
                    item_sel = st.selectbox(f"**6. Secuela ({len(opciones)})**", opciones, format_func=format_text, index=None)
                    
                    if item_sel:
                        fila = df_cat[df_cat['Descripción de Lesión'] == item_sel]
                        # Nombre exacto de tu columna: '% de Incapacidad Laboral'
                        valor = fila['% de Incapacidad Laboral'].iloc[0]
                        
                        # Limpieza de porcentaje (0.05 -> 5.0)
                        try:
                            val_num = float(str(valor).replace('%', '').replace(',', '.'))
                            if 0 < val_num < 1: val_num *= 100
                        except: val_num = 0.0

                        st.success(f"**Valor: {val_num}%**")
                        if st.button("**AGREGAR A LA PERICIA**"):
                            st.session_state.pericia.append({
                                "reg": hoja_nombre, 
                                "desc": item_sel, 
                                "val": val_num
                            })
                            st.rerun()

# --- PANEL DE RESULTADOS ---
if st.session_state.pericia:
    st.subheader("**Detalle del dictamen médico**")
    sumas_seg = {}
    for i, p in enumerate(st.session_state.pericia):
        c1, c2, c3 = st.columns([3, 5, 1])
        c1.write(f"**{p['reg']}**")
        c2.write(f"{p['desc']} ({p['val']}%)")
        if c3.button("🗑️", key=f"del_{i}"):
            st.session_state.pericia.pop(i)
            st.rerun()
        
        # Agrupación para topes
        desc_u = p['desc'].upper()
        if "CERVICAL" in p['reg'] or any(x in desc_u for x in ["CERVICAL", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"]):
            llave = "Columna cervical"
        elif any(x in p['reg'] for x in ["Lumbar", "Dorsal", "Sacro", "Coxis"]):
            llave = "Columna dorsolumbar"
        elif "Superior" in p['reg']:
            llave = "Miembro superior"
        else:
            llave = "Miembro inferior"
        sumas_seg[llave] = sumas_seg.get(llave, 0) + p['val']

    topes = {"Miembro superior": 66.0, "Miembro inferior": 70.0, "Columna cervical": 40.0, "Columna dorsolumbar": 60.0}
    
    st.markdown("---")
    l, r = st.columns(2)
    with l:
        st.write("**Topes regionales:**")
        v_bal = []
        for s, suma in sumas_seg.items():
            t = topes.get(s, 100.0)
            v_f = min(suma, t)
            v_bal.append(v_f)
            st.write(f"{'✅' if suma <= t else '⚠️'} {s}: {suma}% (Tope: {t}%)")

        u_edad = st.number_input("**Edad**", 14, 99, 25)
        f_e = 0.05 if u_edad <= 20 else 0.04 if u_edad <= 30 else 0.03 if u_edad <= 40 else 0.02
        f_d = st.selectbox("**Dificultad**", [0.05, 0.10, 0.20], format_func=lambda x: f"{int(x*100)}%")
        
        fis = balthazard(v_bal)
        inc = fis * (f_e + f_d)
        res_f = min(fis + inc, 65.99) if fis < 66.0 else fis + inc

    with r:
        st.metric("**Daño físico residual**", f"{fis}%")
        st.metric("**Factores aplicados**", f"{round(inc, 2)}%")
        st.metric("**ILP FINAL**", f"{round(res_f, 2)}%")
        if st.button("🚨 **BORRAR TODO**"):
            st.session_state.pericia = []
            st.rerun()