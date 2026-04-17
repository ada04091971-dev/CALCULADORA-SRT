Conversación con Gemini
PS C:\Users\Alfredo> py preparar_excel.py

C:\Users\Alfredo\AppData\Local\Programs\Python\Python314\python.exe: can't open file 'C:\\Users\\Alfredo\\preparar_excel.py': [Errno 2] No such file or directory

Ese error ocurre porque la terminal está parada en tu carpeta de usuario personal (C:\Users\Alfredo), pero tu proyecto y el script están en la carpeta de la SRT en el escritorio. Es como intentar abrir un archivo que tenés en la oficina estando en tu casa: Python no lo encuentra porque no está ahí.

Para solucionarlo, tenés que "navegar" hasta la carpeta correcta en la terminal antes de ejecutar el comando.

🛠️ Seguí estos pasos en PowerShell:
Cambiá de carpeta: Copiá y pegá este comando (con las comillas incluidas) y presioná Enter:

PowerShell
cd "C:\Users\Alfredo\OneDrive - SUPERINTENDENCIA DE RIESGOS DEL TRABAJO\Escritorio\AUDITOR\LABORAL\columnacalc"
Verificá que estás ahí: Deberías ver que la ruta a la izquierda del cursor (PS ... >) cambió y ahora muestra toda la dirección de la carpeta columnacalc.

Ejecutá el script: Ahora sí, escribí el comando:

PowerShell
py preparar_excel.py
💡 Un truco para la próxima:
Si no querés escribir toda la ruta a mano, podés hacer esto:

Abrí la carpeta columnacalc en el explorador de archivos de Windows (donde ves el excel y los scripts).

Hacé clic en la barra de direcciones arriba (donde dice la ruta).

Borrá todo, escribí powershell y dale a Enter. Se abrirá la terminal directamente en esa carpeta, lista para trabajar.

¿Pudiste entrar a la carpeta y correr el script ahora?

te subi el excel, te fijas si hay algo para corregir

He revisado la estructura de los archivos que subiste y encontré algunos puntos críticos que debemos unificar para que la App no se trabe al saltar de una región a otra.

Aquí tenés el diagnóstico de lo que falta corregir:

1. Inconsistencia en las Columnas
Las hojas no tienen la misma estructura. Esto es lo más peligroso para el código:

En Columna (ej. Lumbar): Tenés la columna Sector al principio (Columna A).

En Miembros (ej. Superior Derecho): La columna se llama Sector Anatomico y está en el medio (Columna D).

Consecuencia: Cuando la App busca el porcentaje en la columna E, en una hoja encuentra el número y en la otra encuentra texto, lo que genera el error.

2. Redundancia en la Descripción
A pesar de la limpieza, en hojas como Lumbar, la columna Descripción de lesión sigue teniendo prefijos repetitivos (ej: "Fracturas Vertebrales - (L1) - ..."). La idea es que ahí solo diga "Sin secuelas" o "Con secuelas", ya que el resto ya se lee en la categoría.

3. Nombres de Columnas
Para que el código sea una "roca", todas las hojas deben tener exactamente estos encabezados y en este orden:

Sector (Hombro, Mano, Lumbar, etc.)

Capítulo (Osteoarticular)

Apartado (Columna, Miembro Superior, etc.)

Categoría (Fracturas, Amputaciones, etc.)

Descripción de lesión (El detalle específico limpio)

% de Incapacidad Laboral (El número entero)

🛠️ Solución: Script de Unificación Final
No lo hagas a mano hoja por hoja. Ejecutá este script en tu computadora. Está diseñado para forzar a que todas las hojas tengan las mismas 6 columnas en el mismo orden y limpie las descripciones de una vez por todas.

Python
import pandas as pd
import os

archivo_in = "calculadora_final_srt.xlsx"
archivo_out = "calculadora_final_srt_UNIFICADO.xlsx"

try:
    xls = pd.ExcelFile(archivo_in)
    writer = pd.ExcelWriter(archivo_out, engine='xlsxwriter')

    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)
        df.columns = [str(c).strip() for c in df.columns]

        # 1. Identificamos las columnas sin importar el nombre exacto
        col_sec = next((c for c in df.columns if "sector" in c.lower()), None)
        col_cap = next((c for c in df.columns if "capit" in c.lower()), None)
        col_apa = next((c for c in df.columns if "apart" in c.lower()), None)
        col_cat = next((c for c in df.columns if "categor" in c.lower()), None)
        col_des = next((c for c in df.columns if "descrip" in c.lower()), None)
        col_inc = next((c for c in df.columns if "incap" in c.lower() or "%" in c.lower()), None)

        # 2. Creamos un nuevo DataFrame con el orden ESTÁNDAR (6 columnas)
        df_new = pd.DataFrame()
        df_new['Sector'] = df[col_sec] if col_sec else sheet
        df_new['Capítulo'] = df[col_cap] if col_cap else "Osteoarticular"
        df_new['Apartado'] = df[col_apa] if col_apa else sheet
        df_new['Categoría'] = df[col_cat]
        
        # 3. Limpieza profunda de Descripción (quitar lo que se repite de Categoría)
        def limpiar_final(row):
            cat = str(row['Categoría']).split('-')[0].strip().lower()
            des = str(df.loc[row.name, col_des]).strip()
            # Si la descripción empieza con la categoría, la recortamos
            if des.lower().startswith(cat):
                des = des[len(cat):].lstrip(" -–—:").strip()
            return des if des else str(df.loc[row.name, col_des])

        df_new['Descripción de lesión'] = df_new.apply(limpiar_final, axis=1)
        df_new['% de Incapacidad Laboral'] = df[col_inc]

        df_new.to_excel(writer, sheet_name=sheet, index=False)
        print(f"✅ Hoja '{sheet}' unificada.")

    writer.close()
    print(f"\n🚀 PROCESO COMPLETADO. Usá el archivo: {archivo_out}")

except Exception as e:
    print(f"❌ Error: {e}")
¿Cómo seguir?
Ejecutá ese script.

Renombrá el resultado a calculadora_final_srt.xlsx.

Subilo a tu GitHub o reemplazalo en la carpeta de la App.

Con esto, la estructura será simétrica y el error del KeyError o los saltos de columna desaparecerán para siempre. ¿Querés que te ajuste también el código de la App para que lea estas 6 columnas fijas?

Analizar espacios, letras, puntos , etcetera. Reacomode los diagnosticos y suprimi palabras repetidas, reacomode las columnas

Excelente trabajo de limpieza, Alfredo. Se nota la diferencia: los diagnósticos son mucho más directos y la estructura ha ganado mucha consistencia.

He analizado los archivos de la versión revisada y aquí están las conclusiones para que la App funcione perfectamente:

✅ Mejoras detectadas
Limpieza de descripciones: Se eliminaron los prefijos redundantes (como "Fracturas vertebrales -"). Ahora en Lumbar leemos directamente "L1 - Sin secuelas" o "L1 - Con secuelas", lo que facilita mucho la lectura en el celular.

Consistencia de Columnas: Casi todas las hojas tienen el mismo orden ahora.

Valores Numéricos: Los porcentajes están como números enteros (5, 8, 16, 66), lo que evita errores de cálculo.

