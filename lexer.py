import re

# CORRECCIÓN #4: el punto decimal en MONEDA ahora es OBLIGATORIO (antes era opcional
# con "?", por lo que cualquier número entero como "45" ya hacía match con MONEDA
# y la regla de NUMERO nunca se llegaba a usar). Ahora "45" -> NUMERO y "89.90" -> MONEDA.
MAPA_REGEX = {
    "CAMPO": r"^(ID|Producto|Categoria|Stock|Precio|Proveedor|Pasillo/Estante):",
    "CODIGO": r"^[A-Z]{2,4}-\d{3,4}$",
    "MONEDA": r"^\d+\.\d{1,2}$",
    "NUMERO": r"^\d+$",
    "TEXTO": r"^.+$"
}

ESTADOS = ["q0", "q1", "q2", "q3", "qerr"]
ESTADO_INICIAL = "q0"
ESTADOS_FINALES = ["q1", "q2", "q3"]
ALFABETO = ["C", "D", "S", "O"]

def obtener_definicion_afd():
    return {
        "estados": ESTADOS,
        "estado_inicial": ESTADO_INICIAL,
        "estados_finales": ESTADOS_FINALES,
        "alfabeto": ALFABETO,
        "tabla": {
            "q0": {"C": "q1", "D": "q2", "S": "q0", "O": "qerr"},
            "q1": {"C": "q1", "D": "q1", "S": "q3", "O": "qerr"},
            "q2": {"C": "qerr", "D": "q2", "S": "q3", "O": "qerr"},
            "q3": {"C": "q3", "D": "q3", "S": "q3", "O": "qerr"},
            "qerr": {"C": "qerr", "D": "qerr", "S": "qerr", "O": "qerr"}
        }
    }

def simular_afd(lexema):
    estado = ESTADO_INICIAL
    traza = [{"caracter": None, "clase": None, "desde": None, "hacia": estado}]
    tabla_transiciones = obtener_definicion_afd()["tabla"]

    for c in lexema:
        if c.isalpha() or c == " ":
            clase = "C"
        elif c.isdigit():
            clase = "D"
        elif c in [":", "-", "/", "."]:
            clase = "S"
        else:
            clase = "O"

        siguiente = tabla_transiciones.get(estado, {}).get(clase, "qerr")
        traza.append({"caracter": c, "clase": clase, "desde": estado, "hacia": siguiente})
        estado = siguiente
        if estado == "qerr":
            break

    tipo = "ERROR_LEXICO"
    if estado in ESTADOS_FINALES:
        if re.match(MAPA_REGEX["CAMPO"], lexema): tipo = "CAMPO"
        elif re.match(MAPA_REGEX["CODIGO"], lexema): tipo = "CODIGO"
        elif re.match(MAPA_REGEX["MONEDA"], lexema): tipo = "MONEDA"
        elif re.match(MAPA_REGEX["NUMERO"], lexema): tipo = "NUMERO"
        elif re.match(MAPA_REGEX["TEXTO"], lexema): tipo = "TEXTO"

    return {
        "lexema": lexema,
        "traza": traza,
        "estado_final": estado,
        "acepta": estado in ESTADOS_FINALES and tipo != "ERROR_LEXICO",
        "tipo": tipo
    }

def analizar_lexico_con_traza(texto):
    lineas = [l.strip() for l in texto.split("\n") if l.strip()]
    trazas = []
    tokens = []

    for linea in lineas:
        if ":" in linea:
            izq, der = linea.split(":", 1)
            campo = izq.strip() + ":"
            valor = der.strip()

            t_c = simular_afd(campo)
            trazas.append(t_c)
            tokens.append((campo, t_c["tipo"]))

            if valor:
                t_v = simular_afd(valor)
                trazas.append(t_v)
                tokens.append((valor, t_v["tipo"]))
        else:
            t_e = simular_afd(linea)
            trazas.append(t_e)
            tokens.append((linea, "ERROR_LEXICO"))

    return tokens, trazas
