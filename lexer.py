import re

# Expresiones regulares formales
MAPA_REGEX = {
    "CAMPO": r"^[A-Z][a-zA-Z/]+:$",
    "CODIGO": r"^[A-Z]{1,4}-\d{2,4}$",
    "NUMERO_MONEDA": r"^\d+(\.\d{1,2})?$",
    "TEXTO": r"^.+$"
}

TABLAS_RE_TEORICAS = {
    "CAMPO": {
        "estados": ["q0", "q1", "q2 (OK)"],
        "filas": [
            {"origen": "q0", "entrada": "[A-Z]", "destino": "q1"},
            {"origen": "q1", "entrada": "[a-zA-Z/]", "destino": "q1"},
            {"origen": "q1", "entrada": "':'", "destino": "q2 (OK)"}
        ]
    },
    "CODIGO": {
        "estados": ["q0", "q1", "q2", "q3 (OK)"],
        "filas": [
            {"origen": "q0", "entrada": "[A-Z]", "destino": "q1"},
            {"origen": "q1", "entrada": "'-'", "destino": "q2"},
            {"origen": "q2", "entrada": "[0-9]", "destino": "q3 (OK)"},
            {"origen": "q3 (OK)", "entrada": "[0-9]", "destino": "q3 (OK)"}
        ]
    },
    "NUMERO_MONEDA": {
        "estados": ["q0", "q1", "q2", "q3 (OK)"],
        "filas": [
            {"origen": "q0", "entrada": "[0-9]", "destino": "q1 (OK)"},
            {"origen": "q1 (OK)", "entrada": "[0-9]", "destino": "q1 (OK)"},
            {"origen": "q1 (OK)", "entrada": "'.'", "destino": "q2"},
            {"origen": "q2", "entrada": "[0-9]", "destino": "q3 (OK)"}
        ]
    }
}

