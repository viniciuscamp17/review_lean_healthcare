import re
from pathlib import Path

import rispy
from Bio import Medline

from bibleitor import ler_entradas

# Pasta onde está este script (evita erro de "pasta errada" no terminal)
PASTA = Path(__file__).parent


def limpa(t):
    t = re.sub(r"</?[A-Za-z][A-Za-z0-9:]*(\s[^<>]*)?/?>", "", t or "")   # tags HTML (<sup>, <i>...)
    t = t.replace("\\&", "&").replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", t).strip()                               # quebras de linha


def juntar(v):
    """Campos que o Biopython/rispy devolvem como lista viram texto."""
    return "; ".join(str(x) for x in v) if isinstance(v, list) else (v or "")


def separar_autores_bib(texto):
    """Nos .bib do Scopus e da Web of Science os autores são separados por ' and '."""
    return [a.strip() for a in limpa(texto).split(" and ") if a.strip()]


def ler_bib(caminho, fonte):
    with open(caminho, encoding="utf-8-sig") as f:
        entradas = ler_entradas(f.read())
    out = []
    for e in entradas:
        wos = "unique-id" in e                 # só a Web of Science tem este campo
        out.append({
            "titulo": limpa(e.get("title", "")),
            "ano": e.get("year", ""),
            "autores": separar_autores_bib(e.get("author", "")),
            "doi": e.get("doi", ""),
            "periodico": limpa(e.get("journal") or e.get("booktitle", "")),
            "resumo": limpa(e.get("abstract", "")),
            "palavras_chave": limpa(e.get("keywords", "") if wos else e.get("author_keywords", "")),
            "palavras_indexadas": limpa(e.get("keywords-plus", "") if wos else e.get("keywords", "")),
            "afiliacoes": limpa(e.get("affiliation", "") if wos else e.get("affiliations", "")),
            "idioma": e.get("language", ""),
            "tipo": limpa(e.get("type", "")),
            "acesso": e.get("oa", "") if wos else e.get("note", ""),
            "issn": e.get("issn", ""),
            "indice_wos": limpa(e.get("web-of-science-index", "")),
            "fonte": fonte,
        })
    return out


def ler_ris(caminho, fonte):
    with open(caminho, encoding="utf-8-sig") as f:
        entradas = rispy.load(f)
    return [{
        "titulo": limpa(e.get("title") or e.get("primary_title", "")),
        "ano": e.get("year") or e.get("publication_year", ""),
        "autores": e.get("authors", []),
        "doi": e.get("doi", ""),
        "periodico": limpa(e.get("journal_name") or e.get("secondary_title", "")),
        "resumo": limpa(e.get("abstract") or e.get("notes_abstract", "")),
        "palavras_chave": juntar(e.get("keywords", [])),
        "palavras_indexadas": "",
        "afiliacoes": "",
        "idioma": e.get("language", ""),
        "tipo": e.get("type_of_reference", ""),
        "acesso": "",
        "issn": e.get("issn", ""),
        "indice_wos": "",
        "fonte": fonte,
    } for e in entradas]


def ler_pubmed(caminho, fonte):
    with open(caminho, encoding="utf-8-sig") as f:
        recs = list(Medline.parse(f))
    out = []
    for r in recs:
        doi = next((a.replace(" [doi]", "") for a in r.get("AID", [])
                    if a.endswith("[doi]")), "")
        out.append({
            "titulo": limpa(r.get("TI", "")),
            "ano": r.get("DP", "")[:4],
            "autores": r.get("FAU") or r.get("AU", []),
            "doi": doi,
            "periodico": limpa(r.get("JT") or r.get("TA", "")),
            "resumo": limpa(r.get("AB", "")),
            "palavras_chave": juntar(r.get("OT", [])),
            "palavras_indexadas": juntar(r.get("MH", [])),
            "afiliacoes": juntar(r.get("AD", [])),
            "idioma": juntar(r.get("LA", [])),
            "tipo": juntar(r.get("PT", [])),
            "acesso": "",
            "issn": juntar(r.get("IS", [])),
            "indice_wos": "",
            "fonte": fonte,
        })
    return out


LEITORES = {".bib": ler_bib, ".ris": ler_ris, ".nbib": ler_pubmed}


def eh_medline(caminho):
    with open(caminho, encoding="utf-8-sig", errors="ignore") as f:
        return "PMID- " in f.read(5000)


def ler_pasta(pasta=PASTA):
    registros = []
    for arq in sorted(pasta.iterdir()):
        if arq.suffix.lower() in {".py", ".pkl", ".png", ".gexf", ".csv"} or arq.is_dir():
            continue
        leitor = LEITORES.get(arq.suffix.lower())
        if leitor is None and arq.suffix.lower() == ".txt" and eh_medline(arq):
            leitor = ler_pubmed                 # .txt no formato MEDLINE
        if leitor:
            regs = leitor(arq, arq.stem.split("_")[0])   # wos_1.bib e wos_2.bib = base "wos"
            print(f"{arq.name}: {len(regs)} registros")
            registros += regs
        else:
            print(f"IGNORADO: {arq.name}")
    return registros


if __name__ == "__main__":
    print("Pasta:", PASTA)
    print("Arquivos:", [p.name for p in PASTA.iterdir()])
    print()
    todos = ler_pasta()
    print("\nTOTAL:", len(todos))
    for fonte in sorted({r["fonte"] for r in todos}):
        n = sum(1 for r in todos if r["fonte"] == fonte)
        sem_resumo = sum(1 for r in todos if r["fonte"] == fonte and not r["resumo"])
        print(f"{fonte}: {n} registros, {sem_resumo} sem resumo")
    for fonte in sorted({r["fonte"] for r in todos}):
        exemplo = next(r for r in todos if r["fonte"] == fonte)
        print(f"\nExemplo de {fonte}:\n ", exemplo)