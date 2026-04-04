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
st.title("🧮 **Mega Calculadora SRT: Edición Final**")
st.markdown("---")

if 'pericia' not in st.session_state:
    st.session_state.pericia = []

with st.sidebar:
    st.header("**Carga de Hallazgos**")
    
    region_madre = st.selectbox("**1. Región**", ["Columna", "Miembro Superior", "Miembro Inferior"], index=None)
    
    if region_madre:
        if region_madre == "Columna":
            sub = st.selectbox("**2. Nivel Vertebral**", ["Cervical", "Dorsal", "Lumbar", "Sacrococcigea", "Coxis"], index=None)
            hoja_nombre = sub
        else:
            lat = st.selectbox("**2. Lateralidad**", ["Derecho", "Izquierdo"], index=None)
            hoja_nombre = f"{region_madre} {lat}"
            
        if (region_madre == "Columna" and sub) or (region_madre != "Columna" and lat):
            hallazgo = st.radio("**3. Tipo de Hallazgo**", ["Osteoarticular / Goniometría", "Neurológico / Radicular"])
            
            if "Neurológico" in hallazgo:
                df_final = cargar_hoja("Neurologia")
                kw = sub if region_madre == "Columna" else ("Superior" if "Superior" in region_madre else "Inferior")
                df_final = df_final[df_final['Apartado'].str.contains(kw, case=False, na=False)]
            else:
                df_final = cargar_hoja(hoja_nombre)

            if not df_final.empty:
                # IDENTIFICACIÓN DINÁMICA DE COLUMNAS (A prueba de errores de Excel)
                col_cat = next((c for c in df_final.columns if "categ" in c.lower() or "apartado" in c.lower()), df_final.columns[2])
                col_desc = next((c for c in df_final.columns if "descrip" in c.lower()), df_final.columns[3])
                col_inc = next((c for c in df_final.columns if "incap" in c.lower() or "%" in c.lower()), df_final.columns[-1])

                # 4. Categoría
                categorias = ["Ver todas"] + sorted(df_final[col_cat].unique().tolist())
                cat_sel = st.selectbox("**4. Categoría**", categorias)
                
                df_items = df_final.copy()
                if cat_sel != "Ver todas":
                    df_items = df_items[df_items[col_cat] == cat_sel]
                
                # 5. Filtro de Movimiento
                if any(x in str(cat_sel) for x in ["Anquilosis", "Limitación", "Goniometría"]):
                    movs_ref = ["Flexión", "Extensión", "Inclinación", "Rotación", "Abducción", "Aducción", "Pronación", "Supinación"]
                    opc_mov = [m for m in movs_ref if df_items[col_desc].str.contains(m, case=False).any()]
                    if opc_mov:
                        tipo_mov = st.selectbox("**Tipo de Movimiento**", opc_mov, index=None)
                        if tipo_mov:
                            df_items = df_items[df_items[col_desc].str.contains(tipo_mov, case=False)]

                # 6. Selección Final
                opciones = sorted(df_items[col_desc].unique())
                if opciones:
                    item_sel = st.selectbox(f"**5. Secuela ({len(opciones)})**", opciones, format_func=format_text, index=None)
                    if item_sel:
                        # CORRECCIÓN DE LÓGICA AQUÍ: Buscamos el valor donde la DESCRIPCIÓN coincide
                        fila = df_items[df_items[col_desc] == item_sel]
                        valor_raw = fila[col_inc].iloc[0]
                        
                        # Aseguramos que el valor sea numérico y bien formateado
                        try:
                            valor = float(str(valor_raw).replace('%', '').replace(',', '.'))
                            if 0 < valor < 1: valor = valor * 100
                        except:
                            valor = 0.0

                        st.success(f"**Valor Baremo: {round(valor, 2)}%**")
                        
                        # EL BOTÓN AHORA ES VISIBLE
                        if st.button("**AGREGAR A LA PERICIA**"):
                            st.session_state.pericia.append({"reg": hoja_nombre, "desc": item_sel, "val": round(valor, 2)})
                            st.rerun()

# --- Resultados Finales ---
if st.session_state.pericia:
    st.markdown("---")
    st.subheader("**Detalle del Dictamen Médico**")
    sumas_seg = {}
    for i, p in enumerate(st.session_state.pericia):
        c1, col_desc_p, c3 = st.columns([3, 5, 1])
        c1.write(f"**{p['reg']}**")
        col_desc_p.write(f"{format_text(p['desc'])} ({p['val']}%)")
        if c3.button("🗑️", key=f"del_{i}"):
            st.session_state.pericia.pop(i); st.rerun()
        
        desc_u = p['desc'].upper()
        if "CERVICAL" in p['reg'] or any(x in desc_u for x in ["CERVICAL", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"]):
            llave = "Columna Cervical"
        elif "Columna" in p['reg'] or any(x in p['reg'] for x in ["Lumbar", "Dorsal", "Sacro", "Coxis"]):
            llave = "Columna Dorsolumbar"
        elif "Superior" in p['reg']:
            llave = "Miembro Superior"
        else:
            llave = "Miembro Inferior"
        sumas_seg[llave] = sumas_seg.get(llave, 0) + p['val']

    topes = {"Miembro Superior": 66.0, "Miembro Inferior": 70.0, "Columna Cervical": 40.0, "Columna Dorsolumbar": 60.0}
    
    st.markdown("---")
    col_l, col_r = st.columns(2)
    with col_l:
        st.write("**Análisis de Topes Regionales:**")
        v_bal = []
        for s, suma in sumas_seg.items():
            t = topes.get(s, 100.0)
            v_f = min(suma, t)
            v_bal.append(v_f)
            if suma > t: st.warning(f"⚠️ {s}: {suma}% excede el tope de {t}%.")
            else: st.write(f"✅ {s}: {suma}%")

        st.markdown("### **Factores de Ponderación**")
        u_edad = st.number_input("**Edad del Trabajador**", 14, 99, 25)
        f_e = 0.05 if u_edad <= 20 else 0.04 if u_edad <= 30 else 0.03 if u_edad <= 40 else 0.02
        f_d = st.selectbox("**Dificultad para Tareas**", [0.05, 0.10, 0.20], format_func=lambda x: f"{int(x*100)}%")
        
        fis = balthazard(v_bal)
        inc = fis * (f_e + f_d)
        res_f = min(fis + inc, 65.99) if fis < 66.0 else fis + inc

    with col_r:
        st.metric("**Daño Físico Residual**", f"{fis}%")
        st.metric("**Factores Aplicados**", f"{round(inc, 2)}%")
        if res_f >= 66.0: st.error(f"## **ILP FINAL: {round(res_f, 2)}% (TOTAL)**")
        else: st.success(f"## **ILP FINAL: {round(res_f, 2)}% (PARCIAL)**")
        if st.button("🚨 **BORRAR TODO EL DICTAMEN**"):
            st.session_state.pericia = []; st.rerun()