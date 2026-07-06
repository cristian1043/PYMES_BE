from flask import Blueprint, render_template

facturas = Blueprint("facturas", __name__)

@facturas.route("/Nueva_Factura")
def nueva_factura():
    return render_template("facturas/nueva_factura.html")


@facturas.route("/Ver_Factura")
def ver_facturas():
    return render_template("facturas/ver_facturas.html")


@facturas.route("/Detalle_Factura")
def detalle_factura():
    return render_template("facturas/detalle_factura.html")