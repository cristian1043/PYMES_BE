from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, get_jwt, verify_jwt_in_request
from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(password: str) -> str:
    """Genera un hash seguro utilizando Werkzeug pbkdf2:sha256."""
    if not password:
        return ""
    return generate_password_hash(str(password))


def verify_password(password_hash: str, password: str) -> bool:
    """Verifica si la contraseña coincide con el hash almacenado."""
    if not password_hash or not password:
        return False
    if password_hash.startswith(("pbkdf2:", "scrypt:", "argon2:")):
        return check_password_hash(password_hash, password)
    # Compatibilidad controlada únicamente para hashes legados que aún no hayan sido migrados
    if password_hash == password:
        return True
    return check_password_hash(password_hash, password)


def validar_politica_password(password: str):
    """
    Valida la política de contraseñas:
    - Obligatoria, mínimo 6 caracteres (recomendado 8+).
    - Rechaza contraseñas triviales débiles conocidas ('123456', 'password', '12345678', 'qwerty').
    """
    if not password or not isinstance(password, str):
        return False, "La contraseña es obligatoria"
    pwd = password.strip()
    if len(pwd) < 6:
        return False, "La contraseña debe tener al menos 6 caracteres"
    claves_prohibidas = {"123456", "1234567", "12345678", "password", "qwerty", "000000", "111111"}
    if pwd.lower() in claves_prohibidas:
        return False, "La contraseña elegida es demasiado insegura. Utiliza una combinación más robusta"
    return True, None


def es_identidad_cliente() -> bool:
    """Indica si el token JWT actual pertenece a una cuenta externa del Portal de Clientes."""
    claims = get_jwt() or {}
    return claims.get("identity_type") == "cliente"


def es_super_admin_actual() -> bool:
    """
    Indica si el usuario autenticado es un Super Administrador global de la plataforma PYMESOFT.
    Un administrador de una empresa individual (rol_id=1 en usuario_empresas) NO es super_admin global.
    """
    claims = get_jwt() or {}
    if claims.get("identity_type") == "cliente":
        return False
    return bool(claims.get("es_super_admin", False))


def obtener_empresa_id_request():
    """Extrae empresa_id / id_empresa desde query params, JSON body, header X-Empresa-ID o environ."""
    req_json = request.get_json(silent=True)
    if not isinstance(req_json, dict):
        req_json = {}
    raw = (
        request.args.get("empresa_id")
        or request.args.get("id_empresa")
        or req_json.get("empresa_id")
        or req_json.get("id_empresa")
        or request.headers.get("X-Empresa-ID")
        or request.environ.get("tenant_empresa_id")
    )
    if raw is None or str(raw).strip() == "":
        return None
    try:
        return int(raw)
    except (ValueError, TypeError):
        return None


def obtener_empresas_autorizadas_usuario(user_id=None):
    """Devuelve la lista de IDs de empresa donde el usuario tiene vinculación activa."""
    if user_id is None:
        user_id = get_jwt_identity()
    if not user_id or not str(user_id).isdigit():
        return []
    from src.models.usuario_empresas import UsuarioEmpresas
    vinculaciones = UsuarioEmpresas.get_by_usuario(int(user_id))
    return [int(v.empresa_id) for v in vinculaciones if v.estado == "Activo" and v.empresa_id is not None]


def verificar_acceso_empresa(empresa_id, allow_inactivo=False) -> bool:
    """
    Verifica que el usuario administrativo autenticado tenga acceso activo a la empresa indicada.
    - Rechaza cualquier token de cliente externo (`identity_type == 'cliente'`).
    - Permite acceso global únicamente si `es_super_admin` es True.
    - Verifica que la relación en `usuario_empresas` exista y esté en estado 'Activo'.
    - Verifica que la empresa exista y esté en estado 'Activo' (salvo allow_inactivo=True o rol admin reactivándola).
    """
    if es_identidad_cliente():
        return False
    if not empresa_id:
        return False
    try:
        eid = int(empresa_id)
    except (ValueError, TypeError):
        return False

    if es_super_admin_actual():
        return True

    user_id = get_jwt_identity()
    if not user_id or not str(user_id).isdigit():
        return False

    from src.models.usuario_empresas import UsuarioEmpresas
    from src.models.empresas import Empresas

    vinc = UsuarioEmpresas.get_by_usuario_empresa(int(user_id), eid)
    if not vinc or vinc.estado != "Activo":
        return False

    if not allow_inactivo:
        emp = Empresas.get_by_id(eid)
        if not emp:
            return False
        if (emp.estado or "Activo") != "Activo" and vinc.rol_id != 1:
            return False

    return True


