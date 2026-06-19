CAMPOS_INVENTARIO = [
    "ID:", "Producto:", "Categoria:", "Stock:", "Precio:", "Proveedor:", "Pasillo/Estante:"
]

def analizar_sintaxis(tokens):
    mapa_valores = {}
    i = 0
    limite = len(tokens)

    while i < limite:
        if tokens[i][1] == "CAMPO":
            campo_nombre = tokens[i][0].replace(":", "")
            if i + 1 < limite and tokens[i+1][1] in ["TEXTO", "NUMERO", "CODIGO", "MONEDA"]:
                mapa_valores[campo_nombre] = tokens[i+1][0]
                i += 2
            else:
                mapa_valores[campo_nombre] = ""
                i += 1
        else:
            return f"Error Sintáctico: Símbolo inesperado fuera de asignación: {tokens[i][0]}", {}

    faltantes = [c for c in CAMPOS_INVENTARIO if c.replace(":", "") not in mapa_valores]
    if faltantes:
        return f"Error Sintáctico: Faltan llaves obligatorias en el archivo: {', '.join(faltantes)}", {}

    return "Ficha Válida", mapa_valores

def construir_arbol(mapa_valores):
    hijos_identidad = [
        {"etiqueta": f"ID: {mapa_valores.get('ID')}", "hijos": []},
        {"etiqueta": f"Nombre: {mapa_valores.get('Producto')}", "hijos": []},
    ]
    hijos_logistica = [
        {"etiqueta": f"Stock: {mapa_valores.get('Stock')}", "hijos": []},
        {"etiqueta": f"Precio: {mapa_valores.get('Precio')}", "hijos": []},
        {"etiqueta": f"Ubicación: {mapa_valores.get('Pasillo/Estante')}", "hijos": []}
    ]
    return {
        "etiqueta": "FICHA_INVENTARIO_PROCESADA",
        "hijos": [
            {"etiqueta": "IDENTIFICACION", "hijos": hijos_identidad},
            {"etiqueta": "LOGISTICA_Y_COSTOS", "hijos": hijos_logistica}
        ]
    }

def _calcular_anchos(nodo):
    if not nodo["hijos"]:
        nodo["_ancho"] = 1
        return 1
    ancho = sum(_calcular_anchos(h) for h in nodo["hijos"])
    nodo["_ancho"] = ancho
    return ancho

def _dibujar_nodo(nodo, x, y, ancho_unidad, svg_partes, nivel=0):
    cx = x + (nodo["_ancho"] * ancho_unidad) / 2
    cy = y
    alto_caja, ancho_caja = 30, 180

    x_cursor = x
    for hijo in nodo["hijos"]:
        ancho_hijo_px = hijo["_ancho"] * ancho_unidad
        hx = x_cursor + ancho_hijo_px / 2
        hy = y + 80
        svg_partes.append(f'<line x1="{cx}" y1="{cy + alto_caja/2}" x2="{hx}" y2="{hy - alto_caja/2}" stroke="#0284c7" stroke-width="1.5" />')
        x_cursor += ancho_hijo_px

    color_borde = "#0284c7" if nivel == 0 else ("#d97706" if nivel == 1 else "#16a34a")
    svg_partes.append(f'<rect x="{cx - ancho_caja/2}" y="{cy - alto_caja/2}" width="{ancho_caja}" height="{alto_caja}" rx="4" fill="white" stroke="{color_borde}" stroke-width="2" />')
    svg_partes.append(f'<text x="{cx}" y="{cy + 4}" text-anchor="middle" font-size="10" font-family="monospace" font-weight="bold" fill="#1e293b">{nodo["etiqueta"]}</text>')

    x_cursor = x
    for hijo in nodo["hijos"]:
        ancho_hijo_px = hijo["_ancho"] * ancho_unidad
        _dibujar_nodo(hijo, x_cursor, y + 80, ancho_unidad, svg_partes, nivel + 1)
        x_cursor += ancho_hijo_px

def arbol_a_svg(arbol, ancho_total=600, ancho_unidad=150):
    _calcular_anchos(arbol)
    ancho_svg = max(ancho_total, arbol["_ancho"] * ancho_unidad)
    alto_svg = 260
    svg_partes = []
    _dibujar_nodo(arbol, 0, 30, ancho_unidad, svg_partes, nivel=0)
    return f'<svg viewBox="0 0 {ancho_svg} {alto_svg}" xmlns="http://www.w3.org/2000/svg" width="100%" height="{alto_svg}"><g>{"".join(svg_partes)}</g></svg>'

