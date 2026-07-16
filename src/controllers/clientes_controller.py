from src.models import session
from src.models.categorias import Categorias
from src.models.clientes import Clientes


class ClientesController:

    @staticmethod
    def get():
        return Clientes.get()

    @staticmethod
    def get_by_id(id):
        return Clientes.get_by_id(id)

    @staticmethod
    def save(data):
        cliente = Clientes()
        cliente.documento = data["documento"]
        cliente.nombre = data["nombre"]
        cliente.direccion = data["direccion"]
        cliente.telefono = data["telefono"]
        cliente.email = data["email"]
        cliente.save()
        return cliente

    @staticmethod
    def update(id, data):
        cliente = Clientes.get_by_id(id)

        if cliente is None:
            return None

        cliente.documento = data["documento"]
        cliente.nombre = data["nombre"]
        cliente.direccion = data["direccion"]
        cliente.telefono = data["telefono"]
        cliente.email = data["email"]
        cliente.update()

        return cliente

    @staticmethod
    def delete(id):
        cliente = Clientes.get_by_id(id)

        if cliente is None:
            return False

        cliente.delete()
        return True