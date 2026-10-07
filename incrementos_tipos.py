import re
from pathlib import Path

import pandas as pd

from classificacao_tipo import classifica_registro
from leitura import ler_bib

FATOR_3_BASES = 1235 / 1069     # Scopus -> união das três bases (observado no conjunto original)
REV_TEXTO = re.compile(
    r"systematic(?:ally)?\s+(?:literature\s+)?review|integrative\s+(?:literature\s+)?review|"
    r"scoping\s+review|umbrella\s+review|literature\s+review|review\s+of\s+(?:the\s+)?(?:existing\s+)?literature|"
    r"meta-?analys[ie]s|meta-?synthesis|\bPRISMA\b", re.I)

inc = pd.DataFrame(ler_bib(Path("sondagem") / "scopus_incremento.bib", "scopus")).fillna("")
inc["_t"] = inc["titulo"].str.lower().str.replace(r"[^a-z0-9]", "", regex=True)
inc = inc.drop_duplicates("_t")
N = len(inc)
print(f"Incremento: {N} registros\n")

print("Tipos de documento (rótulo do Scopus):")
for t, c in inc["tipo"].replace("", "(vazio)").value_counts().head(10).items():
    print(f"  {t:28s} {c:5d} ({c / N:4.0%})")

inc["classe"] = inc["tipo"].apply(classifica_registro)
cont = inc["classe"].value_counts()
print(f"\nPela regra de tipo do pipeline: segue {cont.get('manter', 0) + cont.get('revisar', 0)} "
      f"(manter {cont.get('manter', 0)}, revisar {cont.get('revisar', 0)}) | sai {cont.get('excluir', 0)} "
      "(congresso, livros, capítulos, editoriais, cartas...)")

segue = inc[inc["classe"] != "excluir"].copy()
rotulo_rev = segue["tipo"].str.strip().str.lower().isin(["review", "review article"])
texto_rev = (segue["titulo"] + " " + segue["resumo"]).apply(lambda t: bool(REV_TEXTO.search(t)))
print(f"\nEntre os {len(segue)} que seguiriam:")
print(f"  rótulo 'Review' no Scopus:                                    {int(rotulo_rev.sum()):5d}")
print(f"  termos de revisão (sistemática, integrativa, literatura...):  {int(texto_rev.sum()):5d}")
n_rev = int((rotulo_rev | texto_rev).sum())
print(f"  qualquer dos dois:                                            {n_rev:5d}")
print(f"\nTriagem adicional estimada se a extensão fosse só de revisões: ~{n_rev * FATOR_3_BASES:.0f} registros "
      f"(triagem total ~{905 + n_rev * FATOR_3_BASES:.0f}; leitura do revisor 1: "
      f"{(905 + n_rev * FATOR_3_BASES) / 60:.0f} a {2 * (905 + n_rev * FATOR_3_BASES) / 60:.0f} h)")
print(f"Triagem adicional estimada se a extensão fosse de todo o que segue: ~{len(segue) * FATOR_3_BASES:.0f} registros "
      f"(triagem total ~{905 + len(segue) * FATOR_3_BASES:.0f})")
segue[rotulo_rev | texto_rev][["titulo", "ano", "tipo"]].to_csv("sondagem/incremento_revisoes.csv", index=False, encoding="utf-8-sig")
print("\nGerado: sondagem/incremento_revisoes.csv (lista das revisões candidatas, para conferência)")



congresso = inc[inc["tipo"].str.contains(r"conference paper|proceedings paper", case=False)
                & ~inc["tipo"].str.contains(r"editorial|letter|note|comment|conference review|erratum|retract", case=False)]
rev_cong = (congresso["titulo"] + " " + congresso["resumo"]).apply(lambda t: bool(REV_TEXTO.search(t)))
print(f"\nArtigos de congresso no incremento: {len(congresso)} | com termos de revisão: {int(rev_cong.sum())} "
      f"(frente de congresso: ~{int(rev_cong.sum()) * FATOR_3_BASES:.0f} registros a avaliar a mais)")