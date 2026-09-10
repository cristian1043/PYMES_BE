import time
from sqlalchemy import func
from src.models import session
from src.models.usuarios import Usuarios
from src.models.roles import Roles
from src.utils.security import hash_password
from src.utils.pagination import paginate_query

class UsuariosController:
    """
    Controlador encargado de la lógica de negocio de usuarios.
    """

    @staticmethod
    def get():
        return Usuarios.get()

    @staticmethod
    def get_paginated(page=1, per_page=10):
        return paginate_query(Usuarios.get_query(), page, per_page)

    @staticmethod
    def get_by_id(id):
        return Usuarios.get_by_id(id)

    @staticmethod
    def get_by_documento(documento):
        return session.query(Usuarios).filter(Usuarios.documento == str(documento).strip()).first()

    @staticmethod
    def get_by_username(username):
        if not username:
            return None
        return session.query(Usuarios).filter(
            func.lower(Usuarios.username) == str(username).strip().lower()
        ).first()

    @staticmethod
    def get_by_email(email):
        if not email:
            return None
        return session.query(Usuarios).filter(
            func.lower(Usuarios.email) == str(email).strip().lower()
        ).first()

    @staticmethod
    def create(data):
        # 1. Validar unicidad de @username
        username = str(data.get("username") or "").strip()
        if not username:
            email_val = str(data.get("email") or "user").strip()
            username = email_val.split("@")[0] if "@" in email_val else email_val

        username_existente = UsuariosController.get_by_username(username)
        if username_existente:
            raise ValueError(f"El nombre de usuario '@{username}' ya está en uso. Por favor elige otro.")

        # 2. Validar unicidad de correo electrónico
        email = str(data.get("email") or "").strip().lower()
        if not email:
            raise ValueError("El correo electrónico es obligatorio.")

        email_existente = UsuariosController.get_by_email(email)
        if email_existente:
            raise ValueError(f"El correo electrónico '{email}' ya se encuentra registrado.")

        # 3. Rol del usuario
        id_rol = int(data.get("id_rol")) if data.get("id_rol") else 2
        rol_existente = Roles.get_by_id(id_rol)
        if not rol_existente:
            nuevo_rol = Roles()
            nuevo_rol.nombre = "Vendedor"
            nuevo_rol.descripcion = "Gestión de ventas y clientes"
            nuevo_rol.save()
            id_rol = nuevo_rol.id

        raw_password = data.get("password") or data.get("password_hash", "123456")
        
        usuario = Usuarios()
        usuario.tipo_documento = str(data.get("tipo_documento") or "CC").strip().upper()
        
        # Documento único
        doc = str(data.get("documento") or "").strip()
        if not doc:
            doc = f"{int(time.time())}"
        else:
            doc_existente = UsuariosController.get_by_documento(doc)
            if doc_existente:
                raise ValueError(f"El documento '{doc}' ya se encuentra registrado con otro usuario.")
        usuario.documento = doc
        
        usuario.nombre = str(data.get("nombre") or "").strip()
        usuario.apellido = str(data.get("apellido") or "").strip()
        usuario.telefono = str(data.get("telefono") or "0000000000").strip()
        usuario.email = email
        usuario.username = username
        usuario.password_hash = hash_password(raw_password)
        usuario.id_rol = id_rol
        usuario.estado = data.get("estado", "Activo")
        usuario.banco = data.get("banco", "")
        usuario.tipo_cuenta = data.get("tipo_cuenta", "")
        usuario.numero_cuenta = data.get("numero_cuenta", "")
        
        usuario.save()

        # Simulación / Registro del envío de correo de bienvenida y credenciales
        print(f"[NOTIFICACION POR CORREO]: Correo enviado con exito a {usuario.email}")
        print(f"   Asunto: Bienvenido a PYMEsoft Movil! Tus credenciales de acceso")
        print(f"   Usuario: @{usuario.username} | Rol: {rol_existente.nombre if rol_existente else 'Usuario'}")

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
        if usuario:
            usuario.delete()
            return True
        return False
