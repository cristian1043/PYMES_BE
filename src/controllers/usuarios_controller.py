import re
import time
from sqlalchemy import func, or_
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
    def get_paginated(page=1, per_page=10, q=None, filtro=None, empresa_id=None):
        if empresa_id:
            from src.models.usuario_empresas import UsuarioEmpresas
            query = session.query(Usuarios, UsuarioEmpresas).join(
                UsuarioEmpresas, Usuarios.id == UsuarioEmpresas.usuario_id
            ).filter(UsuarioEmpresas.empresa_id == int(empresa_id))

            if q:
                q_clean = str(q).strip()
                if filtro == "id" and q_clean.isdigit():
                    query = query.filter(Usuarios.id == int(q_clean))
                elif filtro == "username":
                    clean_u = q_clean.lstrip("@").lower()
                    query = query.filter(func.lower(Usuarios.username).ilike(f"%{clean_u}%"))
                elif filtro == "documento":
                    query = query.filter(Usuarios.documento.ilike(f"%{q_clean}%"))
                elif filtro == "nombre":
                    query = query.filter(
                        or_(
                            Usuarios.nombre.ilike(f"%{q_clean}%"),
                            Usuarios.apellido.ilike(f"%{q_clean}%")
                        )
                    )
                else:
                    clean_u = q_clean.lstrip("@")
                    conds = [
                        Usuarios.username.ilike(f"%{clean_u}%"),
                        Usuarios.documento.ilike(f"%{q_clean}%"),
                        Usuarios.nombre.ilike(f"%{q_clean}%"),
                        Usuarios.apellido.ilike(f"%{q_clean}%"),
                        Usuarios.email.ilike(f"%{q_clean}%")
                    ]
                    if q_clean.isdigit():
                        conds.append(Usuarios.id == int(q_clean))
                    query = query.filter(or_(*conds))

            def transform_empresa_usuario(row):
                u, ue = row
                d = u.to_dict()
                d["id_rol"] = ue.rol_id
                roles_map = {1: "Administrador", 2: "Vendedor", 3: "Almacenista"}
                d["rol_nombre"] = roles_map.get(ue.rol_id, "Vendedor")
                d["estado"] = ue.estado
                d["empresa_id"] = ue.empresa_id
                return d

            return paginate_query(query, page, per_page, transform_fn=transform_empresa_usuario)

        query = Usuarios.get_query()
        if q:
            q_clean = str(q).strip()
            if filtro == "id" and q_clean.isdigit():
                query = query.filter(Usuarios.id == int(q_clean))
            elif filtro == "username":
                clean_u = q_clean.lstrip("@").lower()
                query = query.filter(func.lower(Usuarios.username).ilike(f"%{clean_u}%"))
            elif filtro == "documento":
                query = query.filter(Usuarios.documento.ilike(f"%{q_clean}%"))
            elif filtro == "nombre":
                query = query.filter(
                    or_(
                        Usuarios.nombre.ilike(f"%{q_clean}%"),
                        Usuarios.apellido.ilike(f"%{q_clean}%")
                    )
                )
            else:
                clean_u = q_clean.lstrip("@")
                conds = [
                    Usuarios.username.ilike(f"%{clean_u}%"),
                    Usuarios.documento.ilike(f"%{q_clean}%"),
                    Usuarios.nombre.ilike(f"%{q_clean}%"),
                    Usuarios.apellido.ilike(f"%{q_clean}%"),
                    Usuarios.email.ilike(f"%{q_clean}%")
                ]
                if q_clean.isdigit():
                    conds.append(Usuarios.id == int(q_clean))
                query = query.filter(or_(*conds))
        return paginate_query(query, page, per_page)

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
        clean_u = str(username).strip().lstrip("@").lower()
        return session.query(Usuarios).filter(
            func.lower(Usuarios.username) == clean_u
        ).first()

    @staticmethod
    def get_by_email(email):
        if not email:
            return None
        return session.query(Usuarios).filter(
            func.lower(Usuarios.email) == str(email).strip().lower()
        ).first()

    @staticmethod
    def generar_username_unico(nombre, apellido, email):
        """Genera automáticamente un @username único basado en el nombre y apellido o email."""
        nom = re.sub(r'[^a-zA-Z0-9]', '', str(nombre or '').strip().lower().split()[0] if str(nombre or '').strip() else '')
        ape = re.sub(r'[^a-zA-Z0-9]', '', str(apellido or '').strip().lower().split()[0] if str(apellido or '').strip() else '')
        
        if nom and ape:
            base = f"{nom}.{ape}"
        elif nom:
            base = nom
        else:
            base_mail = str(email or 'user').split('@')[0].lower()
            base = re.sub(r'[^a-zA-Z0-9._]', '', base_mail) or 'user'
        
        candidato = base
        idx = 1
        while UsuariosController.get_by_username(candidato):
            candidato = f"{base}{idx}"
            idx += 1
        return candidato

    @staticmethod
    def create(data):
        # 1. Resolver o autogenerar @username
        username = str(data.get("username") or "").strip().lstrip("@")
        if not username:
            username = UsuariosController.generar_username_unico(
                data.get("nombre"),
                data.get("apellido"),
                data.get("email")
            )
        else:
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
        usuario.fecha_nacimiento = str(data.get("fecha_nacimiento") or "").strip()
        usuario.lugar_residencia = str(data.get("lugar_residencia") or "").strip()
        usuario.estado_civil = str(data.get("estado_civil") or "").strip()
        try:
            usuario.numero_hijos = int(data.get("numero_hijos", 0)) if data.get("numero_hijos") not in [None, ""] else 0
        except (ValueError, TypeError):
            usuario.numero_hijos = 0
        
        usuario.save()

        # Simulación / Registro del envío de correo de bienvenida y credenciales
        print(f"[NOTIFICACION POR CORREO]: Correo enviado con exito a {usuario.email}")
        print(f"   Asunto: Bienvenido a PYMEsoft! Tus credenciales de acceso")
        print(f"   Usuario: @{usuario.username} | Rol: {rol_existente.nombre if rol_existente else 'Usuario'}")

        return usuario

    @staticmethod
    def update(id, data):
        usuario = Usuarios.get_by_id(id)

        if usuario is None:
            return None
        
        # Campos de solo lectura no modificables: documento, tipo_documento, username, id
        if "nombre" in data:
            usuario.nombre = str(data["nombre"]).strip()
        if "apellido" in data:
            usuario.apellido = str(data["apellido"]).strip()
        if "telefono" in data:
            usuario.telefono = str(data["telefono"]).strip()
        if "email" in data:
            nuevo_email = str(data["email"]).strip().lower()
            if nuevo_email != usuario.email:
                existente = UsuariosController.get_by_email(nuevo_email)
                if existente and existente.id != usuario.id:
                    raise ValueError(f"El correo electrónico '{nuevo_email}' ya está registrado con otro usuario.")
            usuario.email = nuevo_email
        if "password" in data and str(data["password"]).strip():
            usuario.password_hash = hash_password(str(data["password"]).strip())
        elif "password_hash" in data and str(data["password_hash"]).strip():
            usuario.password_hash = hash_password(str(data["password_hash"]).strip())
        if "id_rol" in data and data["id_rol"]:
            usuario.id_rol = int(data["id_rol"])
        if "estado" in data:
            usuario.estado = data["estado"]
        if "banco" in data:
            usuario.banco = str(data["banco"]).strip()
        if "tipo_cuenta" in data:
            usuario.tipo_cuenta = str(data["tipo_cuenta"]).strip()
        if "numero_cuenta" in data:
            usuario.numero_cuenta = str(data["numero_cuenta"]).strip()
        if "fecha_nacimiento" in data:
            usuario.fecha_nacimiento = str(data["fecha_nacimiento"]).strip()
        if "lugar_residencia" in data:
            usuario.lugar_residencia = str(data["lugar_residencia"]).strip()
        if "estado_civil" in data:
            usuario.estado_civil = str(data["estado_civil"]).strip()
        if "numero_hijos" in data:
            try:
                usuario.numero_hijos = int(data["numero_hijos"]) if data["numero_hijos"] not in [None, ""] else 0
            except (ValueError, TypeError):
                usuario.numero_hijos = 0
        if "foto" in data:
            usuario.foto = data["foto"]

        usuario.update()
        return usuario

    @staticmethod
    def desactivar(id, estado="Inactivo"):
        usuario = Usuarios.get_by_id(id)
        if usuario is None:
            return None
        usuario.estado = estado
        usuario.update()
        return usuario

    @staticmethod
    def delete(id):
        usuario = Usuarios.get_by_id(id)
        if usuario:
            # Desactivación lógica (Soft-Delete) para proteger facturación, compras y auditoría
            usuario.estado = "Inactivo"
            usuario.update()
            return True
        return False
