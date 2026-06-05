PALABRAS_RESERVADAS = [
    "AGREGAR",
    "ELIMINAR",
    "BUSCAR",
    "ACTUALIZAR",
    "MOSTRAR"
]

def analizar_lexico(texto):

    tokens = []

    palabras = texto.split()

    for palabra in palabras:

        if palabra in PALABRAS_RESERVADAS:
            tokens.append((palabra, "PALABRA_RESERVADA"))

        elif palabra.isdigit():
            tokens.append((palabra, "NUMERO"))

        else:
            tokens.append((palabra, "IDENTIFICADOR"))

    return tokens