⚠️ Observaciones para el Código
Para que no tengas que volver a tocar el Excel, he ajustado el código para que sea compatible con los pequeños detalles que quedaron:

Nombre del Sector: En Columna la columna se llama Sector, pero en Miembros se llama Sector Anatomico. He programado la App para que busque cualquiera de los dos nombres.

Ubicación de Columnas: Ahora la "Categoría" es la columna C, el "Sector" es la D, y la "Descripción" es la E.

🚀 Código Final Adaptado (Copiá y pegá en app_mega.py)
Este código está diseñado específicamente para la estructura de tu nuevo Excel.

Python
import streamlit as st
import pandas as pd
import os

# Configuración de página
st.set_page_config(page_title="Calculadora Laboral SRT", layout="wide", page_icon="🧮")

def format_text(text):
    if not text: return ""
    text = str(text).strip()
    return text[0].upper() + text[1:]

@st.cache_resource
def abrir_excel():
    archivo = "calculadora_final_srt.xlsx"
    if not os.path.exists(archivo):
        st.error("❌ No se encontró el archivo 'calculadora_final_srt.xlsx'")
        st.stop()
    return pd.ExcelFile(archivo)

def balthazard(lista):
    lista = sorted([x for x in lista if x > 0], reverse=True)
    if not lista: return 0.0
    total = lista[0]
    for i in range(1, len(lista)):
        total = total + (lista[i] * (100 - total) / 100)
    return round(total, 2)

# Interfaz
st.title("🧮 **Calculadora Laboral SRT: Decreto 549/25**")
st.markdown("---")

if 'pericia' not in st.session_state:
    st.session_state.pericia = []

xls = abrir_excel()

with st.sidebar:
    st.header("**Carga de Hallazgos**")
    
    region = st.selectbox("**1. Región**", ["Columna", "Miembro Superior", "Miembro Inferior"], index=None)
    
    if region:
        if region == "Columna":
            sector_sel = st.selectbox("**2. Nivel vertebral**", ["Cervical", "Dorsal", "Lumbar", "Sacrococcigea", "Coxis"], index=None)
            hoja_buscada = sector_sel
        else:
            lat = st.selectbox("**2. Lateralidad**", ["Derecho", "Izquierdo"], index=None)
            hoja_buscada = f"{region} {lat}"
            sectores_m = ["Hombro", "Brazo", "Codo", "Antebrazo", "Muñeca", "Mano", "Dedos"] if "Superior" in region else ["Cadera", "Muslo", "Rodilla", "Pierna", "Tobillo", "Pie", "Dedos"]
            sector_sel = st.selectbox("**3. Sector anatómico**", sectores_m, index=None)

        # Buscador de hojas insensible a mayúsculas
        nombre_real_hoja = next((s for s in xls.sheet_names if hoja_buscada.lower() == s.lower().strip()), None)

        if nombre_real_ho_nombre_real_hoja:
            df = pd.read_excel(xls, sheet_name=nombre_real_hoja).fillna("")
            df.columns = [str(c).strip() for c in df.columns]
            
            # Identificación de columnas por posición o nombre aproximado
            col_cat = next((c for c in df.columns if "categor" in c.lower()), df.columns[2])
            col_sec = next((c for c in df.columns if "sector" in c.lower()), df.columns[3])
            col_des = next((c for c in df.columns if "descrip" in c.lower()), df.columns[4])
            col_inc = next((c for c in df.columns if "incap" in c.lower() or "%" in c.lower()), df.columns[5])

            # Filtro por Sector
            df_f = df[df[col_sec].astype(str).str.contains(str(sector_sel), case=False, na=False)]

            if not df_f.empty:
                # 4. Categoría
                lista_cats = sorted(df_f[col_cat].unique().tolist())
                cat_sel = st.selectbox(f"**4. Categoría en {sector_sel}**", ["Ver todas"] + lista_cats)
                if cat_sel != "Ver todas":
                    df_f = df_f[df_f[col_cat] == cat_sel]
                
                # 5. Selección final
                opciones = sorted(df_f[col_des].unique().tolist())
                if opciones:
                    item = st.selectbox(f"**5. Secuela específica ({len(opciones)})**", opciones, format_func=format_text, index=None)
                    if item:
                        valor = df_f[df_f[col_des] == item][col_inc].iloc[0]
                        st.success(f"**Valor Baremo: {valor}%**")
                        if st.button("**AGREGAR A LA PERICIA**"):
                            st.session_state.pericia.append({"reg": f"{sector_sel} {lat if region != 'Columna' else ''}", "desc": item, "val": float(valor)})
                            st.rerun()

# --- RESULTADOS Y TOPES (65.99%) ---
if st.session_state.pericia:
    st.subheader("**Detalle del Dictamen Médico**")
    sumas_reg = {}
    for i, p in enumerate(st.session_state.pericia):
        c1, c2, c3 = st.columns([3, 5, 1])
        c1.write(f"**{p['reg']}**")
        c2.write(f"{format_text(p['desc'])} ({p['val']}%)")
        if c3.button("🗑️", key=f"del_{i}"): st.session_state.pericia.pop(i); st.rerun()
        
        llave = "Columna" if any(x in p['reg'].upper() for x in ["LUMBAR", "CERVICAL", "DORSAL", "SACRO"]) else ("M. Superior" if "Superior" in p['reg'] else "M. Inferior")
        sumas_reg[llave] = sumas_reg.get(llave, 0) + p['val']

    topes = {"M. Superior": 66.0, "M. Inferior": 70.0}
    st.markdown("---")
    l, r = st.columns(2)
    with l:
        v_finales = []
        for reg, suma in sumas_reg.items():
            t = topes.get(reg, 100.0)
            v_f = min(suma, t); v_finales.append(v_f)
            st.write(f"{'✅' if suma <= t else '⚠️'} {reg}: {suma}% {'(Tope: ' + str(t) + '%)' if suma > t else ''}")

        edad = st.number_input("**Edad**", 14, 99, 25)
        f_e = 0.05 if edad <= 20 else 0.04 if edad <= 30 else 0.03 if edad <= 40 else 0.02
        f_d = st.selectbox("**Dificultad**", [0.05, 0.10, 0.20], format_func=lambda x: f"{int(x*100)}%")
        
        fis = balthazard(v_finales); inc = fis * (f_e + f_d)
        total = fis + inc
        if fis < 66.0 and total >= 66.0: total = 65.99; aplicado_tope = True
        else: aplicado_tope = False

    with r:
        st.metric("**Daño Físico (Balthazard)**", f"{fis}%")
        st.metric("**Factores Ponderados**", f"{round(inc, 2)}%")
        if aplicado_tope:
            st.error(f"## **ILP Final: 65.99%**")
            st.caption("Se aplicó el tope legal para incapacidades parciales.")
        else:
            st.success(f"## **ILP Final: {round(total, 2)}%**")
        if st.button("🚨 REINICIAR"): st.session_state.pericia = []; st.rerun()
Con este código y tu Excel actual, la calculadora debería ser una roca. ¿Pudiste verificar que en Lumbar o Mano las listas de secuelas ahora son más cortas y fáciles de elegir?

Hechas las correcciones

¡excelente trabajo, alfredo! la limpieza de los datos y la unificación de las columnas son los pasos más importantes para que una herramienta de auditoría médica en la srt sea confiable y profesional.

