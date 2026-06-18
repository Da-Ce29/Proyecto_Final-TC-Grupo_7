from flask import Flask, render_template, request, session, send_file
from lexer import analizar_lexico_con_traza, obtener_definicion_afd
from parser import analizar_sintaxis, construir_arbol, arbol_a_svg
import io
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = "mi_llave_secreta_super_segura_para_compiladores_de_inventario"

GRAMATICA_COMPLETA = """
▸ GRAMÁTICA BNF (Ficha de Producto)
<Programa>       ::= <BloqueCampos>
<BloqueCampos>   ::= <Linea> <BloqueCampos> | <Linea>
<Linea>          ::= <CAMPO> <Valor>
<Valor>          ::= <TEXTO> | <NUMERO> | <CODIGO> | <MONEDA>
"""

EXPLICACION_PROCESO = (
    "Este compilador (MiniCompilador de Inventario Estructurado) procesa fichas técnicas "
    "de productos en lote mediante 3 fases:\n"
    "1) ANÁLISIS LÉXICO: Separa las etiquetas de control (campos como 'Producto:') de sus "
    "valores mediante un Autómata Finito Determinista (AFD).\n"
    "2) ANÁLISIS SINTÁCTICO: Valida que el archivo cuente de forma estricta y ordenada con "
    "los campos requeridos para la correcta gestión de almacén.\n"
    "3) ANÁLISIS SEMÁNTICO Y TRADUCCIÓN: Comprueba coherencias (precios mayores a 0, stock no "
    "negativo) y compila la ficha a un objeto estructurado JSON listo para la base de datos."
)

AFD_DEF = obtener_definicion_afd()

def generar_svg_afd(definicion):
    posiciones = {
        "q0": (50, 100),
        "q1": (200, 40),
        "q2": (200, 160),
        "q3": (350, 100),
        "qerr": (500, 100),
    }
    partes = []
    dibujadas = set()
    for origen, trans in definicion["tabla"].items():
        for simbolo, destino in trans.items():
            if origen == destino: continue
            clave = (origen, destino)
            if clave in dibujadas: continue
            dibujadas.add(clave)
            x1, y1 = posiciones[origen]
            x2, y2 = posiciones[destino]
            partes.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arrow)" />')

    for estado, (x, y) in posiciones.items():
        es_final = estado in definicion["estados_finales"]
        relleno = "#f0fdf4" if es_final else ("#fef2f2" if estado == "qerr" else "#f0f9ff")
        borde = "#16a34a" if es_final else ("#dc2626" if estado == "qerr" else "#0284c7")
        partes.append(f'<circle cx="{x}" cy="{y}" r="26" fill="{relleno}" stroke="{borde}" stroke-width="2.5" />')
        partes.append(f'<text x="{x}" y="{y+5}" text-anchor="middle" font-size="12" font-weight="bold" fill="#1e293b">{estado}</text>')

    defs = '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#94a3b8" /></marker></defs>'
    return f'<svg viewBox="0 0 580 200" xmlns="http://www.w3.org/2000/svg" width="100%" height="200">{defs}{"".join(partes)}</svg>'

AFD_SVG = generar_svg_afd(AFD_DEF)

def formatear_traza_afd(trazas):
    bloques = []
    for t in trazas:
        pasos = [t["traza"][0]["hacia"]]
        for paso in t["traza"][1:]:
            pasos.append(f"--{paso['caracter']}({paso['clase']})--> {paso['hacia']}")
        recorrido = " ".join(pasos)
        estado_txt = "ACEPTA" if t["acepta"] else "RECHAZA"
        bloques.append(f"'{t['lexema']}': {recorrido}  =>  {estado_txt} ({t['tipo']})")
    return "\n".join(bloques) if bloques else "Esperando ficha de inventario..."

def formatear_tabla_transiciones(definicion):
    filas = []
    for estado in definicion["estados"]:
        fila = {"estado": estado, "final": estado in definicion["estados_finales"]}
        for simbolo in definicion["alfabeto"]:
            fila[simbolo] = definicion["tabla"][estado].get(simbolo, "qerr")
        filas.append(fila)
    return filas

TABLA_TRANSICIONES_VISTA = formatear_tabla_transiciones(AFD_DEF)

