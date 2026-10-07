import re
import unicodedata
from pathlib import Path

import pandas as pd

from leitura import ler_bib
from planilhas import ler_planilha

FRASES = ["lean six sigma", "lean methodology", "lean principles", "lean implementation", "lean tools",
          "lean process", "lean approach", "lean techniques", "lean practices", "lean philosophy",
          "lean transformation"]


def norm(t):
    t = "".join(c for c in unicodedata.normalize("NFKD", (t or "").lower()) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", t)


pasta = Path("sondagem")
inc = pd.DataFrame(ler_bib(pasta / "scopus_incremento.bib", "scopus")).fillna("")
inc["_tit"] = inc["titulo"].apply(norm)
inc = inc.drop_duplicates("_tit")
texto = (inc["titulo"] + " " + inc["resumo"] + " " + inc["palavras_chave"] + " " + inc["palavras_indexadas"]).str.lower()
for f in FRASES:
    inc[f] = texto.str.contains(re.escape(f))
inc["n_frases"] = inc[FRASES].sum(axis=1)
N = len(inc)
print(f"Incremento (registros únicos): {N}")
print(f"Sem nenhuma das frases exatas (casam por plural/singular ou outra variante): {int((inc['n_frases'] == 0).sum())}\n")

am = ler_planilha("sondagem/amostra_incremento", exigir=["titulo", "decisao"])
am["decisao"] = am["decisao"].str.strip().str.upper()
am["_tit"] = am["titulo"].apply(norm)
j = am.merge(inc[["_tit", "n_frases"] + FRASES], on="_tit", how="left")
j = j[j["decisao"].isin(["I", "D", "E"])]
print(f"Amostra julgada: {len(j)} registros (n pequeno por frase: use como indício)\n")

print(f"{'frase':22s} {'no incr.':>8s} {'só ela':>7s} | {'amostra':>7s} {'I':>3s} {'D':>3s} {'E':>3s}  I+D")
for f in FRASES:
    total = int(inc[f].sum())
    so_ela = int((inc[f] & (inc["n_frases"] == 1)).sum())
    g = j[j[f] == True]
    n = len(g)
    i, d, e = (g["decisao"] == "I").sum(), (g["decisao"] == "D").sum(), (g["decisao"] == "E").sum()
    rend = f"{(i + d) / n:4.0%}" if n else "  - "
    print(f"{f:22s} {total:8d} {so_ela:7d} | {n:7d} {i:3d} {d:3d} {e:3d}  {rend}")

# Sem a frase 'lean six sigma': quantos registros saem e como ficam os julgados
sem_lss = inc[~inc["lean six sigma"]]
j_sem = j[j["lean six sigma"] == False]
print(f"\nSe 'lean six sigma' ficasse de fora: {len(sem_lss)} registros no incremento "
      f"({N - len(sem_lss)} a menos); na amostra, {len(j_sem)} registros, "
      f"I+D = {((j_sem['decisao'] != 'E').sum() / len(j_sem) if len(j_sem) else float('nan')):.0%}")