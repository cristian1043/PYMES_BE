from flask_jwt_extended import create_access_token, create_refresh_token
from src.models import session
from src.models.usuarios import Usuarios
from src.models.roles import Roles
from src.models.usuario_empresas import UsuarioEmpresas
from src.models.empresas import Empresas
from src.utils.security import verify_password, hash_password
from src.utils.mailer import Mailer
from datetime import datetime, timedelta
import secrets

# Almacenes en memoria para tokens y códigos OTP de recuperación y eliminación en 2 pasos
PASSWORD_RECOVERY_TOKENS = {}
PASSWORD_RECOVERY_CODES = {}
ACCOUNT_DELETION_CODES = {}


def _enmascarar_email(email: str) -> str:
    if not email or "@" not in email:
        return email or ""
    parts = email.split("@")
    local = parts[0]
    visible = local[:2] if len(local) > 2 else local[:1]
    return f"{visible}***@{parts[1]}"


class AuthController:
    """Controlador de Autenticación JWT, Recuperación de Acceso y Eliminación en 2 Pasos."""

    @staticmethod
    def login(email_or_username, password):
        if not email_or_username or not password:
            return {"exito": False, "mensaje": "Correo/Usuario y contraseña son requeridos"}, 400

        # Buscar usuario por email o por username
        usuario = Usuarios.get_by_login(email_or_username)
        if not usuario:
            return {"exito": False, "mensaje": "Credenciales inválidas"}, 401

        if usuario.estado and usuario.estado.lower() in ("inactivo", "eliminado"):
            return {"exito": False, "mensaje": "La cuenta se encuentra inactiva o fue eliminada"}, 403

        # Verificar clave
        es_valida = verify_password(usuario.password_hash, password)
        if not es_valida:
            return {"exito": False, "mensaje": "Credenciales inválidas. Verifica tu usuario y contraseña."}, 401

        # Auto-migrar contraseña en texto plano a Hash si es necesario
        if usuario.password_hash == password:
            usuario.password_hash = hash_password(password)
            usuario.update()

        # Obtener información del rol
        rol = Roles.get_by_id(usuario.id_rol)
        nombre_rol = rol.nombre if rol else "Usuario"

        # Obtener empresas activas asociadas al usuario (excluir desvinculadas/inactivas)
        relaciones_empresa = UsuarioEmpresas.get_by_usuario_id(usuario.id)
        empresas_ids = [
            rel.empresa_id for rel in relaciones_empresa
            if (getattr(rel, "estado", "Activo") or "Activo") == "Activo"
        ]

        claims = {
            "usuario_id": usuario.id,
            "username": usuario.username,
            "email": usuario.email,
            "rol": nombre_rol,
            "id_rol": usuario.id_rol,
            "empresas": empresas_ids,
            "sesion_version": getattr(usuario, "sesion_version", 1) or 1
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
                "nombre": f"{usuario.nombre} {usuario.apellido}".strip(),
                "nombre_pila": usuario.nombre,
                "apellido": usuario.apellido,
                "tipo_documento": usuario.tipo_documento,
                "documento": usuario.documento,
                "telefono": usuario.telefono,
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
        """Genera token seguro y código OTP de 6 dígitos para restablecimiento de contraseña."""
        if not identificador or not str(identificador).strip():
            return {"exito": False, "mensaje": "Debes ingresar tu correo electrónico, usuario o documento"}, 400

        val = str(identificador).strip()
        usuario = Usuarios.get_by_login(val)
        if not usuario:
            usuario = session.query(Usuarios).filter(Usuarios.documento == val).first()

        if not usuario:
            return {"exito": False, "mensaje": "No se encontró ningún usuario registrado con ese correo, usuario o documento."}, 404

        if usuario.estado and usuario.estado.lower() in ("inactivo", "eliminado"):
            return {"exito": False, "mensaje": "Esta cuenta se encuentra inactiva. Contacta al administrador."}, 403

        # Generar Token y Código OTP de 6 dígitos
        token = secrets.token_urlsafe(32)
        otp_codigo = f"{secrets.randbelow(900000) + 100000}"
        expiracion = datetime.utcnow() + timedelta(minutes=30)

        record_data = {
            "token": token,
            "codigo": otp_codigo,
            "usuario_id": usuario.id,
            "expira": expiracion,
            "email": usuario.email
        }
        PASSWORD_RECOVERY_TOKENS[token] = record_data
        PASSWORD_RECOVERY_CODES[otp_codigo] = record_data

        link_recuperacion = f"http://127.0.0.1:5001/recuperar_password?token={token}"
        email_enmascarado = _enmascarar_email(usuario.email)
        nombre_completo = f"{usuario.nombre} {usuario.apellido}".strip()

        enviado_smtp = Mailer.enviar_codigo_recuperacion(
            destinatario=usuario.email,
            nombre=nombre_completo,
            otp_codigo=otp_codigo,
            link_recuperacion=link_recuperacion
        )

        print("=" * 60)
        print("[CORREO PYMESOFT] RECUPERACION DE CONTRASENA")
        print(f"Destinatario: {usuario.email} ({nombre_completo})")
        print(f"Codigo OTP (6 digitos): {otp_codigo}")
        print(f"Enlace Directo (Web): {link_recuperacion}")
        print(f"Despacho SMTP real: {'SI' if enviado_smtp else 'MODO LOCAL (entregado en respuesta)'}")
        print("=" * 60)

        return {
            "exito": True,
            "mensaje": (
                f"Código de verificación enviado a {email_enmascarado}."
                if enviado_smtp
                else f"Código de verificación generado para {email_enmascarado}: {otp_codigo}"
            ),
            "email_enmascarado": email_enmascarado,
            "enviado_smtp": enviado_smtp,
            "codigo": otp_codigo,
            "token": token,
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
        record = PASSWORD_RECOVERY_CODES.get(clave) or PASSWORD_RECOVERY_TOKENS.get(clave)

        if not record:
            return {"exito": False, "mensaje": "El enlace o código de recuperación es inválido o ya fue utilizado."}, 400

        if datetime.utcnow() > record["expira"]:
            PASSWORD_RECOVERY_TOKENS.pop(record.get("token", clave), None)
            PASSWORD_RECOVERY_CODES.pop(record.get("codigo", clave), None)
            return {"exito": False, "mensaje": "El enlace o código ha expirado. Por favor solicita uno nuevo."}, 400

        usuario = Usuarios.get_by_id(record["usuario_id"])
        if not usuario:
            return {"exito": False, "mensaje": "Usuario no encontrado"}, 404

        usuario.password_hash = hash_password(password_nueva)
        usuario.update()

        PASSWORD_RECOVERY_TOKENS.pop(record.get("token", clave), None)
        PASSWORD_RECOVERY_CODES.pop(record.get("codigo", clave), None)

        return {
            "exito": True,
            "mensaje": "Tu contraseña ha sido restablecida exitosamente. Ya puedes iniciar sesión con tu nueva contraseña."
        }, 200

    @staticmethod
    def solicitar_eliminacion_cuenta(usuario_id, password_actual):
        """Paso 1 de verificación en 2 pasos para eliminar cuenta: valida contraseña y envía código OTP."""
        if not usuario_id:
            return {"exito": False, "mensaje": "Usuario no identificado."}, 400
        if not password_actual or not str(password_actual).strip():
            return {"exito": False, "mensaje": "Debes ingresar tu contraseña actual para iniciar la verificación de dos pasos."}, 400

        usuario = Usuarios.get_by_id(int(usuario_id))
        if not usuario:
            return {"exito": False, "mensaje": "Usuario no encontrado."}, 404

        if not verify_password(usuario.password_hash, str(password_actual).strip()):
            return {"exito": False, "mensaje": "La contraseña actual es incorrecta. Verificación de primer paso denegada."}, 400

        otp_codigo = f"{secrets.randbelow(900000) + 100000}"
        expiracion = datetime.utcnow() + timedelta(minutes=10)
        ACCOUNT_DELETION_CODES[int(usuario.id)] = {
            "codigo": otp_codigo,
            "expira": expiracion,
            "intentos": 0
        }

        email_enmascarado = _enmascarar_email(usuario.email)
        nombre_completo = f"{usuario.nombre} {usuario.apellido}".strip()
        enviado_smtp = Mailer.enviar_codigo_eliminacion(
            destinatario=usuario.email,
            nombre=nombre_completo,
            otp_codigo=otp_codigo
        )

        print("=" * 60)
        print("[SEGURIDAD 2FA PYMESOFT] SOLICITUD DE ELIMINACION DE CUENTA")
        print(f"Usuario ID: {usuario.id} | Email: {usuario.email}")
        print(f"Codigo de 2do Paso (6 digitos): {otp_codigo}")
        print("=" * 60)

        return {
            "exito": True,
            "mensaje": (
                f"Paso 1 verificado. Se envió un código de 6 dígitos a {email_enmascarado} para confirmar la eliminación."
                if enviado_smtp
                else f"Paso 1 verificado. Código de seguridad de 2do paso generado ({email_enmascarado}): {otp_codigo}"
            ),
            "email_enmascarado": email_enmascarado,
            "enviado_smtp": enviado_smtp,
            "codigo": otp_codigo
        }, 200

    @staticmethod
    def confirmar_eliminacion_cuenta(usuario_id, codigo_otp):
        """Paso 2 de verificación en 2 pasos: verifica el código OTP de 6 dígitos y elimina la cuenta."""
        if not usuario_id:
            return {"exito": False, "mensaje": "Usuario no identificado."}, 400
        if not codigo_otp or not str(codigo_otp).strip():
            return {"exito": False, "mensaje": "Debes ingresar el código de verificación de 6 dígitos del segundo paso."}, 400

        uid = int(usuario_id)
        record = ACCOUNT_DELETION_CODES.get(uid)
        if not record:
            return {"exito": False, "mensaje": "No hay una solicitud activa de eliminación. Realiza primero el Paso 1."}, 400

        if datetime.utcnow() > record["expira"]:
            ACCOUNT_DELETION_CODES.pop(uid, None)
            return {"exito": False, "mensaje": "El código de verificación ha expirado. Inicia el proceso nuevamente."}, 400

        if str(codigo_otp).strip() != record["codigo"]:
            record["intentos"] = record.get("intentos", 0) + 1
            if record["intentos"] >= 5:
                ACCOUNT_DELETION_CODES.pop(uid, None)
                return {"exito": False, "mensaje": "Demasiados intentos fallidos. El código fue invalidado por seguridad."}, 400
            return {"exito": False, "mensaje": "El código de verificación de 6 dígitos es incorrecto."}, 400

        usuario = Usuarios.get_by_id(uid)
        if not usuario:
            ACCOUNT_DELETION_CODES.pop(uid, None)
            return {"exito": False, "mensaje": "Usuario no encontrado."}, 404

        ACCOUNT_DELETION_CODES.pop(uid, None)

        try:
            # 1. Eliminar todas las vinculaciones del usuario con empresas
            session.query(UsuarioEmpresas).filter(UsuarioEmpresas.usuario_id == uid).delete()
            session.flush()
            # 2. Intentar eliminación física de la cuenta
            session.delete(usuario)
            session.commit()
        except Exception:
            # Si el usuario posee facturas/compras históricas con llave foránea, anonimizar credenciales y desactivar permanentemente
            session.rollback()
            try:
                session.query(UsuarioEmpresas).filter(UsuarioEmpresas.usuario_id == uid).delete()
                ts = int(datetime.utcnow().timestamp())
                usuario = Usuarios.get_by_id(uid)
                if usuario:
                    usuario.estado = "Eliminado"
                    usuario.email = f"eliminado_{uid}_{ts}@baja.pymesoft.local"
                    usuario.username = f"eliminado_{uid}_{ts}"
                    usuario.documento = f"DEL-{uid}-{ts}"
                    usuario.password_hash = hash_password(secrets.token_urlsafe(32))
                    usuario.sesion_version = (getattr(usuario, "sesion_version", 1) or 1) + 10
                    session.commit()
            except Exception as inner_e:
                session.rollback()
                return {"exito": False, "mensaje": f"No se pudo completar la eliminación: {str(inner_e)}"}, 500

        return {
            "exito": True,
            "mensaje": "Tu cuenta ha sido eliminada permanentemente tras completar la verificación en dos pasos."
        }, 200

    @staticmethod
    def logout_global(usuario_id):
        try:
            usuario = Usuarios.get_by_id(int(usuario_id))
            if not usuario:
                return {"exito": False, "mensaje": "Usuario no encontrado"}, 404
            
            actual_version = getattr(usuario, "sesion_version", 1) or 1
            usuario.sesion_version = actual_version + 1
            usuario.update()
            return {"exito": True, "mensaje": "Sesión cerrada globalmente en todos los dispositivos"}, 200
        except Exception as e:
            return {"exito": False, "mensaje": f"Error al cerrar sesión global: {str(e)}"}, 500
