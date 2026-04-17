# --- PANEL DE RESULTADOS: Lógica de Lateralidad y Capacidad Restante ---
if st.session_state.pericia:
    st.subheader("**Detalle del Dictamen Médico (Decreto 549/25)**")
    
    # Agrupamos por miembro y lado para aplicar topes individuales
    grupos_topes = {}
    for i, p in enumerate(st.session_state.pericia):
        c1, c2, c3 = st.columns([3, 5, 1])
        c1.write(f"**{p['reg']}**")
        c2.write(f"{p['desc']} ({p['val']}%)") # Se muestra exacto como en el Excel
        if c3.button("🗑️", key=f"del_{i}"):
            st.session_state.pericia.pop(i); st.rerun()
        
        # Identificación de la 'llave' de tope (ej: "Superior Derecho")
        r_up = p['reg'].upper()
        if any(x in r_up for x in ["LUMBAR", "CERVICAL", "DORSAL", "SACRO", "COXIS"]):
            llave_tope = "Columna"
        else:
            lado = "Derecho" if "DERECHO" in r_up else "Izquierdo"
            miembro = "Superior" if "SUPERIOR" in r_up else "Inferior"
            llave_tope = f"{miembro} {lado}"
        
        if llave_tope not in grupos_topes: grupos_topes[llave_tope] = 0.0
        grupos_topes[llave_tope] += p['val']

    # Configuración de topes por lateralidad
    limites = {
        "Superior Derecho": 66.0, "Superior Izquierdo": 66.0,
        "Inferior Derecho": 70.0, "Inferior Izquierdo": 70.0,
        "Columna": 100.0 # La columna no tiene tope regional de amputación
    }

    st.markdown("---")
    col_l, col_r = st.columns(2)
    with col_l:
        st.write("**Análisis de Topes por Lateralidad:**")
        v_finales_para_balthazard = []
        
        for nombre_grupo, suma_puntos in grupos_topes.items():
            tope_max = limites.get(nombre_grupo, 100.0)
            valor_con_tope = min(suma_puntos, tope_max)
            v_finales_para_balthazard.append(valor_con_tope)
            
            if suma_puntos > tope_max:
                st.warning(f"⚠️ {nombre_grupo}: {suma_puntos}% (Tope de ley aplicado: {tope_max}%)")
            else:
                st.write(f"✅ {nombre_grupo}: {suma_puntos}%")

        # Factores de Ponderación
        u_edad = st.number_input("**Edad**", 14, 99, 25)
        f_e = 0.05 if u_edad <= 20 else 0.04 if u_edad <= 30 else 0.03 if u_edad <= 40 else 0.02
        f_d = st.selectbox("**Dificultad**", [0.05, 0.10, 0.20], format_func=lambda x: f"{int(x*100)}%")
        
        # Suma por capacidad restante (Balthazard) entre grupos
        fisico = balthazard(v_finales_para_balthazard)
        factores = fisico * (f_e + f_d)
        
        # Regla del 65.99% para parciales
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
            st.caption("Nota: Se aplicó el tope legal para incapacidades parciales.")
        else:
            color_final = "error" if total_f >= 66.0 else "success"
            st.write(f"## **ILP Final: {round(total_f, 2)}%**")
        
        if st.button("🚨 Reiniciar cálculo"):
            st.session_state.pericia = []; st.rerun()
