import re

# Definición de expresiones regulares exigidas por el dashboard
REGEX_RESERVADAS = r'\b(AGREGAR|ELIMINAR|BUSCAR|ACTUALIZAR|MOSTRAR)\b'
REGEX_IDENTIFICADOR = r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'
REGEX_NUMERO = r'\b\d+\b'

def analizar_lexico(texto):
    tokens = []
    # Separamos por espacios manteniendo un análisis limpio
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