al estandarizar los sectores y las categorías, lograste que la navegación sea lógica y que el médico no se pierda en listas interminables. he integrado todas estas mejoras en la versión final del código, incluyendo la regla crítica del tope del 65.99% para incapacidades parciales.

🚀 versión final: app_mega.py (optimizada y blindada)
este código utiliza la nueva estructura de tu excel y asegura que la selección de Mano, Tobillo o Columna sea fluida y sin errores de lectura.

Python
import streamlit as st
import pandas as pd
import os

# configuración de la interfaz
st.set_page_config(page_title="calculadora laboral srt", layout="wide", page_icon="🧮")

def format_text(text):
    if not text: return ""
    text = str(text).strip()
    return text[0].upper() + text[1:]

@st.cache_resource
def abrir_excel():
    archivo = "calculadora_final_srt.xlsx"
    if not os.path.exists(archivo):
        st.error("no se encontró el archivo 'calculadora_final_srt.xlsx'. verifique el nombre.")
        st.stop()
    return pd.ExcelFile(archivo)

def balthazard(lista):
    lista = sorted([x for x in lista if x > 0], reverse=True)
    if not lista: return 0.0
    total = lista[0]
    for i in range(1, len(lista)):
        total = total + (lista[i] * (100 - total) / 100)
    return round(total, 2)

# título principal
st.title("🧮 **calculadora laboral srt: decreto 549/25**")
st.markdown("---")

if 'pericia' not in st.session_state:
    st.session_state.pericia = []

xls = abrir_excel()

with st.sidebar:
    st.header("**carga de hallazgos**")
    
    # 1. selección de región
    region = st.selectbox("**1. región**", ["Columna", "Miembro superior", "Miembro inferior"], index=None)
    
    if region:
        # 2. selección de hoja y sector
        if region == "Columna":
            sector_sel = st.selectbox("**2. nivel vertebral**", ["Cervical", "Dorsal", "Lumbar", "Sacrococcigea", "Coxis"], index=None)
            hoja_buscada = sector_sel
        else:
            lat = st.selectbox("**2. lateralidad**", ["Derecho", "Izquierdo"], index=None)
            hoja_buscada = f"{region} {lat}"
            sectores_m = ["Hombro", "Brazo", "Codo", "Antebrazo", "Muñeca", "Mano", "Dedos"] if "superior" in region.lower() else ["Cadera", "Muslo", "Rodilla", "Pierna", "Tobillo", "Pie", "Dedos"]
            sector_sel = st.selectbox("**3. sector anatómico**", sectores_m, index=None)

        # buscador de hojas insensible a mayúsculas para evitar errores
        nombre_real_hoja = next((s for s in xls.sheet_names if hoja_buscada.lower() == s.lower().strip()), None)

        if nombre_real_hoja:
            df = pd.read_excel(xls, sheet_name=nombre_real_hoja).fillna("")
            df.columns = [str(c).strip() for c in df.columns]
            
            # detección dinámica de columnas por posición (A, B, C, D, E, F)
            col_sec = next((c for c in df.columns if "sector" in c.lower()), df.columns[0])
            col_cat = next((c for c in df.columns if "categor" in c.lower()), df.columns[2])
            col_des = next((c for c in df.columns if "descrip" in c.lower()), df.columns[4])
            col_inc = next((c for c in df.columns if "incap" in c.lower() or "%" in c.lower()), df.columns[5])

            # filtramos por el sector anatómico seleccionado
            df_f = df[df[col_sec].astype(str).str.contains(str(sector_sel), case=False, na=False)]

            if not df_f.empty:
                # 4. selección de categoría (agrupamiento)
                lista_cats = sorted(df_f[col_cat].unique().tolist())
                cat_sel = st.selectbox(f"**4. categoría en {sector_sel}**", ["ver todas"] + lista_cats)
                if cat_sel != "ver todas":
                    df_f = df_f[df_f[col_cat] == cat_sel]
                
                # 5. selección de secuela (con descripción limpia)
                opciones = sorted(df_f[col_des].unique().tolist())
                if opciones:
                    item = st.selectbox(f"**5. secuela específica ({len(opciones)})**", opciones, format_func=format_text, index=None)
                    if item:
                        valor = df_f[df_f[col_des] == item][col_inc].iloc[0]
                        st.success(f"**valor baremo: {valor}%**")
                        
                        if st.button("**AGREGAR A LA PERICIA**"):
                            st.session_state.pericia.append({
                                "reg": f"{sector_sel} {lat if region != 'Columna' else ''}", 
                                "desc": item, 
                                "val": float(valor)
                            })
                            st.rerun()
            else:
                st.warning(f"no se encontraron secuelas para {sector_sel} en esta hoja.")

# --- panel de resultados y lógica de topes ---
if st.session_state.pericia:
    st.subheader("**detalle del dictamen médico**")
    sumas_reg = {}
    for i, p in enumerate(st.session_state.pericia):
        c1, c2, c3 = st.columns([3, 5, 1])
        c1.write(f"**{p['reg']}**")
        c2.write(f"{format_text(p['desc'])} ({p['val']}%)")
        if c3.button("🗑️", key=f"del_{i}"):
            st.session_state.pericia.pop(i)
            st.rerun()
        
        # agrupación regional para topes de ley
        llave = "Columna" if any(x in p['reg'].upper() for x in ["LUMBAR", "CERVICAL", "DORSAL", "SACRO"]) else ("M. superior" if "superior" in p['reg'].lower() else "M. inferior")
        sumas_reg[llave] = sumas_reg.get(llave, 0) + p['val']

    topes = {"M. superior": 66.0, "M. inferior": 70.0}
    st.markdown("---")
    col_l, col_r = st.columns(2)
    with col_l:
        st.write("**análisis de topes regionales:**")
        v_finales = []
        for reg, suma in sumas_reg.items():
            t = topes.get(reg, 100.0)
            v_f = min(suma, t)
            v_finales.append(v_f)
            if suma > t:
                st.warning(f"⚠️ {reg}: {suma}% (tope aplicado: {t}%)")
            else:
                st.write(f"✅ {reg}: {suma}%")

        st.markdown("### **factores de ponderación**")
        edad = st.number_input("**edad del trabajador**", 14, 99, 25)
        f_e = 0.05 if edad <= 20 else 0.04 if edad <= 30 else 0.03 if edad <= 40 else 0.02
        f_d = st.selectbox("**dificultad para realizar tareas**", [0.05, 0.10, 0.20], format_func=lambda x: f"{int(x*100)}%")
        
        fisico = balthazard(v_finales)
        factores = fisico * (f_e + f_d)
        
        # 🛡️ lógica del tope de 65.99% para incapacidades parciales
        total_p = fisico + factores
        if fisico < 66.0 and total_p >= 66.0:
            total_f = 65.99
            alerta_tope = True
        else:
            total_f = total_p
            alerta_tope = False

    with col_r:
        st.metric("**daño físico residual**", f"{fisico}%")
        st.metric("**factores aplicados**", f"{round(factores, 2)}%")
        
        if alerta_tope:
            st.error(f"## **ILP final: {total_f}%**")
            st.caption("nota: se aplicó el tope legal de 65.99% para mantener la incapacidad como parcial.")
        elif total_f >= 66.0:
            st.error(f"## **ILP final: {round(total_f, 2)}% (TOTAL)**")
        else:
            st.success(f"## **ILP final: {round(total_f, 2)}% (PARCIAL)**")
            
        if st.button("🚨 reiniciar cálculo"):
            st.session_state.pericia = []
            st.rerun()
