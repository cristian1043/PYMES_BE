from src.models.clientes import Clientes
from src.utils.pagination import paginate_query

class ClientesController:

    @staticmethod
    def get():
        return Clientes.get()

    @staticmethod
    def get_paginated(page=1, per_page=10):
        return paginate_query(Clientes.get_query(), page, per_page)

    @staticmethod
    def get_by_id(id):
        return Clientes.get_by_id(id)

    @staticmethod
    def create(data):
        cliente = Clientes()
        cliente.documento = data.get("documento", "")
        cliente.nombre = data.get("nombre", "")
        if hasattr(cliente, 'apellido'):
            cliente.apellido = data.get("apellido", "")
        cliente.direccion = data.get("direccion", "")
        cliente.telefono = data.get("telefono", "")
        cliente.email = data.get("email", "")
        if hasattr(cliente, 'tipo_documento'):
            cliente.tipo_documento = data.get("tipo_documento", "CC")
        cliente.create()
        return cliente

    @staticmethod
    def update(id, data):
        cliente = Clientes.get_by_id(id)

        if cliente is None:
            return None

        cliente.documento = data.get("documento", cliente.documento)
        cliente.nombre = data.get("nombre", cliente.nombre)
        if hasattr(cliente, 'apellido'):
            cliente.apellido = data.get("apellido", getattr(cliente, 'apellido', ''))
        cliente.direccion = data.get("direccion", cliente.direccion)
        cliente.telefono = data.get("telefono", cliente.telefono)
        cliente.email = data.get("email", cliente.email)
        if hasattr(cliente, 'tipo_documento'):
            cliente.tipo_documento = data.get("tipo_documento", getattr(cliente, 'tipo_documento', 'CC'))
        
        cliente.update()

        return cliente

    @staticmethod
    def delete(id):
        cliente = Clientes.get_by_id(id)

        if cliente is None:
            return False

        cliente.delete()
        return True

