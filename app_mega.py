import streamlit as st
import pandas as pd
import os

# Configuración de la aplicación
st.set_page_config(page_title="Calculadora Laboral SRT", layout="wide", page_icon="🧮")

def format_text(text):
    if not text: return ""
    text = str(text).strip()
    return text[0].upper() + text[1:]

@st.cache_resource
def abrir_excel():
    archivo = "calculadora_final_srt.xlsx"
    if not os.path.exists(archivo):
        st.error(f"No se encontró el archivo '{archivo}' en la carpeta.")
        st.stop()
    return pd.ExcelFile(archivo)

def balthazard(lista):
    lista = sorted([x for x in lista if x > 0], reverse=True)
    if not lista: return 0.0
    total = lista[0]
    for i in range(1, len(lista)):
        total = total + (lista[i] * (100 - total) / 100)
    return round(total, 2)

# Interfaz Principal
st.title("🧮 **Calculadora Laboral SRT: Decreto 549/25**")
st.markdown("---")

if 'pericia' not in st.session_state:
    st.session_state.pericia = []

xls = abrir_excel()

with st.sidebar:
    st.header("**Carga de Hallazgos**")
    
    # 1. Selección de Región Principal
    opc_reg = ["Columna", "Miembro Superior", "Miembro Inferior"]
    region_sel = st.selectbox("**1. Región Topográfica**", opc_reg, index=None)
    
    if region_sel:
        # 2. Determinación de Hoja y Sector
        if region_sel == "Columna":
            sector_val = st.selectbox("**2. Nivel vertebral**", ["Cervical", "Dorsal", "Lumbar", "Sacrococcigea", "Coxis"], index=None)
            hoja_buscada = sector_val
        else:
            lat = st.selectbox("**2. Lateralidad**", ["Derecho", "Izquierdo"], index=None)
            hoja_buscada = f"{region_sel} {lat}"
            sectores_m = ["Hombro", "Brazo", "Codo", "Antebrazo", "Muñeca", "Mano", "Dedos"] if "Superior" in region_sel else ["Cadera", "Muslo", "Rodilla", "Pierna", "Tobillo", "Pie", "Dedos"]
            sector_val = st.selectbox("**3. Sector Anatómico**", sectores_m, index=None)

        # Buscador de hojas robusto
        nombre_real_hoja = next((s for s in xls.sheet_names if hoja_buscada and hoja_buscada.lower() == s.lower().strip()), None)

        if nombre_real_hoja and sector_val:
            df = pd.read_excel(xls, sheet_name=nombre_real_hoja).fillna("")
            df.columns = [str(c).strip() for c in df.columns]
            
            # Filtro por Sector (Columna 'Sector')
            df_f = df[df['Sector'].astype(str).str.contains(str(sector_val), case=False, na=False)]

            if not df_f.empty:
                # 3. Categoría
                lista_cats = sorted(df_f['Categoría'].unique().tolist())
                cat_sel = st.selectbox(f"**Categoría en {sector_val}**", ["Ver todas"] + lista_cats)
                
                if cat_sel != "Ver todas":
                    df_f = df_f[df_f['Categoría'] == cat_sel]
                    
                    # 4. Subcategoría (Paso opcional si hay datos)
                    if 'Subcategoría' in df_f.columns:
                        lista_subs = sorted([str(x) for x in df_f['Subcategoría'].unique() if str(x).strip() != ""])
                        if lista_subs:
                            sub_sel = st.selectbox("**Subcategoría**", ["Ver todas"] + lista_subs)
                            if sub_sel != "Ver todas":
                                df_f = df_f[df_f['Subcategoría'] == sub_sel]

                # 5. Selección de Secuela
                opciones = sorted(df_f['Descripción de lesión'].unique().tolist())
                if opciones:
                    item = st.selectbox(f"**Secuela ({len(opciones)})**", opciones, format_func=format_text, index=None)
                    if item:
                        valor = df_f[df_f['Descripción de lesión'] == item]['% de Incapacidad Laboral'].iloc[0]
                        st.success(f"**Valor Baremo: {valor}%**")
                        
                        if st.button("**AGREGAR A LA PERICIA**"):
                            st.session_state.pericia.append({
                                "reg": f"{sector_val} {lat if region_sel != 'Columna' else ''}", 
                                "desc": item, 
                                "val": float(valor)
                            })
                            st.rerun()

# --- Panel de Resultados y Lógica de Topes ---
if st.session_state.pericia:
    st.subheader("**Detalle del Dictamen Médico**")
    sumas_reg = {}
    for i, p in enumerate(st.session_state.pericia):
        c1, c2, c3 = st.columns([3, 5, 1])
        c1.write(f"**{p['reg']}**")
        c2.write(f"{format_text(p['desc'])} ({p['val']}%)")
        if c3.button("🗑️", key=f"del_{i}"):
            st.session_state.pericia.pop(i); st.rerun()
        
        # Agrupación regional
        reg_up = p['reg'].upper()
        llave = "Columna" if any(x in reg_up for x in ["LUMBAR", "CERVICAL", "DORSAL", "SACRO"]) else ("M. Superior" if "SUPERIOR" in reg_up else "M. Inferior")
        sumas_reg[llave] = sumas_reg.get(llave, 0) + p['val']

    topes = {"M. Superior": 66.0, "M. Inferior": 70.0}
    st.markdown("---")
    col_l, col_r = st.columns(2)
    with col_l:
        v_finales = []
        for reg, suma in sumas_reg.items():
            t = topes.get(reg, 100.0)
            v_f = min(suma, t); v_finales.append(v_f)
            if suma > t: st.warning(f"⚠️ {reg}: {suma}% (Tope: {t}%)")
            else: st.write(f"✅ {reg}: {suma}%")

        st.markdown("### **Factores de Ponderación**")
        edad = st.number_input("**Edad**", 14, 99, 25)
        f_e = 0.05 if edad <= 20 else 0.04 if edad <= 30 else 0.03 if edad <= 40 else 0.02
        f_d = st.selectbox("**Dificultad**", [0.05, 0.10, 0.20], format_func=lambda x: f"{int(x*100)}%")
        
        fisico = balthazard(v_finales)
        factores = fisico * (f_e + f_d)
        
        # Lógica del tope legal 65.99%
        total_p = fisico + factores
        if fisico < 66.0 and total_p >= 66.0:
            total_f = 65.99; aplicado_tope = True
        else:
            total_f = total_p; aplicado_tope = False

    with col_r:
        st.metric("**Daño Físico (Balthazard)**", f"{fisico}%")
        st.metric("**Factores Ponderados**", f"{round(factores, 2)}%")
        
        if aplicado_tope:
            st.error(f"## **ILP Final: {total_f}%**")
            st.caption("Se aplicó el tope legal de 65.99% (Incapacidad Parcial).")
        else:
            st.success(f"## **ILP Final: {round(total_f, 2)}%**")
            
        if st.button("🚨 Reiniciar cálculo"):
            st.session_state.pericia = []; st.rerun()