from flask import Flask, render_template, request, session, send_file
from lexer import analizar_lexico_con_traza, obtener_definicion_afd
from parser import analizar_sintaxis, construir_arbol, arbol_a_svg

import json
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = "mi_llave_secreta_super_segura_para_compiladores"

# =========================================================
# GRAMATICA
# =========================================================

GRAMATICA_COMPLETA = """
<Inventario> ::= <Producto>

<Producto> ::=
Producto : TEXTO
Cantidad : NUMERO
Categoria : TEXTO
Proveedor : TEXTO
Codigo : CODIGO
"""

# =========================================================
# EXPLICACION
# =========================================================

EXPLICACION_PROCESO = (
    "Este compilador analiza registros de productos para un inventario.\n\n"
    "1) ANÁLISIS LÉXICO:\n"
    "Reconoce campos y valores mediante expresiones regulares.\n\n"
    "2) ANÁLISIS SINTÁCTICO:\n"
    "Verifica que existan todos los campos obligatorios.\n\n"
    "3) ANÁLISIS SEMÁNTICO:\n"
    "Valida la consistencia de los datos.\n\n"
    "4) TRADUCCIÓN:\n"
    "Genera una representación JSON del producto."
)

# =========================================================
# AFD
# =========================================================

AFD_DEF = obtener_definicion_afd()


def generar_svg_afd(definicion):

    posiciones = {
        "q0": (70, 90),
        "q1": (260, 40),
        "q2": (260, 140),
        "qerr": (450, 90),
    }

    partes = []

    dibujadas = set()

    for origen, trans in definicion["tabla"].items():

        for simbolo, destino in trans.items():

            if origen == destino:
                continue

            clave = (origen, destino)

            if clave in dibujadas:
                continue

            dibujadas.add(clave)

            x1, y1 = posiciones[origen]
            x2, y2 = posiciones[destino]

            partes.append(
                f'<line x1="{x1}" y1="{y1}" '
                f'x2="{x2}" y2="{y2}" '
                f'stroke="#94a3b8" '
                f'stroke-width="1.5" '
                f'marker-end="url(#arrow)" />'
            )

    for estado, trans in definicion["tabla"].items():

        propios = [
            s for s, d in trans.items()
            if d == estado
        ]

        if propios and estado != "qerr":

            x, y = posiciones[estado]

            partes.append(
                f'<path d="M {x-18} {y-22} '
                f'C {x-40} {y-55}, '
                f'{x+40} {y-55}, '
                f'{x+18} {y-22}" '
                f'fill="none" '
                f'stroke="#94a3b8" '
                f'stroke-width="1.5" '
                f'marker-end="url(#arrow)" />'
            )

            partes.append(
                f'<text x="{x}" '
                f'y="{y-58}" '
                f'text-anchor="middle" '
                f'font-size="11">'
                f'{",".join(propios)}</text>'
            )

    for estado, (x, y) in posiciones.items():

        es_final = estado in definicion["estados_finales"]

        relleno = "#f0fdf4" if es_final else "#f0f9ff"

        if estado == "qerr":
            relleno = "#fef2f2"

        partes.append(
            f'<circle cx="{x}" cy="{y}" r="28" '
            f'fill="{relleno}" stroke="#0f172a" '
            f'stroke-width="2"/>'
        )

        partes.append(
            f'<text x="{x}" y="{y+5}" '
            f'text-anchor="middle">{estado}</text>'
        )

    defs = (
        '<defs>'
        '<marker id="arrow" markerWidth="8" markerHeight="8" '
        'refX="6" refY="3" orient="auto">'
        '<path d="M0,0 L6,3 L0,6 Z" fill="#94a3b8"/>'
        '</marker>'
        '</defs>'
    )

    return (
        f'<svg viewBox="0 0 520 200" '
        f'xmlns="http://www.w3.org/2000/svg" '
        f'width="100%" height="200">'
        f'{defs}'
        f'{"".join(partes)}'
        f'</svg>'
    )


AFD_SVG = generar_svg_afd(AFD_DEF)


def formatear_traza_afd(trazas):

    bloques = []

    for t in trazas:

        pasos = []

        for paso in t["traza"]:

            if paso["caracter"] is None:
                pasos.append("q0")

            else:
                pasos.append(
                    f"--{paso['caracter']}({paso['clase']})--> "
                    f"{paso['hacia']}"
                )

        recorrido = " ".join(pasos)

        estado = "ACEPTA" if t["acepta"] else "RECHAZA"

        bloques.append(
            f"{t['lexema']} : {recorrido} => "
            f"{estado} ({t['tipo']})"
        )

    return "\n".join(bloques)


