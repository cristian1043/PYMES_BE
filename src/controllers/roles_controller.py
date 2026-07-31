from src.models.roles import Roles

class RolesController:

    @staticmethod
    def get():
        return Roles.get()

    @staticmethod
    def get_by_id(id):
        return Roles.get_by_id(id)

    @staticmethod
    def create(data):
        rol = Roles()
        rol.nombre = data["nombre"]
        rol.descripcion = data["descripcion"]
        rol.create()
        return rol

    @staticmethod
    def update(id, data):
        rol = Roles.get_by_id(id)
        if rol is None:
            return None
        rol.nombre = data["nombre"]
        rol.descripcion = data["descripcion"]
        rol.update()
        return rol

    @staticmethod
    def delete(id):
        rol = Roles.get_by_id(id)

        if rol is None:
            return False

        rol.delete()
        return True

        rol.nombre = data["nombre"]
        rol.descripcion = data["descripcion"]

        rol.update()

        return rol

    @staticmethod
    def delete(id):
        rol = Roles.get_by_id(id)

        if rol is None:
            return False

        rol.delete()
        return True

        return rol

    @staticmethod
    def delete(id):
        rol = Roles.get_by_id(id)

        if rol is None:
            return False

        rol.delete()
        return True