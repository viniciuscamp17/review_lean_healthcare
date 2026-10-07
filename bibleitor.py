import re


def _valor(s, k):
    """Lê o valor de um campo a partir de s[k] (logo depois do '=')."""
    n = len(s)
    while k < n and s[k].isspace():
        k += 1
    if k >= n:
        return "", k
    if s[k] == "{":
        prof, ini = 0, k
        while k < n:
            c = s[k]
            if c == "\\":
                k += 2
                continue
            if c == "{":
                prof += 1
            elif c == "}":
                prof -= 1
                if prof == 0:
                    return s[ini + 1:k], k + 1
            k += 1
        return s[ini + 1:], n
    if s[k] == '"':
        ini = k + 1
        k = ini
        while k < n and s[k] != '"':
            k += 2 if s[k] == "\\" else 1
        return s[ini:k], k + 1
    ini = k
    while k < n and s[k] not in ",}\n":
        k += 1
    return s[ini:k].strip(), k


def ler_entradas(txt):
    """Devolve uma lista de dicionários, um por entrada @tipo{chave, campo = {valor}, ...}."""
    cabecalho = re.compile(r"@(\w+)\s*\{([^,\n]*),")
    campo = re.compile(r"\s*,?\s*([A-Za-z][\w-]*)\s*=")
    out, pos = [], 0
    while True:
        m = cabecalho.search(txt, pos)
        if not m:
            break
        entrada = {"ENTRYTYPE": m.group(1).lower(), "ID": m.group(2)}
        k = m.end()
        while True:
            c = campo.match(txt, k)
            if not c:
                break
            valor, k = _valor(txt, c.end())
            entrada[c.group(1).lower()] = valor
        out.append(entrada)
        pos = k
    return out