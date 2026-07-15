from flask import Flask
from flask import FlaskControllerRegister
from src.models import Base, engine

#importar los modelos para que se registren en la base de datos

from src.models import clientes
from src.models import productos
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


from src.routes.api import categorias_api, clientes_api, productos_api, proveedores_api, roles_api, usuarios_api, metodos_pago_api, facturas_api, detalle_facturas_api, compras_api, detalle_compras_api
#crear todas las tablas en la base de datos

Base.metadata.create_all(bind=engine)

app = Flask(__name__)

#importar las rutas de la aplicación

register_controllers = FlaskControllerRegister(app)
register_controllers.register.package('src.controllers')

if __name__ == '__main__':
    app.run(debug=True)