def formatear_tabla_transiciones(definicion):

    filas = []

    for estado in definicion["estados"]:

        fila = {
            "estado": estado,
            "final": estado in definicion["estados_finales"]
        }

        for simbolo in definicion["alfabeto"]:
            fila[simbolo] = definicion["tabla"][estado][simbolo]

        filas.append(fila)

    return filas


TABLA_TRANSICIONES_VISTA = formatear_tabla_transiciones(AFD_DEF)

# =========================================================
# RUTA PRINCIPAL
# =========================================================

@app.route("/", methods=["GET", "POST"])
def inicio():

    resultado = ""
    traduccion = ""
    semantica = ""
    gramatica = GRAMATICA_COMPLETA
    instruccion_texto = ""
    arbol_svg = ""

    session["detalle_lexico"] = ""
    session["detalle_sintactico"] = ""
    session["traduccion_json"] = ""
    session["detalle_afd"] = ""

    if request.method == "POST":

        if (
            "archivo_codigo" in request.files
            and request.files["archivo_codigo"].filename != ""
        ):

            archivo = request.files["archivo_codigo"]

            instruccion_texto = (
                archivo.read()
                .decode("utf-8")
                .strip()
            )

        else:

            instruccion_texto = (
                request.form.get(
                    "instruccion",
                    ""
                ).strip()
            )

        if instruccion_texto:

            tokens, trazas = analizar_lexico_con_traza(
                instruccion_texto
            )

            session["detalle_lexico"] = "\n".join(
                f"{tipo}: {lexema}"
                for lexema, tipo in tokens
            )

            session["detalle_afd"] = formatear_traza_afd(
                trazas
            )

            resultado = analizar_sintaxis(tokens)

            if resultado == "Instrucción válida":

                session["detalle_sintactico"] = (
                    "Estructura correcta.\n"
                    "Todos los campos obligatorios encontrados."
                )

                arbol = construir_arbol(tokens)

                arbol_svg = arbol_a_svg(arbol)

                datos = {}

                i = 0

                while i < len(tokens):

                    if tokens[i][1] == "CAMPO":

                        campo = tokens[i][0]

                        if i + 1 < len(tokens):
                            datos[campo] = tokens[i + 1][0]

                        i += 2

                    else:
                        i += 1

                json_producto = {
                    "Producto": datos.get("Producto"),
                    "Cantidad": datos.get("Cantidad"),
                    "Categoria": datos.get("Categoria"),
                    "Proveedor": datos.get("Proveedor"),
                    "Codigo": datos.get("Codigo")
                }

                traduccion = json.dumps(
                    json_producto,
                    indent=4,
                    ensure_ascii=False
                )

                session["traduccion_json"] = traduccion

                semantica = (
                    "Todos los campos obligatorios "
                    "fueron validados correctamente."
                )

                session["ultimo_arbol_svg"] = arbol_svg

                session["ultima_traduccion"] = (
                    "ANALISIS LEXICO\n\n"
                    + session["detalle_lexico"]
                    + "\n\nANALISIS SINTACTICO\n\n"
                    + session["detalle_sintactico"]
                    + "\n\nJSON GENERADO\n\n"
                    + traduccion
                )

                resultado = "Registro de producto válido"

            else:

                session["detalle_sintactico"] = resultado

    return render_template(
        "index.html",
        resultado=resultado,
        traduccion=traduccion,
        gramatica=gramatica,
        semantica=semantica,
        arbol_svg=arbol_svg,
        instruccion_antigua=instruccion_texto,
        explicacion_proceso=EXPLICACION_PROCESO,
        afd_svg=AFD_SVG,
        tabla_transiciones=TABLA_TRANSICIONES_VISTA,
        alfabeto_afd=AFD_DEF["alfabeto"]
    )

# =========================================================
# PDF
# =========================================================

@app.route("/exportar-pdf")
def exportar_pdf():

    texto = session.get(
        "ultima_traduccion",
        "No hay análisis disponible."
    )

    buffer = io.BytesIO()

    p = canvas.Canvas(
        buffer,
        pagesize=letter
    )

    p.setFont("Helvetica-Bold", 16)

    p.drawString(
        50,
        750,
        "REPORTE DEL COMPILADOR"
    )

    y = 700

    p.setFont("Courier", 10)

    for linea in texto.split("\n"):

        p.drawString(
            50,
            y,
            linea
        )

        y -= 15

        if y < 50:

            p.showPage()

            y = 750

    p.save()

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="reporte_compilador.pdf",
        mimetype="application/pdf"
    )


if __name__ == "__main__":
    app.run(debug=True)
```
