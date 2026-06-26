# Mapeo exacto de las producciones gramaticales analizadas
REGLAS_BNF_PRODUCCIONES = {
    "ID": "<LineaID> ::= 'ID:' <CODIGO>",
    "Producto": "<LineaProd> ::= 'Producto:' <TEXTO>",
    "Categoria": "<LineaCat> ::= 'Categoria:' <TEXTO>",
    "Stock": "<LineaStk> ::= 'Stock:' <NUMERO>",
    "Precio": "<LineaPrc> ::= 'Precio:' <MONEDA>",
    "Proveedor": "<LineaProv> ::= 'Proveedor:' <TEXTO>",
    "Pasillo/Estante": "<LineaUbi> ::= 'Pasillo/Estante:' <CODIGO>"
}

def generar_arbol_regla_svg(campo, valor, regla_txt):
    """Dibuja de forma gráfica el árbol de derivación para cada regla gramatical independiente"""
    ancho, alto = 420, 140
    svg = [f'<svg viewBox="0 0 {ancho} {alto}" width="100%" height="{alto}" xmlns="http://www.w3.org/2000/svg">']
    
    # Coordenadas de los nodos
    x_raiz, y_raiz = 210, 25
    x_hijo1, y_hijo1 = 100, 95
    x_hijo2, y_hijo2 = 320, 95
    
    # Aristas (Líneas de derivación sintáctica)
    svg.append(f'<line x1="{x_raiz}" y1="{y_raiz}" x2="{x_hijo1}" y2="{y_hijo1}" stroke="#0ea5e9" stroke-width="1.5" />')
    svg.append(f'<line x1="{x_raiz}" y1="{y_raiz}" x2="{x_hijo2}" y2="{y_hijo2}" stroke="#0ea5e9" stroke-width="1.5" />')
    
    # Nodo Raíz (Símbolo No Terminal de la Regla)
    no_terminal = f"&lt;Linea_{campo.replace('/', '_').upper()}&gt;"
    svg.append(f'<rect x="{x_raiz-85}" y="{y_raiz-12}" width="170" height="24" rx="4" fill="#f0f9ff" stroke="#0ea5e9" stroke-width="1.5"/>')
    svg.append(f'<text x="{x_raiz}" y="{y_raiz+5}" text-anchor="middle" font-family="monospace" font-size="11" font-weight="bold" fill="#0369a1">{no_terminal}</text>')
    
    # Nodo Hijo 1 (Terminal de Control / Token de Campo Estructurado)
    svg.append(f'<rect x="{x_hijo1-65}" y="{y_hijo1-12}" width="130" height="24" rx="4" fill="#f8fafc" stroke="#64748b" stroke-width="1.2"/>')
    svg.append(f'<text x="{x_hijo1}" y="{y_hijo1+5}" text-anchor="middle" font-family="monospace" font-size="10" fill="#334155">Terminal: \'{campo}:\'</text>')
    
    # Nodo Hijo 2 (Valor Derivado)
    svg.append(f'<rect x="{x_hijo2-75}" y="{y_hijo2-12}" width="150" height="24" rx="4" fill="#ecfdf5" stroke="#10b981" stroke-width="1.5"/>')
    svg.append(f'<text x="{x_hijo2}" y="{y_hijo2+5}" text-anchor="middle" font-family="monospace" font-size="10" font-weight="bold" fill="#047857">Valor: \'{valor}\'</text>')
    
    svg.append('</svg>')
    return "".join(svg)

def ejecutar_analisis_sintactico_arboles(bloque_tokens):
    mapa_valores = {}
    arboles_reglas = []
    
    for t in bloque_tokens:
        if t["campo_tok"] == "CAMPO":
            clean_key = t["campo_lex"].replace(":", "")
            mapa_valores[clean_key] = t["valor_lex"]
            
            # Construcción del árbol asociado a esta regla gramatical específica
            regla_bnf = REGLAS_BNF_PRODUCCIONES.get(clean_key, "<Regla> ::= Compilada")
            svg_arbol = generar_arbol_regla_svg(clean_key, t["valor_lex"], regla_bnf)
            arboles_reglas.append({"campo": clean_key, "regla": regla_bnf, "svg": svg_arbol})
            
    return mapa_valores, arboles_reglas