def generar_grafico_automata_svg(tipo, regex_name):
    svg = []
    if regex_name == "CAMPO":
        if tipo == "AFD":
            svg.append('<svg width="100%" height="100" viewBox="0 0 400 100">')
            svg.append('<circle cx="50" cy="50" r="20" fill="none" stroke="#0ea5e9" stroke-width="2"/>\n<text x="50" y="55" text-anchor="middle" font-size="12">q0</text>')
            svg.append('<circle cx="180" cy="50" r="20" fill="none" stroke="#0ea5e9" stroke-width="2"/>\n<text x="180" y="55" text-anchor="middle" font-size="12">q1</text>')
            svg.append('<circle cx="310" cy="50" r="20" fill="none" stroke="#10b981" stroke-width="2"/>\n<circle cx="310" cy="50" r="16" fill="none" stroke="#10b981" stroke-width="1"/>\n<text x="310" y="55" text-anchor="middle" font-size="12">q2</text>')
            svg.append('<line x1="70" y1="50" x2="160" y2="50" stroke="#64748b" stroke-width="1.5"/>\n<text x="115" y="42" text-anchor="middle" font-size="10">[A-Z]</text>')
            svg.append('<path d="M 170,32 A 15,15 0 1,1 190,32" fill="none" stroke="#64748b" stroke-width="1.5"/>\n<text x="180" y="12" text-anchor="middle" font-size="10">[a-zA-Z/]</text>')
            svg.append('<line x1="200" y1="50" x2="290" y2="50" stroke="#64748b" stroke-width="1.5"/>\n<text x="245" y="42" text-anchor="middle" font-size="10">\':\'</text>')
            svg.append('</svg>')
        else:
            svg.append('<svg width="100%" height="100" viewBox="0 0 400 100">')
            svg.append('<circle cx="50" cy="50" r="20" fill="none" stroke="#f59e0b" stroke-width="2"/>\n<text x="50" y="55" text-anchor="middle" font-size="12">n0</text>')
            svg.append('<circle cx="180" cy="50" r="20" fill="none" stroke="#f59e0b" stroke-width="2"/>\n<text x="180" y="55" text-anchor="middle" font-size="12">n1</text>')
            svg.append('<circle cx="310" cy="50" r="20" fill="none" stroke="#10b981" stroke-width="2"/>\n<circle cx="310" cy="50" r="16" fill="none" stroke="#10b981" stroke-width="1"/>\n<text x="310" y="55" text-anchor="middle" font-size="12">n2</text>')
            svg.append('<line x1="70" y1="50" x2="160" y2="50" stroke="#64748b" stroke-width="1.5"/>\n<text x="115" y="42" text-anchor="middle" font-size="10">[A-Z] , ε</text>')
            svg.append('<path d="M 170,32 A 15,15 0 1,1 190,32" fill="none" stroke="#64748b" stroke-width="1.5"/>\n<text x="180" y="12" text-anchor="middle" font-size="10">[a-zA-Z]</text>')
            svg.append('<line x1="200" y1="50" x2="290" y2="50" stroke="#64748b" stroke-width="1.5"/>\n<text x="245" y="42" text-anchor="middle" font-size="10">\':\'</text>')
            svg.append('</svg>')
    elif regex_name == "CODIGO":
        if tipo == "AFD":
            svg.append('<svg width="100%" height="100" viewBox="0 0 400 100">')
            svg.append('<circle cx="40" cy="50" r="18" fill="none" stroke="#0ea5e9" stroke-width="2"/>\n<text x="40" y="54" text-anchor="middle" font-size="11">q0</text>')
            svg.append('<circle cx="140" cy="50" r="18" fill="none" stroke="#0ea5e9" stroke-width="2"/>\n<text x="140" y="54" text-anchor="middle" font-size="11">q1</text>')
            svg.append('<circle cx="240" cy="50" r="18" fill="none" stroke="#0ea5e9" stroke-width="2"/>\n<text x="240" y="54" text-anchor="middle" font-size="11">q2</text>')
            svg.append('<circle cx="340" cy="50" r="18" fill="none" stroke="#10b981" stroke-width="2"/>\n<circle cx="340" cy="50" r="14" fill="none" stroke="#10b981" stroke-width="1"/>\n<text x="340" y="54" text-anchor="middle" font-size="11">q3</text>')
            svg.append('<line x1="58" y1="50" x2="122" y2="50" stroke="#64748b" stroke-width="1.5"/>\n<text x="90" y="42" text-anchor="middle" font-size="9">[A-Z]</text>')
            svg.append('<line x1="158" y1="50" x2="222" y2="50" stroke="#64748b" stroke-width="1.5"/>\n<text x="190" y="42" text-anchor="middle" font-size="9">\'-\'</text>')
            svg.append('<line x1="258" y1="50" x2="322" y2="50" stroke="#64748b" stroke-width="1.5"/>\n<text x="290" y="42" text-anchor="middle" font-size="9">[0-9]</text>')
            svg.append('<path d="M 330,32 A 12,12 0 1,1 350,32" fill="none" stroke="#64748b" stroke-width="1.5"/>\n<text x="340" y="15" text-anchor="middle" font-size="9">[0-9]</text>')
            svg.append('</svg>')
        else:
            svg.append('<svg width="100%" height="100" viewBox="0 0 400 100">')
            svg.append('<circle cx="40" cy="50" r="18" fill="none" stroke="#f59e0b" stroke-width="2"/>\n<text x="40" y="54" text-anchor="middle" font-size="11">n0</text>')
            svg.append('<circle cx="140" cy="50" r="18" fill="none" stroke="#f59e0b" stroke-width="2"/>\n<text x="140" y="54" text-anchor="middle" font-size="11">n1</text>')
            svg.append('<circle cx="240" cy="50" r="18" fill="none" stroke="#f59e0b" stroke-width="2"/>\n<text x="240" y="54" text-anchor="middle" font-size="11">n2</text>')
            svg.append('<circle cx="340" cy="50" r="18" fill="none" stroke="#10b981" stroke-width="2"/>\n<circle cx="340" cy="50" r="14" fill="none" stroke="#10b981" stroke-width="1"/>\n<text x="340" y="54" text-anchor="middle" font-size="11">n3</text>')
            svg.append('<line x1="58" y1="50" x2="122" y2="50" stroke="#64748b" stroke-width="1.5"/>\n<text x="90" y="42" text-anchor="middle" font-size="9">[A-Z]</text>')
            svg.append('<line x1="158" y1="50" x2="222" y2="50" stroke="#64748b" stroke-width="1.5"/>\n<text x="190" y="42" text-anchor="middle" font-size="9">\'-\'</text>')
            svg.append('<line x1="258" y1="50" x2="322" y2="50" stroke="#64748b" stroke-width="1.5"/>\n<text x="290" y="42" text-anchor="middle" font-size="9">[0-9]</text>')
            svg.append('</svg>')
    else:
        svg.append('<svg width="100%" height="100" viewBox="0 0 400 100">')
        svg.append('<circle cx="40" cy="50" r="18" fill="none" stroke="#0ea5e9" stroke-width="2"/>\n<text x="40" y="54" text-anchor="middle" font-size="11">q0</text>')
        svg.append('<circle cx="140" cy="50" r="18" fill="none" stroke="#10b981" stroke-width="2"/>\n<circle cx="140" cy="50" r="14" fill="none" stroke="#10b981" stroke-width="1"/>\n<text x="140" y="54" text-anchor="middle" font-size="11">q1</text>')
        svg.append('<circle cx="240" cy="50" r="18" fill="none" stroke="#0ea5e9" stroke-width="2"/>\n<text x="240" y="54" text-anchor="middle" font-size="11">q2</text>')
        svg.append('<circle cx="340" cy="50" r="18" fill="none" stroke="#10b981" stroke-width="2"/>\n<circle cx="340" cy="50" r="14" fill="none" stroke="#10b981" stroke-width="1"/>\n<text x="340" y="54" text-anchor="middle" font-size="11">q3</text>')
        svg.append('<line x1="58" y1="50" x2="122" y2="50" stroke="#64748b" stroke-width="1.5"/>\n<text x="90" y="42" text-anchor="middle" font-size="9">[0-9]</text>')
        svg.append('<path d="M 130,32 A 12,12 0 1,1 150,32" fill="none" stroke="#64748b" stroke-width="1.5"/>\n<text x="140" y="15" text-anchor="middle" font-size="9">[0-9]</text>')
        svg.append('<line x1="158" y1="50" x2="222" y2="50" stroke="#64748b" stroke-width="1.5"/>\n<text x="190" y="42" text-anchor="middle" font-size="9">\'.\'</text>')
        svg.append('<line x1="258" y1="50" x2="322" y2="50" stroke="#64748b" stroke-width="1.5"/>\n<text x="290" y="42" text-anchor="middle" font-size="9">[0-9]</text>')
        svg.append('</svg>')
    return "".join(svg)

