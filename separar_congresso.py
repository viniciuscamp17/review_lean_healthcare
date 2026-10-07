import re
from pathlib import Path

import pandas as pd

TIPOS_CONGRESSO = re.compile(r"conference paper|proceedings paper", re.I)
TIPOS_FORA = re.compile(r"editorial|letter|note|comment|meeting abstract|conference review|correction|retract", re.I)

ex = pd.read_csv("excluidos_por_tipo.csv").fillna("")
ex["tipo"] = ex["tipo"].astype(str)
ex["ano"] = pd.to_numeric(ex["ano"], errors="coerce").astype("Int64")

eh_cong = ex["tipo"].str.contains(TIPOS_CONGRESSO) & ~ex["tipo"].str.contains(TIPOS_FORA)
cong = ex[eh_cong].copy()
definitivos = ex[~eh_cong].copy()

print("Excluídos por tipo (total):", len(ex))
print("  frente de congresso (avaliação separada):", len(cong))
print("  exclusão definitiva (livros, capítulos, editoriais, cartas, resumos, sumários de anais):", len(definitivos))
assert len(cong) + len(definitivos) == len(ex)

# IDs fixos: ordem determinística e arquivo mestre que não é sobrescrito
mestre = Path("congresso_mestre.csv")
if mestre.exists():
    raise SystemExit("congresso_mestre.csv já existe: não gerei IDs de novo, para não trocar a numeração.")

cong = cong.sort_values(["ano", "titulo"]).reset_index(drop=True)
cong.insert(0, "id_registro", [f"C{i:03d}" for i in range(1, len(cong) + 1)])
cong.to_csv(mestre, index=False, encoding="utf-8-sig")
definitivos.to_csv("excluidos_definitivos.csv", index=False, encoding="utf-8-sig")

colunas = [c for c in ["id_registro", "titulo", "ano", "periodico", "resumo", "tipo", "doi"] if c in cong.columns]
for revisor in ["A", "B"]:
    folha = cong[colunas].copy()
    folha["tema_lean_saude"] = ""        # S / N
    folha["revisao_sistematica"] = ""    # S / N / D (dúvida)
    folha["motivo_exclusao"] = ""        # TEMA, NAO_SISTEMATICA, ESCOPO, PROTOCOLO, PRIMARIO_CONGRESSO, OUTRO
    folha["observacoes"] = ""
    folha.to_csv(f"triagem_congresso_revisor{revisor}.csv", index=False, encoding="utf-8-sig")

print("Gerados: congresso_mestre.csv, excluidos_definitivos.csv, triagem_congresso_revisorA.csv e revisorB.csv")