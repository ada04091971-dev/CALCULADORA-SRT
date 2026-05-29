import streamlit as st
import pandas as pd
import os

# 1. Configuración de la aplicación
st.set_page_config(page_title="Calculadora Laboral SRT - Decreto 549/25", layout="wide", page_icon="🧮")

@st.cache_resource
def abrir_excel():
    archivo = "calculadora_final_srt.xlsx"
    if not os.path.exists(archivo):
        st.error(f"No se encontró el archivo '{archivo}' en la carpeta de GitHub.")
        st.stop()
    return pd.ExcelFile(archivo)

def balthazard(lista, preexistencia=0.0):
    """Método de la capacidad restante (Balthazard) considerando incapacidad preexistente."""
    lista = sorted([x for x in lista if x > 0], reverse=True)
    if not lista: return 0.0
    
    capacidad_restante = 100.0 - preexistencia
    incapacidad_nueva_total = 0.0
    
    for inc in lista:
        valor_real = inc * capacidad_restante / 100.0
        incapacidad_nueva_total += valor_real
        capacidad_restante -= valor_real
        
    return round(incapacidad_nueva_total, 2)

if 'pericia' not in st.session_state:
    st.session_state.pericia = []

st.title("🧮 **Calculadora Laboral SRT: Decreto 549/25**")
st.markdown("---")

xls = abrir_excel()

# 2. Formularios de Ingreso
st.sidebar.header("➕ Agregar Lesión")
cap_val = st.sidebar.selectbox("Capítulo", ["Osteoarticular", "Psiquiatría (D.V.A.)"])

if cap_val == "Psiquiatría (D.V.A.)":
    hoja_psiq = next((s for s in xls.sheet_names if "psiquiatr" in s.lower()), None)
    if hoja_psiq:
        df_p = pd.read_excel(xls, sheet_name=hoja_psiq).fillna("")
        
        # Filtro de Goniometría si aplica
        opciones_lesion = sorted(df_p["Descripción"].unique().tolist())
        item = st.selectbox("Diagnóstico Psiquiátrico", opciones_lesion)
        if item:
            fila = df_p[df_p["Descripción"] == item].iloc[0]
            val = float(fila["%"])
            st.info(f"**Valor: {val}%**")
            if st.button("Agregar a la Pericia"):
                st.session_state.pericia.append({"cap": "Psiquiatría", "reg": "Salud Mental", "val": val, "desc": item})
                st.rerun()

