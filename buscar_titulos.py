import re
import unicodedata

import pandas as pd

from leitura import ler_pasta

# Estudos relevantes que você conhece. O DOI é mais seguro que o título: não depende de como o título foi grafado.
FRAGMENTOS = [
    "Streamlining emergency nursing care",
    "Improving patient safety in a Brazilian healthcare organization",
]
DOIS = [
    "10.1186/s12912-025-02759-w",       # Hussein et al. 2025 (confira)
    "10.47456/bjpe.v11i4.49968",        # Silva et al. 2025 (confira)
    "10.3390/ijerph17155609",           # Zepeda-Lugo et al. 2020 (confira)
]


def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def norm(t):
    return re.sub(r"[^a-z0-9]", "", sem_acento((t or "").lower()))


def norm_doi(d):
    d = (d or "").lower().strip()
    d = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", d)
    d = d.replace("\\", "").replace(" ", "")
    d = re.sub(r"[.,;]+$", "", d)
    while d.endswith(")") and d.count(")") > d.count("("):
        d = d[:-1]
    return d


raw = pd.DataFrame(ler_pasta())            # todos os registros lidos, antes da deduplicação
raw["_t"] = raw["titulo"].apply(norm)
raw["_d"] = raw["doi"].apply(norm_doi)
print("\nRegistros brutos lidos:", len(raw))

destinos = []
for arq, nome in [("dados_tratados.csv", "triagem principal (905)"),
                  ("excluidos_por_tipo.csv", "excluídos por tipo (120 definitivos + 210 de congresso)")]:
    d = pd.read_csv(arq).fillna("")
    destinos.append((nome, d["titulo"].apply(norm), d["doi"].apply(norm_doi)))


def relata(rotulo, achou, f, por_doi):
    print("\n>>", rotulo)
    if achou.empty:
        print("   NÃO está em nenhum dos registros lidos: nenhuma das três bases o recuperou na busca.")
        return
    print(achou[["fonte", "ano", "tipo", "doi"]].to_string(index=False))
    onde = []
    for nome, titulos, dois in destinos:
        serie = dois if por_doi else titulos
        if (serie == f).any() if por_doi else serie.str.contains(f, regex=False).any():
            onde.append(nome)
    print("   Destino no tratamento:", ", ".join(onde) if onde else "não aparece em nenhum arquivo de saída (confira a deduplicação)")


for frag in FRAGMENTOS:
    f = norm(frag)
    relata("TÍTULO: " + frag, raw[raw["_t"].str.contains(f, regex=False)], f, por_doi=False)

for doi in DOIS:
    f = norm_doi(doi)
    relata("DOI: " + doi, raw[raw["_d"] == f], f, por_doi=True)