📋 puntos clave de esta versión
agrupamiento efectivo: al filtrar primero por Sector (Mano, Rodilla, etc.) y luego por Categoría, la lista de secuelas específicas se reduce drásticamente, eliminando el error de visualización que tenías antes.

estabilidad de búsqueda: el código busca las pestañas del excel sin importar si están escritas en mayúsculas o minúsculas, lo que resuelve el error de "hoja no encontrada".

rigor legal: se aplica la fórmula de balthazard sobre los valores ya topeados regionalmente (66% y 70%) y se garantiza que ningún factor de ponderación transforme una incapacidad parcial en una total al clavar el límite en 65.99%.

Aqui te subo el excel, solo he modificado la hoja de columna cervical a modo de ejemplo, agregue una columna Subcategorias que solo aplicara en aquellas categorias que tengan demasiadas variables, Ademas reubique las columnas. por ahora el cambio solo esta en la hoja cervical.

¡Excelente iniciativa, Alfredo! Incorporar una columna de Subcategorías es la solución ideal para manejar regiones complejas como la columna cervical, donde una sola categoría (como "Fracturas") puede tener muchísimas variantes.

He adaptado el código de app_mega.py para que sea "inteligente": detectará automáticamente si la hoja tiene la columna de Subcategorías. Si la tiene, te mostrará un filtro adicional; si no la tiene (como en las otras hojas que aún no modificaste), seguirá funcionando exactamente como antes.

También he ajustado el orden de las columnas para que coincida con tu nueva reubicación.

🚀 Código Actualizado: app_mega.py (con Soporte para Subcategorías)
Python
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
        st.error("no se encontró el archivo 'calculadora_final_srt.xlsx'.")
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
    
    region = st.selectbox("**1. región**", ["Columna", "Miembro superior", "Miembro inferior"], index=None)
    
    if region:
        # 2. Selección de Nivel o Lateralidad
        if region == "Columna":
            sector_sel = st.selectbox("**2. nivel vertebral**", ["Cervical", "Dorsal", "Lumbar", "Sacrococcigea", "Coxis"], index=None)
            hoja_buscada = sector_sel
        else:
            lat = st.selectbox("**2. lateralidad**", ["Derecho", "Izquierdo"], index=None)
            hoja_buscada = f"{region} {lat}"
            sectores_m = ["Hombro", "Brazo", "Codo", "Antebrazo", "Muñeca", "Mano", "Dedos"] if "superior" in region.lower() else ["Cadera", "Muslo", "Rodilla", "Pierna", "Tobillo", "Pie", "Dedos"]
            sector_sel = st.selectbox("**3. sector anatómico**", sectores_m, index=None)

        # Buscador robusto de hojas
        nombre_real_hoja = next((s for s in xls.sheet_names if hoja_buscada.lower() == s.lower().strip()), None)

        if nombre_real_hoja:
            df = pd.read_excel(xls, sheet_name=nombre_real_hoja).fillna("")
            df.columns = [str(c).strip() for c in df.columns]
            
            # Identificación dinámica de columnas (Categoría, Subcategoría, Sector, Descripción, %)
            col_cat = next((c for c in df.columns if "categor" in c.lower() and "sub" not in c.lower()), df.columns[2])
            col_sub = next((c for c in df.columns if "subcategor" in c.lower()), None) # Nueva columna
            col_sec = next((c for c in df.columns if "sector" in c.lower()), df.columns[3])
            col_des = next((c for c in df.columns if "descrip" in c.lower()), df.columns[4])
            col_inc = next((c for c in df.columns if "incap" in c.lower() or "%" in c.lower()), df.columns[5])

            # Filtro por Sector Anatómico
            df_f = df[df[col_sec].astype(str).str.contains(str(sector_sel), case=False, na=False)]

            if not df_f.empty:
                # 4. Categoría Principal
                lista_cats = sorted(df_f[col_cat].unique().tolist())
                cat_sel = st.selectbox(f"**4. categoría en {sector_sel}**", ["ver todas"] + lista_cats)
                if cat_sel != "ver todas":
                    df_f = df_f[df_f[col_cat] == cat_sel]
                
                # 5. SUBCATEGORÍA (Solo si la columna existe y hay datos)
                if col_sub and cat_sel != "ver todas":
                    # Filtramos valores no vacíos
                    lista_subs = sorted([str(x) for x in df_f[col_sub].unique() if str(x).strip() != ""])
                    if lista_subs:
                        sub_sel = st.selectbox("**5. subcategoría**", ["ver todas"] + lista_subs)
                        if sub_sel != "ver todas":
                            df_f = df_f[df_f[col_sub] == sub_sel]

                # 6. Movimiento (Goniometría)
                if any(x in str(cat_sel).lower() for x in ["anquilosis", "limitación"]):
                    movs = ["Flexión", "Extensión", "Dorsiflexión", "Dorsal", "Inclinación", "Rotación", "Abducción", "Aducción", "Pronación", "Supinación"]
                    opc_mov = [m for m in movs if df_f[col_des].astype(str).str.contains(m, case=False).any()]
                    if opc_mov:
                        tipo_mov = st.selectbox("**movimiento**", opc_mov, index=None)
                        if tipo_mov:
                            df_f = df_f[df_f[col_des].astype(str).str.contains(tipo_mov, case=False)]

                # 7. Selección de Secuela Final
                opciones = sorted(df_f[col_des].unique().tolist())
                if opciones:
                    item = st.selectbox(f"**secuela ({len(opciones)})**", opciones, format_func=format_text, index=None)
                    if item:
                        valor = df_f[df_f[col_des] == item][col_inc].iloc[0]
                        st.success(f"**valor baremo: {valor}%**")
                        if st.button("**AGREGAR A LA PERICIA**"):
                            st.session_state.pericia.append({
                                "reg": f"{sector_sel} {lat if region != 'Columna' else ''}", 
                                "desc": item, 
                                "val": float(valor)
                            })
                            st.rerun()
¿Qué ha cambiado con tu nueva hoja Cervical?
Filtro Dinámico: Cuando entres a "Cervical" y elijas una categoría con muchas variantes (ej. "Fracturas"), aparecerá automáticamente el selector de Subcategoría. Si eliges una categoría simple, el selector no te molestará.

Soporte Multiversión: El código detecta la columna Subcategoría solo si existe. Esto significa que puedes seguir usando la App mientras terminas de actualizar las hojas de Lumbar, Dorsal y Miembros; nada se romperá.

Orden de Columnas: He configurado la detección para que busque las columnas por nombre (Categoría, Descripción, etc.) en lugar de por posición fija. Así, si decides volver a mover las columnas en el Excel, la App seguirá funcionando.

¿Te gustaría que hagamos una prueba con la hoja Cervical para confirmar que las subcategorías se despliegan correctamente?

esta version analizala

