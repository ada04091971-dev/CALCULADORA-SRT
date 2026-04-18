Ese error de sintaxis ocurre porque, al copiar el código, una de las líneas de texto se cortó por la mitad, dejando las comillas abiertas. Es un error común de "copy-paste" cuando las líneas son muy largas.

Aquí tenés el código de la aplicación app_mega.py corregido (sin errores de sintaxis) y, más abajo, el script de testeo masivo que me pediste para poner a prueba todas las reglas de topes, lateralidad y columna.

1. Aplicación corregida: app_mega.py
Python
import streamlit as st
import pandas as pd
import os

# Configuración de la aplicación
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
    """Suma por capacidad restante según fórmula de Balthazard."""
    lista = sorted([x for x in lista if x > 0], reverse=True)
    if not lista: return 0.0
    total = lista[0]
    for i in range(1, len(lista)):
        total = total + (lista[i] * (100 - total) / 100)
    return round(total, 2)

# Inicialización de la sesión
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
            sectores_col = ["Cervical", "Dorsal", "Lumbar", "Sacrococcigea", "Coxis"]
            sector_val = st.selectbox("**2. Sector Anatómico**", sectores_col, index=None, placeholder="Elegir opción")
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
            
            col_cat = next((c for c in df.columns if "categor" in c.lower() and "sub" not in c.lower()), "Categoría")
            col_sub = next((c for c in df.columns if "subcategor" in c.lower()), None)
            col_sec = next((c for c in df.columns if "sector" in c.lower()), "Sector")
            col_des = next((c for c in df.columns if "descrip" in c.lower()), "Descripción de lesión")
            col_inc = next((c for c in df.columns if "incap" in c.lower() or "%" in c.lower()), "% de Incapacidad Laboral")

            df_f = df[df[col_sec].astype(str).str.contains(str(sector_val), case=False, na=False)]

            if not df_f.empty:
                cat_sel = st.selectbox(f"**4. Categoría en {sector_val}**", ["Ver todas"] + sorted(df_f[col_cat].unique().tolist()), placeholder="Elegir opción")
                
                sub_sel = ""
                if cat_sel != "Ver todas":
                    df_f = df_f[df_f[col_cat] == cat_sel]
                    if col_sub:
                        lista_subs = sorted([str(x) for x in df_f[col_sub].unique() if str(x).strip() != ""])
                        if lista_subs:
                            sub_sel = st.selectbox("**5. Subcategoría**", ["Ver todas"] + lista_subs, placeholder="Elegir opción")
                            if sub_sel != "Ver todas": df_f = df_f[df_f[col_sub] == sub_sel]
                            else: sub_sel = ""

                opciones = sorted(df_f[col_des].unique().tolist())
                if opciones:
                    item = st.selectbox(f"**6. Descripción de la lesión ({len(opciones)})**", opciones, index=None, placeholder="Elegir opción")
                    if item:
                        valor = float(df_f[df_f[col_des] == item][col_inc].iloc[0])
                        st.success(f"**Valor baremo: {valor}%**")
                        if st.button("**Agregar lesion**"):
                            sector_final = f"Columna {sector_val}" if region_sel == "Columna" else f"{sector_val} {lat_sel}"
                            desc_final = f"{cat_sel} - {sub_sel} - {item}" if sub_sel else f"{cat_sel} - {item}"
                            st.session_state.pericia.append({"reg": sector_final, "desc": desc_final, "val": valor})
                            st.rerun()

# --- Resultados ---
if st.session_state.pericia:
    st.subheader("**Detalle de secuelas**")
    grupos = {}
    informe = "INFORME SRT - DECRETO 549/25\n" + "="*30 + "\n\nSECUELAS:\n"
    for i, p in enumerate(st.session_state.pericia):
        c1, c2, c3 = st.columns([3, 5, 1])
        c1.write(f"**{p['reg']}**")
        c2.write(f"{p['desc']} ({p['val']}%)")
        informe += f"- {p['reg']}: {p['desc']} ({p['val']}%)\n"
        if c3.button("🗑️", key=f"del_{i}"): st.session_state.pericia.pop(i); st.rerun()
        
        r_up = p['reg'].upper()
        llave = "Columna" if "COLUMNA" in r_up else (f"Superior {'Derecho' if 'DERECHO' in r_up else 'Izquierdo'}" if "SUPERIOR" in r_up or "HOMBRO" in r_up or "BRAZO" in r_up or "CODO" in r_up or "ANTEBRAZO" in r_up or "MUÑECA" in r_up or "MANO" in r_up or "DEDOS" in r_up else f"Inferior {'Derecho' if 'DERECHO' in r_up else 'Izquierdo'}")
        grupos[llave] = grupos.get(llave, 0.0) + p['val']

    st.markdown("---")
    col_l, col_r = st.columns(2)
    with col_l:
        topes = {"Superior Derecho": 66.0, "Superior Izquierdo": 66.0, "Inferior Derecho": 70.0, "Inferior Izquierdo": 70.0}
        v_finales = []
        for g, s in grupos.items():
            t = topes.get(g, 100.0)
            v_finales.append(min(s, t))
            st.write(f"{'✅' if s <= t else '⚠️'} {g}: {s}%")
        
        edad = st.number_input("**Edad**", 14, 99, 25)
        f_e = 0.05 if edad <= 20 else 0.04 if edad <= 30 else 0.03 if edad <= 40 else 0.02
        f_d = st.selectbox("**Dificultad**", [0.05, 0.10, 0.20], format_func=lambda x: f"{int(x*100)}%", placeholder="Elegir opción")
        
        fisico = balthazard(v_finales)
        factores = fisico * (f_e + f_d)
        total_p = fisico + factores
        total_f = min(total_p, 65.99) if fisico < 66.0 else min(total_p, 100.0)

    with col_r:
        st.metric("**Daño físico (Balthazard)**", f"{fisico}%")
        st.metric("**Factores aplicados**", f"{round(factores, 2)}%")
        st.success(f"## **ILP final: {round(total_f, 2)}%**")
        
        informe += f"\nCÁLCULO:\n- Daño Físico: {fisico}%\n- Factores: {round(factores, 2)}%\n- Total ILP: {round(total_f, 2)}%\n\nNota: Balthazard aplicado entre miembros y columna. Tope 100% absoluto."
        st.download_button("💾 **Exportar cálculo**", data=informe, file_name="pericia_srt.txt")
        if st.button("🚨 Reiniciar"): st.session_state.pericia = []; st.rerun()