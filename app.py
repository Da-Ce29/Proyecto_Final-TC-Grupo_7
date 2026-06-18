from flask import Flask, render_template, request, session, send_file
from lexer import analizar_lexico_con_traza, obtener_definicion_afd
from parser import analizar_sintaxis, construir_arbol, arbol_a_svg
import io
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)
# Llave secreta obligatoria para poder usar 'session' en Flask
app.secret_key = "mi_llave_secreta_super_segura_para_compiladores"

GRAMATICA_COMPLETA = """
▸ GRAMÁTICA BNF
<Programa> ::= <Instruccion>
<Instruccion> ::= <Agregar> | <Eliminar> | <Buscar> | <Actualizar> | <Mostrar>
<Agregar>     ::= AGREGAR <IDENTIFICADOR> <NUMERO>
<Eliminar>    ::= ELIMINAR <IDENTIFICADOR>
<Buscar>      ::= BUSCAR <IDENTIFICADOR>
<Actualizar>  ::= ACTUALIZAR <IDENTIFICADOR> <NUMERO>
<Mostrar>     ::= MOSTRAR
"""

# Punto 1 del PPTX: breve explicación del proceso del compilador
EXPLICACION_PROCESO = (
    "Este compilador (MiniCompilador de Inventario) procesa instrucciones en un mini "
    "lenguaje propio mediante 3 fases clásicas:\n"
    "1) ANÁLISIS LÉXICO: recorre el texto carácter por carácter usando un Autómata "
    "Finito Determinista (AFD) que agrupa los caracteres en lexemas y los clasifica "
    "en tokens (PALABRA_RESERVADA, IDENTIFICADOR, NUMERO o ERROR_LEXICO).\n"
    "2) ANÁLISIS SINTÁCTICO: verifica que la secuencia de tokens respete las reglas "
    "de la gramática BNF del lenguaje y construye el árbol sintáctico de la instrucción.\n"
    "3) ANÁLISIS SEMÁNTICO Y TRADUCCIÓN: valida el significado de la instrucción contra "
    "el estado actual del inventario (p. ej. evitar duplicados o eliminar productos "
    "inexistentes) y traduce la instrucción a una representación JSON ejecutable."
)

# Definición formal del AFD (estados, alfabeto, tabla de transiciones) — Punto 3 del PPTX
AFD_DEF = obtener_definicion_afd()


def generar_svg_afd(definicion):
    """Genera un diagrama SVG simple del AFD (estados y transiciones)."""
    posiciones = {
        "q0": (70, 90),
        "q1": (260, 40),
        "q2": (260, 140),
        "qerr": (450, 90),
    }
    partes = []

    # Transiciones (flechas) entre estados distintos
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
                f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#94a3b8" '
                f'stroke-width="1.5" marker-end="url(#arrow)" />'
            )

    # Bucles propios (self-loops) representados como pequeño arco con etiqueta
    for estado, trans in definicion["tabla"].items():
        propios = [s for s, d in trans.items() if d == estado]
        if propios and estado != "qerr":
            x, y = posiciones[estado]
            partes.append(
                f'<path d="M {x-18} {y-22} C {x-40} {y-55}, {x+40} {y-55}, {x+18} {y-22}" '
                f'fill="none" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arrow)" />'
            )
            partes.append(
                f'<text x="{x}" y="{y-58}" text-anchor="middle" font-size="11" '
                f'fill="#475569">{",".join(propios)}</text>'
            )

    # Círculos de cada estado
    for estado, (x, y) in posiciones.items():
        es_final = estado in definicion["estados_finales"]
        relleno = "#f0fdf4" if es_final else ("#fef2f2" if estado == "qerr" else "#f0f9ff")
        borde = "#16a34a" if es_final else ("#dc2626" if estado == "qerr" else "#0284c7")
        partes.append(f'<circle cx="{x}" cy="{y}" r="28" fill="{relleno}" stroke="{borde}" stroke-width="2.5" />')
        if es_final:
            partes.append(f'<circle cx="{x}" cy="{y}" r="22" fill="none" stroke="{borde}" stroke-width="1.5" />')
        partes.append(
            f'<text x="{x}" y="{y+5}" text-anchor="middle" font-size="13" font-weight="bold" '
            f'fill="#1e293b">{estado}</text>'
        )

    # Flecha de entrada al estado inicial
    ix, iy = posiciones[definicion["estado_inicial"]]
    partes.append(
        f'<line x1="{ix-65}" y1="{iy}" x2="{ix-29}" y2="{iy}" stroke="#1e293b" '
        f'stroke-width="2" marker-end="url(#arrow)" />'
    )
    partes.append(f'<text x="{ix-67}" y="{iy-8}" text-anchor="end" font-size="11" fill="#1e293b">inicio</text>')

    defs = (
        '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" '
        'orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#94a3b8" /></marker></defs>'
    )
    return f'<svg viewBox="0 0 520 200" xmlns="http://www.w3.org/2000/svg" width="100%" height="200">{defs}{"".join(partes)}</svg>'