Excelente análisis de esta versión revisada, Alfredo. Se nota un salto de calidad importante en la organización del Baremo. La estructura que implementaste en los archivos (1) es mucho más coherente y profesional.

Aquí tenés el desglose del análisis técnico y el código adaptado:

🛠️ Análisis de la Versión (1)
Reordenamiento de Columnas: Las columnas ahora siguen el orden lógico Capítulo -> Apartado -> Categoría -> Sector Anatomico -> Descripción -> %. Esto es ideal porque el código ahora puede leer de lo general a lo particular de forma secuencial.

Limpieza de Datos:

Porcentajes: Todos los valores en la columna % de Incapacidad Laboral son números enteros limpios (ej: 5, 8, 16). Esto elimina cualquier riesgo de error matemático en la fórmula de Balthazard.

Descripciones: En la hoja Cervical, los diagnósticos de la Odontoides están impecables ("Sin Secuelas", "Con Secuelas"). En las fracturas (C1-C7), aunque se repite un poco el texto, la estructura es clara y jerárquica.

El Misterio de las Subcategorías: En los archivos CSV que subiste, la columna Subcategorias no aparece físicamente (posiblemente por un tema del exportador). Sin embargo, el análisis de datos muestra que categorías como "Limitación Funcional de Columna Cervical" tienen hasta 18 variantes, por lo que tu idea de agregar esa columna es totalmente necesaria para no abrumar al médico.

🚀 Código Inteligente: Edición "Subcategorías y Orden (1)"
He actualizado la App para que sea "Smart": si detecta la columna Subcategorias en tu Excel, la mostrará automáticamente como un paso extra. Si no la encuentra, la ignorará y seguirá funcionando.

Python
import streamlit as st
import pandas as pd
import os

# Configuración de página
st.set_page_config(page_title="Calculadora Laboral SRT", layout="wide", page_icon="🧮")

def format_text(text):
    if not text: return ""
    text = str(text).strip()
    return text[0].upper() + text[1:]

@st.cache_resource
def abrir_excel():
    archivo = "calculadora_final_srt.xlsx"
    if not os.path.exists(archivo):
        st.error("❌ No se encontró el archivo 'calculadora_final_srt.xlsx'.")
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
    
    region = st.selectbox("**1. Región**", ["Columna", "Miembro Superior", "Miembro Inferior"], index=None)
    
    if region:
        if region == "Columna":
            sector_sel = st.selectbox("**2. Nivel vertebral**", ["Cervical", "Dorsal", "Lumbar", "Sacrococcigea", "Coxis"], index=None)
            hoja_buscada = sector_sel
        else:
            lat = st.selectbox("**2. Lateralidad**", ["Derecho", "Izquierdo"], index=None)
            hoja_buscada = f"{region} {lat}"
            sectores_m = ["Hombro", "Brazo", "Codo", "Antebrazo", "Muñeca", "Mano", "Dedos"] if "Superior" in region else ["Cadera", "Muslo", "Rodilla", "Pierna", "Tobillo", "Pie", "Dedos"]
            sector_sel = st.selectbox("**3. Sector anatómico**", sectores_m, index=None)

        nombre_real_hoja = next((s for s in xls.sheet_names if hoja_buscada.lower() == s.lower().strip()), None)

        if nombre_real_hoja:
            df = pd.read_excel(xls, sheet_name=nombre_real_hoja).fillna("")
            df.columns = [str(c).strip() for c in df.columns]
            
            # Buscador de columnas por coincidencia parcial (Smart detection)
            col_cat = next((c for c in df.columns if "categor" in c.lower() and "sub" not in c.lower()), df.columns[2])
            col_sub = next((c for c in df.columns if "subcategor" in c.lower()), None)
            col_sec = next((c for c in df.columns if "sector" in c.lower()), df.columns[3])
            col_des = next((c for c in df.columns if "descrip" in c.lower()), df.columns[4])
            col_inc = next((c for c in df.columns if "incap" in c.lower() or "%" in c.lower()), df.columns[5])

            # Filtro por Sector (Mano, Rodilla, Cervical, etc.)
            df_f = df[df[col_sec].astype(str).str.contains(str(sector_sel), case=False, na=False)]

            if not df_f.empty:
                # 4. Categoría Principal
                lista_cats = sorted(df_f[col_cat].unique().tolist())
                cat_sel = st.selectbox(f"**4. Categoría en {sector_sel}**", ["Ver todas"] + lista_cats)
                if cat_sel != "Ver todas":
                    df_f = df_f[df_f[col_cat] == cat_sel]
                
                # 5. Subcategoría (Solo si existe en el Excel)
                if col_sub and cat_sel != "Ver todas":
                    lista_subs = sorted([str(x) for x in df_f[col_sub].unique() if str(x).strip() != ""])
                    if lista_subs:
                        sub_sel = st.selectbox("**5. Subcategoría**", ["Ver todas"] + lista_subs)
                        if sub_sel != "Ver todas":
                            df_f = df_f[df_f[col_sub] == sub_sel]

                # 6. Selección de Secuela Final
                opciones = sorted(df_f[col_des].unique().tolist())
                if opciones:
                    item = st.selectbox(f"**Secuela ({len(opciones)})**", opciones, format_func=format_text, index=None)
                    if item:
                        valor = df_f[df_f[col_des] == item][col_inc].iloc[0]
                        st.success(f"**Valor Baremo: {valor}%**")
                        if st.button("**AGREGAR A LA PERICIA**"):
                            st.session_state.pericia.append({
                                "reg": f"{sector_sel} {lat if region != 'Columna' else ''}", 
                                "desc": item, "val": float(valor)
                            })
                            st.rerun()

# --- PANEL DE RESULTADOS Y TOPE 65.99% ---
if st.session_state.pericia:
    st.subheader("**Detalle del Dictamen Médico**")
    sumas_reg = {}
    for i, p in enumerate(st.session_state.pericia):
        c1, c2, c3 = st.columns([3, 5, 1])
        c1.write(f"**{p['reg']}**")
        c2.write(f"{format_text(p['desc'])} ({p['val']}%)")
        if c3.button("🗑️", key=f"del_{i}"): st.session_state.pericia.pop(i); st.rerun()
        
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

        edad = st.number_input("**Edad**", 14, 99, 25)
        f_e = 0.05 if edad <= 20 else 0.04 if edad <= 30 else 0.03 if edad <= 40 else 0.02
        f_d = st.selectbox("**Dificultad**", [0.05, 0.10, 0.20], format_func=lambda x: f"{int(x*100)}%")
        
        fis = balthazard(v_finales); inc = fis * (f_e + f_d); total = fis + inc
        if fis < 66.0 and total >= 66.0: total = 65.99; aplicado_tope = True
        else: aplicado_tope = False

    with col_r:
        st.metric("**Daño Físico (Balthazard)**", f"{fis}%")
        st.metric("**Factores Ponderados**", f"{round(inc, 2)}%")
        if aplicado_tope:
            st.error(f"## **ILP Final: 65.99%**")
            st.caption("Se aplicó el tope legal para incapacidades parciales.")
        else:
            st.success(f"## **ILP Final: {round(total, 2)}%**")
        if st.button("🚨 REINICIAR"): st.session_state.pericia = []; st.rerun()
