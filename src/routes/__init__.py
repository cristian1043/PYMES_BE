from .categorias_api import categorias_bp
from .clientes_api import clientes_bp
from .productos_api import productos_bp
from .proveedores_api import proveedores_bp
from .roles_api import roles_bp
from .usuarios_api import usuarios_bp
from .facturas_api import facturas_bp
from .detalle_facturas_api import detalle_facturas_bp
from .compras_api import compras_bp
from .detalle_compras_api import detalle_compras_bp


def register_routes(app):
    app.register_blueprint(categorias_bp, url_prefix="/api/categorias")
    app.register_blueprint(clientes_bp, url_prefix="/api/clientes")
    app.register_blueprint(productos_bp, url_prefix="/api/productos")
    app.register_blueprint(proveedores_bp, url_prefix="/api/proveedores")
    app.register_blueprint(roles_bp, url_prefix="/api/roles")
    app.register_blueprint(usuarios_bp, url_prefix="/api/usuarios")
    app.register_blueprint(facturas_bp, url_prefix="/api/facturas")
    app.register_blueprint(detalle_facturas_bp, url_prefix="/api/detalle_facturas")
    app.register_blueprint(compras_bp, url_prefix="/api/compras")
    app.register_blueprint(detalle_compras_bp, url_prefix="/api/detalle_compras")
 