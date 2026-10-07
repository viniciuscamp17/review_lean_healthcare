from collections import Counter, defaultdict

import pandas as pd

df = pd.read_pickle("dados_tratados.pkl")

COMUNS = {"WANG", "LI", "ZHANG", "LIU", "CHEN", "YANG", "ZHAO", "HUANG",
          "ZHOU", "WU", "XU", "SUN", "MA", "ZHU", "HU", "GUO", "HE", "LIN",
          "LUO", "SINGH", "KUMAR", "SHARMA", "GUPTA", "PATEL", "SMITH",
          "JOHNSON", "BROWN", "DAVIS", "KIM", "LEE", "PARK", "SILVA",
          "SANTOS", "OLIVEIRA", "SOUZA", "COSTA", "PEREIRA"}

por_sobrenome = defaultdict(Counter)
for lista in df["autores"]:
    for a in lista:
        if a and ", " in a:
            sob, ini = a.split(", ", 1)
            if ini:                      # ignora autores sem iniciais
                por_sobrenome[sob][ini] += 1

# Variantes que aparecem juntas no mesmo artigo = pessoas diferentes
juntas = set()
for lista in df["autores"]:
    for i, a in enumerate(lista):
        for b in lista[i + 1:]:
            juntas.add(frozenset((a, b)))

mapa = {}
for sob, iniciais in por_sobrenome.items():
    if sob in COMUNS:
        continue
    lista = sorted(iniciais, key=len, reverse=True)
    for curta in lista:
        cands = [l for l in lista if len(l) > len(curta) and l.startswith(curta)]
        if len(cands) == 1:
            a, b = f"{sob}, {curta}", f"{sob}, {cands[0]}"
            if frozenset((a, b)) not in juntas:
                mapa[a] = b

print(f"{len(mapa)} variantes mescladas. Exemplos:")
for k, v in list(mapa.items())[:40]:
    print(f"  {k}  ->  {v}")

df["autores"] = df["autores"].apply(
    lambda L: list(dict.fromkeys(mapa.get(a, a) for a in L))
)
df.to_pickle("dados_tratados.pkl")
df.drop(columns="autores").to_csv("dados_tratados.csv", index=False, encoding="utf-8-sig")
print("\nSalvo.")