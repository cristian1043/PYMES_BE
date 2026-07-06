from flask import Blueprint, render_template

reportes = Blueprint("reportes", __name__)

@reportes.route("/Reporte_Ventas")
def reporte_ventas():
    return render_template("reportes/reporte_ventas.html")


@reportes.route("/Reporte_Clientes")
def reporte_clientes():
    return render_template("reportes/reporte_clientes.html")