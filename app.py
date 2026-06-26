from flask import Flask, render_template, request, session, send_file
from lexer import analizar_lexico_completo, generar_grafico_automata_svg, TABLAS_RE_TEORICAS
from parser import ejecutar_analisis_sintactico_arboles, GRAMATICA_FORMAL
import io
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = "teoria_de_automatas_y_gramaticas_puras_ajustadas_v3"

@app.route("/", methods=["GET", "POST"])
def inicio():
    if 'inventario' not in session: session['inventario'] = {}

    resultado, traduccion = "", ""
    tokens_individuales, grupos_valores = [], []
    arboles_reglas = []
    atributos_semanticos = {}
    
    automatas_regex = {
        "CAMPO": {"afd": generar_grafico_automata_svg("AFD", "CAMPO"), "afnd": generar_grafico_automata_svg("AFND", "CAMPO"), "tabla": TABLAS_RE_TEORICAS["CAMPO"]},
        "CODIGO": {"afd": generar_grafico_automata_svg("AFD", "CODIGO"), "afnd": generar_grafico_automata_svg("AFND", "CODIGO"), "tabla": TABLAS_RE_TEORICAS["CODIGO"]},
        "NUMERO_MONEDA": {"afd": generar_grafico_automata_svg("AFD", "NUMERO_MONEDA"), "afnd": generar_grafico_automata_svg("AFND", "NUMERO_MONEDA"), "tabla": TABLAS_RE_TEORICAS["NUMERO_MONEDA"]}
    }

    if request.method == "POST":
        if 'archivo_codigo' in request.files and request.files['archivo_codigo'].filename != '':
            file = request.files['archivo_codigo']
            try: contenido = file.read().decode('utf-8').strip()
            except UnicodeDecodeError: contenido = file.read().decode('latin-1').strip()
            
            # Análisis Léxico
            bloque_tokens = analizar_lexico_completo(contenido)
            
            lexemas_codigo = []
            lexemas_texto = []
            lexemas_moneda = []
            
            for t in bloque_tokens:
                # 1. Los TOK_... ahora se separan y van en casillas individuales
                if t["campo_tok"].startswith("TOK_"):
                    tokens_individuales.append({
                        "lex": t["campo_lex"],
                        "tok": t["campo_tok"],
                        "regex": t["campo_regex"],
                        "clase": "red"
                    })
                else:
                    if t["campo_lex"]:
                        tokens_individuales.append({
                            "lex": t["campo_lex"],
                            "tok": t["campo_tok"],
                            "regex": t["campo_regex"],
                            "clase": "red"
                        })
                
                # 2. Los valores se acumulan para juntarse por tipo de token en una sola casilla
                if t["valor_tok"] == "CODIGO":
                    lexemas_codigo.append(f'"{t["valor_lex"]}"')
                elif t["valor_tok"] == "TEXTO":
                    lexemas_texto.append(f'"{t["valor_lex"]}"')
                elif t["valor_tok"] == "NUMERO_MONEDA":
                    lexemas_moneda.append(f'"{t["valor_lex"]}"')
                elif t["valor_tok"] != "NINGUNO":
                    tokens_individuales.append({
                        "lex": t["valor_lex"],
                        "tok": t["valor_tok"],
                        "regex": t["valor_regex"],
                        "clase": "blue"
                    })
            
            # Consolidación unificada de casillas para los tokens de datos
            if lexemas_codigo:
                grupos_valores.append({
                    "lexemas": ", ".join(lexemas_codigo),
                    "token": "CODIGO",
                    "regex": r"^[A-Z]{1,4}-\d{2,4}$"
                })
            if lexemas_texto:
                grupos_valores.append({
                    "lexemas": ", ".join(lexemas_texto),
                    "token": "TEXTO",
                    "regex": r"^.+$"
                })
            if lexemas_moneda:
                grupos_valores.append({
                    "lexemas": ", ".join(lexemas_moneda),
                    "token": "NUMERO_MONEDA",
                    "regex": r"^\d+(\.\d{1,2})?$"
                })

            # Análisis Sintáctico estructurado
            mapa_valores, arboles_reglas = ejecutar_analisis_sintactico_arboles(bloque_tokens)
            
            if "ID" in mapa_valores and "Producto" in mapa_valores:
                resultado = "Análisis Estructural Completo y Válido"
                
                # Análisis Semántico
                try:
                    stock = int(mapa_valores.get("Stock", "0"))
                    precio = float(mapa_valores.get("Precio", "0.0"))
                    id_prod = mapa_valores.get("ID")
                    
                    atributos_semanticos = {
                        "heredados": [{"nodo": f"Rama_{c}", "tipo": "Asignación de Tipo", "desc": "Hereda especificación formal de token"} for c in mapa_valores.keys()],
                        "sintetizados": [{"nodo": "RAIZ_SISTEMA", "tipo": "Cálculo Comercial", "desc": f"Monto Total Inventario: S/. {stock * precio:.2f}"}]
                    }
                    
                    local_inv = session['inventario']
                    local_inv[id_prod] = {"Producto": mapa_valores.get("Producto"), "Stock": stock, "Precio": precio}
                    session['inventario'] = local_inv
                    
                    json_out = {"status": "SUCCESS", "meta": "G01 X01 Y20", "payload": mapa_valores}
                    traduccion = json.dumps(json_out, indent=2, ensure_ascii=False)
                    session['reporte'] = f"COMPILADOR REPORTE\n\nDATOS:\n{traduccion}"
                except ValueError:
                    resultado = "Error Semántico: Fallo en conversión"
            else:
                resultado = "Error Sintáctico: Estructura incompleta"

    return render_template(
        "index.html",
        resultado=resultado,
        inventario=session['inventario'],
        traduccion=traduccion,
        tokens_individuales=tokens_individuales,
        grupos_valores=grupos_valores,
        arboles_reglas=arboles_reglas,
        automatas_regex=automatas_regex,
        atributos=atributos_semanticos,
        gramatica_formal=GRAMATICA_FORMAL
    )

@app.route("/exportar-pdf")
def exportar_pdf():
    traduccion_final = session.get('reporte', 'Sin datos.')
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Courier-Bold", 12)
    p.drawString(40, 750, "REPORTE DE TRADUCCIÓN DEL MINI-COMPILADOR")
    y = 710
    p.setFont("Courier", 10)
    for linea in traduccion_final.split('\n'):
        p.drawString(40, y, linea)
        y -= 15
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="reporte.pdf", mimetype="application/pdf")

if __name__ == "__main__":
    app.run(debug=True)
