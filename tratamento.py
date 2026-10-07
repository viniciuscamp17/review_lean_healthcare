import re
import unicodedata
from difflib import SequenceMatcher
from itertools import combinations

import pandas as pd

from classificacao_tipo import classifica_registro
from leitura import ler_pasta

# ---------- Configuração ----------
# Prioridade da cópia mantida em cada duplicata (Scopus primeiro: metadados mais completos)
PRIORIDADE = {"scopus": 0, "wos": 1, "pubmed": 2}

# Campos vazios do registro mantido são completados com os de outras cópias
CAMPOS_PREENCHER = ["doi", "resumo", "palavras_chave", "afiliacoes", "periodico",
                    "idioma", "issn", "acesso", "indice_wos"]

PARTICULAS = {"da", "de", "do", "dos", "das", "e", "del", "della",
              "van", "von", "der", "den", "la", "le", "di", "du"}


# ---------- Funções de normalização ----------
def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s)
                   if not unicodedata.combining(c))


def chave_autor(nome):
    """Padroniza para 'SOBRENOME, INICIAIS' ignorando partículas."""
    nome = sem_acento(re.sub(r"\s+", " ", nome.strip()))
    if not nome:
        return ""
    if "," in nome:                          # "Sobrenome, Nome"
        sob, resto = nome.split(",", 1)
    else:                                    # "Nome Sobrenome"
        partes = nome.split()
        if len(partes) < 2:
            return nome.upper()
        sob, resto = partes[-1], " ".join(partes[:-1])
    palavras = [p for p in re.findall(r"[A-Za-z]+", resto)
                if p.lower() not in PARTICULAS]
    iniciais = "".join(p[0] for p in palavras)
    return f"{sob.strip().upper()}, {iniciais.upper()}"


def norm_doi(d):
    """Normaliza o DOI: minúsculas, sem prefixo de URL, sem escapes do BibTeX (\\_) e sem pontuação final."""
    d = (d or "").lower().strip()
    d = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", d)
    d = d.replace("\\", "").replace(" ", "")
    d = re.sub(r"[.,;]+$", "", d)
    while d.endswith(")") and d.count(")") > d.count("("):      # parêntese final sobrando
        d = d[:-1]
    return d


def norm_titulo(t):
    t = sem_acento((t or "").lower())
    return re.sub(r"[^a-z0-9]", "", t)


# ---------- Comparação de resumos (mesma obra com DOIs diferentes) ----------
def resumo_curto(r):
    return re.sub(r"\s+", " ", (r or "").lower()).strip()[:400]


def mesma_obra(resumos, limiar=0.85):
    """True se há dois resumos quase idênticos no grupo (indício de que é a mesma obra)."""
    rs = [resumo_curto(r) for r in resumos if resumo_curto(r)]
    sims = [SequenceMatcher(None, x, y).ratio() for x, y in combinations(rs, 2)]
    return bool(sims) and max(sims) >= limiar


# ---------- Deduplicação em passadas ----------
def junta_tipos(s):
    return " | ".join(sorted({p for x in s for p in x.split(" | ") if p}))


def deduplicar(df, coluna_chave):
    """Remove duplicatas pela chave; registros com chave vazia são mantidos."""
    com_chave = df[df[coluna_chave] != ""]
    sem_chave = df[df[coluna_chave] == ""]
    fontes = com_chave.groupby(coluna_chave)["fonte"].apply(
        lambda s: "+".join(sorted(set("+".join(s).split("+")))))
    tipos = com_chave.groupby(coluna_chave)["tipo"].apply(junta_tipos)
    unicos = com_chave.drop_duplicates(subset=coluna_chave).copy()
    for col in CAMPOS_PREENCHER:
        cheio = com_chave[col].replace("", pd.NA).groupby(com_chave[coluna_chave]).transform("first")
        unicos[col] = cheio.loc[unicos.index].fillna("")
    unicos["fonte"] = unicos[coluna_chave].map(fontes)
    unicos["tipo"] = unicos[coluna_chave].map(tipos)
    return pd.concat([unicos, sem_chave]).sort_index()


# ---------- Carregar e tratar ----------
df = pd.DataFrame(ler_pasta())
total_lido = len(df)
print("\nTotal lido:", total_lido)
print(df["fonte"].value_counts())

desconhecidas = set(df["fonte"]) - set(PRIORIDADE)
if desconhecidas:
    print("ATENÇÃO: bases fora da lista de prioridade (confira os nomes dos arquivos):", desconhecidas)

df["ano"] = pd.to_numeric(df["ano"].astype(str).str.extract(r"(\d{4})")[0],
                          errors="coerce")
df["autores"] = df["autores"].apply(lambda L: [chave_autor(a) for a in L if a.strip()])
df["doi"] = df["doi"].apply(norm_doi)
df["tipo"] = df["tipo"].fillna("")