AFD_SVG = generar_svg_afd(AFD_DEF)


def formatear_traza_afd(trazas):
    """Convierte las trazas del AFD (por lexema) en texto legible para el dashboard."""
    bloques = []
    for t in trazas:
        pasos = []
        for paso in t["traza"]:
            if paso["caracter"] is None:
                pasos.append(t["traza"][0]["hacia"])
            else:
                pasos.append(f"--{paso['caracter']}({paso['clase']})--> {paso['hacia']}")
        recorrido = " ".join(pasos)
        estado_txt = "ACEPTA" if t["acepta"] else "RECHAZA"
        bloques.append(f"'{t['lexema']}': {recorrido}  =>  {estado_txt} ({t['tipo']})")
    return "\n".join(bloques) if bloques else "Esperando entrada de código..."


def formatear_tabla_transiciones(definicion):
    """Devuelve la tabla de transiciones como lista de filas para la plantilla."""
    filas = []
    for estado in definicion["estados"]:
        fila = {"estado": estado, "final": estado in definicion["estados_finales"]}
        for simbolo in definicion["alfabeto"]:
            fila[simbolo] = definicion["tabla"][estado][simbolo]
        filas.append(fila)
    return filas


TABLA_TRANSICIONES_VISTA = formatear_tabla_transiciones(AFD_DEF)


