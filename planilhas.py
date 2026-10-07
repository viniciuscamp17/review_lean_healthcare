import io
from pathlib import Path

import pandas as pd


def _ler_csv(caminho):
    texto = None
    for enc in ("utf-8-sig", "cp1252"):          # Excel em português costuma salvar em cp1252
        try:
            texto = Path(caminho).read_text(encoding=enc)
            break
        except UnicodeDecodeError:
            continue
    if texto is None:
        raise ValueError(f"Não consegui decodificar {caminho}.")
    cabecalho = texto.splitlines()[0] if texto.strip() else ""
    # Excel em português salva com ';'; o pandas grava com ','. Escolhe pelo cabeçalho.
    sep = max([",", ";", "\t"], key=cabecalho.count)
    return pd.read_csv(io.StringIO(texto), sep=sep, dtype=str).fillna("")


def ler_planilha(base, exigir=None):
    """Lê <base>.xlsx ou <base>.csv (o mais recente). Aceita ',' ou ';' e UTF-8 ou Windows-1252.
    Devolve None se nenhum dos dois existir. 'exigir' lista as colunas obrigatórias."""
    base = Path(base)
    candidatos = [base.parent / (base.name + ext) for ext in (".xlsx", ".csv")]
    existentes = [c for c in candidatos if c.exists()]
    if not existentes:
        return None
    arquivo = max(existentes, key=lambda c: c.stat().st_mtime)
    print(f"Lendo {arquivo}")
    if arquivo.suffix == ".xlsx":
        try:
            df = pd.read_excel(arquivo, dtype=str).fillna("")
        except ImportError:
            raise SystemExit("Para ler .xlsx instale o openpyxl: pip install openpyxl")
    else:
        df = _ler_csv(arquivo)
    df.columns = [str(c).strip() for c in df.columns]
    faltam = [c for c in (exigir or []) if c not in df.columns]
    if faltam:
        raise SystemExit(
            f"{arquivo}: faltam as colunas {faltam}. Colunas encontradas: {list(df.columns)[:8]}...\n"
            "Se aparecer uma coluna só com tudo junto, o CSV foi aberto sem separar as colunas: "
            "abra com Dados > De Texto/CSV (UTF-8, vírgula) ou salve como .xlsx.")
    return df