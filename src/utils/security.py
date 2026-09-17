from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, get_jwt, verify_jwt_in_request
from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password: str) -> str:
    """Genera un hash seguro utilizando Werkzeug pbkdf2:sha256."""
    if not password:
        return ""
    return generate_password_hash(password)

def verify_password(password_hash: str, password: str) -> bool:
    """Verifica si la contraseña coincide con el hash almacenado."""
    if not password_hash or not password:
        return False
    # Compatibilidad si hay alguna clave guardada en texto plano temporalmente
    if password_hash == password:
        return True
    return check_password_hash(password_hash, password)

def roles_required(*roles):
    """
    Decorador RBAC: Verifica que el usuario autenticado posea alguno de los roles permitidos.
    Uso: @roles_required('Administrador', 'Vendedor', 'Almacenista')
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                verify_jwt_in_request(optional=True)
            except Exception:
                pass
            
            claims = get_jwt() or {}
            if not claims:
                return jsonify({"exito": False, "mensaje": "Se requiere autenticación para realizar esta acción."}), 401

            rol_usuario = claims.get("rol", "")
            id_rol = claims.get("id_rol", 0)
            
            # Administrador maestro (Rol 1 o nombre 'Administrador') siempre tiene acceso total
            if id_rol == 1 or rol_usuario == "Administrador":
                return fn(*args, **kwargs)

            # Si el rol del usuario está en los roles permitidos (por nombre o ID)
            roles_permitidos_str = [str(r) for r in roles]
            if rol_usuario in roles or str(id_rol) in roles_permitidos_str:
                return fn(*args, **kwargs)

            return jsonify({
                "exito": False,
                "mensaje": "Acceso denegado: No posee el rol requerido para esta acción.",
                "rol_actual": rol_usuario,
                "roles_requeridos": list(roles)
            }), 403
        return wrapper
    return decorator

def tenant_required(allow_global_admin=True):
    """
    Decorador ABAC / Multi-Tenant: Verifica que el usuario autenticado tenga acceso a la empresa solicitada.
    Busca `empresa_id` o `id_empresa` en query params, json body o headers (X-Empresa-ID).
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                verify_jwt_in_request()
            except Exception:
                return jsonify({"exito": False, "mensaje": "Se requiere autenticación para acceder a este recurso multi-tenant."}), 401

            claims = get_jwt() or {}
            rol_usuario = claims.get("rol", "")
            id_rol = claims.get("id_rol", 0)
            empresas_usuario = [int(e) for e in claims.get("empresas", []) if str(e).isdigit()]

            # Administrador global (Rol 1 o nombre Administrador) tiene acceso global si allow_global_admin está activo
            if allow_global_admin and (id_rol == 1 or rol_usuario == "Administrador"):
                return fn(*args, **kwargs)

            # Obtener empresa_id desde query params, json body o headers
            req_json = request.get_json(silent=True) or {}
            empresa_id = (
                request.args.get("empresa_id") or 
                request.args.get("id_empresa") or 
                req_json.get("empresa_id") or 
                req_json.get("id_empresa") or 
                request.headers.get("X-Empresa-ID")
            )

            if not empresa_id:
                return jsonify({
                    "exito": False,
                    "mensaje": "Se requiere especificar el identificador de empresa ('empresa_id') para esta operación multi-tenant."
                }), 400

            try:
                empresa_id = int(empresa_id)
            except (ValueError, TypeError):
                return jsonify({"exito": False, "mensaje": "Formato de empresa_id inválido."}), 400

            if empresa_id not in empresas_usuario:
                user_id = get_jwt_identity()
                from src.models.usuario_empresas import UsuarioEmpresas
                vinculacion = UsuarioEmpresas.get_by_usuario_empresa(user_id, empresa_id) if user_id else None
                if not vinculacion or vinculacion.estado != 'Activo':
                    return jsonify({
                        "exito": False,
                        "mensaje": f"Acceso denegado: El usuario no pertenece ni está activo en la empresa ID {empresa_id}."
                    }), 403

            request.environ['tenant_empresa_id'] = empresa_id
            return fn(*args, **kwargs)
        return wrapper
    return decorator
