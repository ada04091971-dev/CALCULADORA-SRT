import streamlit as st
import pandas as pd
import os

# 1. Configuración de la aplicación
st.set_page_config(page_title="Calculadora laboral SRT", layout="wide", page_icon="🧮")

def format_text(text):
    if not text: return ""
    return str(text).strip()

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

# 2. Inicialización de la sesión
if 'pericia' not in st.session_state:
    st.session_state.pericia = []

# Título Principal
st.title("🧮 **Calculadora laboral SRT: Decreto 549/25**")
st.markdown("---")

xls = abrir_excel()

with st.sidebar:
    st.header("**Carga de hallazgos**")
    
    # 1. Región Topográfica
    region_sel = st.selectbox(
        "**1. Región Topográfica**", 
        ["Columna", "Miembro Superior", "Miembro Inferior"], 
        index=None, 
        placeholder="Elegir opción"
    )
    
    if region_sel:
        # 2. Sector Anatómico
        if region_sel == "Columna":
            sectores_col = ["Cervical", "Dorsal", "Lumbar", "Sacrococcigea", "Coxis"]
            sector_val = st.selectbox("**2. Sector Anatómico**", sectores_col, index=None, placeholder="Elegir opción")
            hoja_buscada = sector_val
            lat_sel = None
        else:
            sectores_m = ["Hombro", "Brazo", "Codo", "Antebrazo", "Muñeca", "Mano", "Dedos"] if "Superior" in region_sel else ["Cadera", "Muslo", "Rodilla", "Pierna", "Tobillo", "Pie", "Dedos"]
            sector_val = st.selectbox("**2. Sector Anatómico**", sectores_m, index=None, placeholder="Elegir opción")
            
            if sector_val:
                # 3. Lateralidad con concordancia de género
                femininos = ["Muñeca", "Mano", "Cadera", "Rodilla", "Pierna"]
                opc_lat = ["Derecha", "Izquierda"] if sector_val in femininos else ["Derecho", "Izquierdo"]
                
                # El 'key' dinámico soluciona el ValueError al cambiar de sector
                lat_sel = st.selectbox(
                    "**3. Lateralidad**", 
                    opc_lat, 
                    index=None, 
                    placeholder="Elegir opción",
                    key=f"lat_select_{sector_val}"
                )
                
                # Mapeo interno para el Excel (siempre masculino en el archivo)
                lat_hoja = "Derecho" if lat_sel in ["Derecho", "Derecha"] else "Izquierdo" if lat_sel else None
                hoja_buscada = f"{region_sel} {lat_hoja}" if lat_hoja else None

        # Búsqueda en el archivo
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
                lista_cats = sorted(df_f[col_cat].unique().tolist())
                cat_sel = st.selectbox(f"**Categoría en {sector_val}**", ["Ver todas"] + lista_cats, placeholder="Elegir opción")
                
                sub_sel = ""
                if cat_sel != "Ver todas":
                    df_f = df_f[df_f[col_cat] == cat_sel]
                    if col_sub:
                        lista_subs = sorted([str(x) for x in df_f[col_sub].unique() if str(x).strip() != ""])
                        if lista_subs:
                            sub_sel = st.selectbox("**Subcategoría**", ["Ver todas"] + lista_subs, placeholder="Elegir opción")
                            if sub_sel != "Ver todas":
                                df_f = df_f[df_f[col_sub] == sub_sel]
                            else: sub_sel = ""

                opciones = sorted(df_f[col_des].unique().tolist())
                if opciones:
                    item = st.selectbox(f"**Descripción de la lesión ({len(opciones)})**", opciones, index=None, placeholder="Elegir opción")
                    if item:
                        valor = df_f[df_f[col_des] == item][col_inc].iloc[0]
                        st.success(f"**Valor baremo: {valor}%**")
                        
                        if st.button("**Agregar lesion**"):
                            # Lógica prolija: Agregamos "Columna" solo al guardar para el dictamen
                            if region_sel == "Columna":
                                reg_final = f"Columna {sector_val}"
                            else:
                                reg_final = f"{sector_val} {lat_sel}"

                            nombre_completo = f"{cat_sel}"
                            if sub_sel: nombre_completo += f" - {sub_sel}"
                            nombre_completo += f" - {item}"
                            
                            st.session_state.pericia.append({
                                "reg": reg_final, 
                                "desc": nombre_completo, 
                                "val": float(valor)
                            })
                            st.rerun()

