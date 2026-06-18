import re

# =========================================================
# CAMPOS DEL INVENTARIO
# =========================================================

CAMPOS_VALIDOS = (
    "Producto",
    "Cantidad",
    "Categoria",
    "Proveedor",
    "Codigo"
)

# =========================================================
# EXPRESIONES REGULARES
# =========================================================

REGEX_PRODUCTO = r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ0-9_\-\s]+$'
REGEX_CANTIDAD = r'^\d+$'
REGEX_CATEGORIA = r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$'
REGEX_PROVEEDOR = r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$'
REGEX_CODIGO = r'^[A-Z]{1,3}\d{1,5}$'

# =========================================================
# AFD
# =========================================================

ESTADOS = ["q0", "q1", "q2", "qerr"]

ESTADO_INICIAL = "q0"

ESTADOS_FINALES = ["q1", "q2"]

ALFABETO = ["L", "D", "O"]

TABLA_TRANSICIONES = {
    "q0": {"L": "q1", "D": "q2", "O": "qerr"},
    "q1": {"L": "q1", "D": "q1", "O": "q1"},
    "q2": {"L": "q1", "D": "q2", "O": "qerr"},
    "qerr": {"L": "qerr", "D": "qerr", "O": "qerr"}
}


def obtener_definicion_afd():
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

    estado = ESTADO_INICIAL

    traza = [
        {
            "caracter": None,
            "clase": None,
            "desde": None,
            "hacia": estado
        }
    ]

    for c in lexema:

        clase = _clasificar_caracter(c)

        siguiente = TABLA_TRANSICIONES[estado][clase]

        traza.append({
            "caracter": c,
            "clase": clase,
            "desde": estado,
            "hacia": siguiente
        })

        estado = siguiente

    acepta = estado in ESTADOS_FINALES

    return {
        "lexema": lexema,
        "traza": traza,
        "estado_final": estado,
        "acepta": acepta,
        "tipo": "LEXEMA"
    }


# =========================================================
# ANALIZADOR LEXICO PARA ARCHIVOS DE INVENTARIO
# =========================================================

def analizar_lexico(texto):

    tokens = []

    lineas = texto.splitlines()

    for linea in lineas:

        linea = linea.strip()

        if not linea:
            continue

        if ":" not in linea:
            tokens.append((linea, "ERROR_LEXICO"))
            continue

        campo, valor = linea.split(":", 1)

        campo = campo.strip()
        valor = valor.strip()

        if campo not in CAMPOS_VALIDOS:
            tokens.append((campo, "ERROR_CAMPO"))
            continue

        tokens.append((campo, "CAMPO"))

        if campo == "Cantidad":

            if re.fullmatch(REGEX_CANTIDAD, valor):
                tokens.append((valor, "NUMERO"))
            else:
                tokens.append((valor, "ERROR_CANTIDAD"))

        elif campo == "Codigo":

            if re.fullmatch(REGEX_CODIGO, valor):
                tokens.append((valor, "CODIGO"))
            else:
                tokens.append((valor, "ERROR_CODIGO"))

        else:
            tokens.append((valor, "TEXTO"))

    return tokens


def analizar_lexico_con_traza(texto):

    tokens = analizar_lexico(texto)

    trazas = []

    for lexema, tipo in tokens:

        trazas.append({
            "lexema": lexema,
            "traza": simular_afd(str(lexema))["traza"],
            "estado_final": "q1",
            "acepta": not tipo.startswith("ERROR"),
            "tipo": tipo
        })

    return tokens, trazas
