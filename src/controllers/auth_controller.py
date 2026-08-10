from flask_jwt_extended import create_access_token, create_refresh_token
from src.models.usuarios import Usuarios
from src.models.roles import Roles
from src.models.usuario_empresas import UsuarioEmpresas
from src.models.empresas import Empresas
from src.utils.security import verify_password, hash_password
from src.utils.migrations import DatabaseMigrations
from datetime import timedelta

class AuthController:
    """Controlador de Autenticación JWT y Gestión de Sesiones."""

    @staticmethod
    def login(email_or_username, password):
        DatabaseMigrations.ejecutar_migraciones()
        
        if not email_or_username or not password:
            return {"exito": False, "mensaje": "Correo/Usuario y contraseña son requeridos"}, 400

        # Buscar usuario por email o por username
        usuario = Usuarios.get_by_login(email_or_username)
        if not usuario:
            return {"exito": False, "mensaje": "Credenciales inválidas"}, 401

        if usuario.estado and usuario.estado.lower() == "inactivo":
            return {"exito": False, "mensaje": "El usuario se encuentra inactivo"}, 403

        # Verificar clave
        es_valida = verify_password(usuario.password_hash, password)
        if not es_valida:
            return {"exito": False, "mensaje": "Credenciales inválidas"}, 401

        # Auto-migrar contraseña en texto plano a Hash si es necesario
        if usuario.password_hash == password:
            usuario.password_hash = hash_password(password)
            usuario.update()

        # Obtener información del rol
        rol = Roles.get_by_id(usuario.id_rol)
        nombre_rol = rol.nombre if rol else "Usuario"

        # Obtener empresas asociadas al usuario
        relaciones_empresa = UsuarioEmpresas.get_by_usuario_id(usuario.id)
        empresas_ids = [rel.empresa_id for rel in relaciones_empresa]

        claims = {
            "usuario_id": usuario.id,
            "username": usuario.username,
            "email": usuario.email,
            "rol": nombre_rol,
            "id_rol": usuario.id_rol,
            "empresas": empresas_ids
        }

        # Generar tokens con tiempos de expiración definidos
        access_token = create_access_token(
            identity=str(usuario.id),
            additional_claims=claims,
            expires_delta=timedelta(hours=2)
        )
        refresh_token = create_refresh_token(
            identity=str(usuario.id),
            expires_delta=timedelta(days=30)
        )

        return {
            "exito": True,
            "mensaje": "Inicio de sesión exitoso",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "usuario": {
                "id": usuario.id,
                "nombre": f"{usuario.nombre} {usuario.apellido}",
                "email": usuario.email,
                "username": usuario.username,
                "rol": nombre_rol,
                "empresas": empresas_ids
            }
        }, 200

    @staticmethod
    def get_user_profile(user_id):
        usuario = Usuarios.get_by_id(int(user_id))
        if not usuario:
            return {"mensaje": "Usuario no encontrado"}, 404
        
        rol = Roles.get_by_id(usuario.id_rol)
        user_dict = usuario.to_dict()
        user_dict["rol_nombre"] = rol.nombre if rol else "Sin Rol"
        return user_dict, 200