def obtener_rol_en_empresa(empresa_id, user_id=None):
    """
    Resuelve el rol efectivo `(rol_id, rol_nombre)` del usuario dentro de `empresa_id`.
    Nunca asume que el rol global concede permisos sobre empresas ajenas o donde tiene un rol menor.
    """
    if es_identidad_cliente():
        return None, None
    if es_super_admin_actual():
        return 1, "Administrador"

    if user_id is None:
        user_id = get_jwt_identity()
    if not user_id or not str(user_id).isdigit() or not empresa_id:
        return None, None

    try:
        eid = int(empresa_id)
    except (ValueError, TypeError):
        return None, None

    from src.models.usuario_empresas import UsuarioEmpresas
    vinc = UsuarioEmpresas.get_by_usuario_empresa(int(user_id), eid)
    if not vinc or vinc.estado != "Activo":
        return None, None

    roles_map = {1: "Administrador", 2: "Vendedor", 3: "Almacenista"}
    return vinc.rol_id, roles_map.get(vinc.rol_id, "Vendedor")


def roles_required(*roles):
    """
    Decorador RBAC Multi-Empresa:
    - Rechaza tokens de clientes externos.
    - Si se especifica o resuelve una empresa activa (`empresa_id`), valida estrictamente el rol del usuario
      en ESA empresa (`usuario_empresas.rol_id`), evitando escaladas de privilegios entre empresas.
    - Si el endpoint no recibe `empresa_id` (ej. creación de nueva empresa o catálogo de roles),
      verifica el rol global o que posea el rol requerido en al menos una empresa activa.
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

            if claims.get("identity_type") == "cliente":
                return jsonify({
                    "exito": False,
                    "mensaje": "Acceso denegado: Las cuentas de clientes no tienen permisos administrativos."
                }), 403

            if es_super_admin_actual():
                return fn(*args, **kwargs)

            roles_permitidos_str = [str(r) for r in roles]
            empresa_id = obtener_empresa_id_request()
            user_id = get_jwt_identity()

            if empresa_id is not None:
                rol_id_emp, rol_nombre_emp = obtener_rol_en_empresa(empresa_id, user_id)
                if rol_id_emp is None:
                    return jsonify({
                        "exito": False,
                        "mensaje": f"Acceso denegado: No pertenece ni está activo en la empresa solicitada (ID {empresa_id})."
                    }), 403
                if rol_id_emp == 1 or rol_nombre_emp in roles or str(rol_id_emp) in roles_permitidos_str:
                    return fn(*args, **kwargs)
                return jsonify({
                    "exito": False,
                    "mensaje": "Acceso denegado: No posee el rol requerido en la empresa activa para esta acción.",
                    "rol_actual": rol_nombre_emp,
                    "roles_requeridos": list(roles)
                }), 403

            # Sin empresa_id explícito en la petición: verificar rol en sus vinculaciones activas o rol global
            rol_usuario = claims.get("rol", "")
            id_rol = claims.get("id_rol", 0)
            if user_id and str(user_id).isdigit():
                from src.models.usuario_empresas import UsuarioEmpresas
                roles_map = {1: "Administrador", 2: "Vendedor", 3: "Almacenista"}
                vincs = UsuarioEmpresas.get_by_usuario(int(user_id))
                vincs_activas = [v for v in vincs if v.estado == "Activo"]
                if vincs_activas:
                    for v in vincs_activas:
                        r_nom = roles_map.get(v.rol_id, "Vendedor")
                        if v.rol_id == 1 or r_nom in roles or str(v.rol_id) in roles_permitidos_str:
                            return fn(*args, **kwargs)
                    return jsonify({
                        "exito": False,
                        "mensaje": "Acceso denegado: No posee el rol requerido en ninguna de sus empresas activas.",
                        "roles_requeridos": list(roles)
                    }), 403

            if id_rol == 1 or rol_usuario == "Administrador" or rol_usuario in roles or str(id_rol) in roles_permitidos_str:
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
    Decorador ABAC / Multi-Tenant:
    Verifica que el usuario autenticado tenga acceso activo a la empresa solicitada (`empresa_id` / `id_empresa` / `X-Empresa-ID`),
    y que la empresa se encuentre operativa.
    Solo el Super Administrador de plataforma (`es_super_admin=True`) puede omitir el filtro si `allow_global_admin=True`.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                verify_jwt_in_request()
            except Exception:
                return jsonify({"exito": False, "mensaje": "Se requiere autenticación para acceder a este recurso multi-tenant."}), 401

            claims = get_jwt() or {}
            if claims.get("identity_type") == "cliente":
                return jsonify({
                    "exito": False,
                    "mensaje": "Acceso denegado: Las cuentas de clientes no pueden invocar endpoints administrativos."
                }), 403

            empresa_id = obtener_empresa_id_request()

            if allow_global_admin and es_super_admin_actual():
                if empresa_id is not None:
                    request.environ["tenant_empresa_id"] = empresa_id
                return fn(*args, **kwargs)

            if empresa_id is None:
                return jsonify({
                    "exito": False,
                    "mensaje": "Se requiere especificar el identificador de empresa ('empresa_id') para esta operación multi-tenant."
                }), 400

            user_id = get_jwt_identity()
            from src.models.usuario_empresas import UsuarioEmpresas
            from src.models.empresas import Empresas

            vinculacion = (
                UsuarioEmpresas.get_by_usuario_empresa(int(user_id), empresa_id)
                if (user_id and str(user_id).isdigit())
                else None
            )
            if not vinculacion or vinculacion.estado != "Activo":
                return jsonify({
                    "exito": False,
                    "mensaje": f"Acceso denegado: El usuario no pertenece ni está activo en la empresa ID {empresa_id}."
                }), 403

            emp = Empresas.get_by_id(empresa_id)
            if not emp:
                return jsonify({"exito": False, "mensaje": "La empresa especificada no existe."}), 404
            if (emp.estado or "Activo") != "Activo" and vinculacion.rol_id != 1:
                return jsonify({
                    "exito": False,
                    "mensaje": f"La empresa '{emp.nombre}' se encuentra inactiva. Contacte al administrador."
                }), 403

            request.environ["tenant_empresa_id"] = empresa_id
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def cliente_jwt_required():
    """
    Decorador exclusivo para rutas autenticadas del Portal de Clientes (`PYMES_CLIENTES`).
    Verifica que el JWT sea válido, que `identity_type == 'cliente'`, y que la cuenta exista,
    esté activa y su `sesion_version` coincida.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                verify_jwt_in_request()
            except Exception:
                return jsonify({"exito": False, "mensaje": "Inicia sesión en el portal de clientes para continuar."}), 401

            claims = get_jwt() or {}
            if claims.get("identity_type") != "cliente":
                return jsonify({
                    "exito": False,
                    "mensaje": "Este recurso requiere una sesión de cliente del portal público."
                }), 403

            cuenta_id = get_jwt_identity()
            if not cuenta_id or not str(cuenta_id).isdigit():
                return jsonify({"exito": False, "mensaje": "Identidad de cliente inválida."}), 401

            from src.models.cuentas_clientes import CuentasClientes
            cuenta = CuentasClientes.get_by_id(int(cuenta_id))
            if not cuenta or (cuenta.estado or "Activo") != "Activo":
                return jsonify({"exito": False, "mensaje": "La cuenta de cliente no existe o se encuentra inactiva."}), 401

            token_sv = claims.get("sesion_version", 1)
            db_sv = cuenta.sesion_version or 1
            if token_sv != db_sv:
                return jsonify({"exito": False, "mensaje": "Tu sesión ha expirado o fue cerrada desde otro dispositivo."}), 401

            request.environ["cuenta_cliente_actual"] = cuenta
            return fn(*args, **kwargs)
        return wrapper
    return decorator
