import os
from datetime import timedelta
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, verify_jwt_in_request, get_jwt_identity, get_jwt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()

from src.models import Base, engine, session
from src.routes.auth_api import auth_bp
from src.routes.usuarios_api import usuarios_bp
from src.routes.roles_api import roles_bp
from src.routes.clientes_api import clientes_bp
from src.routes.productos_api import productos_bp
from src.routes.categorias_api import categorias_bp
from src.routes.proveedores_api import proveedores_bp
from src.routes.metodos_pago_api import metodos_pago_bp
from src.routes.facturas_api import facturas_bp
from src.routes.detalle_facturas_api import detalle_facturas_bp
from src.routes.compras_api import compras_bp
from src.routes.detalle_compras_api import detalle_compras_bp
from src.routes.reportes_api import reportes_bp
from src.routes.empresas_api import empresas_bp
from src.routes.usuario_empresas_api import usuario_empresas_bp
from src.routes.terminales_api import terminales_bp
from src.routes.cobros_api import cobros_bp
from src.routes.webhooks_api import webhooks_bp
from src.routes.membresias_api import membresias_bp
from src.routes.portal_publico_api import portal_publico_bp
from src.routes.portal_clientes_api import portal_clientes_bp
from src.routes.portal_admin_api import portal_admin_bp
from src.utils.migrations import DatabaseMigrations

app = Flask(__name__)
app.url_map.strict_slashes = False

is_prod = (
    os.environ.get("FLASK_ENV", "").lower() == "production"
    or os.environ.get("APP_ENV", "").lower() == "production"
)

jwt_secret = os.environ.get("JWT_SECRET_KEY")
if is_prod and (not jwt_secret or jwt_secret == "pymes-jwt-secret-key-2026-secure-key-32bytes"):
    raise RuntimeError("JWT_SECRET_KEY segura es obligatoria en entorno de producción.")

app.config["JWT_SECRET_KEY"] = jwt_secret or "pymes-jwt-secret-key-2026-secure-key-32bytes"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=2)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)

jwt = JWTManager(app)

cors_origins_env = os.environ.get("CORS_ORIGINS", "*")
cors_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()] if "," in cors_origins_env else cors_origins_env
CORS(app, resources={r"/api/*": {"origins": cors_origins}}, supports_credentials=True)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["5000 per day", "1000 per hour"],
    storage_uri="memory://"
)

# Ejecutar migraciones estructurales seguras e idempotentes
DatabaseMigrations.ejecutar_migraciones()

BLUEPRINTS_ADMINISTRATIVOS = {
    "usuarios",
    "roles",
    "clientes",
    "productos",
    "categorias",
    "proveedores",
    "metodos_pago",
    "facturas",
    "detalle_facturas",
    "compras",
    "detalle_compras",
    "reportes",
    "empresas",
    "usuario_empresas",
    "terminales",
    "cobros",
    "membresias",
    "portal_admin",
}

# Registrar Blueprints Administrativos y de Sistema
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(usuarios_bp, url_prefix="/api/usuarios")
app.register_blueprint(roles_bp, url_prefix="/api/roles")
app.register_blueprint(clientes_bp, url_prefix="/api/clientes")
app.register_blueprint(productos_bp, url_prefix="/api/productos")
app.register_blueprint(categorias_bp, url_prefix="/api/categorias")
app.register_blueprint(proveedores_bp, url_prefix="/api/proveedores")
app.register_blueprint(metodos_pago_bp, url_prefix="/api/metodos_pago")
app.register_blueprint(facturas_bp, url_prefix="/api/facturas")
app.register_blueprint(detalle_facturas_bp, url_prefix="/api/detalle_facturas")
app.register_blueprint(compras_bp, url_prefix="/api/compras")
app.register_blueprint(detalle_compras_bp, url_prefix="/api/detalle_compras")
app.register_blueprint(reportes_bp, url_prefix="/api/reportes")
app.register_blueprint(empresas_bp, url_prefix="/api/empresas")
app.register_blueprint(usuario_empresas_bp, url_prefix="/api/usuario_empresas")
app.register_blueprint(terminales_bp, url_prefix="/api/terminales")
app.register_blueprint(cobros_bp, url_prefix="/api/cobros")
app.register_blueprint(webhooks_bp, url_prefix="/api/webhooks")
app.register_blueprint(membresias_bp, url_prefix="/api/membresias")

