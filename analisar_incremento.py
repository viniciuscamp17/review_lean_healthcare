import re
import unicodedata

from pathlib import Path

from planilhas import ler_planilha
from leitura import ler_bib

FRASES = ["lean methodology", "lean approach", "lean tools", "lean six sigma", "lean principles",
          "lean implementation", "lean philosophy", "lean practices", "lean techniques",
          "lean transformation", "lean process"]
LEAN = re.compile(r"\blean\b(?!\s+(?:body|mass|tissue|muscle|weight))", re.I)


def norm(t):
    t = "".join(c for c in unicodedata.normalize("NFKD", (t or "").lower()) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", t)


def n_lean(x):
    return len(LEAN.findall(x or ""))


pasta = Path("sondagem")
inc = pd.DataFrame(ler_bib(pasta / "scopus_incremento.bib", "scopus")).fillna("")
inc["_tit"] = inc["titulo"].apply(norm)
inc = inc.drop_duplicates("_tit")
N = len(inc)

inc["lean_titulo"] = inc["titulo"].apply(n_lean) > 0
inc["lean_kw"] = inc["palavras_chave"].apply(n_lean) > 0
inc["mencoes_resumo"] = inc["resumo"].apply(n_lean)
inc["foco"] = inc["lean_titulo"] | inc["lean_kw"]
inc["foco_ampliado"] = inc["foco"] | (inc["mencoes_resumo"] >= 2)

print(f"Incremento (registros únicos): {N}\n")
print("Foco temático dentro do incremento:")
print(f"  Lean no título:                           {int(inc['lean_titulo'].sum()):5d} ({inc['lean_titulo'].mean():.0%})")
print(f"  Lean no título ou palavras-chave do autor: {int(inc['foco'].sum()):5d} ({inc['foco'].mean():.0%})")
print(f"  ... ou 2+ menções no resumo:              {int(inc['foco_ampliado'].sum()):5d} ({inc['foco_ampliado'].mean():.0%})")

texto = (inc["titulo"] + " " + inc["resumo"] + " " + inc["palavras_chave"] + " " + inc["palavras_indexadas"]).str.lower()
print("\nRegistros que contêm cada frase acrescentada (título, resumo ou palavras-chave):")
linhas = [(f, int(texto.str.contains(re.escape(f)).sum())) for f in FRASES]
for f, c in sorted(linhas, key=lambda x: -x[1]):
    print(f"  {f:22s} {c:5d} ({c / N:.0%})")

am = ler_planilha("sondagem/amostra_incremento", exigir=["titulo", "decisao"])
if am is not None:
    am["decisao"] = am["decisao"].str.strip().str.upper()
    am["_tit"] = am["titulo"].apply(norm)
    j = am.merge(inc[["_tit", "foco", "foco_ampliado"]], on="_tit", how="left")
    j = j[j["decisao"].isin(["I", "E", "D"])]
    print(f"\nJulgamentos da amostra: {len(j)} registros")
    print(f"{'grupo':44s} {'n':>3s} {'I':>3s} {'D':>3s} {'E':>3s}  rendimento (I+D)")
    grupos = {
        "todos": j,
        "com foco (Lean no título ou kw do autor)": j[j["foco"] == True],
        "sem foco": j[j["foco"] == False],
    }
    for nome, g in grupos.items():
        n = len(g)
        i, d, e = (g["decisao"] == "I").sum(), (g["decisao"] == "D").sum(), (g["decisao"] == "E").sum()
        r = (i + d) / n if n else float("nan")
        print(f"{nome:44s} {n:3d} {i:3d} {d:3d} {e:3d}  {r:.0%}")
    g = grupos["com foco (Lean no título ou kw do autor)"]
    if len(g):
        r = ((g["decisao"] != "E").sum()) / len(g)
        print(f"\nSe a ampliação exigisse foco: ~{int(inc['foco'].sum())} registros novos no Scopus, "
              f"com ~{r * inc['foco'].sum():.0f} relevantes esperados (amostra pequena: use como ordem de grandeza).")
else:
    print("\n(amostra_incremento.csv não encontrada)")