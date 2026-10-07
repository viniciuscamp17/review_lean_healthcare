import math
import re
import unicodedata
from pathlib import Path

import pandas as pd

from leitura import ler_bib
from planilhas import ler_planilha

TODAS = ["lean six sigma", "lean methodology", "lean principles", "lean implementation", "lean tools",
         "lean process", "lean approach", "lean techniques", "lean practices", "lean philosophy",
         "lean transformation"]
DEMAIS = [f for f in TODAS if f not in ("lean six sigma", "lean methodology")]

# Cenários de ampliação: edite à vontade (nome -> frases que ficariam na busca)
CENARIOS = {
    "A  todas as 11 frases": TODAS,
    "B  sem lean six sigma": [f for f in TODAS if f != "lean six sigma"],
    "C  sem lean methodology": [f for f in TODAS if f != "lean methodology"],
    "D  só lean six sigma + lean methodology": ["lean six sigma", "lean methodology"],
    "E  sem lean six sigma e sem lean methodology": DEMAIS,
    "F  só lean six sigma": ["lean six sigma"],
}


def norm(t):
    t = "".join(c for c in unicodedata.normalize("NFKD", (t or "").lower()) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", t)


pasta = Path("sondagem")
inc = pd.DataFrame(ler_bib(pasta / "scopus_incremento.bib", "scopus")).fillna("")
inc["_tit"] = inc["titulo"].apply(norm)
inc = inc.drop_duplicates("_tit")
texto = (inc["titulo"] + " " + inc["resumo"] + " " + inc["palavras_chave"] + " " + inc["palavras_indexadas"]).str.lower()
for f in TODAS:
    inc[f] = texto.str.contains(re.escape(f))
sem_frase = int((~inc[TODAS].any(axis=1)).sum())

am = ler_planilha("sondagem/amostra_incremento", exigir=["titulo", "decisao"])
am["decisao"] = am["decisao"].str.strip().str.upper()
am["_tit"] = am["titulo"].apply(norm)
j = am.merge(inc[["_tit"] + TODAS], on="_tit", how="left")
j = j[j["decisao"].isin(["I", "D", "E"])]

print(f"Incremento: {len(inc)} registros | amostra julgada: {len(j)} | sem frase exata (variantes): {sem_frase}\n")
print(f"{'cenário':46s} {'regs':>5s} | {'n':>3s} {'I+D':>4s} {'rend.':>6s} {'±':>5s} | relevantes esperados")
for nome, frases in CENARIOS.items():
    mi = inc[frases].any(axis=1)
    mj = j[frases].any(axis=1)
    total, n = int(mi.sum()), int(mj.sum())
    k = int((j[mj]["decisao"] != "E").sum())
    if n:
        p = k / n
        h = 1.96 * math.sqrt(p * (1 - p) / n)
        aviso = "  (n pequeno)" if n < 15 else ""
        print(f"{nome:46s} {total:5d} | {n:3d} {k:4d} {p:6.0%} {h:5.0%} | ~{p * total:.0f}{aviso}")
    else:
        print(f"{nome:46s} {total:5d} | {n:3d}    -      -     - | sem julgados")
print("\nObs.: some cerca de 6% a cada cenário pelos registros que casam por variante (singular/plural/hífen).")