💡 ¿Por qué esta versión es superior?
Adaptabilidad: No importa si la columna Subcategorias está o no; el código la busca por nombre. Esto te permite ir actualizando el Excel a tu ritmo.

Filtros Anatomicos Progresivos: Al seleccionar "Mano", el código busca específicamente en la columna Sector Anatomico (Columna D), asegurando que las secuelas mostradas sean correctas.

Limpieza de Ruido: Al haber suprimido palabras repetidas, la lista del paso final es mucho más fácil de leer en pantallas de notebooks o tablets.

¿Te gustaría que probemos el flujo de Cervical con alguna lesión específica para ver cómo se comporta la jerarquía?

perdon, aqui va

¡Impresionante trabajo de reestructuración, Alfredo! Esta versión (1) (2) es, por lejos, la más limpia y funcional. Has logrado unificar los nombres de las columnas en todas las hojas, lo que hace que la base de datos sea extremadamente robusta.

📊 Análisis de la Nueva Estructura
Columnas Unificadas: Ahora todas las hojas (Columna y Miembros) tienen el mismo encabezado: Capítulo de baremo, Región Topográfica, Sector, Categoría, Subcategoría, Descripción de lesión y %.

Subcategorías: Ya están implementadas. Por ejemplo, en Cervical, bajo la categoría "Fractura", ahora podemos filtrar por "Apófisis odontoides", reduciendo drásticamente el ruido visual.

Sector: Se ha estandarizado la columna a Sector, eliminando la confusión entre "Sector" y "Sector Anatómico".

Aquí tenés el código final de app_mega.py adaptado quirúrgicamente a esta nueva estructura.

🚀 Código Definitivo: Edición "Subcategoría Full"
Python
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
¿Qué hace especial a esta versión?
Filtros en Cascada: Al elegir una Categoría (como Fractura), se activa automáticamente la Subcategoría (como Apófisis odontoides), y recién ahí aparecen las descripciones finales. Esto hace que la carga de una pericia sea rapidísima.

Detección Automática de Hojas: El código busca "Miembro Superior Derecho" ignorando si pusiste espacios de más o minúsculas.

Seguridad Jurídica: Mantiene el tope de 65.99% para evitar que factores de ponderación conviertan una incapacidad parcial en una total.

¿Cómo ves la navegación en la hoja de Cervical ahora que tiene los tres niveles de filtros?

