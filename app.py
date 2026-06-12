from flask import Flask, render_template, request, session, send_file
from lexer import analizar_lexico
from parser import analizar_sintaxis
import io
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
    arbol = ""
    instruccion_texto = ""
    
    if request.method == "POST":
        # Bloque 2: Soporte para escribir texto o cargar archivo (.txt)
        if 'archivo_codigo' in request.files and request.files['archivo_codigo'].filename != '':
            file = request.files['archivo_codigo']
            instruccion_texto = file.read().decode('utf-8').strip()
        else:
            instruccion_texto = request.form.get("instruccion", "").strip()
        
        if instruccion_texto:
            tokens = analizar_lexico(instruccion_texto)
            
            # Verificar si hay errores léxicos previos
            if any(tipo == "ERROR_LEXICO" for _, tipo in tokens):
                resultado = "Error Léxico: Se detectaron caracteres o palabras inválidas."
                semantica = "✘ Falló el análisis semántico debido a errores léxicos."
            else:
                resultado = analizar_sintaxis(tokens)

            if resultado == "Instrucción válida":
                comando = tokens[0][0]
                # Traer copia local modificable del inventario en sesión
                local_inv = session['inventario']

                if comando == "AGREGAR":
                    producto = tokens[1][0]
                    cantidad = int(tokens[2][0])

                    if producto in local_inv:
                        resultado = f"Error semántico: el producto '{producto}' ya existe en el inventario."
                        semantica = "✘ Producto ya registrado."
                    else:
                        local_inv[producto] = cantidad
                        resultado = f"Producto '{producto}' agregado exitosamente."
                        semantica = "✔ Producto no registrado previamente. ✔ Cantidad válida."                  
                   
                    arbol = f"INSTRUCCION\n└─ AGREGAR\n   ├── {producto}\n   └─ {cantidad}"
                    traduccion = f"inventario['{producto}'] = {cantidad}"

                elif comando == "ACTUALIZAR":
                    producto = tokens[1][0]
                    cantidad = int(tokens[2][0])

                    if producto not in local_inv:
                        resultado = f"Error semántico: el producto '{producto}' no existe para ser actualizado."
                        semantica = "✘ Producto inexistente."
                    else:
                        local_inv[producto] = cantidad
                        resultado = f"Producto '{producto}' actualizado a una cantidad de {cantidad}."
                        semantica = "✔ Producto actualizado correctamente."
                    
                    arbol = f"INSTRUCCION\n└─ ACTUALIZAR\n   ├── {producto}\n   └─ {cantidad}"
                    traduccion = f"inventario['{producto}'] = {cantidad}"

                elif comando == "BUSCAR":
                    producto = tokens[1][0]

                    if producto in local_inv:
                        cantidad = local_inv[producto]
                        resultado = f"Resultado de búsqueda -> {producto}: {cantidad}"
                        semantica = "✔ Producto encontrado."
                    else:
                        resultado = f"Error semántico: el producto '{producto}' no fue encontrado."
                        semantica = "✘ Producto inexistente."
                    
                    arbol = f"INSTRUCCION\n└─ BUSCAR\n   └─ {producto}"
                    traduccion = f"print(inventario.get('{producto}', 'No encontrado'))"

                elif comando == "ELIMINAR":
                    producto = tokens[1][0]

                    if producto in local_inv:
                        del local_inv[producto]
                        resultado = f"Producto '{producto}' eliminado correctamente del inventario."
                        semantica = "✔ Producto eliminado."
                    else:
                        resultado = f"Error semántico: el producto '{producto}' no existe."
                        semantica = "✘ Producto inexistente."
                    
                    arbol = f"INSTRUCCION\n└─ ELIMINAR\n   └─ {producto}"
                    traduccion = f"inventario.pop('{producto}', None)"

                elif comando == "MOSTRAR":
                    if len(local_inv) == 0:
                        resultado = "El inventario actual está vacío."
                        semantica = "✔ Inventario vacío."
                    else:
                        resultado = "Estructura interna del inventario desplegada de manera óptima."
                        semantica = "✔ Inventario mostrado correctamente."

                    arbol = "INSTRUCCION\n└─ MOSTRAR"
                    traduccion = "print(inventario)"
                
                # Guardar cambios de vuelta en la sesión
                session['inventario'] = local_inv
                # Guardar traducción en sesión temporal para exportarla al PDF si se solicita
                session['ultima_traduccion'] = f"Instrucción original: {instruccion_texto}\nTraducción Generada:\n{traduccion}\nResultado: {resultado}"
                gramatica = GRAMATICA_COMPLETA
            else:
                traduccion = "No disponible (Error en fases previas)"
                gramatica = "Error: Estructura de tokens inválida para el lenguaje formal."     
                 
    return render_template(
        "index.html",
        tokens=tokens,
        resultado=resultado,
        inventario=session['inventario'],
        traduccion=traduccion,
        gramatica=gramatica,
        semantica=semantica,
        arbol=arbol,
        instruccion_antigua=instruccion_texto
    )

# Bloque 3: Descarga Obligatoria de Reporte PDF
@app.route("/exportar-pdf", methods=["GET"])
def exportar_pdf():
    traduccion_final = session.get('ultima_traduccion', 'No se ha procesado ninguna traducción válida aún.')
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 750, "REPORTE DE TRADUCCIÓN - MINI-COMPILADOR")
    p.setFont("Helvetica", 12)
    p.drawString(50, 730, "Curso: Teoría de la Computación / Compiladores")
    p.drawString(50, 715, "---------------------------------------------------------------------------------------------------------")
    
    y = 680
    p.setFont("Courier", 11)
    for linea in traduccion_final.split('\n'):
        p.drawString(50, y, linea)
        y -= 22
        if y < 50:
            p.showPage()
            y = 750
            
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="reporte_compilador.pdf", mimetype="application/pdf")

if __name__ == "__main__":
    app.run(debug=True)
