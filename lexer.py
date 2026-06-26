import re

# MODIFICACIÓN: Expresión de CAMPO ahora es genérica con clases de caracteres
MAPA_REGEX = {
    "CAMPO": r"^[A-Z][a-zA-Z/]+:$",
    "CODIGO": r"^[A-Z]{1,4}-\d{2,4}$",
    "MONEDA": r"^\d+\.\d{1,2}$",
    "NUMERO": r"^\d+$",
    "TEXTO": r"^.+$"
}

ESTADOS_DFA = ["q0", "q1", "q2", "q3", "qerr"]
ALFABETO = ["C", "D", "S", "O"] # C: Carácter/Letra, D: Dígito, S: Símbolo, O: Otro

TABLA_DFA = {
    "q0": {"C": "q1", "D": "q2", "S": "q0", "O": "qerr"},
    "q1": {"C": "q1", "D": "q1", "S": "q3", "O": "qerr"},
    "q2": {"C": "qerr", "D": "q2", "S": "q3", "O": "qerr"},
    "q3": {"C": "q3", "D": "q3", "S": "q3", "O": "qerr"},
    "qerr": {"C": "qerr", "D": "qerr", "S": "qerr", "O": "qerr"}
}

def clasificar_caracter(c):
    if c.isalpha() or c == " ": return "C"
    if c.isdigit(): return "D"
    if c in [":", "-", "/", "."]: return "S"
    return "O"

def simular_automatas_por_lexema(lexema):
    """Genera la simulación de DFA, NFA y tabla de transiciones para un único lexema"""
    # 1. Simulación del DFA
    estado_dfa = "q0"
    traza_dfa = ["q0"]
    tabla_especifica = []

    for c in lexema:
        clase = clasificar_caracter(c)
        sig_dfa = TABLA_DFA[estado_dfa].get(clase, "qerr")
        
        # Guardar registro para la tabla de transiciones local de este lexema
        tabla_especifica.append({
            "caracter": c,
            "clase": clase,
            "origen": estado_dfa,
            "destino": sig_dfa
        })
        estado_dfa = sig_dfa
        traza_dfa.append(estado_dfa)

    # 2. Reconstrucción Teórica del NFA correspondiente (Admitiendo transiciones no deterministas equivalentes)
    # Para fines educativos, mostramos los conjuntos de estados posibles del NFA
    estado_nfa = "{n0}"
    traza_nfa = ["{n0}"]
    for c in lexema:
        clase = clasificar_caracter(c)
        if estado_nfa == "{n0}" and clase == "C": estado_nfa = "{n0, n1}"
        elif "n1" in estado_nfa and clase == "S": estado_nfa = "{n2}"
        elif "n2" in estado_nfa: estado_nfa = "{n2}"
        else: estado_nfa = "{n_err}"
        traza_nfa.append(estado_nfa)

    # Clasificación de tipo
    tipo = "ERROR_LEXICO"
    es_valido = estado_dfa in ["q1", "q2", "q3"]
    if es_valido:
        if re.match(MAPA_REGEX["CAMPO"], lexema): tipo = "CAMPO"
        elif re.match(MAPA_REGEX["CODIGO"], lexema): tipo = "CODIGO"
        elif re.match(MAPA_REGEX["MONEDA"], lexema): tipo = "MONEDA"
        elif re.match(MAPA_REGEX["NUMERO"], lexema): tipo = "NUMERO"
        elif re.match(MAPA_REGEX["TEXTO"], lexema): tipo = "TEXTO"
        if tipo == "ERROR_LEXICO": es_valido = False

    return {
        "lexema": lexema,
        "tipo": tipo,
        "valido": es_valido,
        "traza_dfa": " ➔ ".join(traza_dfa),
        "traza_nfa": " ➔ ".join(traza_nfa),
        "tabla_pasos": tabla_especifica
    }

def analizar_lexico_con_traza(texto):
    """Analiza secuencialmente todo el archivo sin separaciones externas artificiales"""
    lineas = [l.strip() for l in texto.split("\n") if l.strip()]
    tokens = []
    analisis_por_lexema = []

    for linea in lineas:
        # Escaneo continuo buscando la separación estructural del campo ':'
        match_linea = re.match(r"^([A-Z][a-zA-Z/]+:)\s*(.*)$", linea)
        if match_linea:
            lex_campo = match_linea.group(1)
            lex_valor = match_linea.group(2).strip()

            # Procesar Campo
            res_c = simular_automatas_por_lexema(lex_campo)
            tokens.append((lex_campo, res_c["tipo"]))
            analisis_por_lexema.append(res_c)

            # Procesar Valor si existe
            if lex_valor:
                res_v = simular_automatas_por_lexema(lex_valor)
                tokens.append((lex_valor, res_v["tipo"]))
                analisis_por_lexema.append(res_v)
        else:
            # Línea corrupta sin formato de campo reconocible
            res_e = simular_automatas_por_lexema(linea)
            tokens.append((linea, "ERROR_LEXICO"))
            analisis_por_lexema.append(res_e)

    return tokens, analisis_por_lexema