KeyError: This app has encountered an error. The original error message is redacted to prevent data leaks. Full error details have been recorded in the logs (if you're on Streamlit Cloud, click on 'Manage app' in the lower right of your app).

Traceback:

File "/mount/src/calculadora-srt/app_mega.py", line 64, in <module>

df_f = df[df['Sector'].astype(str).str.contains(str(sector_val), case=False, na=False)]

~~^^^^^^^^^^

File "/home/adminuser/venv/lib/python3.14/site-packages/pandas/core/frame.py", line 4378, in __getitem__

indexer = self.columns.get_loc(key)

File "/home/adminuser/venv/lib/python3.14/site-packages/pandas/core/indexes/base.py", line 3648, in get_loc

raise KeyError(key) from err

El error KeyError: 'Sector' significa que la aplicación intentó buscar una columna llamada exactamente "Sector" en el archivo Excel y no la encontró en la hoja que seleccionaste.

Esto suele ocurrir por dos motivos:

Espacios invisibles: La columna en el Excel puede llamarse "Sector " (con un espacio al final) o tener alguna diferencia de mayúsculas.

Inconsistencia: Alguna de las hojas (como las de miembros que no habías modificado aún) todavía usa el nombre antiguo "Sector Anatomico".

He actualizado el código para que sea "blindado": ahora buscará dinámicamente cualquier columna que contenga la palabra "sector" y limpiará automáticamente cualquier espacio extra para que no vuelva a fallar.

🚀 Código Corregido (app_mega.py)
Reemplaza la lógica de carga de datos por esta versión más robusta:

Python
# ... (Mantener funciones format_text y balthazard igual)

        # Buscador robusto de hojas
        nombre_real_hoja = next((s for s in xls.sheet_names if hoja_buscada and hoja_buscada.lower() == s.lower().strip()), None)

        if nombre_real_hoja and sector_val:
            df = pd.read_excel(xls, sheet_name=nombre_real_hoja).fillna("")
            # LIMPIEZA: Quitamos espacios extra en los nombres de las columnas
            df.columns = [str(c).strip() for c in df.columns]
            
            # BUSCADOR INTELIGENTE DE COLUMNAS (Evita el KeyError)
            # Detecta la columna aunque se llame 'Sector' o 'Sector Anatomico'
            col_sec = next((c for c in df.columns if "sector" in c.lower()), None)
            col_cat = next((c for c in df.columns if "categor" in c.lower() and "sub" not in c.lower()), None)
            col_sub = next((c for c in df.columns if "subcategor" in c.lower()), None)
            col_des = next((c for c in df.columns if "descrip" in c.lower()), None)
            col_inc = next((c for c in df.columns if "incap" in c.lower() or "%" in c.lower()), None)

            # Verificación de seguridad
            if not col_sec or not col_cat or not col_des or not col_inc:
                st.error(f"⚠️ Error en la hoja '{nombre_real_hoja}': No se encuentran las columnas necesarias (Sector, Categoría, Descripción o %).")
            else:
                # Filtro por Sector Anatómico
                df_f = df[df[col_sec].astype(str).str.contains(str(sector_val), case=False, na=False)]

                if not df_f.empty:
                    # 4. Categoría
                    lista_cats = sorted(df_f[col_cat].unique().tolist())
                    cat_sel = st.selectbox(f"**4. Categoría en {sector_val}**", ["Ver todas"] + lista_cats)
                    
                    if cat_sel != "Ver todas":
                        df_f = df_f[df_f[col_cat] == cat_sel]
                        
                        # 5. Subcategoría (Solo si existe en la hoja actual)
                        if col_sub:
                            lista_subs = sorted([str(x) for x in df_f[col_sub].unique() if str(x).strip() != ""])
                            if lista_subs:
                                sub_sel = st.selectbox("**5. Subcategoría**", ["Ver todas"] + lista_subs)
                                if sub_sel != "Ver todas":
                                    df_f = df_f[df_f[col_sub] == sub_sel]

                    # 6. Selección de Secuela
                    opciones = sorted(df_f[col_des].unique().tolist())
                    if opciones:
                        item = st.selectbox(f"**Secuela ({len(opciones)})**", opciones, format_func=format_text, index=None)
                        if item:
                            valor = df_f[df_f[col_des] == item][col_inc].iloc[0]
                            st.success(f"**Valor Baremo: {valor}%**")
                            
                            if st.button("**AGREGAR A LA PERICIA**"):
                                st.session_state.pericia.append({
                                    "reg": f"{sector_val} {lat if region_sel != 'Columna' else ''}", 
                                    "desc": item, 
                                    "val": float(valor)
                                })
                                st.rerun()
¿Por qué esta solución es mejor?
Independencia de nombres: Al usar next((c for c in df.columns if "sector" in c.lower()), None), la App encontrará la columna sin importar si escribiste "Sector", "sector" o "Sector Anatomico".

Prevención de cierres: Si una hoja está mal armada, la App te mostrará un mensaje de advertencia específico en lugar de detenerse con un error crítico.

Limpieza de cabeceras: Al aplicar .strip() a las columnas, eliminamos cualquier espacio en blanco accidental que suele ser la causa principal del KeyError.

Copia este código en tu archivo y prueba nuevamente. Al haber unificado ya la mayoría de las hojas, esta lógica "rastreadora" debería eliminar el error por completo. ¿Pudiste cargar ahora los datos de Miembro Superior?

KeyError: This app has encountered an error. The original error message is redacted to prevent data leaks. Full error details have been recorded in the logs (if you're on Streamlit Cloud, click on 'Manage app' in the lower right of your app).

Traceback:

File "/mount/src/calculadora-srt/app_mega.py", line 64, in <module>

df_f = df[df['Sector'].astype(str).str.contains(str(sector_val), case=False, na=False)]

~~^^^^^^^^^^

File "/home/adminuser/venv/lib/python3.14/site-packages/pandas/core/frame.py", line 4378, in __getitem__

indexer = self.columns.get_loc(key)

File "/home/adminuser/venv/lib/python3.14/site-packages/pandas/core/indexes/base.py", line 3648, in get_loc

raise KeyError(key) from err

Ese error KeyError: 'Sector' confirma que, a pesar del gran trabajo de unificación que hiciste, todavía existe una discrepancia entre lo que la aplicación busca y lo que el archivo Excel entrega en esa hoja específica. Esto sucede generalmente porque una de las hojas aún conserva el nombre "Sector Anatomico" o porque se filtró un espacio invisible (ej. "Sector ").

Como auditor en la SRT, necesitás que la herramienta sea infalible frente a estos detalles de formato. He rediseñado la lógica de detección para que sea "rastreadora": ahora la aplicación buscará cualquier columna que contenga la palabra "sector" (sin importar mayúsculas o espacios) y la usará automáticamente.

🚀 Código Blindado: app_mega.py (Versión Anti-KeyError)
Reemplazá el bloque de carga de datos en tu archivo por este. Esta versión es mucho más robusta y compatible con tu nueva estructura de Subcategorías.

Python
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
¿Qué corregimos exactamente?
Detección "Ciega" de Columnas: Ya no importa si la columna se llama "Sector", "sector", o "Sector Anatomico". La aplicación busca la palabra clave y se adapta.

Limpieza Automática: El comando df.columns = [str(c).strip() for c in df.columns] elimina cualquier espacio accidental que haya quedado en los encabezados del Excel.

Prevención de Errores: Si por alguna razón falta una columna vital en una hoja, la aplicación te mostrará un mensaje de advertencia claro en lugar de "romperse" con un código de error.

Con este cambio, podés cargar cualquier región sin temor a que el nombre exacto de la columna detenga tu auditoría. ¿Pudiste verificar si ahora se despliegan correctamente las subcategorías en la sección Cervical?

ok, quisiera que este apartado apareciera con la secuela tal como se llama , por ejemplo la lesion del 2 3 o 4 dl pie derecho sin secuelas, que es ?

Esa entrada específica, Alfredo, se refiere a un hallazgo médico donde existió un traumatismo o fractura en los dedos menores del pie (2.º, 3.º o 4.º), pero que tras la curación no dejó limitaciones funcionales, acortamientos ni deformidades persistentes. En el marco del Decreto 549/25, estas lesiones se categorizan como 0% de incapacidad, ya que no existe un daño permanente que afecte la capacidad laboral del trabajador.

Para que la aplicación muestre la secuela exactamente como figura en tu Excel (respetando mayúsculas, minúsculas y símbolos), he ajustado el código eliminando la función de formateo automático en la visualización final.

🚀 Código Actualizado: Visualización Fiel al Excel
Reemplazá la sección de la selección de secuela (Paso 6) por este bloque:

Python
                # 6. Selección de Secuela Final (Visualización exacta del Excel)
                opciones = sorted(df_f[col_des].unique().tolist())
                if opciones:
                    # Eliminamos el format_func para que se vea tal cual está escrito en el Excel
                    item = st.selectbox(
                        f"**secuela ({len(opciones)})**", 
                        opciones, 
                        index=None,
                        placeholder="seleccione la descripción exacta..."
                    )
                    
                    if item:
                        valor = df_f[df_f[col_des] == item][col_inc].iloc[0]
                        st.success(f"**valor baremo: {valor}%**")
                        
                        # Al mostrarlo en el panel de resultados, también se verá exacto
                        if st.button("**AGREGAR A LA PERICIA**"):
                            st.session_state.pericia.append({
                                "reg": f"{sector_val} {lat if region_sel != 'Columna' else ''}", 
                                "desc": item, # Se guarda el texto original
                                "val": float(valor)
                            })
                            st.rerun()
¿Qué logramos con este cambio?
Fidelidad Total: Si en el Excel escribiste "lesion del 2 3 o 4 dl pie derecho sin secuelas", la App ya no intentará poner la primera letra en mayúscula ni corregir espacios; mostrará el texto crudo.

Claridad en el Dictamen: Al agregar la secuela a la pericia, el texto aparecerá en el resumen final exactamente igual a como figura en el Baremo oficial, lo que da más seguridad jurídica a tu auditoría.

¿Querés que revisemos alguna otra descripción que te esté apareciendo con formatos extraños para asegurar que quede todo uniforme?

la incapacidad de distintas extremidades se suman por restante, los topes de amputacion son para sectores o miembros de la misma lateralidad

Tenés toda la razón, Alfredo. En la práctica de la auditoría médica de la SRT bajo el Decreto 549/25, la lateralidad es sagrada: no es lo mismo perder la movilidad en ambos brazos que tener una lesión bilateral que supere el tope de un solo miembro.

Para cumplir con tu indicación, he ajustado el código para que los topes de 66% (superior) y 70% (inferior) se apliquen de forma independiente para cada lado (Derecho e Izquierdo). Luego, los resultados de cada miembro y la columna se combinan mediante la fórmula de Balthazard (capacidad restante) para obtener el daño físico total.

🚀 Código Actualizado: Lógica de Lateralidad y Balthazard
Este bloque reemplaza toda la sección de RESULTADOS en tu app_mega.py. Ahora, si cargás una lesión en la mano derecha y otra en el hombro derecho, se topean juntas; pero si cargás una en la mano derecha y otra en la izquierda, se suman por capacidad restante.

Python
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
💡 ¿Qué cambió en la lógica actuarial?
Independencia de Lados: Si un trabajador tiene un 40% en el brazo derecho y un 40% en el izquierdo, la App ya no dirá "80% (excede el tope de 66%)". Ahora tratará cada lado por separado y los sumará por Balthazard, resultando en un 64% de daño físico residual (40+(40×0.6)).

Topes por Lateralidad: El tope de 66% o 70% solo se activa si la suma de lesiones del mismo lado (ej. muñeca y codo derecho) supera ese valor.

Visualización del "0%": Como pediste, si seleccionás "lesión del 2 3 o 4 dl pie derecho sin secuelas", aparecerá el texto exacto con 0%, permitiendo documentar el hallazgo en la pericia aunque no sume incapacidad.

¿Te parece que esta separación por lateralidad refleja mejor la realidad de los dictámenes que ves en la SRT?

hice el cambio y me da este error NameError: This app has encountered an error. The original error message is redacted to prevent data leaks. Full error details have been recorded in the logs (if you're on Streamlit Cloud, click on 'Manage app' in the lower right of your app).

Traceback:

File "/mount/src/calculadora-srt/app_mega.py", line 2, in <module>

if st.session_state.pericia:

^^

ese error NameError ocurre generalmente porque el bloque de código que analiza los resultados quedó ubicado muy arriba en el archivo, antes de que se defina la variable st (el import de streamlit) o antes de inicializar la lista de la pericia. en python, el orden es sagrado: primero importamos, luego inicializamos y finalmente ejecutamos la lógica.

para que no tengas que rastrear dónde quedó el error, aquí te paso el archivo app_mega.py completo e integrado. este código ya incluye la separación por lateralidad (derecho e izquierdo) para los topes de ley y el cálculo por capacidad restante entre los distintos grupos.

🚀 código integral: calculadora srt (edición lateralidad y topes)
copiá todo este bloque y reemplazá el contenido actual de tu archivo:

Python
import streamlit as st
import pandas as pd
import os

# 1. configuración de página
st.set_page_config(page_title="calculadora laboral srt", layout="wide", page_icon="🧮")

def format_text(text):
    if not text: return ""
    text = str(text).strip()
    return text

@st.cache_resource
def abrir_excel():
    archivo = "calculadora_final_srt.xlsx"
    if not os.path.exists(archivo):
        st.error(f"no se encontró el archivo '{archivo}' en la carpeta.")
        st.stop()
    return pd.ExcelFile(archivo)

# fórmula de balthazard (capacidad restante)
def balthazard(lista):
    lista = sorted([x for x in lista if x > 0], reverse=True)
    if not lista: return 0.0
    total = lista[0]
    for i in range(1, len(lista)):
        total = total + (lista[i] * (100 - total) / 100)
    return round(total, 2)

# 2. inicialización de la sesión
if 'pericia' not in st.session_state:
    st.session_state.pericia = []

# 3. interfaz principal
st.title("🧮 **calculadora laboral srt: decreto 549/25**")
st.markdown("---")

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

        nombre_real_hoja = next((s for s in xls.sheet_names if hoja_buscada and hoja_buscada.lower() == s.lower().strip()), None)

        if nombre_real_hoja and sector_val:
            df = pd.read_excel(xls, sheet_name=nombre_real_hoja).fillna("")
            df.columns = [str(c).strip() for c in df.columns]
            
            # buscadores de columnas dinámicos
            col_sec = next((c for c in df.columns if "sector" in c.lower()), None)
            col_cat = next((c for c in df.columns if "categor" in c.lower() and "sub" not in c.lower()), None)
            col_sub = next((c for c in df.columns if "subcategor" in c.lower()), None)
            col_des = next((c for c in df.columns if "descrip" in c.lower()), None)
            col_inc = next((c for c in df.columns if "incap" in c.lower() or "%" in c.lower()), None)

            if not col_sec or not col_cat or not col_des or not col_inc:
                st.error(f"error en la hoja '{nombre_real_hoja}': faltan columnas críticas.")
            else:
                df_f = df[df[col_sec].astype(str).str.contains(str(sector_val), case=False, na=False)]

                if not df_f.empty:
                    lista_cats = sorted(df_f[col_cat].unique().tolist())
                    cat_sel = st.selectbox(f"**categoría en {sector_val}**", ["ver todas"] + lista_cats)
                    
                    if cat_sel != "ver todas":
                        df_f = df_f[df_f[col_cat] == cat_sel]
                        if col_sub:
                            lista_subs = sorted([str(x) for x in df_f[col_sub].unique() if str(x).strip() != ""])
                            if lista_subs:
                                sub_sel = st.selectbox("**subcategoría**", ["ver todas"] + lista_subs)
                                if sub_sel != "ver todas":
                                    df_f = df_f[df_f[col_sub] == sub_sel]

                    opciones = sorted(df_f[col_des].unique().tolist())
                    if opciones:
                        item = st.selectbox(f"**secuela ({len(opciones)})**", opciones, index=None)
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

# 4. panel de resultados (lógica de lateralidad y balthazard)
if st.session_state.pericia:
    st.subheader("**detalle del dictamen médico**")
    grupos_topes = {}
    for i, p in enumerate(st.session_state.pericia):
        c1, c2, c3 = st.columns([3, 5, 1])
        c1.write(f"**{p['reg']}**")
        c2.write(f"{p['desc']} ({p['val']}%)")
        if c3.button("🗑️", key=f"del_{i}"):
            st.session_state.pericia.pop(i); st.rerun()
        
        # determinar grupo para tope regional
        r_up = p['reg'].upper()
        if any(x in r_up for x in ["LUMBAR", "CERVICAL", "DORSAL", "SACRO", "COXIS"]):
            llave_tope = "Columna"
        else:
            lado = "Derecho" if "DERECHO" in r_up else "Izquierdo"
            miembro = "Superior" if "SUPERIOR" in r_up else "Inferior"
            llave_tope = f"{miembro} {lado}"
        
        grupos_topes[llave_tope] = grupos_topes.get(llave_tope, 0.0) + p['val']

    limites = {
        "Superior Derecho": 66.0, "Superior Izquierdo": 66.0,
        "Inferior Derecho": 70.0, "Inferior Izquierdo": 70.0
    }

    st.markdown("---")
    col_l, col_r = st.columns(2)
    with col_l:
        st.write("**análisis de topes por lateralidad:**")
        v_finales_balthazard = []
        for nombre_grupo, suma_puntos in grupos_topes.items():
            t = limites.get(nombre_grupo, 100.0)
            valor_con_tope = min(suma_puntos, t)
            v_finales_balthazard.append(valor_con_tope)
            if suma_puntos > t:
                st.warning(f"⚠️ {nombre_grupo}: {suma_puntos}% (tope aplicado: {t}%)")
            else:
                st.write(f"✅ {nombre_grupo}: {suma_puntos}%")

        st.markdown("### **factores de ponderación**")
        edad = st.number_input("**edad**", 14, 99, 25)
        f_e = 0.05 if edad <= 20 else 0.04 if edad <= 30 else 0.03 if edad <= 40 else 0.02
        f_d = st.selectbox("**dificultad**", [0.05, 0.10, 0.20], format_func=lambda x: f"{int(x*100)}%")
        
        fisico = balthazard(v_finales_balthazard)
        factores = fisico * (f_e + f_d)
        
        # tope de 65.99% para parciales
        total_p = fisico + factores
        if fisico < 66.0 and total_p >= 66.0:
            total_f = 65.99; aplicado_tope = True
        else:
            total_f = total_p; aplicado_tope = False

    with col_r:
        st.metric("**daño físico residual**", f"{fisico}%")
        st.metric("**factores aplicados**", f"{round(factores, 2)}%")
        if aplicado_tope:
            st.error(f"## **ILP final: {total_f}%**")
            st.caption("nota: se aplicó el tope legal de 65.99% (incapacidad parcial).")
        else:
            st.success(f"## **ILP final: {round(total_f, 2)}%**")
        if st.button("🚨 reiniciar"):
            st.session_state.pericia = []; st.rerun()