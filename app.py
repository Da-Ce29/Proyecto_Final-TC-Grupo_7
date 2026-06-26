from flask import Flask, render_template, request, session, send_file
from lexer import analizar_lexico_con_traza, MAPA_REGEX
from parser import analizar_sintaxis, construir_arboles_individuales, GRAMATICA_FORMAL
import io
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = "llave_secreta_computacion_teorica"

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
    "Fase Léxica: Flujo continuo de caracteres analizados por lexema mediante AFND/AFD.\n"
    "Fase Sintáctica: Agrupación estructural basada en Gramáticas Libres de Contexto G=(V,T,P,S).\n"
    "Fase Semántica: Evaluación de reglas mediante Atributos Heredados y Sintetizados."
)

@app.route("/", methods=["GET", "POST"])
def inicio():
    if 'inventario' not in session:
        session['inventario'] = {}

    resultado, traduccion = "", ""
    arboles_lista, analisis_lexemas = [], []
    atributos_semanticos = {}

    if request.method == "POST":
        if 'archivo_codigo' in request.files and request.files['archivo_codigo'].filename != '':
            file = request.files['archivo_codigo']
            try:
                contenido = file.read().decode('utf-8').strip()
            except UnicodeDecodeError:
                contenido = file.read().decode('latin-1').strip()
            
            # 1. Análisis Léxico
            tokens, analisis_lexemas = analizar_lexico_con_traza(contenido)
            
            if any(t[1] == "ERROR_LEXICO" for t in tokens):
                resultado = "Error Léxico: Símbolos o patrones fuera del alfabeto comercial."
            else:
                # 2. Análisis Sintáctico
                resultado, mapa_valores = analizar_sintaxis(tokens)

            if "Error" not in resultado:
                arboles_lista = construir_arboles_individuales(mapa_valores)
                
                # 3. Análisis Semántico (Rúbrica: Atributos Heredados y Sintetizados)
                try:
                    stock = int(mapa_valores.get("Stock", "0"))
                    precio = float(mapa_valores.get("Precio", "0.0"))
                    id_prod = mapa_valores.get("ID")

                    # Definición de Atributos para renderizado en Interfaz
                    atributos_semanticos = {
                        "heredados": [
                            {"nodo": "NODO_STOCK", "atributo": "Tipo Esperado", "valor": "Entero Puro (Inherited de etiqueta)"},
                            {"nodo": "NODO_PRECIO", "atributo": "Tipo Esperado", "valor": "Flotante Decimal (Inherited de etiqueta)"}
                        ],
                        "sintetizados": [
                            {"nodo": "RAIZ_FICHA", "atributo": "Valor Comercial Total", "valor": f"S/. {stock * precio:.2f} (Synthesized de Stock * Precio)"},
                            {"nodo": "RAIZ_FICHA", "atributo": "Consistencia de Tipos", "valor": "Válida (Tipos correctos ascendentes)"}
                        ]
                    }

                    if stock < 0 or precio <= 0.0:
                        resultado = "Error Semántico: Regla de negocio violada (Stock negativo o precio inválido)."
                    else:
                        local_inv = session['inventario']
                        local_inv[id_prod] = {
                            "Producto": mapa_valores.get("Producto"),
                            "Stock": stock,
                            "Precio": precio
                        }
                        session['inventario'] = local_inv
                        resultado = f"Producto [{id_prod}] Compilado y Registrado Exitosamente."
                except ValueError:
                    resultado = "Error Semántico: Conflicto de tipos en conversión numérica."

                if "Error" not in resultado:
                    # Traducción final requerida por la sección B de la imagen
                    json_out = {
                        "status": "COMPILADO",
                        "meta_informacion": "G01 X01 Y20",
                        "datos_objeto": {k: v for k, v in mapa_valores.items()}
                    }
                    traduccion = json.dumps(json_out, indent=2, ensure_ascii=False)
                    session['ultima_traduccion'] = f"REPORTE FORMAL DE COMPILACIÓN\nESTADO: {resultado}\n\nDATA GENERADA:\n{traduccion}"
        else:
            resultado = "Error: Archivo de texto estructurado requerido."

    return render_template(
        "index.html",
        resultado=resultado,
        inventario=session['inventario'],
        traduccion=traduccion,
        arboles_lista=arboles_lista,
        analisis_lexemas=analisis_lexemas,
        explicacion_proceso=EXPLICACION_PROCESO,
        gramatica_partes=GRAMATICA_POR_PARTES,
        gramatica_formal=GRAMATICA_FORMAL,
        atributos=atributos_semanticos,
        mapa_regex=MAPA_REGEX
    )

@app.route("/exportar-pdf")
def exportar_pdf():
    traduccion_final = session.get('ultima_traduccion', 'Sin transacciones válidas.')
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Courier-Bold", 14)
    p.drawString(40, 750, "REPORTE TÉCNICO COMPILADOR - INVENTARIO AUTOMATIZADO")
    y = 710
    p.setFont("Courier", 10)
    for linea in traduccion_final.split('\n'):
        p.drawString(40, y, linea)
        y -= 15
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="reporte_compilacion.pdf", mimetype="application/pdf")

if __name__ == "__main__":
    app.run(debug=True)
