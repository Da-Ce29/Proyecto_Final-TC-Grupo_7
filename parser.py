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
            return f"Error Sintáctico: Componente inesperado: {tokens[i][0]}", {}

    faltantes = [c for c in CAMPOS_INVENTARIO if c.replace(":", "") not in mapa_valores]
    if faltantes:
        return f"Error Sintáctico: Faltan llaves de control: {', '.join(faltantes)}", {}

    return "Ficha Válida", mapa_valores

def construir_arboles_individuales(mapa_valores):
    """Construye un AST independiente para cada campo procesado"""
    arboles_svg = []
    
    for campo, valor in mapa_valores.items():
        ast_nodo = {
            "etiqueta": f"RAMA_{campo.upper()}",
            "hijos": [
                {"etiqueta": f"Etiqueta: '{campo}:'", "hijos": []},
                {"etiqueta": f"Valor Asignado: '{valor}'", "hijos": []}
            ]
        }
        # Renderizado individualizado en formato SVG compacto
        svg_render = arbol_a_svg(ast_nodo, ancho_total=360, alto_solicitado=140)
        arboles_svg.append({"campo": campo, "svg": svg_render})
        
    return arboles_svg

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
    alto_caja, ancho_caja = 26, 160

    x_cursor = x
    for hijo in nodo["hijos"]:
        ancho_hijo_px = hijo["_ancho"] * ancho_unidad
        hx = x_cursor + ancho_hijo_px / 2
        hy = y + 55
        svg_partes.append(f'<line x1="{cx}" y1="{cy + alto_caja/2}" x2="{hx}" y2="{hy - alto_caja/2}" stroke="#0ea5e9" stroke-width="1.2" />')
        x_cursor += ancho_hijo_px

    color_borde = "#0ea5e9" if nivel == 0 else "#10b981"
    svg_partes.append(f'<rect x="{cx - ancho_caja/2}" y="{cy - alto_caja/2}" width="{ancho_caja}" height="{alto_caja}" rx="4" fill="white" stroke="{color_borde}" stroke-width="1.5" />')
    svg_partes.append(f'<text x="{cx}" y="{cy + 4}" text-anchor="middle" font-size="10" font-family="monospace" font-weight="bold" fill="#1e293b">{nodo["etiqueta"]}</text>')

    x_cursor = x
    for hijo in nodo["hijos"]:
        ancho_hijo_px = hijo["_ancho"] * ancho_unidad
        _dibujar_nodo(hijo, x_cursor, y + 55, ancho_unidad, svg_partes, nivel + 1)
        x_cursor += ancho_hijo_px

def arbol_a_svg(arbol, ancho_total=360, alto_solicitado=140):
    _calcular_anchos(arbol)
    svg_partes = []
    _dibujar_nodo(arbol, 0, 25, 170, svg_partes, nivel=0)
    return f'<svg viewBox="0 0 {ancho_total} {alto_solicitado}" xmlns="http://www.w3.org/2000/svg" width="100%" height="{alto_solicitado}"><g>{"".join(svg_partes)}</g></svg>'
