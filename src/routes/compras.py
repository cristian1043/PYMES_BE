from flask import Blueprint, render_template

compras = Blueprint("compras", __name__)

@compras.route("/Nueva_Compra")
def nueva_compra():
    return render_template("compras/nueva_compra.html")


@compras.route("/Ver_Compras")
def ver_compras():
    return render_template("compras/ver_compras.html")