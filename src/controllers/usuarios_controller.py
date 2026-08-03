from src.models.usuarios import Usuarios
from src.models.roles import Roles

class UsuariosController:

    @staticmethod
    def get():
        return Usuarios.get()

    @staticmethod
    def get_by_id(id):
        return Usuarios.get_by_id(id)

    @staticmethod
    def create(data):
        id_rol = data.get("id_rol", 1)
        rol_existente = Roles.get_by_id(id_rol)
        if not rol_existente:
            nuevo_rol = Roles()
            nuevo_rol.nombre = "Administrador"
            nuevo_rol.descripcion = "Rol administrador del sistema"
            nuevo_rol.save()
            id_rol = nuevo_rol.id

        username = data.get("username")
        if not username:
            username = data["email"].split("@")[0]

        usuario = Usuarios()
        usuario.tipo_documento = data["tipo_documento"]
        usuario.documento = data["documento"]
        usuario.nombre = data["nombre"]
        usuario.apellido = data["apellido"]
        usuario.telefono = data["telefono"]
        usuario.email = data["email"]
        usuario.username = username
        usuario.password_hash = data["password_hash"]
        usuario.id_rol = id_rol
        usuario.estado = data.get("estado", "Activo")
        
        usuario.save()
        return usuario

    @staticmethod
    def update(id, data):
        usuario = Usuarios.get_by_id(id)

        if usuario is None:
            return None
        
        if "tipo_documento" in data:
            usuario.tipo_documento = data["tipo_documento"]
        if "documento" in data:
            usuario.documento = data["documento"]
        if "nombre" in data:
            usuario.nombre = data["nombre"]
        if "apellido" in data:
            usuario.apellido = data["apellido"]
        if "telefono" in data:
            usuario.telefono = data["telefono"]
        if "email" in data:
            usuario.email = data["email"]
        if "username" in data:
            usuario.username = data["username"]
        if "password_hash" in data:
            usuario.password_hash = data["password_hash"]
        if "id_rol" in data:
            usuario.id_rol = int(data["id_rol"])
        if "estado" in data:
            usuario.estado = data["estado"]

        usuario.update()
        return usuario

    @staticmethod
    def delete(id):
        usuario = Usuarios.get_by_id(id)

        if usuario is None:
            return False

        usuario.delete()
        return True
