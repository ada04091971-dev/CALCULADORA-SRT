import timeit

setup = """
v_balthazard_base = list(range(10))
otros_capitulos = list(range(1000))
"""

code_loop = """
v_balthazard = v_balthazard_base.copy()
for v in otros_capitulos:
    v_balthazard.append(v)
"""

code_extend = """
v_balthazard = v_balthazard_base.copy()
v_balthazard.extend(otros_capitulos)
"""

time_loop = timeit.timeit(code_loop, setup=setup, number=100000)
time_extend = timeit.timeit(code_extend, setup=setup, number=100000)

print(f"For Loop: {time_loop:.5f} seconds")
print(f"Extend:   {time_extend:.5f} seconds")
print(f"Improvement: {(time_loop - time_extend) / time_loop * 100:.2f}%")
