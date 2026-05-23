import time
import pandas as pd
import streamlit as st

@st.cache_data
def cargar_hoja_excel(_xls, sheet_name):
    return pd.read_excel(_xls, sheet_name=sheet_name).fillna("")

xls = pd.ExcelFile("calculadora_final_srt.xlsx")

# Simulate without cache
start = time.time()
for _ in range(10):
    df = pd.read_excel(xls, sheet_name="Psiquiatría").fillna("")
end = time.time()
print(f"Without cache: {end - start:.4f}s")

# Simulate with cache (streamlit cache)
start2 = time.time()
for _ in range(10):
    df2 = cargar_hoja_excel(xls, "Psiquiatría")
end2 = time.time()
print(f"With st.cache_data: {end2 - start2:.4f}s")
