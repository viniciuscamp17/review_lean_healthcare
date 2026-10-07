from collections import Counter

import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_pickle("dados_tratados.pkl")

# ---------- Publicações por ano ----------
por_ano = df["ano"].astype(int).value_counts().sort_index()
por_ano.to_csv("publicacoes_por_ano.csv", header=["publicacoes"])

print("Publicações por ano:")
print(por_ano.to_string())
print("\nAno mais recente:", por_ano.index.max(),
      "| Ano mais antigo:", por_ano.index.min())

fig, ax = plt.subplots(figsize=(10, 4))
por_ano.plot(kind="bar", ax=ax, color="#4C72B0")
ax.set_title("Publicações por ano")
ax.set_xlabel("Ano")
ax.set_ylabel("Nº de publicações")
plt.tight_layout()
plt.savefig("publicacoes_por_ano.png", dpi=150)
plt.close()

# ---------- Autores mais produtivos ----------
contagem = Counter(a for lista in df["autores"] for a in lista if a)
top = pd.DataFrame(contagem.most_common(20), columns=["autor", "publicacoes"])
top.to_csv("top_autores.csv", index=False, encoding="utf-8-sig")

print("\nTop 20 autores:")
print(top.to_string(index=False))

# ---------- Tamanho das equipes ----------
n_aut = df["autores"].apply(len)
com_autores = n_aut[n_aut > 0]
print("\nMédia de autores por artigo:", round(com_autores.mean(), 2))
print("Mediana:", com_autores.median())
print("Máximo:", com_autores.max())
print("Artigos com mais de 20 autores:", (com_autores > 20).sum())