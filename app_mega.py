import streamlit as st
import pandas as pd
import os

# Configuración de página
st.set_page_config(page_title="calculadora laboral SRT", layout="wide", page_icon="🧮")

def format_text(text):
    if not text: return ""
    text = str(text).strip()
    return text[0].upper() + text[1:]

@st.cache_resource
def abrir_excel():
    archivo = "calculadora_final_srt.xlsx"
    if not os.path.exists(archivo):
        st.error(f"no se encontró el archivo '{archivo}' en la carpeta.")
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
st.title("🧮 **calculadora laboral SRT: decreto 549/25**")
st.markdown("---")

if 'pericia' not in st.session_state:
    st.session_state.pericia = []

xls = abrir_excel()

with st.sidebar:
    st.header("**carga de hallazgos**")
    
    region_sel = st.selectbox("**1. región topográfica**", ["Columna", "Miembro Superior", "Miembro Inferior"], index=None)
    
    if region_sel:
        if region_sel == "Columna":
            sector_val = st.selectbox("**2. nivel vertebral**", ["Cervical", "Dorsal", "Lumbar", "Sacrococcigea", "Coxis"], index=None)
            hoja_buscada = sector_val
        else:
            lat = st.selectbox("**2. lateralidad**", ["Derecho", "Izquierdo"], index=None)
            hoja_buscada = f"{region_sel} {lat}"
            sectores_m = ["Hombro", "Brazo", "Codo", "Antebrazo", "Muñeca", "Mano", "Dedos"] if "Superior" in region_sel else ["Cadera", "Muslo", "Rodilla", "Pierna", "Tobillo", "Pie", "Dedos"]
            sector_val = st.selectbox("**3. sector anatómico**", sectores_m, index=None)

        # Buscador de hojas robusto (ignora mayúsculas y espacios)
        nombre_real_hoja = next((s for s in xls.sheet_names if hoja_buscada and hoja_buscada.lower() == s.lower().strip()), None)

        if nombre_real_hoja and sector_val:
            df = pd.read_excel(xls, sheet_name=nombre_real_hoja).fillna("")
            
            # 🛠️ LIMPIEZA CRÍTICA: Quitamos espacios en los nombres de las columnas
            df.columns = [str(c).strip() for c in df.columns]
            
            # 🕵️ DETECCIÓN DINÁMICA: Buscamos las columnas por "palabra clave" para evitar el KeyError
            col_sec = next((c for c in df.columns if "sector" in c.lower()), None)
            col_cat = next((c for c in df.columns if "categor" in c.lower() and "sub" not in c.lower()), None)
            col_sub = next((c for c in df.columns if "subcategor" in c.lower()), None)
            col_des = next((c for c in df.columns if "descrip" in c.lower()), None)
            col_inc = next((c for c in df.columns if "incap" in c.lower() or "%" in c.lower()), None)

            # Verificación de integridad
            if not col_sec or not col_cat or not col_des or not col_inc:
                st.error(f"⚠️ error en hoja '{nombre_real_hoja}': faltan columnas críticas (sector, categoría, descripción o %).")
            else:
                # Filtro por Sector
                df_f = df[df[col_sec].astype(str).str.contains(str(sector_val), case=False, na=False)]

                if not df_f.empty:
                    # 4. Selección de Categoría
                    lista_cats = sorted(df_f[col_cat].unique().tolist())
                    cat_sel = st.selectbox(f"**categoría en {sector_val}**", ["ver todas"] + lista_cats)
                    
                    if cat_sel != "ver todas":
                        df_f = df_f[df_f[col_cat] == cat_sel]
                        
                        # 5. Subcategoría (Solo si existe en la hoja y hay datos)
                        if col_sub:
                            lista_subs = sorted([str(x) for x in df_f[col_sub].unique() if str(x).strip() != ""])
                            if lista_subs:
                                sub_sel = st.selectbox("**subcategoría**", ["ver todas"] + lista_subs)
                                if sub_sel != "ver todas":
                                    df_f = df_f[df_f[col_sub] == sub_sel]

                    # 6. Selección de Secuela Final
                    opciones = sorted(df_f[col_des].unique().tolist())
                    if opciones:
                        item = st.selectbox(f"**secuela ({len(opciones)})**", opciones, format_func=format_text, index=None)
                        if item:
                            valor = df_f[df_f[col_des] == item][col_inc].iloc[0]
                            st.success(f"**valor baremo: {valor}%**")
                            
                            if st.button("**AGREGAR A LA PERICIA**"):
                                st.session_state.pericia.append({
                                    "reg": f"{sector_val} {lat if region_sel != 'Columna' else ''}", 
                                    "desc": item, 
                                    "val": float(valor)
                                })
                                st.rerun()

# --- LÓGICA DE RESULTADOS Y TOPE 65.99% ---
if st.session_state.pericia:
    st.subheader("**detalle del dictamen médico**")
    sumas_reg = {}
    for i, p in enumerate(st.session_state.pericia):
        c1, c2, c3 = st.columns([3, 5, 1])
        c1.write(f"**{p['reg']}**")
        c2.write(f"{format_text(p['desc'])} ({p['val']}%)")
        if c3.button("🗑️", key=f"del_{i}"):
            st.session_state.pericia.pop(i); st.rerun()
        
        # Agrupación regional para topes de Decreto 549/25
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
            if suma > t: st.warning(f"⚠️ {reg}: {suma}% (tope aplicado: {t}%)")
            else: st.write(f"✅ {reg}: {suma}%")

        edad = st.number_input("**edad**", 14, 99, 25)
        f_e = 0.05 if edad <= 20 else 0.04 if edad <= 30 else 0.03 if edad <= 40 else 0.02
        f_d = st.selectbox("**dificultad**", [0.05, 0.10, 0.20], format_func=lambda x: f"{int(x*100)}%")
        
        fisico = balthazard(v_finales)
        factores = fisico * (f_e + f_d)
        
        # 🛡️ REGLA DE ORO: Tope 65.99% para parciales
        total_p = fisico + factores
        if fisico < 66.0 and total_p >= 66.0:
            total_f = 65.99; aplicado_tope = True
        else:
            total_f = total_p; aplicado_tope = False

    with col_r:
        st.metric("**daño físico (balthazard)**", f"{fisico}%")
        st.metric("**factores aplicados**", f"{round(factores, 2)}%")
        if aplicado_tope:
            st.error(f"## **ILP final: {total_f}%**")
            st.caption("nota: se aplicó el tope legal para incapacidades parciales.")
        else:
            st.success(f"## **ILP final: {round(total_f, 2)}%**")
        if st.button("🚨 reiniciar"): st.session_state.pericia = []; st.rerun()