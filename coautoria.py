from collections import Counter
from itertools import combinations

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

df = pd.read_pickle("dados_tratados.pkl")

# Artigos com muitos autores criam cliques enormes e distorcem a rede
LIMITE = 20
df_rede = df[df["autores"].apply(lambda L: 2 <= len(L) <= LIMITE)]
print(f"Artigos usados na rede: {len(df_rede)} de {len(df)} "
      f"(excluídos: sem coautores ou com mais de {LIMITE} autores)")

# ---------- Construção da rede ----------
contagem = Counter(a for L in df_rede["autores"] for a in L)

G = nx.Graph()
for lista in df_rede["autores"]:
    for a in lista:
        G.add_node(a)
    for a, b in combinations(sorted(set(lista)), 2):
        if G.has_edge(a, b):
            G[a][b]["weight"] += 1
        else:
            G.add_edge(a, b, weight=1)

nx.set_node_attributes(G, {a: contagem[a] for a in G}, "publicacoes")

# ---------- Métricas gerais ----------
componentes = sorted(nx.connected_components(G), key=len, reverse=True)
print("\nAutores (nós):", G.number_of_nodes())
print("Ligações (arestas):", G.number_of_edges())
print("Densidade:", round(nx.density(G), 5))
print("Componentes conectados:", len(componentes))
print("Maior componente:", len(componentes[0]), "autores")
print("Grau médio:", round(sum(d for _, d in G.degree()) / G.number_of_nodes(), 2))

# ---------- Métricas por autor ----------
grau = dict(G.degree())
forca = dict(G.degree(weight="weight"))
inter = nx.betweenness_centrality(G)

metricas = pd.DataFrame({
    "autor": list(G.nodes),
    "publicacoes": [contagem[a] for a in G],
    "coautores": [grau[a] for a in G],
    "forca": [forca[a] for a in G],
    "intermediacao": [round(inter[a], 5) for a in G],
}).sort_values(["coautores", "publicacoes"], ascending=False)
metricas.to_csv("metricas_autores.csv", index=False, encoding="utf-8-sig")

print("\nTop 15 por número de coautores:")
print(metricas.head(15).to_string(index=False))

# ---------- Pares que mais colaboram ----------
pares = sorted(G.edges(data="weight"), key=lambda x: x[2], reverse=True)[:15]
print("\nPares que mais publicam juntos:")
for a, b, w in pares:
    print(f"  {a}  +  {b}: {w} artigos")

# ---------- Exportar para Gephi ----------
nx.write_gexf(G, "coautoria.gexf")

# ---------- Visualização do núcleo ----------
# Apenas autores com 3+ publicações e dentro do maior componente do núcleo
nucleo_nos = [a for a in G if contagem[a] >= 3]
H = G.subgraph(nucleo_nos)
H = H.subgraph(max(nx.connected_components(H), key=len))
print(f"\nNúcleo desenhado: {H.number_of_nodes()} autores")

plt.figure(figsize=(13, 10))
pos = nx.spring_layout(H, k=0.5, seed=42)
nx.draw_networkx(
    H, pos,
    node_size=[contagem[a] * 60 for a in H],
    font_size=6,
    width=[H[u][v]["weight"] * 0.6 for u, v in H.edges],
    edge_color="#999999",
    node_color="#4C72B0",
)
plt.axis("off")
plt.tight_layout()
plt.savefig("rede_coautoria.png", dpi=150)
print("Salvo: metricas_autores.csv, coautoria.gexf, rede_coautoria.png")