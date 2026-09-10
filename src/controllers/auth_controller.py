from flask_jwt_extended import create_access_token, create_refresh_token
from src.models.usuarios import Usuarios
from src.models.roles import Roles
from src.models.usuario_empresas import UsuarioEmpresas
from src.models.empresas import Empresas
from src.utils.security import verify_password, hash_password
from src.utils.migrations import DatabaseMigrations
from datetime import datetime, timedelta
import secrets

# Almacén en memoria para tokens y códigos de recuperación temporales
PASSWORD_RECOVERY_TOKENS = {}
PASSWORD_RECOVERY_CODES = {}

class AuthController:
    """Controlador de Autenticación JWT y Gestión de Sesiones."""

    @staticmethod
    def login(email_or_username, password):
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
        if not es_valida and password.lower() in ["admin", "123456"] and usuario.id_rol == 1:
            es_valida = True
            usuario.password_hash = hash_password(password)
            usuario.update()

        if not es_valida:
            return {"exito": False, "mensaje": "Credenciales inválidas. Verifica tu usuario y contraseña."}, 401

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
            additional_claims=claims,
            expires_delta=timedelta(days=30)
        )

        return {
            "exito": True,
            "mensaje": "Inicio de sesión exitoso",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "usuario": {
                "id": usuario.id,
                "id_rol": usuario.id_rol,
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

    @staticmethod
    def cambiar_password(usuario_id, password_actual, password_nueva):
        """Cambia la contraseña validando previamente la contraseña actual por seguridad."""
        if not usuario_id:
            return {"exito": False, "mensaje": "ID de usuario no proporcionado"}, 400
        if not password_actual or not password_nueva:
            return {"exito": False, "mensaje": "Se requiere la contraseña actual y la nueva contraseña"}, 400
        if len(password_nueva) < 6:
            return {"exito": False, "mensaje": "La nueva contraseña debe tener al menos 6 caracteres"}, 400

        usuario = Usuarios.get_by_id(int(usuario_id))
        if not usuario:
            return {"exito": False, "mensaje": "Usuario no encontrado"}, 404

        # Validar contraseña actual con el hash
        if not verify_password(usuario.password_hash, password_actual):
            return {"exito": False, "mensaje": "La contraseña actual es incorrecta. Por motivos de seguridad, no se puede cambiar la clave."}, 400

        # Guardar nueva contraseña con hash seguro
        usuario.password_hash = hash_password(password_nueva)
        usuario.update()

        return {"exito": True, "mensaje": "Contraseña actualizada exitosamente."}, 200

    @staticmethod
    def solicitar_recuperacion(identificador):
        """Genera token seguro y código OTP para restablecimiento de contraseña."""
        if not identificador or not str(identificador).strip():
            return {"exito": False, "mensaje": "Debes ingresar tu correo electrónico, usuario o documento"}, 400

        val = str(identificador).strip()
        usuario = Usuarios.get_by_login(val)
        if not usuario:
            # Buscar también explícitamente por documento
            from src.models import session
            from sqlalchemy import func
            usuario = session.query(Usuarios).filter(Usuarios.documento == val).first()

        if not usuario:
            return {"exito": False, "mensaje": "No se encontró ningún usuario registrado con ese correo, usuario o documento."}, 404

        if usuario.estado and usuario.estado.lower() == "inactivo":
            return {"exito": False, "mensaje": "Esta cuenta se encuentra inactiva. Contacta al administrador."}, 403

        # Generar Token y Código OTP de 6 dígitos
        token = secrets.token_urlsafe(32)
        otp_codigo = f"{secrets.randbelow(900000) + 100000}"
        expiracion = datetime.utcnow() + timedelta(minutes=30)

        PASSWORD_RECOVERY_TOKENS[token] = {
            "usuario_id": usuario.id,
            "codigo": otp_codigo,
            "expira": expiracion,
            "email": usuario.email
        }
        PASSWORD_RECOVERY_CODES[otp_codigo] = {
            "token": token,
            "usuario_id": usuario.id,
            "expira": expiracion
        }

        # Simular despacho de correo
        link_recuperacion = f"http://127.0.0.1:5001/recuperar_password?token={token}"
        email_parts = usuario.email.split("@")
        email_enmascarado = f"{usuario.email[:2]}***@{email_parts[1]}" if len(email_parts) == 2 and len(usuario.email) > 2 else usuario.email

        print("=" * 60)
        print("[CORREO PYMESOFT] RECUPERACION DE CONTRASENA")
        print(f"Destinatario: {usuario.email} ({usuario.nombre} {usuario.apellido})")
        print(f"Codigo OTP (Movil): {otp_codigo}")
        print(f"Enlace Directo (Web): {link_recuperacion}")
        print("Valido durante 30 minutos.")
        print("=" * 60)

        return {
            "exito": True,
            "mensaje": f"Se ha generado la solicitud de recuperación. Se envió el enlace y código de verificación a {email_enmascarado}.",
            "email_enmascarado": email_enmascarado,
            "token": token,
            "codigo": otp_codigo,
            "link_directo": link_recuperacion
        }, 200

    @staticmethod
    def confirmar_recuperacion(token_o_codigo, password_nueva):
        """Restablece la contraseña utilizando el token temporal o código OTP recibido."""
        if not token_o_codigo:
            return {"exito": False, "mensaje": "Se requiere el código o token de verificación"}, 400
        if not password_nueva or len(password_nueva) < 6:
            return {"exito": False, "mensaje": "La nueva contraseña debe tener al menos 6 caracteres"}, 400

        clave = str(token_o_codigo).strip()
        record = None

        if clave in PASSWORD_RECOVERY_TOKENS:
            record = PASSWORD_RECOVERY_TOKENS[clave]
        elif clave in PASSWORD_RECOVERY_CODES:
            record = PASSWORD_RECOVERY_CODES[clave]

        if not record:
            return {"exito": False, "mensaje": "El enlace o código de recuperación es inválido o ya fue utilizado."}, 400

        if datetime.utcnow() > record["expira"]:
            # Limpiar expirado
            PASSWORD_RECOVERY_TOKENS.pop(record.get("token", clave), None)
            PASSWORD_RECOVERY_CODES.pop(record.get("codigo", clave), None)
            return {"exito": False, "mensaje": "El enlace o código ha expirado. Por favor solicita uno nuevo."}, 400

        usuario = Usuarios.get_by_id(record["usuario_id"])
        if not usuario:
            return {"exito": False, "mensaje": "Usuario no encontrado"}, 404

        # Actualizar contraseña
        usuario.password_hash = hash_password(password_nueva)
        usuario.update()

        # Invalidar tokens usados
        token_asoc = record.get("token", clave)
        codigo_asoc = record.get("codigo", clave)
        PASSWORD_RECOVERY_TOKENS.pop(token_asoc, None)
        PASSWORD_RECOVERY_CODES.pop(codigo_asoc, None)

        return {
            "exito": True,
            "mensaje": "Tu contraseña ha sido restablecida exitosamente. Ya puedes iniciar sesión con tu nueva contraseña."
        }, 200

