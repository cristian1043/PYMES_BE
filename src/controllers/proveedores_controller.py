from src.models.proveedores import Proveedores


class ProveedoresController:

    @staticmethod
    def get():
        return Proveedores.get()

    @staticmethod
    def get_by_id(id):
        return Proveedores.get_by_id(id)

    @staticmethod
    def save(data):
        proveedor = Proveedores()
        proveedor.nit = data["nit"]
        proveedor.nombre = data["nombre"]
        proveedor.contacto = data["contacto"]
        proveedor.telefono = data["telefono"]
        proveedor.direccion = data["direccion"]
        proveedor.email = data["email"]
        proveedor.save()
        return proveedor

    @staticmethod
    def update(id, data):
        proveedor = Proveedores.get_by_id(id)

        if proveedor is None:
            return None

        proveedor.nit = data["nit"]
        proveedor.nombre = data["nombre"]
        proveedor.contacto = data["contacto"]
        proveedor.telefono = data["telefono"]
        proveedor.direccion = data["direccion"]
        proveedor.email = data["email"]

        proveedor.update()

        return proveedor

    @staticmethod
    def delete(id):
        proveedor = Proveedores.get_by_id(id)

        if proveedor is None:
            return False

        proveedor.delete()
        return True