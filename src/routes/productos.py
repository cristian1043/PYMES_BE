from flask import Blueprint, render_template

productos = Blueprint("productos", __name__)

@productos.route("/Nuevo_Producto")
def nuevo_producto():
    return render_template("productos/nuevo_producto.html")


@productos.route("/Ver_Producto")
def ver_productos():
    return render_template("productos/ver_productos.html")