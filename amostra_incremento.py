from pathlib import Path

import pandas as pd

from leitura import ler_bib

N_AMOSTRA = 50
SEMENTE = 2026

arquivo = Path("sondagem") / "scopus_incremento.bib"
saida = Path("sondagem") / "amostra_incremento.csv"
if saida.exists():
    raise SystemExit(f"{saida} já existe: não sorteei de novo, para não perder julgamentos já feitos.")

regs = ler_bib(arquivo, "scopus")
df = pd.DataFrame(regs)
print("Registros no incremento:", len(df))

amostra = df.sample(n=min(N_AMOSTRA, len(df)), random_state=SEMENTE).reset_index(drop=True)
amostra.insert(0, "n", range(1, len(amostra) + 1))
folha = amostra[["n", "titulo", "ano", "periodico", "resumo", "palavras_chave", "tipo", "doi"]].copy()
folha["decisao"] = ""            # I (incluir) / E (excluir) / D (dúvida), pelos mesmos critérios da triagem
folha["motivo_exclusao"] = ""    # TEMA, NAO_SISTEMATICA, ESCOPO, PROTOCOLO, OUTRO
folha.to_csv(saida, index=False, encoding="utf-8-sig")
print(f"Gerado: {saida} ({len(folha)} registros sorteados, semente {SEMENTE})")