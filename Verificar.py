import re, collections
from pathlib import Path
import bibtexparser
from bibtexparser.bparser import BibTexParser

txt = Path("scopus.bib").read_text(encoding="utf-8-sig", errors="ignore")
no_arquivo = collections.Counter(t.upper() for t in re.findall(r"^@(\w+)\s*\{", txt, flags=re.M))

parser = BibTexParser(common_strings=True, ignore_nonstandard_types=False)
db = bibtexparser.loads(txt, parser=parser)
lidos = collections.Counter(e["ENTRYTYPE"].upper() for e in db.entries)

print("No arquivo:", sum(no_arquivo.values()), dict(no_arquivo))

print("Lidos:     ", sum(lidos.values()), dict(lidos))






import re, collections
from pathlib import Path

txt = Path("scopus.bib").read_text(encoding="utf-8-sig", errors="ignore")
chaves = re.findall(r"^@\w+\s*\{\s*([^,\s]+)\s*,", txt, flags=re.M)
cont = collections.Counter(chaves)
rep = {k: v for k, v in cont.items() if v > 1}
print("Entradas:", len(chaves), "| chaves únicas:", len(cont), "| chaves repetidas:", len(rep))
print("Registros que sumiriam se só a 1ª de cada chave ficasse:", sum(v - 1 for v in rep.values()))

