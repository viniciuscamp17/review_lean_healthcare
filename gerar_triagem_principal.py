from pathlib import Path

import pandas as pd

N_CALIBRACAO = 50     # registros que os dois revisores avaliam primeiro, para alinhar os critérios
SEMENTE = 2026        # sorteio reprodutível

mestre = Path("triagem_principal_mestre.csv")
if mestre.exists():
    raise SystemExit("triagem_principal_mestre.csv já existe: não gerei IDs nem planilhas de novo, "
                     "para não trocar a numeração nem sobrescrever planilhas preenchidas.")

df = pd.read_pickle("dados_tratados.pkl")
df["ano"] = pd.to_numeric(df["ano"], errors="coerce").astype("Int64")

# IDs fixos: ordem determinística
df = df.sort_values(["ano", "titulo"]).reset_index(drop=True)
df.insert(0, "id_registro", [f"P{i:04d}" for i in range(1, len(df) + 1)])

amostra = df.sample(n=min(N_CALIBRACAO, len(df)), random_state=SEMENTE)["id_registro"]
df["calibracao"] = df["id_registro"].isin(amostra).map({True: "S", False: ""})

df.drop(columns="autores").to_csv(mestre, index=False, encoding="utf-8-sig")

colunas = [c for c in ["id_registro", "calibracao", "titulo", "ano", "periodico", "resumo",
                       "palavras_chave", "tipo", "doi"] if c in df.columns]
for revisor in ["A", "B"]:
    folha = df[colunas].copy()
    folha["decisao"] = ""            # I (incluir) / E (excluir) / D (dúvida)
    folha["motivo_exclusao"] = ""    # TEMA, NAO_SISTEMATICA, ESCOPO, PROTOCOLO, OUTRO
    folha["observacoes"] = ""
    folha.to_csv(f"triagem_principal_revisor{revisor}.csv", index=False, encoding="utf-8-sig")

print("Registros na frente principal:", len(df))
print("Calibração:", int((df["calibracao"] == "S").sum()), "registros (marcados com S)")
print("Gerados: triagem_principal_mestre.csv, triagem_principal_revisorA.csv e revisorB.csv")