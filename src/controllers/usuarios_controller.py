from src.models.usuarios import Usuarios
from src.models.roles import Roles
from src.utils.migrations import DatabaseMigrations
from src.utils.security import hash_password
from src.utils.pagination import paginate_query

class UsuariosController:
    """
    Controlador encargado única y exclusivamente de la Lógica de Negocio de Usuarios (SRP).
    """

    @staticmethod
    def get():
        DatabaseMigrations.ejecutar_migraciones()
        return Usuarios.get()

    @staticmethod
    def get_paginated(page=1, per_page=10):
        DatabaseMigrations.ejecutar_migraciones()
        return paginate_query(Usuarios.get_query(), page, per_page)

    @staticmethod
    def get_by_id(id):
        DatabaseMigrations.ejecutar_migraciones()
        return Usuarios.get_by_id(id)

    @staticmethod
    def create(data):
        DatabaseMigrations.ejecutar_migraciones()
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

        raw_password = data.get("password") or data.get("password_hash", "123456")
        
        usuario = Usuarios()
        usuario.tipo_documento = data["tipo_documento"]
        usuario.documento = data["documento"]
        usuario.nombre = data["nombre"]
        usuario.apellido = data["apellido"]
        usuario.telefono = data["telefono"]
        usuario.email = data["email"]
        usuario.username = username
        usuario.password_hash = hash_password(raw_password)
        usuario.id_rol = id_rol
        usuario.estado = data.get("estado", "Activo")
        usuario.banco = data.get("banco", "")
        usuario.tipo_cuenta = data.get("tipo_cuenta", "")
        usuario.numero_cuenta = data.get("numero_cuenta", "")
        
        usuario.save()
        return usuario

    @staticmethod
    def update(id, data):
        DatabaseMigrations.ejecutar_migraciones()
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
        if "password" in data:
            usuario.password_hash = hash_password(data["password"])
        elif "password_hash" in data:
            usuario.password_hash = hash_password(data["password_hash"])
        if "id_rol" in data:
            usuario.id_rol = int(data["id_rol"])
        if "estado" in data:
            usuario.estado = data["estado"]
        if "banco" in data:
            usuario.banco = data["banco"]
        if "tipo_cuenta" in data:
            usuario.tipo_cuenta = data["tipo_cuenta"]
        if "numero_cuenta" in data:
            usuario.numero_cuenta = data["numero_cuenta"]

        usuario.update()
        return usuario

    @staticmethod
    def delete(id):
        usuario = Usuarios.get_by_id(id)

        if usuario is None:
            return False

        usuario.delete()
        return True
