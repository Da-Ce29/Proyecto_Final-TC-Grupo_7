from flask import Flask, render_template, request
from lexer import analizar_lexico
from parser import analizar_sintaxis

app = Flask(__name__)

inventario = {}

@app.route("/", methods=["GET", "POST"])
def inicio():
    tokens = []
    resultado = ""
    traduccion = ""
    gramatica = ""
    GRAMATICA_COMPLETA = """
    ▸ GRAMÁTICA BNF

    <Programa> ::= <Instruccion>

    <Instruccion> ::= <Agregar>
                    | <Eliminar>
                    | <Buscar>
                    | <Actualizar>
                    | <Mostrar>

    <Agregar> ::= AGREGAR <IDENTIFICADOR> <NUMERO>

    <Eliminar> ::= ELIMINAR <IDENTIFICADOR>

    <Buscar> ::= BUSCAR <IDENTIFICADOR>

    <Actualizar> ::= ACTUALIZAR <IDENTIFICADOR> <NUMERO>

    <Mostrar> ::= MOSTRAR
    """
    semantica = ""
    arbol = ""
    
    if request.method == "POST":
        instruccion = request.form["instruccion"]
        
        tokens = analizar_lexico(instruccion)
    
        resultado = analizar_sintaxis(tokens)

       
        if resultado == "Instrucción válida":
            comando = tokens[0][0]

            if comando == "AGREGAR":
                producto = tokens[1][0]
                cantidad = int(tokens[2][0])

                if producto in inventario:
                    resultado = f"Error semántico: el producto '{producto}' ya existe en el inventario."
                    semantica = "✘ Producto ya registrado."
                else:
                    inventario[producto] = cantidad
                    resultado = f"Producto '{producto}' agregado exitosamente."
                    semantica = "✔ Producto no registrado previamente. ✔ Cantidad válida."                  
               
                arbol = f"""
                INSTRUCCION
                │
                └── AGREGAR
                    ├── {producto}
                    └── {cantidad}
                """
               
                traduccion = f"inventario['{producto}'] = {cantidad}"
                gramatica = GRAMATICA_COMPLETA

            elif comando == "ACTUALIZAR":
                producto = tokens[1][0]
                cantidad = int(tokens[2][0])

                if producto not in inventario:
                    resultado = f"Error semántico: el producto '{producto}' no existe para ser actualizado."
                    semantica = "✘ Producto inexistente."
                else:
                    inventario[producto] = cantidad
                    resultado = f"Producto '{producto}' actualizado a una cantidad de {cantidad}."
                    semantica = "✔ Producto actualizado correctamente."
                
                arbol = f"""
                INSTRUCCION
                │
                └── ACTUALIZAR
                    ├── {producto}
                    └── {cantidad}
                """
                    
                traduccion = f"inventario['{producto}'] = {cantidad}"
                gramatica = GRAMATICA_COMPLETA

            elif comando == "BUSCAR":
                producto = tokens[1][0]

                if producto in inventario:
                    cantidad = inventario[producto]
                    resultado = f"Resultado de búsqueda -> {producto}: {cantidad}"
                    semantica = "✔ Producto encontrado."
                else:
                    resultado = f"Error semántico: el producto '{producto}' no fue encontrado."
                    semantica = "✘ Producto inexistente."
                
                arbol = f"""
                INSTRUCCION
                │
                └── BUSCAR
                    └── {producto}
                """
                
                traduccion = f"print(inventario.get('{producto}', 'No encontrado'))"
                gramatica = GRAMATICA_COMPLETA

            elif comando == "ELIMINAR":
                producto = tokens[1][0]

                if producto in inventario:
                    del inventario[producto]
                    resultado = f"Producto '{producto}' eliminado correctamente del inventario."
                    semantica = "✔ Producto eliminado."
                else:
                    resultado = f"Error semántico: el producto '{producto}' no existe."
                    semantica = "✘ Producto inexistente."
                
                arbol = f"""
                INSTRUCCION
                │
                └── ELIMINAR
                    └── {producto}
                """
                
                traduccion = f"inventario.pop('{producto}', None)"
                gramatica = GRAMATICA_COMPLETA

            elif comando == "MOSTRAR":

                if len(inventario) == 0:
                    resultado = "El inventario actual está vacío."
                    semantica = "✔ Inventario vacío."
                else:
                    resultado = "Estructura interna del inventario desplegada de manera óptima."
                    semantica = "✔ Inventario mostrado correctamente."

                arbol = """
                INSTRUCCION
                │
                └── MOSTRAR
                """

                traduccion = "print(inventario)"
                gramatica = GRAMATICA_COMPLETA
        else:
            traduccion = "No disponible (Error en fases previas)"
            gramatica = "Error: Estructura de tokens inválida para el lenguaje formal."     
               
    return render_template(
    "index.html",
    tokens=tokens,
    resultado=resultado,
    inventario=inventario,
    traduccion=traduccion,
    gramatica=gramatica,
    semantica=semantica,
    arbol=arbol
)

if __name__ == "__main__":
    app.run(debug=True)
    