elif cap_val == "Osteoarticular":
    regiones = ["Columna Cervical", "Columna Dorsolumbar y Pelvis", "Miembro Superior", "Miembro Inferior"]
    reg_val = st.sidebar.selectbox("Región Anatómica", regiones)
    
    if reg_val:
        if "Miembro Superior" in reg_val:
            hoja = "Miembro Superior"
            sec_val = st.selectbox("Sector", ["Hombro", "Brazo", "Codo", "Antebrazo", "Muñeca", "Mano", "Dedos"])
            lat = st.radio("Lado", ["Derecho", "Izquierdo"], horizontal=True)
        elif "Miembro Inferior" in reg_val:
            hoja = "Miembro Inferior"
            sec_val = st.selectbox("Sector", ["Cadera", "Muslo", "Rodilla", "Pierna", "Tobillo", "Pie", "Dedos"])
            lat = st.radio("Lado", ["Derecho", "Izquierdo"], horizontal=True)
        elif "Cervical" in reg_val:
            hoja, sec_val = "Columna Vertebral", "Columna Cervical"
        else:
            hoja, sec_val = "Columna Vertebral", st.selectbox("Sector", ["Columna Dorsal", "Columna Lumbar", "Sacro / Coxis"])
        
        if sec_val and hoja:
            nombre_real = next((s for s in xls.sheet_names if hoja.lower() == s.lower().strip()), None)
            if nombre_real:
                df = pd.read_excel(xls, sheet_name=nombre_real).fillna("")
                col_sector = next((c for c in df.columns if "sector" in c.lower()), df.columns[0])
                df_f = df[df[col_sector].astype(str).str.contains(sec_val, case=False, na=False)]
                
                col_cat = next((c for c in df_f.columns if "categor" in c.lower() and "sub" not in c.lower()), "Categoría")
                cat = st.selectbox("Categoría", ["Elegir..."] + sorted(df_f[col_cat].unique().tolist()))
                if cat != "Elegir...":
                    df_f = df_f[df_f[col_cat] == cat]
                    col_des = next((c for c in df_f.columns if "descrip" in c.lower()), "Descripción")
                    col_sub = next((c for c in df_f.columns if "subcategor" in c.lower()), None)
                    
                    opciones_lesion = sorted(df_f[col_des].unique().tolist())
                    
                    # Filtro Goniométrico: Si las lesiones contienen el símbolo de grados "°", permitir filtrar
                    sugerencia_index = None
                    if any("°" in str(x) for x in opciones_lesion):
                        grados_medidos = st.number_input("Opcional: Ingrese grados medidos para filtrar automáticamente", min_value=0, max_value=360, value=None, step=1)
                        if grados_medidos is not None:
                            import re
                            for idx, opt in enumerate(opciones_lesion):
                                opt_str = str(opt).replace(" ", "")
                                
                                # Caso 1: Rango (e.g. >10°y<30°, >0°y≤10°)
                                # Asumiremos las lógicas estándar de los baremos
                                nums = [int(n) for n in re.findall(r'\d+', opt_str)]
                                if len(nums) == 2:
                                    if nums[0] < grados_medidos <= nums[1] or nums[0] <= grados_medidos < nums[1]:
                                        sugerencia_index = idx
                                        break
                                # Caso 2: Valor único exacto (e.g. Flexión 0°)
                                elif len(nums) == 1:
                                    if grados_medidos == nums[0]:
                                        sugerencia_index = idx
                                        break
                            
                            if sugerencia_index is not None:
                                st.success(f"Sugerencia automática aplicada: **{opciones_lesion[sugerencia_index]}**")
                            else:
                                st.warning("No se encontró un rango exacto para los grados ingresados. Seleccione manualmente.")

                    item = st.selectbox("Lesión", opciones_lesion, index=sugerencia_index)
                    if item:
                        fila_seleccionada = df_f[df_f[col_des] == item].iloc[0]
                        col_inc = next((c for c in df_f.columns if "incap" in c.lower() or "%" in c.lower()), "%")
                        valor = float(fila_seleccionada[col_inc])
                        
                        subcat_val = str(fila_seleccionada.get(col_sub, '')).strip() if col_sub else ''
                        subcat = f" - {subcat_val}" if subcat_val and subcat_val.lower() not in [item.lower(), cat.lower()] else ""
                        desc_final = f"{cat}{subcat}: {item}"
                        
                        st.info(f"**Valor: {valor}%**")
                        if st.button("Agregar Lesión"):
                            st.session_state.pericia.append({"cap": "Osteoarticular", "reg": hoja, "val": valor, "desc": desc_final, "sector": sec_val, "lado": lat if 'lat' in locals() else None})
                            st.rerun()

