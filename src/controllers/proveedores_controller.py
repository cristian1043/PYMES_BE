from src.models.proveedores import Proveedores
from src.utils.pagination import paginate_query

class ProveedoresController:

    @staticmethod
    def get(empresa_id=None):
        query = Proveedores.get_query()
        if empresa_id:
            query = query.filter(Proveedores.id_empresa == int(empresa_id))
        else:
            return []
        return query.all()

    @staticmethod
    def get_paginated(page=1, per_page=10, empresa_id=None):
        query = Proveedores.get_query()
        if empresa_id:
            query = query.filter(Proveedores.id_empresa == int(empresa_id))
        else:
            return paginate_query(query.filter(Proveedores.id_empresa == -1), page, per_page)
        return paginate_query(query, page, per_page)

    @staticmethod
    def get_by_id(id):
        return Proveedores.get_by_id(id)

    @staticmethod
    def create(data):
        proveedor = Proveedores()
        proveedor.nit = data.get("nit", "")
        proveedor.nombre = data.get("nombre", "")
        if hasattr(proveedor, 'contacto'):
            proveedor.contacto = data.get("contacto", "")
        proveedor.telefono = data.get("telefono", "")
        proveedor.direccion = data.get("direccion", "")
        proveedor.email = data.get("email", "")
        proveedor.detalle_servicios = data.get("detalle_servicios", "")
        proveedor.estado = data.get("estado", "Activo")
        emp_id = data.get("id_empresa") or data.get("empresa_id")
        proveedor.id_empresa = int(emp_id) if emp_id else None
        proveedor.save()
        return proveedor

    @staticmethod
    def update(id, data):
        proveedor = Proveedores.get_by_id(id)
        if proveedor is None:
            return None
        proveedor.nit = data.get("nit", proveedor.nit)
        proveedor.nombre = data.get("nombre", proveedor.nombre)
        if hasattr(proveedor, 'contacto'):
            proveedor.contacto = data.get("contacto", getattr(proveedor, 'contacto', ''))
        proveedor.telefono = data.get("telefono", proveedor.telefono)
        proveedor.direccion = data.get("direccion", proveedor.direccion)
        proveedor.email = data.get("email", proveedor.email)
        proveedor.detalle_servicios = data.get("detalle_servicios", proveedor.detalle_servicios)
        if "estado" in data:
            proveedor.estado = data["estado"]
        proveedor.update()
        return proveedor

    @staticmethod
    def desactivar(id, estado="Inactivo"):
        proveedor = Proveedores.get_by_id(id)
        if proveedor is None:
            return None
        proveedor.estado = estado
        proveedor.update()
        return proveedor

    @staticmethod
    def delete(id):
        proveedor = Proveedores.get_by_id(id)

        if proveedor is None:
            return False

        # Desactivación lógica (Soft-Delete) para proteger historial de compras
        proveedor.estado = "Inactivo"
        proveedor.update()
        return True