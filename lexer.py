import re

# =========================================================
# Expresiones regulares exigidas por el dashboard
# =========================================================
REGEX_RESERVADAS = r'\b(AGREGAR|ELIMINAR|BUSCAR|ACTUALIZAR|MOSTRAR)\b'
REGEX_IDENTIFICADOR = r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'
REGEX_NUMERO = r'\b\d+\b'

PALABRAS_RESERVADAS = ("AGREGAR", "ELIMINAR", "BUSCAR", "ACTUALIZAR", "MOSTRAR")

# =========================================================
# AUTÓMATA FINITO DETERMINISTA (AFD) DEL ANALIZADOR LÉXICO
# =========================================================
# Clases de entrada (alfabeto agrupado en clases de caracteres)
#   L = Letra o guion bajo  (a-z, A-Z, _)
#   D = Dígito              (0-9)
#   O = Otro carácter (espacio, símbolo no permitido, etc.)
#
# Estados:
#   q0   -> Estado inicial
#   q1   -> Reconociendo PALABRA (identificador / palabra reservada)
#   q2   -> Reconociendo NUMERO
#   qerr -> Estado de error léxico (estado trampa)
#
# Estados finales (de aceptación): q1 y q2
ESTADOS = ["q0", "q1", "q2", "qerr"]
ESTADO_INICIAL = "q0"
ESTADOS_FINALES = ["q1", "q2"]
ALFABETO = ["L", "D", "O"]

TABLA_TRANSICIONES = {
    "q0":   {"L": "q1",   "D": "q2",   "O": "qerr"},
    "q1":   {"L": "q1",   "D": "q1",   "O": "qerr"},
    "q2":   {"L": "qerr", "D": "q2",   "O": "qerr"},
    "qerr": {"L": "qerr", "D": "qerr", "O": "qerr"},
}


def obtener_definicion_afd():
    """Devuelve la definición formal del AFD usado por el analizador léxico."""
    return {
        "estados": ESTADOS,
        "estado_inicial": ESTADO_INICIAL,
        "estados_finales": ESTADOS_FINALES,
        "alfabeto": ALFABETO,
        "tabla": TABLA_TRANSICIONES,
    }


def _clasificar_caracter(c):
    if c.isalpha() or c == "_":
        return "L"
    if c.isdigit():
        return "D"
    return "O"


def simular_afd(lexema):
    """
    Recorre el AFD carácter por carácter para un lexema dado y devuelve
    la traza de estados visitados, útil para visualizar el proceso
    interno del analizador léxico (REGLAS / AFD / TABLA DE TRANSICIONES).
    """
    estado = ESTADO_INICIAL
    traza = [{"caracter": None, "clase": None, "desde": None, "hacia": estado}]

    for c in lexema:
        clase = _clasificar_caracter(c)
        siguiente = TABLA_TRANSICIONES[estado][clase]
        traza.append({"caracter": c, "clase": clase, "desde": estado, "hacia": siguiente})
        estado = siguiente
        if estado == "qerr":
            break

    acepta = estado in ESTADOS_FINALES
    if estado == "q1":
        tipo = "PALABRA_RESERVADA" if lexema in PALABRAS_RESERVADAS else "IDENTIFICADOR"
    elif estado == "q2":
        tipo = "NUMERO"
    else:
        tipo = "ERROR_LEXICO"

    return {
        "lexema": lexema,
        "traza": traza,
        "estado_final": estado,
        "acepta": acepta,
        "tipo": tipo,
    }


def analizar_lexico(texto):
    """Analizador léxico clásico: devuelve la lista de tokens (lexema, tipo)."""
    tokens = []
    palabras = texto.split()

    for palabra in palabras:
        if re.fullmatch(REGEX_RESERVADAS, palabra):
            tokens.append((palabra, "PALABRA_RESERVADA"))
        elif re.fullmatch(REGEX_NUMERO, palabra):
            tokens.append((palabra, "NUMERO"))
        elif re.fullmatch(REGEX_IDENTIFICADOR, palabra):
            tokens.append((palabra, "IDENTIFICADOR"))
        else:
            tokens.append((palabra, "ERROR_LEXICO"))

    return tokens


def analizar_lexico_con_traza(texto):
    """
    Analiza el texto igual que analizar_lexico, pero además devuelve,
    por cada lexema, la traza de ejecución del AFD (proceso interno).
    """
    palabras = texto.split()
    trazas = [simular_afd(p) for p in palabras]
    tokens = [(t["lexema"], t["tipo"]) for t in trazas]
    return tokens, trazas
