from flask import Flask

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

#crear todas las tablas en la base de datos

Base.metadata.create_all(bind=engine)

app = Flask(__name__)

#importar las rutas de la aplicación

from src.routes.home import home
from src.routes.clientes import clientes
from src.routes.productos import productos
from src.routes.facturas import facturas
from src.routes.compras import compras
from src.routes.reportes import reportes

#registrar las rutas de la aplicación

app.register_blueprint(home)
app.register_blueprint(clientes)
app.register_blueprint(productos)
app.register_blueprint(facturas)
app.register_blueprint(compras)
app.register_blueprint(reportes)

if __name__ == '__main__':
    app.run(debug=True)