# --- 2. Cálculos y Visualización ---
if st.session_state.pericia:
    st.subheader("**Detalle de la Pericia Médica**")
    
    # Validaciones de exclusión mutua
    for i, p1 in enumerate(st.session_state.pericia):
        for j, p2 in enumerate(st.session_state.pericia):
            if i < j and p1.get('reg') == p2.get('reg') and p1.get('cap') == 'Osteoarticular':
                d1 = p1.get('desc', '').lower()
                d2 = p2.get('desc', '').lower()
                if ('anquilosis' in d1 and 'limitación funcional' in d2) or ('anquilosis' in d2 and 'limitación funcional' in d1):
                    st.warning(f"⚠️ **Atención:** Hay una 'Anquilosis' y una 'Limitación Funcional' en la misma región ({p1.get('reg')}). Según el baremo, generalmente no deben sumarse.")
                    break

    acum_cervical, acum_dorsolumbar, acum_sacro = 0.0, 0.0, 0.0
    miembros = {"superior derecho": {}, "superior izquierdo": {}, "inferior derecho": {}, "inferior izquierdo": {}}
    otros_capitulos = []

    for i, p in enumerate(st.session_state.pericia):
        c1, c2, c3 = st.columns([2, 6, 1])
        cap = p.get('cap', 'Osteoarticular')
        reg = p.get('reg', 'N/A')
        val = p.get('val', 0.0)
        desc = p.get('desc', 'Sin descripción')
        sector = p.get('sector', '').lower()
        lado = p.get('lado', '').lower() if p.get('lado') else ""

        c1.markdown(f"**{cap} - {reg}**")
        c2.write(f"{desc} (**{val}%**)")
        if c3.button("🗑️", key=f"del_{i}"):
            st.session_state.pericia.pop(i)
            st.rerun()

        if cap == "Psiquiatría":
            otros_capitulos.append(val)
        elif "cervical" in sector or "cervical" in reg.lower(): acum_cervical += val
        elif any(x in sector or x in reg.lower() for x in ["dorsal", "lumbar"]): acum_dorsolumbar += val
        elif any(x in sector or x in reg.lower() for x in ["sacro", "coxis"]): acum_sacro += val
        elif lado:
            m_llave = f"{'superior' if 'superior' in reg.lower() else 'inferior'} {lado}"
            if m_llave in miembros: miembros[m_llave][sector] = miembros[m_llave].get(sector, 0.0) + val

    v_balthazard = []
    # Columna: Tope Cervical (40%) + Dorsolumbar (60%)
    col_final = min(min(acum_cervical, 40.0) + min(acum_dorsolumbar, 60.0) + acum_sacro, 100.0)
    if col_final > 0: v_balthazard.append(col_final)
    
    # Miembros (Lógica de Escalera Infranqueable)
    for m, datos in miembros.items():
        if datos:
            if "superior" in m:
                s1 = min(datos.get("dedos",0) + datos.get("mano",0) + datos.get("muñeca",0), 50.0)
                s2 = min(s1 + datos.get("antebrazo",0), 55.0)
                s3 = min(s2 + datos.get("codo",0) + datos.get("brazo",0), 60.0)
                v_balthazard.append(min(s3 + datos.get("hombro",0), 66.0))
            else:
                s1 = min(datos.get("dedos",0) + datos.get("pie",0) + datos.get("tobillo",0), 35.0)
                s2 = min(s1 + datos.get("pierna",0), 40.0)
                s3 = min(s2 + datos.get("rodilla",0), 55.0)
                v_balthazard.append(min(s3 + datos.get("muslo",0) + datos.get("cadera",0), 70.0))
    
    # Salud Mental (D.V.A.)
    v_balthazard.extend(otros_capitulos)

    st.markdown("---")
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("### **Factores de Ponderación (Decreto 549/25)**")
        
        preexistencia = st.number_input("**Incapacidad Preexistente (%)** (Capacidad restante)", 0.0, 99.0, 0.0, step=0.1)
        
        edad = st.number_input("**Edad al momento de la consolidación**", 14, 99, 54)
        # Rangos página 6: <21, 21-35, 36-45, >45
        f_e = 0.05 if edad < 21 else 0.04 if edad <= 35 else 0.03 if edad <= 45 else 0.02
        
        dif_map = {"Leve (5%)": 0.05, "Intermedia (10%)": 0.10, "Alta (20%)": 0.20}
        f_d = dif_map[st.selectbox("**Dificultad para tareas habituales**", list(dif_map.keys()))]
        
        fisico = balthazard(v_balthazard, preexistencia)
        factores = fisico * (f_e + f_d)
        
        # Barrera de incapacidad total: si físico < 66%, el final NO toca 66%
        total_f = min(fisico + factores, 65.99) if fisico < 66.0 else min(fisico + factores, 100.0)

    with col_r:
        st.metric("**Daño Físico Global (Balthazard)**", f"{fisico}%")
        st.metric("**Suma de Factores**", f"{round(factores, 2)}%")
        st.success(f"## **ILP FINAL: {round(total_f, 2)}%**")
        
        # --- Exportación de Informe ---
        informe_txt = f"INFORME PERICIAL MÉDICO - DECRETO 549/25\n{'='*40}\n\n"
        informe_txt += "1. DETALLE DE LESIONES:\n"
        for p in st.session_state.pericia:
            informe_txt += f" - {p.get('cap', '')} | {p.get('reg', '')}: {p.get('desc', '')} -> {p.get('val', 0.0)}%\n"
        
        informe_txt += f"\n2. CÁLCULO DE INCAPACIDAD FÍSICA:\n"
        if preexistencia > 0:
            informe_txt += f" - Incapacidad Preexistente: {preexistencia}%\n"
            informe_txt += f" - Capacidad Restante Inicial: {round(100.0 - preexistencia, 2)}%\n"
        informe_txt += f" - Daño Físico Global (Balthazard): {fisico}%\n"
        
        informe_txt += f"\n3. FACTORES DE PONDERACIÓN:\n"
        informe_txt += f" - Edad ({edad} años): {f_e * 100}%\n"
        informe_txt += f" - Dificultad para Tareas Habituales: {f_d * 100}%\n"
        informe_txt += f" - Suma de Factores Aplicada: {round(factores, 2)}%\n"
        
        informe_txt += f"\n{'='*40}\n"
        informe_txt += f"ILP FINAL: {round(total_f, 2)}%\n"
        informe_txt += f"{'='*40}\n"
        
        st.download_button(
            label="📄 Descargar Informe Pericial (.txt)",
            data=informe_txt,
            file_name="informe_pericial_srt.txt",
            mime="text/plain"
        )

        if st.button("🚨 Reiniciar Pericia"):
            st.session_state.pericia = []
            st.rerun()