import re
import unicodedata
from difflib import SequenceMatcher
from itertools import combinations

import pandas as pd


def norm(t):
    t = "".join(c for c in unicodedata.normalize("NFKD", (t or "").lower()) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", t)


def texto(r):
    return re.sub(r"\s+", " ", (r or "").lower()).strip()[:400]


a = pd.read_csv("dados_tratados.csv").fillna("")
a["situacao"] = "triagem"
b = pd.read_csv("excluidos_por_tipo.csv").fillna("")
b["situacao"] = "excluido_tipo"

cols = ["titulo", "ano", "doi", "resumo", "tipo", "fonte", "situacao"]
todos = pd.concat([a[cols], b[cols]], ignore_index=True)
todos["chave"] = todos["titulo"].apply(norm) + "_" + todos["ano"].astype(str)
todos = todos[todos["titulo"].apply(norm) != ""]

com_doi = todos[todos["doi"] != ""]
n_doi = com_doi.groupby("chave")["doi"].nunique()
grupos = list(n_doi[n_doi > 1].index)

linhas = []
for i, g in enumerate(grupos, 1):
    membros = todos[todos["chave"] == g]
    resumos = [texto(r) for r in membros["resumo"] if texto(r)]
    sims = [SequenceMatcher(None, x, y).ratio() for x, y in combinations(resumos, 2)]
    if not sims:
        sim, classe = None, "sem resumo para comparar"
    else:
        sim = max(sims)
        classe = "provável mesma obra" if sim >= 0.85 else "provável obras diferentes"
    for _, m in membros.iterrows():
        linhas.append({"grupo": i, "titulo": m["titulo"], "ano": m["ano"], "doi": m["doi"],
                       "fonte": m["fonte"], "tipo": m["tipo"], "situacao": m["situacao"],
                       "similaridade_resumo": None if sim is None else round(sim, 2),
                       "classificacao": classe})

res = pd.DataFrame(linhas)
res.to_csv("conflitos_classificados.csv", index=False, encoding="utf-8-sig")

print("Grupos com DOIs diferentes (mesmo título e ano):", len(grupos))
if len(res):
    por_grupo = res.groupby("grupo").agg(classificacao=("classificacao", "first"),
                                         na_triagem=("situacao", lambda s: (s == "triagem").any()))
    print("\nClassificação dos grupos:")
    print(por_grupo["classificacao"].value_counts())
    print("\nGrupos com ao menos um registro na triagem:", int(por_grupo["na_triagem"].sum()))
    print(por_grupo[por_grupo["na_triagem"]]["classificacao"].value_counts())
    print("\nGrupos que tocam a triagem:")
    toca = res[res["grupo"].isin(por_grupo[por_grupo["na_triagem"]].index)]
    print(toca[["grupo", "titulo", "ano", "doi", "fonte", "situacao", "classificacao"]].to_string(index=False, max_colwidth=60))