@app.route("/", methods=["GET", "POST"])
def inicio():
    # Inicializar el inventario en la sesión del usuario si no existe
    if 'inventario' not in session:
        session['inventario'] = {}

    tokens = []
    resultado = ""
    traduccion = ""
    gramatica = ""
    semantica = ""
    instruccion_texto = ""
    arbol_svg = ""

    # Inicializar las variables de sesión para el proceso detallado
    session['detalle_lexico'] = ""
    session['detalle_sintactico'] = ""
    session['traduccion_json'] = ""
    session['detalle_afd'] = ""

    if request.method == "POST":
        # Bloque 2 del PPTX: ingreso por texto o carga de archivo (.txt)
        if 'archivo_codigo' in request.files and request.files['archivo_codigo'].filename != '':
            file = request.files['archivo_codigo']
            instruccion_texto = file.read().decode('utf-8').strip()
        else:
            instruccion_texto = request.form.get("instruccion", "").strip()

        if instruccion_texto:
            tokens, trazas_afd = analizar_lexico_con_traza(instruccion_texto)

            # --- PASO 1: ANÁLISIS LÉXICO DETALLADO (Estilo comanda) ---
            lineas_lexico = []
            for lex, tipo in tokens:
                lineas_lexico.append(f"{tipo}: {lex}")
            session['detalle_lexico'] = "\n".join(lineas_lexico)

            # --- PROCESO INTERNO: traza del AFD (REGLAS / AFD / TABLA DE TRANSICIONES) ---
            session['detalle_afd'] = formatear_traza_afd(trazas_afd)

            # Verificar si hay errores léxicos previos
            if any(tipo == "ERROR_LEXICO" for _, tipo in tokens):
                resultado = "Error Léxico: Se detectaron caracteres o palabras inválidas."
                semantica = "Falló el análisis semántico debido a errores léxicos."
                session['detalle_sintactico'] = "Error: Estructura no analizable por fallas léxicas."
            else:
                resultado = analizar_sintaxis(tokens)

            if resultado == "Instrucción válida":
                comando = tokens[0][0]
                # Traer copia local modificable del inventario en sesión
                local_inv = session['inventario']

                # --- PASO 2: ANÁLISIS SINTÁCTICO DETALLADO (Estilo reglas/flechas) ---
                reglas_por_comando = {
                    "AGREGAR": "<Agregar> ::= AGREGAR <IDENTIFICADOR> <NUMERO>",
                    "ELIMINAR": "<Eliminar> ::= ELIMINAR <IDENTIFICADOR>",
                    "BUSCAR": "<Buscar> ::= BUSCAR <IDENTIFICADOR>",
                    "ACTUALIZAR": "<Actualizar> ::= ACTUALIZAR <IDENTIFICADOR> <NUMERO>",
                    "MOSTRAR": "<Mostrar> ::= MOSTRAR"
                }
                gramatica_aplicada = reglas_por_comando.get(comando, "")

                if len(tokens) == 3:
                    estructura = f"{tokens[0][0]}({tokens[1][0]}) → CANTIDAD({tokens[2][0]})"
                elif len(tokens) == 2:
                    estructura = f"{tokens[0][0]} → PRODUCTO({tokens[1][0]})"
                else:
                    estructura = f"{tokens[0][0]} (Sin parámetros)"

                session['detalle_sintactico'] = f"Gramática aplicada:\n{gramatica_aplicada}\n\nEstructura detectada:\n{estructura}\n\nEstado: Estructura aceptable"

                # --- Árbol sintáctico GRÁFICO (SVG), punto 3 del PPTX ---
                arbol_dict = construir_arbol(tokens)
                arbol_svg = arbol_a_svg(arbol_dict)

                # Lógicas Semánticas y del Negocio
                if comando == "AGREGAR":
                    producto = tokens[1][0]
                    cantidad = int(tokens[2][0])

                    if producto in local_inv:
                        resultado = f"Error semántico: el producto '{producto}' ya existe en el inventario."
                        semantica = "Producto ya registrado."
                    else:
                        local_inv[producto] = cantidad
                        resultado = f"Producto '{producto}' agregado exitosamente."
                        semantica = "Producto no registrado previamente. Cantidad válida."

                    traduccion = f"inventario['{producto}'] = {cantidad}"

                elif comando == "ACTUALIZAR":
                    producto = tokens[1][0]
                    cantidad = int(tokens[2][0])

                    if producto not in local_inv:
                        resultado = f"Error semántico: el producto '{producto}' no existe para ser actualizado."
                        semantica = "Producto inexistente."
                    else:
                        local_inv[producto] = cantidad
                        resultado = f"Producto '{producto}' actualizado a una cantidad de {cantidad}."
                        semantica = "Producto actualizado correctamente."

                    traduccion = f"inventario['{producto}'] = {cantidad}"

                elif comando == "BUSCAR":
                    producto = tokens[1][0]

                    if producto in local_inv:
                        cantidad = local_inv[producto]
                        resultado = f"Resultado de búsqueda -> {producto}: {cantidad}"
                        semantica = "Producto encontrado."
                    else:
                        resultado = f"Error semántico: el producto '{producto}' no fue encontrado."
                        semantica = "Producto inexistente."

                    traduccion = f"print(inventario.get('{producto}', 'No encontrado'))"

                elif comando == "ELIMINAR":
                    producto = tokens[1][0]

                    if producto in local_inv:
                        del local_inv[producto]
                        resultado = f"Producto '{producto}' eliminado correctamente del inventario."
                        semantica = "Producto eliminado."
                    else:
                        resultado = f"Error semántico: el producto '{producto}' no existe."
                        semantica = "Producto inexistente."

                    traduccion = f"inventario.pop('{producto}', None)"

                elif comando == "MOSTRAR":
                    if len(local_inv) == 0:
                        resultado = "El inventario actual está vacío."
                        semantica = "Inventario vacío."
                    else:
                        resultado = "Estructura interna del inventario desplegada de manera óptima."
                        semantica = "Inventario mostrado correctamente."

                    traduccion = "print(inventario)"

                # --- PASO 3: TRADUCCIÓN (JSON ESTRUCTURADO) ---
                json_output = {
                    "operacion": comando.lower(),
                    "estado_analisis": "EXITOSO",
                    "detalles": {
                        "producto": tokens[1][0] if len(tokens) > 1 else None,
                        "cantidad": int(tokens[2][0]) if len(tokens) > 2 else None
                    },
                    "respuesta_sistema": {
                        "resultado": resultado,
                        "validacion_semantica": semantica.replace("✔ ", "").replace("✘ ", "")
                    }
                }
                session['traduccion_json'] = json.dumps(json_output, indent=2, ensure_ascii=False)

                # Guardar cambios de vuelta en la sesión
                session['inventario'] = local_inv
                session['ultimo_arbol_svg'] = arbol_svg

                # Reporte combinado para el PDF
                session['ultima_traduccion'] = (
                    f"Instrucción original: {instruccion_texto}\n\n"
                    f"1. ANALISIS LEXICO:\n{session['detalle_lexico']}\n\n"
                    f"2. PROCESO INTERNO (AFD):\n{session['detalle_afd']}\n\n"
                    f"3. ANALISIS SINTACTICO:\n{session['detalle_sintactico']}\n\n"
                    f"4. TRADUCCION (JSON):\n{session['traduccion_json']}"
                )
                gramatica = GRAMATICA_COMPLETA
            else:
                traduccion = "No disponible (Error en fases previas)"
                gramatica = "Error: Estructura de tokens inválida para el lenguaje formal."
                session['detalle_sintactico'] = f"Gramática rechazada:\n{resultado}"

    return render_template(
        "index.html",
        tokens=tokens,
        resultado=resultado,
        inventario=session['inventario'],
        traduccion=traduccion,
        gramatica=gramatica,
        semantica=semantica,
        arbol_svg=arbol_svg,
        instruccion_antigua=instruccion_texto,
        explicacion_proceso=EXPLICACION_PROCESO,
        afd_svg=AFD_SVG,
        tabla_transiciones=TABLA_TRANSICIONES_VISTA,
        alfabeto_afd=AFD_DEF["alfabeto"],
    )


# Bloque 3: Descarga Obligatoria de Reporte PDF
@app.route("/exportar-pdf", methods=["GET"])
def exportar_pdf():
    traduccion_final = session.get('ultima_traduccion', 'No se ha procesado ninguna traducción válida aún.')

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 750, "REPORTE DE PROCESAMIENTO ESTRUCTURADO")
    p.setFont("Helvetica", 12)
    p.drawString(50, 730, "Curso: Teoría de la Computación / Compiladores")
    p.drawString(50, 715, "-" * 95)

    y = 680
    p.setFont("Courier", 10)
    for linea in traduccion_final.split('\n'):
        p.drawString(50, y, linea)
        y -= 18
        if y < 50:
            p.showPage()
            y = 750

    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="reporte_compilador.pdf", mimetype="application/pdf")


if __name__ == "__main__":
    app.run(debug=True)
