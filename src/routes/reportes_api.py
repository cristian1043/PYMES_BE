from flask import Blueprint, jsonify
from src.controllers.reportes_controller import ReportesController

reportes_bp = Blueprint("reportes", __name__)

# ===========================
# Reporte Financiero de Ventas
# ===========================
@reportes_bp.route("/ventas", methods=["GET"])
def get_reporte_ventas():
    resumen = ReportesController.get_reporte_ventas()
    return jsonify(resumen), 200

# ===========================
# Reporte Comercial de Clientes
# ===========================
@reportes_bp.route("/clientes", methods=["GET"])
def get_reporte_clientes():
    ranking = ReportesController.get_reporte_clientes()
    return jsonify(ranking), 200

# ===========================
# Reporte Operativo de Inventario
# ===========================
@reportes_bp.route("/inventario", methods=["GET"])
def get_reporte_inventario():
    inventario = ReportesController.get_reporte_inventario()
    return jsonify(inventario), 200

# ===========================
# Reporte Comercial de Top Productos
# ===========================
@reportes_bp.route("/top-productos", methods=["GET"])
def get_reporte_top_productos():
    ranking = ReportesController.get_reporte_top_productos()
    return jsonify(ranking), 200