@app.route("/", methods=["GET", "POST"])
def inicio():
    if 'inventario' not in session:
        session['inventario'] = {}

    tokens = []
    resultado = ""
    traduccion = ""
    gramatica = ""
    semantica = ""
    instruccion_texto = ""
    arbol_svg = ""

    session['detalle_lexico'] = ""
    session['detalle_sintactico'] = ""
    session['traduccion_json'] = ""
    session['detalle_afd'] = ""

    if request.method == "POST":
        if 'archivo_codigo' in request.files and request.files['archivo_codigo'].filename != '':
            file = request.files['archivo_codigo']
            instruccion_texto = file.read().decode('utf-8').strip()
        else:
            instruccion_texto = request.form.get("instruccion", "").strip()

        if instruccion_texto:
            tokens, trazas_afd = analizar_lexico_con_traza(instruccion_texto)
            session['detalle_lexico'] = "\n".join([f"{tipo}: {lex}" for lex, tipo in tokens])
            session['detalle_afd'] = formatear_traza_afd(trazas_afd)

            if any(tipo == "ERROR_LEXICO" for _, tipo in tokens):
                resultado = "Error Léxico: Estructura de caracteres no permitida."
                semantica = "Fallo semántico debido a problemas léxicos."
            else:
                resultado, mapa_valores = analizar_sintaxis(tokens)

            if "válido" in resultado.lower():
                session['detalle_sintactico'] = f"Gramática Aplicada correctamente.\nCampos validados: {len(mapa_valores)}/7"
                arbol_dict = construir_arbol(mapa_valores)
                arbol_svg = arbol_a_svg(arbol_dict)

                # --- ANÁLISIS SEMÁNTICO (Lógica de Almacén) ---
                try:
                    stock = int(mapa_valores.get("Stock", "0"))
                    precio = float(mapa_valores.get("Precio", "0.0"))
                    id_prod = mapa_valores.get("ID")

                    if stock < 0:
                        resultado = "Error Semántico: El Stock disponible no puede ser negativo."
                        semantica = "Validación fallida: Stock inconsistente."
                    elif precio <= 0.0:
                        resultado = "Error Semántico: El Precio unitario debe ser mayor a 0."
                        semantica = "Validación fallida: Precio inválido."
                    else:
                        # Guardar o actualizar en el almacén de la sesión
                        local_inv = session['inventario']
                        local_inv[id_prod] = {
                            "Producto": mapa_valores.get("Producto"),
                            "Stock": stock,
                            "Precio": precio
                        }
                        session['inventario'] = local_inv
                        resultado = f"Producto [{id_prod}] procesado e ingresado correctamente al inventario."
                        semantica = "Validación exitosa de tipos, rangos numéricos e integridad de datos."
                except ValueError:
                    resultado = "Error Semántico: Tipos numéricos corruptos en Stock o Precio."
                    semantica = "Fallo de casteo de datos."

                if "Error" not in resultado:
                    json_output = {
                        "transaccion": "REGISTRO_INVENTARIO",
                        "estado_compilacion": "EXITOSO",
                        "datos_producto": {
                            "id_codigo": mapa_valores.get("ID"),
                            "descripcion": mapa_valores.get("Producto"),
                            "categoria": mapa_valores.get("Categoria"),
                            "proveedor": mapa_valores.get("Proveedor"),
                            "ubicacion_almacen": mapa_valores.get("Pasillo/Estante"),
                            "valores_monetarios": {
                                "precio_unitario": precio,
                                "stock_inicial": stock
                            }
                        }
                    }
                    traduccion = json.dumps(json_output, indent=2, ensure_ascii=False)
                    session['traduccion_json'] = traduccion

                    session['ultima_traduccion'] = (
                        f"REPORTE DE COMPILACIÓN DE INVENTARIOS\n\n"
                        f"1. ANALISIS LEXICO:\n{session['detalle_lexico']}\n\n"
                        f"2. ANALISIS SINTACTICO:\n{session['detalle_sintactico']}\n\n"
                        f"3. TRADUCCION TRADUCIDA (JSON):\n{session['traduccion_json']}"
                    )
            else:
                traduccion = "Fases previas fallidas."
                session['detalle_sintactico'] = f"Rechazo de Layout:\n{resultado}"

    return render_template(
        "index.html",
        tokens=tokens,
        resultado=resultado,
        inventario=session['inventario'],
        traduccion=traduccion,
        gramatica=GRAMATICA_COMPLETA,
        semantica=semantica,
        arbol_svg=arbol_svg,
        instruccion_antigua=instruccion_texto,
        explicacion_proceso=EXPLICACION_PROCESO,
        afd_svg=AFD_SVG,
        tabla_transiciones=TABLA_TRANSICIONES_VISTA,
        alfabeto_afd=AFD_DEF["alfabeto"]
    )

@app.route("/exportar-pdf", methods=["GET"])
def exportar_pdf():
    traduccion_final = session.get('ultima_traduccion', 'Sin transacciones de inventario válidas.')
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(40, 750, "REPORTE COMPILADO - CONTROL DE INVENTARIO ESTRUCTURADO")
    p.drawString(40, 725, "="*90)
    
    y = 690
    p.setFont("Courier", 9)
    for linea in traduccion_final.split('\n'):
        p.drawString(40, y, linea)
        y -= 14
        if y < 40:
            p.showPage()
            y = 750
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="reporte_inventario.pdf", mimetype="application/pdf")

if __name__ == "__main__":
    app.run(debug=True)
