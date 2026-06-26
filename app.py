from flask import Flask, render_template, request, session, send_file
from lexer import analizar_lexico_con_traza
from parser import analizar_sintaxis, construir_arboles_individuales
import io
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = "clave_de_seguridad_automatas_estructurados"

# Especificación detallada de reglas BNF vinculadas a secciones específicas de la Ficha
GRAMATICA_POR_PARTES = {
    "ID": "<LineaID> ::= 'ID:' <CODIGO>\n<CODIGO>  ::= [A-Z]{1,4} '-' [0-9]{2,4}",
    "Producto": "<LineaProd> ::= 'Producto:' <TEXTO>\n<TEXTO>   ::= [A-Za-z0-9 ]+",
    "Categoria": "<LineaCat>  ::= 'Categoria:' <TEXTO>",
    "Stock": "<LineaStk>  ::= 'Stock:' <NUMERO>\n<NUMERO>   ::= [0-9]+",
    "Precio": "<LineaPrc>  ::= 'Precio:' <MONEDA>\n<MONEDA>   ::= [0-9]+ '.' [0-9]{1,2}",
    "Proveedor": "<LineaProv> ::= 'Proveedor:' <TEXTO>",
    "Pasillo/Estante": "<LineaUbi>  ::= 'Pasillo/Estante:' <CODIGO>"
}

EXPLICACION_PROCESO = (
    "Este compilador académico procesa archivos estructurados de inventario (.txt).\n"
    "Realiza un análisis léxico continuo de flujo, evalúa autómatas (NFA/DFA) de forma\n"
    "aislada por cada lexema detectado, genera árboles de análisis sintáctico (AST) individuales\n"
    "por campo y mapea sus derivaciones gramaticales BNF correspondientes."
)

@app.route("/", methods=["GET", "POST"])
def inicio():
    if 'inventario' not in session:
        session['inventario'] = {}

    tokens = []
    resultado = ""
    traduccion = ""
    semantica = ""
    arboles_lista = []
    analisis_lexemas = []

    if request.method == "POST":
        if 'archivo_codigo' in request.files and request.files['archivo_codigo'].filename != '':
            file = request.files['archivo_codigo']
            try:
                instruccion_texto = file.read().decode('utf-8').strip()
            except UnicodeDecodeError:
                instruccion_texto = file.read().decode('latin-1').strip()
            
            # Análisis Léxico Unificado
            tokens, analisis_lexemas = analizar_lexico_con_traza(instruccion_texto)
            session['detalle_lexico'] = "\n".join([f"Token -> [{tipo}]: '{lex}'" for lex, tipo in tokens])

            if any(tipo == "ERROR_LEXICO" for _, tipo in tokens):
                resultado = "Error Léxico: Se detectaron caracteres o patrones fuera del alfabeto permitido."
                semantica = "Fallo de compilación en fase léxica."
            else:
                resultado, mapa_valores = analizar_sintaxis(tokens)

            if "Error" not in resultado:
                session['detalle_sintactico'] = f"Análisis Sintáctico Exitoso.\nTotal de componentes validados: {len(mapa_valores)}"
                arboles_lista = construir_arboles_individuales(mapa_valores)

                try:
                    stock = int(mapa_valores.get("Stock", "0"))
                    precio = float(mapa_valores.get("Precio", "0.0"))
                    id_prod = mapa_valores.get("ID")

                    if stock < 0 or precio <= 0.0:
                        resultado = "Error Semántico: Valores fuera de límites comerciales tolerados."
                        semantica = "Validación Semántica Fallida: Stock negativo o precio menor/igual a cero."
                    else:
                        local_inv = session['inventario']
                        local_inv[id_prod] = {
                            "Producto": mapa_valores.get("Producto"),
                            "Stock": stock,
                            "Precio": precio
                        }
                        session['inventario'] = local_inv
                        resultado = f"Ficha del Producto [{id_prod}] Compilada y Guardada en Almacén."
                        semantica = "Consistencia semántica e integridad de tipos de datos verificada."
                except ValueError:
                    resultado = "Error Semántico: Fallo crítico de conversión de tipos numéricos."
                    semantica = "Datos corruptos detectados en análisis semántico."

                if "Error" not in resultado:
                    json_output = {
                        "objeto": "COMPILACION_PRODUCTO",
                        "propiedades": {k: v for k, v in mapa_valores.items()}
                    }
                    traduccion = json.dumps(json_output, indent=2, ensure_ascii=False)
                    session['traduccion_json'] = traduccion
                    session['ultima_traduccion'] = f"REPORTE DE COMPILACIÓN AUTOMATIZADA\n\nRESULTADO: {resultado}\n\nJSON GENERADO:\n{traduccion}"
            else:
                session['detalle_sintactico'] = f"Rechazo de Layout:\n{resultado}"
        else:
            resultado = "Error de Entrada: Por favor, suba un archivo .txt válido del inventario."

    return render_template(
        "index.html",
        tokens=tokens,
        resultado=resultado,
        inventario=session['inventario'],
        traduccion=traduccion,
        semantica=semantica,
        arboles_lista=arboles_lista,
        analisis_lexemas=analisis_lexemas,
        explicacion_proceso=EXPLICACION_PROCESO,
        gramatica_partes=GRAMATICA_POR_PARTES
    )

@app.route("/exportar-pdf", methods=["GET"])
def exportar_pdf():
    traduccion_final = session.get('ultima_traduccion', 'Sin transacciones válidas.')
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Courier-Bold", 12)
    p.drawString(40, 750, "REPORTE ACADÉMICO DE COMPILACIÓN")
    y = 720
    p.setFont("Courier", 9)
    for linea in traduccion_final.split('\n'):
        p.drawString(40, y, linea)
        y -= 15
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="reporte_compilador.pdf", mimetype="application/pdf")

if __name__ == "__main__":
    app.run(debug=True)
