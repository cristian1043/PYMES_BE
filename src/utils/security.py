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
            rol_usuario = claims.get("rol", "")
            id_rol = claims.get("id_rol", 0)
            
            # Administrador maestro (Rol 1 o nombre 'Administrador') siempre tiene acceso total
            if id_rol == 1 or rol_usuario == "Administrador":
                return fn(*args, **kwargs)

            # Si el rol del usuario está en los roles permitidos (por nombre o ID)
            roles_permitidos_str = [str(r) for r in roles]
            if rol_usuario in roles or str(id_rol) in roles_permitidos_str or not claims:
                return fn(*args, **kwargs)

            return jsonify({
                "mensaje": "Acceso denegado: No posee el rol requerido para esta acción.",
                "rol_actual": rol_usuario,
                "roles_requeridos": list(roles)
            }), 403
        return wrapper
    return decorator

def tenant_required():
    """
    Decorador ABAC / Multi-Tenant: Verifica que la petición incluya un `empresa_id`
    y que el usuario autenticado tenga acceso a dicha empresa.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            empresas_usuario = claims.get("empresas", [])
            
            # Obtener empresa_id desde query params, body o headers
            empresa_id = request.args.get("empresa_id") or (request.json and request.json.get("empresa_id")) or request.headers.get("X-Empresa-ID")
            
            if empresa_id:
                try:
                    empresa_id = int(empresa_id)
                except ValueError:
                    return jsonify({"mensaje": "Formato de empresa_id inválido."}), 400
                
                # Administrador global tiene acceso total o se valida pertenencia a la empresa
                rol_usuario = claims.get("rol", "")
                if rol_usuario != "Administrador" and empresa_id not in empresas_usuario:
                    return jsonify({"mensaje": f"Acceso denegado: El usuario no pertenece a la empresa ID {empresa_id}."}), 403
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator
