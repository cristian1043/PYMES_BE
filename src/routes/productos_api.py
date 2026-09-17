from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from src.controllers.productos_controller import ProductosController
from src.utils.pagination import get_pagination_params
from src.utils.security import roles_required, tenant_required

productos_bp = Blueprint("productos", __name__)

def validar_acceso_producto(producto):
    if not producto or not producto.id_empresa:
        return True
    claims = get_jwt() or {}
    id_rol = claims.get("id_rol", 0)
    rol = claims.get("rol", "")
    if id_rol == 1 or rol == "Administrador":
        return True
    empresas = [int(e) for e in claims.get("empresas", []) if str(e).isdigit()]
    if int(producto.id_empresa) in empresas:
        return True
    user_id = get_jwt_identity()
    from src.models.usuario_empresas import UsuarioEmpresas
    vinc = UsuarioEmpresas.get_by_usuario_empresa(user_id, producto.id_empresa) if user_id else None
    return vinc is not None and vinc.estado == "Activo"

# ===========================
# Obtener productos (con paginación)
# ===========================
@productos_bp.route("/", methods=["GET"])
@jwt_required()
@tenant_required(allow_global_admin=True)
def get_productos():
    page, per_page = get_pagination_params()
    empresa_id = (
        request.args.get("empresa_id") or 
        request.args.get("id_empresa") or 
        request.headers.get("X-Empresa-ID") or 
        request.environ.get('tenant_empresa_id')
    )
    resultado = ProductosController.get_paginated(page, per_page, empresa_id=empresa_id)
    return jsonify(resultado), 200

# ===========================
# Obtener el siguiente código de producto
# ===========================
@productos_bp.route("/siguiente_codigo", methods=["GET"])
@jwt_required()
def get_siguiente_codigo():
    empresa_id = (
        request.args.get("empresa_id") or 
        request.args.get("id_empresa") or 
        request.headers.get("X-Empresa-ID") or 
        request.environ.get('tenant_empresa_id')
    )
    codigo = ProductosController.obtener_siguiente_codigo(empresa_id=empresa_id)
    return jsonify({"siguiente_codigo": codigo}), 200

# ===========================
# Obtener un producto por ID
# ===========================
@productos_bp.route("/<int:id>", methods=["GET"])
@jwt_required()
def get_producto(id):
    producto = ProductosController.get_by_id(id)
    if not producto:
        return jsonify({"mensaje": "Producto no encontrado"}), 404
    if not validar_acceso_producto(producto):
        return jsonify({"exito": False, "mensaje": "Acceso denegado: El producto no pertenece a la empresa autorizada."}), 403
    return jsonify(producto.to_dict()), 200

# ===========================
# Crear producto
# ===========================
@productos_bp.route("/", methods=["POST"])
@jwt_required()
@roles_required("Administrador", "Vendedor", "Almacenista", 1, 2, 3)
@tenant_required(allow_global_admin=True)
def create_producto():
    data = request.get_json() or {}
    if not data.get("id_empresa"):
        emp_id = (
            request.headers.get("X-Empresa-ID") or 
            request.args.get("empresa_id") or 
            request.args.get("id_empresa") or 
            request.environ.get('tenant_empresa_id')
        )
        if emp_id:
            data["id_empresa"] = emp_id
    try:
        producto = ProductosController.create(data)
        return jsonify(producto.to_dict()), 201
    except ValueError as ve:
        return jsonify({"exito": False, "mensaje": str(ve)}), 400

# ===========================
# Actualizar producto
# ===========================
@productos_bp.route("/<int:id>", methods=["PUT"])
@jwt_required()
@roles_required("Administrador", "Vendedor", "Almacenista", 1, 2, 3)
def update_producto(id):
    producto = ProductosController.get_by_id(id)
    if not producto:
        return jsonify({"mensaje": "Producto no encontrado"}), 404
    if not validar_acceso_producto(producto):
        return jsonify({"exito": False, "mensaje": "Acceso denegado: No tiene permisos sobre productos de esta empresa."}), 403
    data = request.get_json() or {}
    producto_actualizado = ProductosController.update(id, data)
    return jsonify(producto_actualizado.to_dict()), 200

# ===========================
# Cambiar estado del producto (Activar / Desactivar)
# ===========================
@productos_bp.route("/<int:id>/estado", methods=["PATCH"])
@jwt_required()
@roles_required("Administrador", 1)
def toggle_estado_producto(id):
    producto = ProductosController.get_by_id(id)
    if not producto:
        return jsonify({"mensaje": "Producto no encontrado"}), 404
    if not validar_acceso_producto(producto):
        return jsonify({"exito": False, "mensaje": "Acceso denegado: No tiene permisos sobre productos de esta empresa."}), 403
    data = request.get_json() or {}
    nuevo_estado = data.get("estado", "Inactivo")
    producto_actualizado = ProductosController.desactivar(id, estado=nuevo_estado)
    return jsonify({"mensaje": f"Producto actualizado a estado {nuevo_estado}", "producto": producto_actualizado.to_dict()}), 200

# ===========================
# Eliminar producto
# ===========================
@productos_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
@roles_required("Administrador", 1)
def delete_producto(id):
    producto = ProductosController.get_by_id(id)
    if not producto:
        return jsonify({"mensaje": "Producto no encontrado"}), 404
    if not validar_acceso_producto(producto):
        return jsonify({"exito": False, "mensaje": "Acceso denegado: No tiene permisos sobre productos de esta empresa."}), 403
    eliminado = ProductosController.delete(id)
    if eliminado:
        return jsonify({"mensaje": "Producto desactivado correctamente"}), 200
    return jsonify({"mensaje": "Producto no encontrado"}), 404