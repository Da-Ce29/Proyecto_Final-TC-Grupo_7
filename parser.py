GRAMATICA_FORMAL = {
    "V": ["<FICHA>", "<LINEA_ID>", "<LINEA_PROD>", "<LINEA_CAT>", "<LINEA_STK>", "<LINEA_PRE>", "<LINEA_PROV>", "<LINEA_UBI>"],
    "T": ["CAMPO", "CODIGO", "TEXTO", "NUMERO_MONEDA"],
    "S": "<FICHA>",
    "P": [
        "<FICHA>      ::= <LINEA_ID> <LINEA_PROD> <LINEA_CAT> <LINEA_STK> <LINEA_PRE> <LINEA_PROV> <LINEA_UBI>",
        "<LINEA_ID>   ::= 'ID:' CODIGO",
        "<LINEA_PROD> ::= 'Producto:' TEXTO",
        "<LINEA_CAT>  ::= 'Categoria:' TEXTO",
        "<LINEA_STK>  ::= 'Stock:' NUMERO_MONEDA",
        "<LINEA_PRE>  ::= 'Precio:' NUMERO_MONEDA",
        "<LINEA_PROV> ::= 'Proveedor:' TEXTO",
        "<LINEA_UBI>  ::= 'Pasillo/Estante:' CODIGO"
    ],
    "TIPO_DETALLADO": "Gramática Libre de Contexto Determinista (No Ambigua) / Clase LL(1)",
    "EXPLICACION_TIPO": "Es una gramática libre de contexto determinista de tipo LL(1) porque puede ser analizada de izquierda a derecha (Left-to-right scanning) mediante derivaciones por la izquierda (Leftmost derivation) utilizando un único token de preanálisis (Lookahead = 1). No posee ambigüedad ni conflictos de recursividad izquierda, permitiendo un árbol sintáctico único por producción."
}

REGLAS_BNF_PRODUCCIONES = {
    "ID": "<LineaID> ::= 'ID:' <CODIGO>",
    "Producto": "<LineaProd> ::= 'Producto:' <TEXTO>",
    "Categoria": "<LineaCat> ::= 'Categoria:' <TEXTO>",
    "Stock": "<LineaStk> ::= 'Stock:' <NUMERO_MONEDA>",
    "Precio": "<LineaPrc> ::= 'Precio:' <NUMERO_MONEDA>",
    "Proveedor": "<LineaProv> ::= 'Proveedor:' <TEXTO>",
    "Pasillo/Estante": "<LineaUbi> ::= 'Pasillo/Estante:' <CODIGO>"
}

def generar_arbol_regla_svg(campo, valor, regla_txt):
    ancho, alto = 420, 140
    svg = [f'<svg viewBox="0 0 {ancho} {alto}" width="100%" height="{alto}" xmlns="http://www.w3.org/2000/svg">']
    
    x_raiz, y_raiz = 210, 25
    x_hijo1, y_hijo1 = 100, 95
    x_hijo2, y_hijo2 = 320, 95
    
    svg.append(f'<line x1="{x_raiz}" y1="{y_raiz}" x2="{x_hijo1}" y2="{y_hijo1}" stroke="#0ea5e9" stroke-width="1.5" />')
    svg.append(f'<line x1="{x_raiz}" y1="{y_raiz}" x2="{x_hijo2}" y2="{y_hijo2}" stroke="#0ea5e9" stroke-width="1.5" />')
    
    no_terminal = f"&lt;Linea_{campo.replace('/', '_').upper()}&gt;"
    svg.append(f'<rect x="{x_raiz-85}" y="{y_raiz-12}" width="170" height="24" rx="4" fill="#f0f9ff" stroke="#0ea5e9" stroke-width="1.5"/>')
    svg.append(f'<text x="{x_raiz}" y="{y_raiz+5}" text-anchor="middle" font-family="monospace" font-size="11" font-weight="bold" fill="#0369a1">{no_terminal}</text>')
    
    svg.append(f'<rect x="{x_hijo1-65}" y="{y_hijo1-12}" width="130" height="24" rx="4" fill="#f8fafc" stroke="#64748b" stroke-width="1.2"/>')
    svg.append(f'<text x="{x_hijo1}" y="{y_hijo1+5}" text-anchor="middle" font-family="monospace" font-size="10" fill="#334155">Terminal: \'{campo}:\'</text>')
    
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
            
            regla_bnf = REGLAS_BNF_PRODUCCIONES.get(clean_key, "<Regla> ::= Compilada")
            svg_arbol = generar_arbol_regla_svg(clean_key, t["valor_lex"], regla_bnf)
            arboles_reglas.append({"campo": clean_key, "regla": regla_bnf, "svg": svg_arbol})
            
    return mapa_valores, arboles_reglas
