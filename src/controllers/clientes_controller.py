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
        
        cliente.tiene_tarjeta = data.get("tiene_tarjeta", "No")
        cliente.tipo_tarjeta = data.get("tipo_tarjeta")
        cliente.banco_tarjeta = data.get("banco_tarjeta")
        cliente.franquicia_tarjeta = data.get("franquicia_tarjeta")
        cliente.ultimos_digitos_tarjeta = data.get("ultimos_digitos_tarjeta")

        cliente.save()
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
        
        if "tiene_tarjeta" in data:
            cliente.tiene_tarjeta = data["tiene_tarjeta"]
        if "tipo_tarjeta" in data:
            cliente.tipo_tarjeta = data["tipo_tarjeta"]
        if "banco_tarjeta" in data:
            cliente.banco_tarjeta = data["banco_tarjeta"]
        if "franquicia_tarjeta" in data:
            cliente.franquicia_tarjeta = data["franquicia_tarjeta"]
        if "ultimos_digitos_tarjeta" in data:
            cliente.ultimos_digitos_tarjeta = data["ultimos_digitos_tarjeta"]

        cliente.update()

        return cliente

    @staticmethod
    def delete(id):
        cliente = Clientes.get_by_id(id)

        if cliente is None:
            return False

        cliente.delete()
        return True

