from src.models.usuarios import Usuarios
 

class UsuariosController:

    @staticmethod
    def get():
        return Usuarios.get()

    @staticmethod
    def get_by_id(id):
        return Usuarios.get_by_id(id)

    @staticmethod
    def create(data):
        usuario = Usuarios()
        usuario.tipo_documento = data["tipo_documento"]
        usuario.documento = data["documento"]
        usuario.nombre = data["nombre"]
        usuario.apellido = data["apellido"]
        usuario.telefono = data["telefono"]
        usuario.email = data["email"]
        usuario.username = data["username"]
        usuario.password_hash = data["password_hash"]
        usuario.id_rol = data["id_rol"]
        usuario.create()
        return usuario

    @staticmethod
    def update(id, data):
        usuario = Usuarios.get_by_id(id)

        if usuario is None:
            return None
        
        usuario.tipo_documento = data["tipo_documento"]
        usuario.documento = data["documento"]
        usuario.nombre = data["nombre"]
        usuario.apellido = data["apellido"]
        usuario.telefono = data["telefono"]
        usuario.email = data["email"]
        usuario.username = data["username"]
        usuario.password_hash = data["password_hash"]
        usuario.id_rol = data["id_rol"]

        usuario.update()

        return usuario

    @staticmethod
    def delete(id):
        usuario = Usuarios.get_by_id(id)

        if usuario is None:
            return False

        usuario.delete()
        return True