# 3. Panel de Resultados: Detalle de secuelas
if st.session_state.pericia:
    st.subheader("**Detalle de secuelas**")
    grupos_topes = {}
    informe_texto = "INFORME DE CALIFICACIÓN DE INCAPACIDAD - SRT\n"
    informe_texto += "="*40 + "\n\nDETALLE DE SECUELAS:\n"

    for i, p in enumerate(st.session_state.pericia):
        c1, c2, c3 = st.columns([3, 5, 1])
        c1.write(f"**{p['reg']}**")
        c2.write(f"{p['desc']} ({p['val']}%)")
        informe_texto += f"- {p['reg']}: {p['desc']} ({p['val']}%)\n"

        if c3.button("🗑️", key=f"del_{i}"):
            st.session_state.pericia.pop(i); st.rerun()
        
        r_up = p['reg'].upper()
        if "COLUMNA" in r_up:
            llave_tope = "Columna"
        else:
            lado = "Derecho" if "DERECHO" in r_up or "DERECHA" in r_up else "Izquierdo"
            miembro = "Superior" if "SUPERIOR" in r_up else "Inferior"
            llave_tope = f"{miembro} {lado}"
        grupos_topes[llave_tope] = grupos_topes.get(llave_tope, 0.0) + p['val']

    limites = {"Superior Derecho": 66.0, "Superior Izquierdo": 66.0, "Inferior Derecho": 70.0, "Inferior Izquierdo": 70.0}
    
    st.markdown("---")
    col_l, col_r = st.columns(2)
    with col_l:
        st.write("**Análisis de topes por lateralidad:**")
        v_finales = []
        for nombre_grupo, suma_puntos in grupos_topes.items():
            t = limites.get(nombre_grupo, 100.0)
            v_f = min(suma_puntos, t); v_finales.append(v_f)
            st.write(f"{'✅' if suma_puntos <= t else '⚠️'} {nombre_grupo}: {suma_puntos}%")

        st.markdown("### **Factores de ponderación**")
        edad = st.number_input("**Edad**", 14, 99, 25)
        f_e = 0.05 if edad <= 20 else 0.04 if edad <= 30 else 0.03 if edad <= 40 else 0.02
        f_d = st.selectbox("**Dificultad**", [0.05, 0.10, 0.20], format_func=lambda x: f"{int(x*100)}%", placeholder="Elegir opción")
        
        fisico = balthazard(v_finales)
        factores = fisico * (f_e + f_d)
        total_p = fisico + factores
        total_f = 65.99 if (fisico < 66.0 and total_p >= 66.0) else total_p

    with col_r:
        st.metric("**Daño físico (Balthazard)**", f"{fisico}%")
        st.metric("**Factores aplicados**", f"{round(factores, 2)}%")
        st.success(f"## **ILP final: {round(total_f, 2)}%**")
        
        # Informe para exportar
        informe_texto += f"\nRESUMEN DE CÁLCULO:\n"
        informe_texto += f"- Daño físico residual (Balthazard): {fisico}%\n"
        informe_texto += f"- Factores de ponderación aplicados: {round(factores, 2)}%\n"
        informe_texto += f"- Incapacidad Laboral Permanente (ILP): {round(total_f, 2)}%\n\n"
        informe_texto += "MÉTODO DE CÁLCULO:\n"
        informe_texto += "Se utiliza el método de la capacidad restante (fórmula de Balthazard) para la combinación de incapacidades múltiples. "
        informe_texto += "Los factores de ponderación se calculan linealmente sobre el daño físico residual acumulado tras aplicar los topes por lateralidad. "
        informe_texto += "Las incapacidades parciales tienen un tope máximo de 65.99%."

        st.download_button(
            label="💾 **Exportar cálculo completo**",
            data=informe_texto,
            file_name="detalle_secuelas_srt.txt",
            mime="text/plain"
        )
        
        if st.button("🚨 Reiniciar cálculo"):
            st.session_state.pericia = []; st.rerun()