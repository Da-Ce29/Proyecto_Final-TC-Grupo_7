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


# =========================================================
# CONSTRUCCIÓN DEL ÁRBOL SINTÁCTICO (estructura de datos)
# =========================================================
def construir_arbol(tokens):
    """
    Construye una representación jerárquica (dict anidado) del árbol
    sintáctico para la instrucción válida recibida. Esta estructura es
    luego utilizada para dibujar el árbol gráficamente (SVG).
    """
    if not tokens:
        return {"etiqueta": "INSTRUCCION", "hijos": []}

    comando = tokens[0][0]
    nodo_comando = {"etiqueta": comando, "hijos": []}

    if comando in ("AGREGAR", "ACTUALIZAR") and len(tokens) == 3:
        nodo_comando["hijos"] = [
            {"etiqueta": f"PRODUCTO\n{tokens[1][0]}", "hijos": []},
            {"etiqueta": f"CANTIDAD\n{tokens[2][0]}", "hijos": []},
        ]
    elif comando in ("ELIMINAR", "BUSCAR") and len(tokens) == 2:
        nodo_comando["hijos"] = [
            {"etiqueta": f"PRODUCTO\n{tokens[1][0]}", "hijos": []},
        ]
    # MOSTRAR no tiene hijos

    return {"etiqueta": "INSTRUCCION", "hijos": [nodo_comando]}


# =========================================================
# RENDERIZADO GRÁFICO DEL ÁRBOL (SVG, sin dependencias externas)
# =========================================================
def _calcular_anchos(nodo):
    """Calcula recursivamente cuántas 'hojas' ocupa cada nodo (para el layout)."""
    if not nodo["hijos"]:
        nodo["_ancho"] = 1
        return 1
    ancho = sum(_calcular_anchos(h) for h in nodo["hijos"])
    nodo["_ancho"] = ancho
    return ancho


def _dibujar_nodo(nodo, x, y, ancho_unidad, svg_partes, nivel=0):
    cx = x + (nodo["_ancho"] * ancho_unidad) / 2
    cy = y

    lineas = nodo["etiqueta"].split("\n")
    alto_caja = 26 + (len(lineas) - 1) * 16
    ancho_caja = max(70, 16 + max(len(l) for l in lineas) * 8)

    # Conectar con los hijos primero (para que las líneas queden detrás)
    x_cursor = x
    for hijo in nodo["hijos"]:
        ancho_hijo_px = hijo["_ancho"] * ancho_unidad
        hx = x_cursor + ancho_hijo_px / 2
        hy = y + 100
        svg_partes.append(
            f'<line x1="{cx}" y1="{cy + alto_caja/2}" x2="{hx}" y2="{hy - 30}" '
            f'stroke="var(--accent, #0284c7)" stroke-width="2" />'
        )
        x_cursor += ancho_hijo_px

    # Dibujar la caja del nodo actual
    color_borde = "#0284c7" if nivel == 0 else ("#d97706" if nivel == 1 else "#16a34a")
    svg_partes.append(
        f'<rect x="{cx - ancho_caja/2}" y="{cy - alto_caja/2}" width="{ancho_caja}" '
        f'height="{alto_caja}" rx="8" fill="white" stroke="{color_borde}" stroke-width="2" />'
    )
    for i, linea in enumerate(lineas):
        ty = cy - (len(lineas) - 1) * 8 + i * 16 + 4
        peso = "bold" if i == 0 else "normal"
        svg_partes.append(
            f'<text x="{cx}" y="{ty}" text-anchor="middle" font-size="12" '
            f'font-family="Consolas, monospace" font-weight="{peso}" fill="#1e293b">{linea}</text>'
        )

    # Dibujar recursivamente los hijos
    x_cursor = x
    for hijo in nodo["hijos"]:
        ancho_hijo_px = hijo["_ancho"] * ancho_unidad
        _dibujar_nodo(hijo, x_cursor, y + 100, ancho_unidad, svg_partes, nivel + 1)
        x_cursor += ancho_hijo_px


def arbol_a_svg(arbol, ancho_total=560, ancho_unidad=160):
    """Convierte la estructura jerárquica del árbol sintáctico en SVG."""
    _calcular_anchos(arbol)
    ancho_svg = max(ancho_total, arbol["_ancho"] * ancho_unidad)
    alto_svg = 100 * 3

    svg_partes = []
    _dibujar_nodo(arbol, 0, 50, ancho_unidad, svg_partes, nivel=0)

    contenido = "".join(svg_partes)
    return (
        f'<svg viewBox="0 0 {ancho_svg} {alto_svg}" xmlns="http://www.w3.org/2000/svg" '
        f'width="100%" height="{alto_svg}">{contenido}</svg>'
    )
