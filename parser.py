def analizar_sintaxis(tokens):

    if len(tokens) == 0:
        return "Error: instrucción vacía"

    comando = tokens[0][0]

    # AGREGAR producto cantidad
    if comando == "AGREGAR":

        if len(tokens) != 3:
            return "Error: AGREGAR requiere producto y cantidad"

        if tokens[1][1] != "IDENTIFICADOR":
            return "Error: nombre de producto inválido"

        if tokens[2][1] != "NUMERO":
            return "Error: cantidad inválida"

        return "Instrucción válida"

    # ELIMINAR producto
    elif comando == "ELIMINAR":

        if len(tokens) != 2:
            return "Error: ELIMINAR requiere un producto"

        return "Instrucción válida"

    # BUSCAR producto
    elif comando == "BUSCAR":

        if len(tokens) != 2:
            return "Error: BUSCAR requiere un producto"

        return "Instrucción válida"

    # ACTUALIZAR producto cantidad
    elif comando == "ACTUALIZAR":

        if len(tokens) != 3:
            return "Error: ACTUALIZAR requiere producto y cantidad"

        if tokens[1][1] != "IDENTIFICADOR":
            return "Error: nombre de producto inválido"

        if tokens[2][1] != "NUMERO":
            return "Error: cantidad inválida"

        return "Instrucción válida"

    # MOSTRAR
    elif comando == "MOSTRAR":

        if len(tokens) != 1:
            return "Error: MOSTRAR no recibe parámetros"

        return "Instrucción válida"

    else:
        return "Error: comando no reconocido"