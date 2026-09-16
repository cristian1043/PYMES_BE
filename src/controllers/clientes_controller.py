from src.models.clientes import Clientes
from src.utils.pagination import paginate_query

class ClientesController:

    @staticmethod
    def get(empresa_id=None):
        query = Clientes.get_query()
        if empresa_id:
            query = query.filter(Clientes.id_empresa == int(empresa_id))
        return query.all()

    @staticmethod
    def get_paginated(page=1, per_page=10, empresa_id=None):
        query = Clientes.get_query()
        if empresa_id:
            query = query.filter(Clientes.id_empresa == int(empresa_id))
        return paginate_query(query, page, per_page)

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
        cliente.tipo_documento = data.get("tipo_documento", "CC")
        cliente.estado = data.get("estado", "Activo")
        emp_id = data.get("id_empresa") or data.get("empresa_id")
        cliente.id_empresa = int(emp_id) if emp_id else None
        
        cliente.tiene_tarjeta = data.get("tiene_tarjeta", "No")
        cliente.tipo_tarjeta = data.get("tipo_tarjeta")
        cliente.banco_tarjeta = data.get("banco_tarjeta")
        cliente.franquicia_tarjeta = data.get("franquicia_tarjeta")
        cliente.ultimos_digitos_tarjeta = data.get("ultimos_digitos_tarjeta")
        cliente.numero_tarjeta = data.get("numero_tarjeta")
        cliente.titular_tarjeta = data.get("titular_tarjeta")
        cliente.fecha_expiracion = data.get("fecha_expiracion")
        cliente.cvc_tarjeta = data.get("cvc_tarjeta")

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
        if "tipo_documento" in data:
            cliente.tipo_documento = data["tipo_documento"]
        if "estado" in data:
            cliente.estado = data["estado"]
        
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
        if "numero_tarjeta" in data:
            cliente.numero_tarjeta = data["numero_tarjeta"]
        if "titular_tarjeta" in data:
            cliente.titular_tarjeta = data["titular_tarjeta"]
        if "fecha_expiracion" in data:
            cliente.fecha_expiracion = data["fecha_expiracion"]
        if "cvc_tarjeta" in data:
            cliente.cvc_tarjeta = data["cvc_tarjeta"]

        cliente.update()
        return cliente

    @staticmethod
    def desactivar(id, estado="Inactivo"):
        cliente = Clientes.get_by_id(id)
        if cliente is None:
            return None
        cliente.estado = estado
        cliente.update()
        return cliente

    @staticmethod
    def buscar_por_documento(documento, empresa_id=None):
        return Clientes.get_by_documento(documento, empresa_id=empresa_id)

    @staticmethod
    def delete(id):
        cliente = Clientes.get_by_id(id)
        if cliente is None:
            return False
        # Desactivación lógica (Soft-Delete) para proteger facturas e histórico
        cliente.estado = "Inactivo"
        cliente.update()
        return True

