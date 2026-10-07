import re
import unicodedata

import pandas as pd

from planilhas import ler_planilha

# Títulos conhecidos como relevantes (teste de sensibilidade): acrescente os seus.
CONHECIDOS = [
    "Assessing the impact of lean healthcare on inpatient care",
    "A literature review on Lean healthcare: implementation strategies, challenges",
    "Streamlining emergency nursing care post-pandemic",
    "Improving patient safety in a Brazilian healthcare organization using lean thinking",
    "Lean management in health care: effects on patient outcomes",
]

LEAN = re.compile(r"\b(?:lean(?!\s+(?:body|mass|tissue|muscle|weight))|pensamento enxuto|gest[aã]o enxuta|producci[oó]n esbelta)\b", re.I)


def norm(t):
    t = "".join(c for c in unicodedata.normalize("NFKD", (t or "").lower()) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", t)


def n_mencoes(texto):
    return len(LEAN.findall(texto or ""))


df = pd.read_pickle("dados_tratados.pkl").fillna("")
n = len(df)

df["lean_titulo"] = df["titulo"].apply(lambda t: n_mencoes(t) > 0)
df["lean_palavras"] = df["palavras_chave"].apply(lambda t: n_mencoes(t) > 0)
df["mencoes_resumo"] = df["resumo"].apply(n_mencoes)
df["tipo_revisao"] = df["tipo"].str.contains(r"review", case=False)

df["C1_titulo_ou_palavras"] = df["lean_titulo"] | df["lean_palavras"]
df["C2_so_titulo"] = df["lean_titulo"]
# Sem resumo e sem palavras-chave não dá para julgar por este critério: o registro é mantido para a triagem humana
sem_informacao = (df["resumo"] == "") & (df["palavras_chave"] == "")
df["C3_foco"] = df["C1_titulo_ou_palavras"] | (df["mencoes_resumo"] >= 2) | sem_informacao
df["C4_tipo_revisao"] = df["tipo_revisao"]

criterios = {
    "C1  Lean no título ou nas palavras-chave do autor": "C1_titulo_ou_palavras",
    "C2  Lean no título": "C2_so_titulo",
    "C3  C1 ou Lean 2+ vezes no resumo (sem informação: mantido)": "C3_foco",
    "C4  tipo de documento marcado como revisão (referência)": "C4_tipo_revisao",
}
print(f"Registros: {n}\n")
print(f"{'Critério':62s} {'passam':>7s} {'saem':>6s}  % que sai")
for nome, col in criterios.items():
    passam = int(df[col].sum())
    print(f"{nome:62s} {passam:7d} {n - passam:6d}  {(n - passam) / n:6.0%}")

print("\nRegistros sem resumo:", int((df["resumo"] == "").sum()),
      "| sem palavras-chave:", int((df["palavras_chave"] == "").sum()))

# Teste de sensibilidade: os conhecidos estão no conjunto? passariam em cada critério?
print("\nTeste de sensibilidade (títulos conhecidos):")
chaves = df["titulo"].apply(norm)
for c in CONHECIDOS:
    achou = df[chaves.str.contains(norm(c)[:60], regex=False)]
    if achou.empty:
        print(f"  não está nos registros: {c[:70]}")
    else:
        r = achou.iloc[0]
        print(f"  C1={'sim' if r['C1_titulo_ou_palavras'] else 'NÃO'}  C3={'sim' if r['C3_foco'] else 'NÃO'}  | {c[:60]}")

# Amostra dos que sairiam em C3, para conferência humana
saem = df[~df["C3_foco"]]
saem[["titulo", "ano", "fonte", "tipo"]].sample(n=min(30, len(saem)), random_state=2026) \
    .to_csv("amostra_saem_C3.csv", index=False, encoding="utf-8-sig")
df[["titulo", "lean_titulo", "lean_palavras", "mencoes_resumo", "C1_titulo_ou_palavras", "C3_foco", "tipo", "fonte"]] \
    .to_csv("simulacao_criterios.csv", index=False, encoding="utf-8-sig")
print("\nGerados: simulacao_criterios.csv e amostra_saem_C3.csv (até 30 registros que sairiam, para você conferir)")