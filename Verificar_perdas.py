import re
from pathlib import Path
from bibleitor import ler_entradas

txt = Path("scopus.bib").read_text(encoding="utf-8-sig", errors="ignore")

cabecalhos = re.findall(r"^@\w+\s*\{[^\n]*", txt, flags=re.M)
lidas = ler_entradas(txt)

print("Cabeçalhos no arquivo:", len(cabecalhos))
print("Entradas lidas:       ", len(lidas))

ids = {e["ID"].strip() for e in lidas}
perdidas = []
for h in cabecalhos:
    chave = h.split("{", 1)[1].split(",", 1)[0].strip()
    if chave not in ids:
        perdidas.append(h)

print("Perdidas:", len(perdidas))
for h in perdidas[:15]:
    print("  ", h[:100])