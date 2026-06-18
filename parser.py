# =========================================================
# ANALISIS SINTACTICO
# =========================================================

CAMPOS_OBLIGATORIOS = [
    "Producto",
    "Descripcion",
    "Proveedor",
    "Ubicacion",
    "Precio",
    "Stock"
]


def analizar_sintaxis(tokens):

    if not tokens:
        return "Error: archivo vacío"

    errores = [t for t in tokens if t[1].startswith("ERROR")]

    if errores:
        return f"Error léxico detectado: {errores[0][0]}"

    campos_encontrados = []

    for lexema, tipo in tokens:
        if tipo == "CAMPO":
            campos_encontrados.append(lexema)

    for campo in CAMPOS_OBLIGATORIOS:
        if campo not in campos_encontrados:
            return f"Error: falta el campo obligatorio '{campo}'"

    return "Instrucción válida"


# =========================================================
# CONSTRUCCION DEL ARBOL SINTACTICO
# =========================================================

def construir_arbol(tokens):

    datos = {}

    i = 0

    while i < len(tokens):

        if tokens[i][1] == "CAMPO":

            campo = tokens[i][0]

            if i + 1 < len(tokens):
                valor = tokens[i + 1][0]
                datos[campo] = valor

            i += 2

        else:
            i += 1

    return {
        "etiqueta": "INVENTARIO",
        "hijos": [
            {
                "etiqueta": "PRODUCTO",
                "hijos": [
                    {
                        "etiqueta": f"Producto\n{datos.get('Producto', '')}",
                        "hijos": []
                    },
                    {
                        "etiqueta": f"Descripcion\n{datos.get('Descripcion', '')}",
                        "hijos": []
                    },
                    {
                        "etiqueta": f"Proveedor\n{datos.get('Proveedor', '')}",
                        "hijos": []
                    },
                    {
                        "etiqueta": f"Ubicacion\n{datos.get('Ubicacion', '')}",
                        "hijos": []
                    },
                    {
                        "etiqueta": f"Precio\n{datos.get('Precio', '')}",
                        "hijos": []
                    },
                    {
                        "etiqueta": f"Stock\n{datos.get('Stock', '')}",
                        "hijos": []
                    }
                ]
            }
        ]
    }


# =========================================================
# RENDERIZADO SVG
# =========================================================

def _calcular_anchos(nodo):

    if not nodo["hijos"]:
        nodo["_ancho"] = 1
        return 1

    ancho = sum(_calcular_anchos(h) for h in nodo["hijos"])

    nodo["_ancho"] = ancho

    return ancho


def _dibujar_nodo(
        nodo,
        x,
        y,
        ancho_unidad,
        svg_partes,
        nivel=0
):

    cx = x + (nodo["_ancho"] * ancho_unidad) / 2

    cy = y

    lineas = nodo["etiqueta"].split("\n")

    alto_caja = 30 + (len(lineas) - 1) * 16

    ancho_caja = max(
        110,
        18 + max(len(l) for l in lineas) * 8
    )

    x_cursor = x

    for hijo in nodo["hijos"]:

        ancho_hijo_px = hijo["_ancho"] * ancho_unidad

        hx = x_cursor + ancho_hijo_px / 2

        hy = y + 100

        svg_partes.append(
            f'<line x1="{cx}" y1="{cy + alto_caja/2}" '
            f'x2="{hx}" y2="{hy - 30}" '
            f'stroke="#64748b" stroke-width="2" />'
        )

        x_cursor += ancho_hijo_px

    colores = [
        "#0284c7",
        "#16a34a",
        "#d97706",
        "#7c3aed"
    ]

    color = colores[min(nivel, len(colores)-1)]

    svg_partes.append(
        f'<rect x="{cx - ancho_caja/2}" '
        f'y="{cy - alto_caja/2}" '
        f'width="{ancho_caja}" '
        f'height="{alto_caja}" '
        f'rx="8" '
        f'fill="white" '
        f'stroke="{color}" '
        f'stroke-width="2"/>'
    )

    for i, linea in enumerate(lineas):

        ty = cy - (len(lineas)-1)*8 + i*16 + 4

        svg_partes.append(
            f'<text x="{cx}" y="{ty}" '
            f'text-anchor="middle" '
            f'font-size="12" '
            f'font-family="Consolas">'
            f'{linea}</text>'
        )

    x_cursor = x

    for hijo in nodo["hijos"]:

        ancho_hijo_px = hijo["_ancho"] * ancho_unidad

        _dibujar_nodo(
            hijo,
            x_cursor,
            y + 100,
            ancho_unidad,
            svg_partes,
            nivel + 1
        )

        x_cursor += ancho_hijo_px


def arbol_a_svg(
        arbol,
        ancho_total=1200,
        ancho_unidad=180
):

    _calcular_anchos(arbol)

    ancho_svg = max(
        ancho_total,
        arbol["_ancho"] * ancho_unidad
    )

    alto_svg = 450

    svg_partes = []

    _dibujar_nodo(
        arbol,
        0,
        50,
        ancho_unidad,
        svg_partes
    )

    return (
        f'<svg viewBox="0 0 {ancho_svg} {alto_svg}" '
        f'xmlns="http://www.w3.org/2000/svg" '
        f'width="100%" '
        f'height="{alto_svg}">'
        f'{"".join(svg_partes)}'
        f'</svg>'
    )
