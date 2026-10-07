import re

ARTIGO = {"article", "journal article", "research article"}
REVISAO = {"review", "review article", "systematic review", "meta-analysis"}
NEUTROS = {"early access"}
NAO_ELEGIVEIS = {
    "conference paper", "conference review", "proceedings paper", "congress",
    "meeting abstract", "book", "book chapter", "editorial", "editorial material",
    "letter", "note", "comment", "correction", "book review", "news item",
    "erratum", "published erratum", "retracted publication",
    "retraction notice", "news", "interview",
}


def norm_tipo(t):
    return re.sub(r"\s+", " ", t.lower().strip())


def classifica_copia(rotulo):
    partes = {norm_tipo(p) for p in (rotulo or "").split(";") if p.strip()} - NEUTROS
    if not partes:
        return "sem_tipo"
    elegivel = bool(partes & (ARTIGO | REVISAO))
    inelegivel = bool(partes & NAO_ELEGIVEIS)
    if elegivel and inelegivel:
        return "revisar"            # ex.: "Article; Proceedings Paper"
    if inelegivel:
        return "excluir"
    if elegivel:
        return "manter"
    return "revisar"


def classifica_registro(tipo_unido):
    classes = [classifica_copia(r) for r in (tipo_unido or "").split(" | ")]
    if "manter" in classes:
        return "manter"
    if all(c == "excluir" for c in classes):
        return "excluir"
    return "revisar"