# Scopus primeiro, depois Web of Science, depois PubMed (ordem estável)
df["_ordem"] = df["fonte"].map(PRIORIDADE).fillna(99)
df = df.sort_values("_ordem", kind="stable").drop(columns="_ordem").reset_index(drop=True)

# Passada 1: DOI
df["chave_doi"] = df["doi"]
df = deduplicar(df, "chave_doi")
apos_doi = len(df)

# Passada 2: título normalizado + ano
df["chave_titulo"] = df.apply(
    lambda r: f"{norm_titulo(r['titulo'])}_{r['ano']}" if norm_titulo(r["titulo"]) else "",
    axis=1,
)

# Grupos com mais de um DOI diferente (mesmo título e ano):
#  - resumos quase idênticos  -> mesma obra com dois DOIs: são fundidos
#  - resumos diferentes ou ausentes -> NÃO são fundidos (podem ser obras distintas); ficam para conferência
com_doi = df[(df["chave_titulo"] != "") & (df["doi"] != "")]
n_doi = com_doi.groupby("chave_titulo")["doi"].nunique()
conflito = list(n_doi[n_doi > 1].index)
manter_separados = []
linhas_conf = []
for chave in conflito:
    membros = df[df["chave_titulo"] == chave]
    funde = mesma_obra(membros["resumo"])
    if not funde:
        manter_separados.append(chave)
    for _, m in membros.iterrows():
        linhas_conf.append({"titulo": m["titulo"], "ano": m["ano"], "doi": m["doi"], "fonte": m["fonte"],
                            "tipo": m["tipo"], "decisao": "fundido" if funde else "mantido separado"})
if linhas_conf:
    pd.DataFrame(linhas_conf).sort_values("titulo").to_csv("grupos_doi_conflitante.csv",
                                                           index=False, encoding="utf-8-sig")
df.loc[df["chave_titulo"].isin(manter_separados), "chave_titulo"] = ""

df = deduplicar(df, "chave_titulo")
apos_titulo = len(df)

# Classificação por tipo (depois da deduplicação)
df["classe_tipo"] = df["tipo"].apply(classifica_registro)
excluidos = df[df["classe_tipo"] == "excluir"]
excluidos.drop(columns="autores").to_csv("excluidos_por_tipo.csv",
                                         index=False, encoding="utf-8-sig")
df = df[df["classe_tipo"] != "excluir"].copy()

# Títulos repetidos entre os registros que seguem (conferência manual)
t = df["titulo"].apply(norm_titulo)
rep = df[t.duplicated(keep=False) & (t != "")].assign(_t=t).sort_values("_t")
rep[["titulo", "ano", "doi", "fonte", "tipo"]].to_csv("titulos_repetidos.csv",
                                                      index=False, encoding="utf-8-sig")

# ---------- Diagnóstico (números para o fluxograma PRISMA) ----------
print("\nRemovidos na passada 1 (DOI):", total_lido - apos_doi)
print("Removidos na passada 2 (título + ano):", apos_doi - apos_titulo)
print("Grupos com DOIs diferentes:", len(conflito), "| fundidos (resumos iguais):", len(conflito) - len(manter_separados),
      "| mantidos separados:", len(manter_separados), "(ver grupos_doi_conflitante.csv)")
print("Registros únicos:", apos_titulo)
print("Excluídos por tipo:", len(excluidos))
print("Para triagem:", len(df))
print("  dos quais 'revisar' (tipo misto ou desconhecido):",
      (df["classe_tipo"] == "revisar").sum())
print("Registros com título repetido:", len(rep), "| grupos:", rep["_t"].nunique(),
      "(ver titulos_repetidos.csv)")
print("\nSobreposição entre bases:")
print(df["fonte"].value_counts())
print("\nSem DOI:", (df["doi"] == "").sum())
print("Sem ano:", df["ano"].isna().sum())
print("Sem autores:", (df["autores"].apply(len) == 0).sum())
print("Sem resumo:", (df["resumo"] == "").sum())

# Guarda os números do fluxo para usar depois
pd.Series({
    "identificados": total_lido,
    "removidos_doi": total_lido - apos_doi,
    "removidos_titulo_ano": apos_doi - apos_titulo,
    "unicos": apos_titulo,
    "excluidos_por_tipo": len(excluidos),
    "restantes_apos_tipo": len(df),
}).to_csv("contagens_prisma.csv", header=["n"], encoding="utf-8-sig")

# Salva o resultado para os próximos passos
df.to_pickle("dados_tratados.pkl")
df.drop(columns="autores").to_csv("dados_tratados.csv", index=False, encoding="utf-8-sig")
print("\nSalvo: dados_tratados.pkl, dados_tratados.csv, excluidos_por_tipo.csv e contagens_prisma.csv")