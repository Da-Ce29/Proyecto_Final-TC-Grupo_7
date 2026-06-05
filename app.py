from flask import Flask, render_template, request
from lexer import analizar_lexico
from parser import analizar_sintaxis

app = Flask(__name__)

inventario = {}

@app.route("/", methods=["GET", "POST"])
def inicio():

    tokens = []
    resultado = ""

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

                    resultado = f"Error semántico: el producto {producto} ya existe"

                else:

                    inventario[producto] = cantidad

                    resultado = f"Producto {producto} agregado con cantidad {cantidad}"
            
            elif comando == "ACTUALIZAR":

                producto = tokens[1][0]
                cantidad = int(tokens[2][0])

                if producto not in inventario:

                    resultado = f"Error semántico: el producto {producto} no existe"

                else:

                    inventario[producto] = cantidad

                    resultado = f"Producto {producto} actualizado a {cantidad}"
            
            elif comando == "BUSCAR":

                producto = tokens[1][0]

                if producto in inventario:

                    cantidad = inventario[producto]

                    resultado = f"{producto}: {cantidad}"

                else:

                    resultado = f"Producto {producto} no encontrado"
            
            elif comando == "ELIMINAR":

                producto = tokens[1][0]

                if producto in inventario:

                    del inventario[producto]

                    resultado = f"Producto {producto} eliminado"
                        
                else:

                    resultado = f"Producto {producto} no existe"
            
            elif comando == "MOSTRAR":

                if len(inventario) == 0:

                    resultado = "El inventario está vacío"

                else:

                    resultado = "Inventario mostrado correctamente"
                
    return render_template(
        "index.html",
        tokens=tokens,
        resultado=resultado,
        inventario=inventario
    )

if __name__ == "__main__":
    app.run(debug=True)