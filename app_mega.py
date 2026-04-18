import streamlit as st
import pandas as pd
import os

# 1. Configuración de la aplicación
st.set_page_config(page_title="Calculadora laboral SRT", layout="wide", page_icon="🧮")

@st.cache_resource
def abrir_excel():
    archivo = "calculadora_final_srt.xlsx"
    if not os.path.exists(archivo):
        st.error(f"No se encontró el archivo '{archivo}' en la carpeta.")
        st.stop()
    return pd.ExcelFile(archivo)

def balthazard(lista):
    """Método de la capacidad restante para combinar regiones distintas."""
    lista = sorted([x for x in lista if x > 0], reverse=True)
    if not lista: return 0.0
    total = lista[0]
    for i in range(1, len(lista)):
        total = total + (lista[i] * (100 - total) / 100)
    return round(total, 2)

if 'pericia' not in st.session_state:
    st.session_state.pericia = []

st.title("🧮 **Calculadora laboral SRT: Decreto 549/25**")
st.markdown("---")

xls = abrir_excel()

with st.sidebar:
    st.header("**Carga de hallazgos**")
    region_sel = st.selectbox("**1. Región Topográfica**", ["Columna", "Miembro Superior", "Miembro Inferior"], index=None, placeholder="Elegir opción")
    
    if region_sel:
        if region_sel == "Columna":
            sec_col = ["Cervical", "Dorsal", "Lumbar", "Sacrococcigea", "Coxis"]
            sector_val = st.selectbox("**2. Sector Anatómico**", sec_col, index=None, placeholder="Elegir opción")
            hoja_buscada = sector_val
            lat_sel = None
        else:
            lat_sel = st.selectbox("**2. Lateralidad**", ["Derecho", "Izquierdo"], index=None, placeholder="Elegir opción")
            sectores_m = ["Hombro", "Brazo", "Codo", "Antebrazo", "Muñeca", "Mano", "Dedos"] if "Superior" in region_sel else ["Cadera", "Muslo", "Rodilla", "Pierna", "Tobillo", "Pie", "Dedos"]
            sector_val = st.selectbox("**3. Sector Anatómico**", sectores_m, index=None, placeholder="Elegir opción")
            hoja_buscada = f"{region_sel} {lat_sel}" if lat_sel else None

        nombre_real_hoja = next((s for s in xls.sheet_names if hoja_buscada and hoja_buscada.lower() == s.lower().strip()), None)

        if nombre_real_hoja and sector_val:
            df = pd.read_excel(xls, sheet_name=nombre_real_hoja).fillna("")
            df.columns = [str(c).strip() for c in df.columns]
            
            col_sec = next((c for c in df.columns if "sector" in c.lower()), "Sector")
            col_cat = next((c for c in df.columns if "categor" in c.lower() and "sub" not in c.lower()), "Categoría")
            col_sub = next((c for c in df.columns if "subcategor" in c.lower()), None)
            col_des = next((c for c in df.columns if "descrip" in c.lower()), "Descripción de lesión")
            col_inc = next((c for c in df.columns if "incap" in c.lower() or "%" in c.lower()), "% de Incapacidad Laboral")

            df_f = df[df[col_sec].astype(str).str.contains(str(sector_val), case=False, na=False)]

            if not df_f.empty:
                cat_sel = st.selectbox(f"**Categoría en {sector_val}**", ["Ver todas"] + sorted(df_f[col_cat].unique().tolist()), placeholder="Elegir opción")
                
                sub_sel = ""
                if cat_sel != "Ver todas":
                    df_f = df_f[df_f[col_cat] == cat_sel]
                    if col_sub:
                        lista_subs = sorted([str(x) for x in df_f[col_sub].unique() if str(x).strip() != ""])
                        if lista_subs:
                            sub_sel = st.selectbox("**Subcategoría**", ["Ver todas"] + lista_subs, placeholder="Elegir opción")
                            if sub_sel != "Ver todas": df_f = df_f[df_f[col_sub] == sub_sel]
                            else: sub_sel = ""

                opciones = sorted(df_f[col_des].unique().tolist())
                if opciones:
                    item = st.selectbox(f"**Descripción de la lesión ({len(opciones)})**", opciones, index=None, placeholder="Elegir opción")
                    if item:
                        valor = float(df_f[df_f[col_des] == item][col_inc].iloc[0])
                        st.info(f"**Valor baremo: {valor}%**")
                        if st.button("**Agregar lesion**"):
                            st.session_state.pericia.append({
                                "reg": f"Columna {sector_val}" if region_sel == "Columna" else f"{sector_val} {lat_sel}",
                                "val": valor, "miembro": region_sel, "sector": sector_val, "lado": lat_sel,
                                "desc": f"{cat_sel} - {item}"
                            })
                            st.rerun()

