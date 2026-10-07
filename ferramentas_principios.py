import math
import re
import unicodedata
from pathlib import Path

import pandas as pd

from leitura import ler_bib
from planilhas import ler_planilha

# --- Vocabulário (edite à vontade). Siglas diferenciam maiúsculas de minúsculas. ---
FERRAMENTAS = [  # termos específicos de ferramentas Lean
    (r"value[- ]stream", re.I), (r"\bVSM\b", 0), (r"\b5S\b", 0), (r"\bkaizen\b", re.I), (r"\bA3\b", 0),
    (r"\bkanban\b", re.I), (r"standardi[sz]ed work|standard work", re.I), (r"visual (?:management|control)", re.I),
    (r"\bgemba\b", re.I), (r"poka[- ]yoke|mistake[- ]proofing", re.I), (r"\bSMED\b|single[- ]minute exchange", 0),
    (r"heijunka|production levell?ing", re.I), (r"takt time", re.I), (r"pull system", re.I),
    (r"just[- ]in[- ]time|\bJIT\b", re.I), (r"\bPDCA\b|\bPDSA\b", 0), (r"\bDMAIC\b", 0), (r"root cause", re.I),
    (r"5 whys|five whys", re.I), (r"fishbone|ishikawa|cause[- ]and[- ]effect", re.I), (r"spaghetti", re.I),
    (r"kaizen (?:event|blitz)|rapid (?:process )?improvement (?:event|workshop)", re.I),
    (r"toyota production system|\bTPS\b", re.I), (r"process mapping", re.I),
]
PRINCIPIOS = [  # termos genéricos de princípios (mais ruidosos)
    (r"\bwaste", re.I), (r"\bmuda\b", re.I), (r"non[- ]value[- ]added|value[- ]added", re.I),
    (r"continuous (?:flow|improvement)", re.I), (r"(?:customer|patient) value|value for (?:the )?patients?", re.I),
    (r"respect for people", re.I), (r"\bperfection\b", re.I),
]
FATOR_TRIAGEM = 905 / 1235 * 1235 / 1069   # Scopus -> triagem principal (3 bases x fração que segue)


def compila(lista):
    return [re.compile(p, f) for p, f in lista]


FER, PRI = compila(FERRAMENTAS), compila(PRINCIPIOS)


def norm(t):
    t = "".join(c for c in unicodedata.normalize("NFKD", (t or "").lower()) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", t)


def tem(padroes, texto):
    return any(p.search(texto) for p in padroes)


def marca(df):
    texto = df["titulo"] + " " + df["resumo"] + " " + df["palavras_chave"] + " " + df["palavras_indexadas"]
    df["fer"] = texto.apply(lambda t: tem(FER, t))
    df["pri"] = texto.apply(lambda t: tem(PRI, t))
    df["qualquer"] = df["fer"] | df["pri"]
    return df


def linha(nome, d):
    n = len(d)
    return (f"  {nome:42s} {n:5d} ({n / max(total, 1):4.0%})")


# ---------------- Conjunto atual (905) ----------------
atual = pd.read_pickle("dados_tratados.pkl").fillna("")
for c in ("palavras_indexadas",):
    if c not in atual.columns:
        atual[c] = ""
atual = marca(atual)
total = len(atual)
print(f"CONJUNTO ATUAL ({total} registros)")
print(linha("com ferramenta específica", atual[atual["fer"]]))
print(linha("com princípio genérico (e sem ferramenta)", atual[~atual["fer"] & atual["pri"]]))
print(linha("sem nenhum dos dois", atual[~atual["qualquer"]]))
atual[~atual["qualquer"]][["titulo", "ano", "fonte", "tipo"]].to_csv("sem_ferramenta_905.csv", index=False, encoding="utf-8-sig")
print("  -> lista dos sem nenhum dos dois: sem_ferramenta_905.csv (confira se há estudos de desafios/cultura/liderança)\n")

# ---------------- Incremento (Scopus) ----------------
pasta = Path("sondagem")
inc = pd.DataFrame(ler_bib(pasta / "scopus_incremento.bib", "scopus")).fillna("")
inc["_tit"] = inc["titulo"].apply(norm)
inc = inc.drop_duplicates("_tit")
inc = marca(inc)
total = len(inc)
print(f"INCREMENTO ({total} registros)")
print(linha("com ferramenta específica", inc[inc["fer"]]))
print(linha("com princípio genérico (e sem ferramenta)", inc[~inc["fer"] & inc["pri"]]))
print(linha("sem nenhum dos dois", inc[~inc["qualquer"]]))

# ---------------- Rendimento na amostra julgada ----------------
am = ler_planilha("sondagem/amostra_incremento", exigir=["titulo", "decisao"])
am["decisao"] = am["decisao"].str.strip().str.upper()
am["_tit"] = am["titulo"].apply(norm)
j = am.merge(inc[["_tit", "fer", "pri", "qualquer"]], on="_tit", how="left")
j = j[j["decisao"].isin(["I", "D", "E"])]
print(f"\nRENDIMENTO NA AMOSTRA JULGADA ({len(j)} registros)")
print(f"  {'grupo':36s} {'n':>3s} {'I':>3s} {'D':>3s} {'E':>3s}  I+D     ±")
grupos = {
    "com ferramenta específica": j[j["fer"] == True],
    "com ferramenta ou princípio": j[j["qualquer"] == True],
    "sem ferramenta nem princípio": j[j["qualquer"] == False],
}
for nome, g in grupos.items():
    n = len(g)
    i, d, e = (g["decisao"] == "I").sum(), (g["decisao"] == "D").sum(), (g["decisao"] == "E").sum()
    if n:
        p = (i + d) / n
        h = 1.96 * math.sqrt(p * (1 - p) / n)
        print(f"  {nome:36s} {n:3d} {i:3d} {d:3d} {e:3d}  {p:4.0%}  {h:4.0%}")
    else:
        print(f"  {nome:36s}   0")

# ---------------- Cenários de volume ----------------
print("\nVOLUME SE O INCREMENTO EXIGIR ... (estimativa: triagem = 905 + 0,85 x registros do Scopus)")
for nome, mask in (("ferramenta específica", inc["fer"]), ("ferramenta ou princípio", inc["qualquer"]),
                   ("todo o incremento", inc["fer"] | True)):
    n = int(mask.sum())
    tri = 905 + FATOR_TRIAGEM * n
    print(f"  {nome:28s} {n:5d} registros -> triagem total ~{tri:5.0f} | leitura do revisor 1: {tri / 60:3.0f} a {2 * tri / 60:3.0f} h")