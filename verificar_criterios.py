import re

import pandas as pd

ANO_MIN, ANO_MAX = 2015, 2026
PERMITIDOS = {"EN", "PT", "ES"}
MAPA = {"english": "EN", "eng": "EN", "en": "EN",
        "portuguese": "PT", "por": "PT", "pt": "PT", "portugues": "PT", "português": "PT",
        "spanish": "ES", "spa": "ES", "es": "ES", "español": "ES", "espanol": "ES"}

df = pd.read_pickle("dados_tratados.pkl")
print("Registros avaliados:", len(df))

# ---- Período ----
fora_ano = df[~df["ano"].between(ANO_MIN, ANO_MAX)]
print(f"\nFora de {ANO_MIN}-{ANO_MAX}:", len(fora_ano))
if len(fora_ano):
    print(fora_ano[["titulo", "ano", "fonte"]].to_string(index=False, max_colwidth=70))


# ---- Idioma ----
def codigos(valor):
    partes = [p.strip().lower() for p in re.split(r"[;,|]", valor or "") if p.strip()]
    return {MAPA[p] for p in partes if p in MAPA}


df["_cod_idioma"] = df["idioma"].apply(codigos)
sem_idioma = df[df["idioma"].fillna("").str.strip() == ""]
fora_idioma = df[(df["idioma"].fillna("").str.strip() != "") &
                 df["_cod_idioma"].apply(lambda s: not (s & PERMITIDOS))]
print("\nValores de idioma mais frequentes:")
print(df["idioma"].fillna("").replace("", "(vazio)").value_counts().head(12))
print("\nSem idioma informado:", len(sem_idioma))
print("Idioma fora de EN/PT/ES:", len(fora_idioma))
if len(fora_idioma):
    print(fora_idioma[["titulo", "idioma", "fonte"]].to_string(index=False, max_colwidth=70))

# ---- Arquivo de conferência ----
conf = pd.concat([fora_ano.assign(motivo="fora do período"),
                  fora_idioma.assign(motivo="idioma fora de EN/PT/ES"),
                  sem_idioma.assign(motivo="idioma não informado")])
if len(conf):
    conf[["titulo", "ano", "idioma", "fonte", "motivo"]].to_csv("conferir_periodo_idioma.csv", index=False, encoding="utf-8-sig")
    print("\nGerado: conferir_periodo_idioma.csv")
else:
    print("\nNenhum registro fora do período ou dos idiomas definidos.")