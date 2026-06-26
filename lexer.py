import re

# Expresiones regulares estrictas solicitadas por la rúbrica
MAPA_REGEX = {
    "CAMPO": r"^[A-Z][a-zA-Z/]+:$",
    "CODIGO": r"^[A-Z]{1,4}-\d{2,4}$",
    "MONEDA": r"^\d+\.\d{1,2}$",
    "NUMERO": r"^\d+$",
    "TEXTO": r"^.+$"
}

# Definición del Autómata Finito Determinista (AFD) Global
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
    """Simulación detallada de AFND y AFD requerida por la rúbrica"""
    estado_dfa = "q0"
    traza_dfa = ["q0"]
    tabla_especifica = []

    for c in lexema:
        clase = clasificar_caracter(c)
        sig_dfa = TABLA_DFA[estado_dfa].get(clase, "qerr")
        
        tabla_especifica.append({
            "caracter": c,
            "clase": clase,
            "origen": estado_dfa,
            "destino": sig_dfa
        })
        estado_dfa = sig_dfa
        traza_dfa.append(estado_dfa)

    # Reconstrucción didáctica del AFND (Conjuntos de Estados)
    estado_nfa = "{n0}"
    traza_nfa = ["{n0}"]
    for c in lexema:
        clase = clasificar_caracter(c)
        if estado_nfa == "{n0}" and clase == "C": estado_nfa = "{n0, n1}"
        elif "n1" in estado_nfa and clase == "S": estado_nfa = "{n2}"
        elif "n2" in estado_nfa: estado_nfa = "{n2}"
        else: estado_nfa = "{n_err}"
        traza_nfa.append(estado_nfa)

    # Clasificación e identificación del Agrupador de Tokens según la imagen
    tipo = "ERROR_LEXICO"
    agrupador = "Ninguno"
    if estado_dfa in ["q1", "q2", "q3"]:
        if re.match(MAPA_REGEX["CAMPO"], lexema): 
            tipo, agrupador = "CAMPO", "mis_etiquetas_control"
        elif re.match(MAPA_REGEX["CODIGO"], lexema): 
            tipo, agrupador = "CODIGO", "mis_variables_texto"
        elif re.match(MAPA_REGEX["MONEDA"], lexema): 
            tipo, agrupador = "MONEDA", "mis_variables_numericas"
        elif re.match(MAPA_REGEX["NUMERO"], lexema): 
            tipo, agrupador = "NUMERO", "mis_variables_numericas"
        elif re.match(MAPA_REGEX["TEXTO"], lexema): 
            tipo, agrupador = "TEXTO", "mis_variables_texto"

    return {
        "lexema": lexema,
        "tipo": tipo,
        "agrupador": agrupador,
        "traza_dfa": " ➔ ".join(traza_dfa),
        "traza_nfa": " ➔ ".join(traza_nfa),
        "tabla_pasos": tabla_especifica
    }

def analizar_lexico_con_traza(texto):
    lineas = [l.strip() for l in texto.split("\n") if l.strip()]
    tokens = []
    analisis_lexemas = []

    for linea in lineas:
        match_linea = re.match(r"^([A-Z][a-zA-Z/]+:)\s*(.*)$", linea)
        if match_linea:
            lex_campo = match_linea.group(1)
            lex_valor = match_linea.group(2).strip()

            res_c = simular_automatas_por_lexema(lex_campo)
            tokens.append((lex_campo, res_c["tipo"]))
            analisis_lexemas.append(res_c)

            if lex_valor:
                res_v = simular_automatas_por_lexema(lex_valor)
                tokens.append((lex_valor, res_v["tipo"]))
                analisis_lexemas.append(res_v)
        else:
            res_e = simular_automatas_por_lexema(linea)
            tokens.append((linea, "ERROR_LEXICO"))
            analisis_lexemas.append(res_e)

    return tokens, analisis_lexemas
