import time
import pandas as pd
import sys

xls = pd.ExcelFile("calculadora_final_srt.xlsx")

# Simulate without cache
start = time.time()
for _ in range(10):
    df = pd.read_excel(xls, sheet_name="Psiquiatría").fillna("")
end = time.time()
print(f"Without cache: {end - start:.4f}s")

# Simulate with cache (in-memory dict)
cache = {}
def get_excel_sheet(xls_obj, sheet_name):
    if sheet_name not in cache:
        cache[sheet_name] = pd.read_excel(xls_obj, sheet_name=sheet_name).fillna("")
    return cache[sheet_name]

start2 = time.time()
for _ in range(10):
    df2 = get_excel_sheet(xls, "Psiquiatría")
end2 = time.time()
print(f"With cache: {end2 - start2:.4f}s")