def analizar_lexico_completo(texto):
    lineas = [l.strip() for l in texto.split("\n") if l.strip()]
    bloque_tokens = []

    for linea in lineas:
        match = re.match(r"^([A-Z][a-zA-Z/]+:)\s*(.*)$", linea)
        if match:
            campo = match.group(1)
            valor = match.group(2).strip()
            
            t_campo = "CAMPO" if re.match(MAPA_REGEX["CAMPO"], campo) else "ERROR_LEXICO"
            regex_campo = MAPA_REGEX["CAMPO"]
            
            if re.match(MAPA_REGEX["CODIGO"], valor):
                t_valor = "CODIGO"
                regex_valor = MAPA_REGEX["CODIGO"]
            elif re.match(MAPA_REGEX["NUMERO_MONEDA"], valor):
                t_valor = "NUMERO_MONEDA"
                regex_valor = MAPA_REGEX["NUMERO_MONEDA"]
            else:
                t_valor = "TEXTO"
                regex_valor = MAPA_REGEX["TEXTO"]
            
            bloque_tokens.append({
                "campo_lex": campo, "campo_tok": t_campo, "campo_regex": regex_campo,
                "valor_lex": valor, "valor_tok": t_valor, "valor_regex": regex_valor
            })
        else:
            bloque_tokens.append({
                "campo_lex": linea, "campo_tok": "ERROR_LEXICO", "campo_regex": "Ninguno",
                "valor_lex": "", "valor_tok": "NINGUNO", "valor_regex": "Ninguno"
            })
            
    return bloque_tokens
