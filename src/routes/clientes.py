from flask import Blueprint, render_template

clientes = Blueprint("clientes", __name__)

@clientes.route("/Nuevo_Clientes")
def nuevo_cliente():
    return render_template("clientes/nuevo_cliente.html")


@clientes.route("/Ver_Clientes")
def ver_clientes():
    return render_template("clientes/ver_clientes.html")