# Registrar Blueprints del Portal de Clientes (Público, Clientes y Administración)
app.register_blueprint(portal_publico_bp, url_prefix="/api/portal/publico")
app.register_blueprint(portal_clientes_bp, url_prefix="/api/portal/clientes")
app.register_blueprint(portal_admin_bp, url_prefix="/api/portal/admin")


@app.before_request
def verificar_version_sesion_y_aislamiento_identidad():
    """
    Middleware global de seguridad:
    1. Separa estrictamente las identidades `admin` (`Usuarios`) y `cliente` (`CuentasClientes`).
       Impide que un token de cliente acceda a cualquier blueprint administrativo.
    2. Valida la versión de sesión (`sesion_version`) y el estado activo de la cuenta en BD.
    """
    if request.method == "OPTIONS":
        return None
    if request.endpoint in ("auth.login", "health_check", "portal_clientes.login_cliente", "portal_clientes.register_cliente"):
        return None

    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        if not identity:
            return None

        claims = get_jwt() or {}
        identity_type = claims.get("identity_type", "admin")
        bp_actual = request.blueprint

        if identity_type == "cliente":
            # Bloquear acceso de clientes externos a todos los módulos administrativos
            if bp_actual in BLUEPRINTS_ADMINISTRATIVOS or bp_actual == "auth":
                return jsonify({
                    "exito": False,
                    "mensaje": "Acceso denegado: Las cuentas de clientes externos no tienen permisos sobre módulos administrativos."
                }), 403

            from src.models.cuentas_clientes import CuentasClientes
            cuenta = CuentasClientes.get_by_id(int(identity))
            if not cuenta or (cuenta.estado or "Activo") != "Activo":
                return jsonify({"exito": False, "mensaje": "La cuenta de cliente se encuentra inactiva."}), 401
            token_sv = claims.get("sesion_version", 1)
            db_sv = cuenta.sesion_version or 1
            if token_sv != db_sv:
                return jsonify({"exito": False, "mensaje": "Tu sesión ha expirado o fue cerrada globalmente."}), 401
            return None

        # Identidad administrativa (`Usuarios`)
        from src.models.usuarios import Usuarios
        usuario = Usuarios.get_by_id(int(identity))
        if not usuario or (usuario.estado or "Activo") in ("Inactivo", "Eliminado"):
            return jsonify({"exito": False, "mensaje": "La cuenta de usuario se encuentra inactiva."}), 401
        token_version = claims.get("sesion_version", 1)
        db_version = getattr(usuario, "sesion_version", 1) or 1
        if token_version != db_version:
            return jsonify({
                "exito": False,
                "mensaje": "La sesión ha sido cerrada globalmente desde otro dispositivo. Por favor inicia sesión de nuevo."
            }), 401
    except Exception:
        pass


@app.after_request
def aplicar_cabeceras_seguridad(response):
    """Cabeceras HTTP de seguridad estándar."""
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    return response


@app.teardown_appcontext
def shutdown_session(exception=None):
    session.remove()


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "ok",
        "service": "PYMES_BE API",
        "version": "2.1.0",
        "modules": ["admin_erp", "multi_tenant", "portal_clientes"]
    }), 200


@app.errorhandler(404)
def resource_not_found(e):
    return jsonify({"exito": False, "error": "Recurso no encontrado", "detalle": str(e)}), 404


@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"exito": False, "error": "Demasiadas peticiones. Por favor, intente más tarde.", "detalle": str(e)}), 429


@app.errorhandler(500)
def internal_server_error(e):
    session.rollback()
    return jsonify({"exito": False, "error": "Error interno del servidor"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = (os.environ.get("FLASK_DEBUG", "true").lower() == "true") and not is_prod
    app.run(debug=debug_mode, host="0.0.0.0", port=port)