# --- 2. Lógica de Cálculo con Suma Aritmética en Columna ---
if st.session_state.pericia:
    st.subheader("**Detalle de secuelas**")
    
    # Agrupadores específicos por reglas del Decreto 549/25
    cervical_arit = 0.0
    dorsolumbar_arit = 0.0
    sacro_arit = 0.0
    miembros_data = {"Superior Derecho": {}, "Superior Izquierdo": {}, "Inferior Derecho": {}, "Inferior Izquierdo": {}}

    for i, p in enumerate(st.session_state.pericia):
        c1, c2, c3 = st.columns([3, 5, 1])
        c1.write(f"**{p['reg']}**")
        c2.write(f"{p['desc']} ({p['val']}%)")
        if c3.button("🗑️", key=f"del_{i}"): st.session_state.pericia.pop(i); st.rerun()

        v, s, m, l = p['val'], p['sector'], p['miembro'], p['lado']
        
        if m == "Columna":
            if s == "Cervical": cervical_arit += v
            elif s in ["Dorsal", "Lumbar"]: dorsolumbar_arit += v
            else: sacro_arit += v
        else:
            llave = f"{m.replace('Miembro ', '')} {l}"
            if s not in miembros_data[llave]: miembros_data[llave][s] = 0.0
            miembros_data[llave][s] += v

    # --- Procesamiento de Columna (Estrictamente Aritmético) ---
    cervical_final = min(cervical_arit, 40.0)
    dorsolumbar_final = min(dorsolumbar_arit, 60.0)
    # Suma aritmética de los sectores de la columna según esquema validado
    total_columna = min(cervical_final + dorsolumbar_final + sacro_arit, 100.0)

    # --- Procesamiento de Miembros (Escaleras de Topes) ---
    v_regionales_para_balthazard = []
    if total_columna > 0: v_regionales_para_balthazard.append(total_columna)

    for lado in ["Superior Derecho", "Superior Izquierdo"]:
        d = miembros_data[lado]
        if d:
            s1 = min(d.get("Dedos", 0) + d.get("Mano", 0) + d.get("Muñeca", 0), 50.0)
            s2 = min(s1 + d.get("Antebrazo", 0), 55.0)
            s3 = min(s2 + d.get("Codo", 0) + d.get("Brazo", 0), 60.0)
            v_regionales_para_balthazard.append(min(s3 + d.get("Hombro", 0), 66.0))

    for lado in ["Inferior Derecho", "Inferior Izquierdo"]:
        d = miembros_data[lado]
        if d:
            s1 = min(d.get("Dedos", 0) + d.get("Pie", 0) + d.get("Tobillo", 0), 35.0)
            s2 = min(s1 + d.get("Pierna", 0), 40.0)
            s3 = min(s2 + d.get("Rodilla", 0), 55.0)
            v_regionales_para_balthazard.append(min(s3 + d.get("Muslo", 0) + d.get("Cadera", 0), 70.0))

    # --- 3. Resultados Finales ---
    st.markdown("---")
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("### **Factores de ponderación**")
        edad = st.number_input("**Edad**", 14, 99, 25)
        f_e = 0.05 if edad <= 20 else 0.04 if edad <= 30 else 0.03 if edad <= 40 else 0.02
        f_d = st.selectbox("**Dificultad**", [0.05, 0.10, 0.20], format_func=lambda x: f"{int(x*100)}%", placeholder="Elegir opción")
        
        fisico = balthazard(v_regionales_para_balthazard)
        factores = fisico * (f_e + f_d)
        total_p = fisico + factores
        total_f = min(total_p, 65.99) if fisico < 66.0 else min(total_p, 100.0)

    with col_r:
        st.metric("**Daño físico (Balthazard)**", f"{fisico}%")
        st.metric("**Factores aplicados**", f"{round(factores, 2)}%")
        st.success(f"## **ILP final: {round(total_f, 2)}%**")
        if st.button("🚨 Reiniciar"): st.session_state.pericia = []; st.rerun()