from flask import Flask
from src.models import Base, engine

#importar los modelos para que se registren en la base de datos

from src.models.categorias import Categorias
from src.models.clientes import Clientes
from src.models.productos import Productos
from src.models.proveedores import Proveedores
from src.models.roles import Roles
from src.models.usuarios import Usuarios
from src.models.metodos_pago import MetodosPago
from src.models.facturas import Facturas
from src.models.detalle_facturas import DetalleFacturas
from src.models.compras import Compras
from src.models.detalle_compras import DetalleCompras


#crear todas las tablas en la base de datos

Base.metadata.create_all(bind=engine)


app = Flask(__name__)

from src.routes import (
    categorias_bp,
    clientes_bp, 
    productos_bp, 
    proveedores_bp, 
    roles_bp, 
    usuarios_bp, 
    facturas_bp, 
    detalle_facturas_bp, 
    compras_bp, 
    detalle_compras_bp,
    metodo_pago_bp
)


# Register all blueprints

app.register_blueprint(categorias_bp,url_prefix="/api/categorias")
app.register_blueprint(clientes_bp, url_prefix="/api/clientes")
app.register_blueprint(productos_bp, url_prefix="/api/productos")
app.register_blueprint(proveedores_bp, url_prefix="/api/proveedores")
app.register_blueprint(roles_bp, url_prefix="/api/roles")
app.register_blueprint(usuarios_bp, url_prefix="/api/usuarios")
app.register_blueprint(facturas_bp, url_prefix="/api/facturas")
app.register_blueprint(detalle_facturas_bp, url_prefix="/api/detalle_facturas")
app.register_blueprint(compras_bp, url_prefix="/api/compras")
app.register_blueprint(detalle_compras_bp, url_prefix="/api/detalle_compras")
app.register_blueprint(metodo_pago_bp, url_prefix="/api/metodos_pago")

if __name__ == '__main__':
    app.run(debug=True)