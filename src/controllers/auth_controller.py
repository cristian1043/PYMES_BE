import os
import secrets
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token, create_refresh_token
from src.models import session
from src.models.usuarios import Usuarios
from src.models.roles import Roles
from src.models.usuario_empresas import UsuarioEmpresas
from src.models.tokens_seguridad import TokensSeguridad
from src.utils.security import verify_password, hash_password, validar_politica_password
from src.utils.mailer import Mailer


def _enmascarar_email(email: str) -> str:
    if not email or "@" not in email:
        return "tu correo registrado"
    parts = email.split("@")
    local = parts[0]
    visible = local[:2] if len(local) > 2 else local[:1]
    return f"{visible}***@{parts[1]}"


def _es_produccion() -> bool:
    return (
        os.environ.get("FLASK_ENV", "").lower() == "production"
        or os.environ.get("APP_ENV", "").lower() == "production"
    )


class AuthController:
    """Controlador de Autenticación JWT Administrativa, Recuperación Persistente y Eliminación en 2 Pasos."""

    @staticmethod
    def login(email_or_username, password):
        if not email_or_username or not password:
            return {"exito": False, "mensaje": "Correo/Usuario y contraseña son requeridos"}, 400

        usuario = Usuarios.get_by_login(email_or_username)
        if not usuario:
            return {"exito": False, "mensaje": "Credenciales inválidas"}, 401

        if usuario.estado and usuario.estado.lower() in ("inactivo", "eliminado"):
            return {"exito": False, "mensaje": "La cuenta se encuentra inactiva o fue eliminada"}, 403

        es_valida = verify_password(usuario.password_hash, password)
        if not es_valida:
            return {"exito": False, "mensaje": "Credenciales inválidas. Verifica tu usuario y contraseña."}, 401

        # Auto-migrar contraseña en texto plano a Hash seguro si proviene de datos legados
        if usuario.password_hash == password:
            usuario.password_hash = hash_password(password)
            usuario.update()

        rol = Roles.get_by_id(usuario.id_rol)
        nombre_rol = rol.nombre if rol else "Usuario"

        relaciones_empresa = UsuarioEmpresas.get_by_usuario_id(usuario.id)
        empresas_ids = [
            rel.empresa_id for rel in relaciones_empresa
            if (getattr(rel, "estado", "Activo") or "Activo") == "Activo"
        ]
        es_super = bool(getattr(usuario, "es_super_admin", 0))

        claims = {
            "identity_type": "admin",
            "usuario_id": usuario.id,
            "username": usuario.username,
            "email": usuario.email,
            "rol": nombre_rol,
            "id_rol": usuario.id_rol,
            "es_super_admin": es_super,
            "empresas": empresas_ids,
            "sesion_version": getattr(usuario, "sesion_version", 1) or 1
        }

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
                "es_super_admin": es_super,
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
        """Cambia la contraseña validando previamente la contraseña actual y la política de seguridad."""
        if not usuario_id:
            return {"exito": False, "mensaje": "ID de usuario no proporcionado"}, 400
        if not password_actual or not password_nueva:
            return {"exito": False, "mensaje": "Se requiere la contraseña actual y la nueva contraseña"}, 400

        valida_pol, msg_pol = validar_politica_password(password_nueva)
        if not valida_pol:
            return {"exito": False, "mensaje": msg_pol}, 400

        usuario = Usuarios.get_by_id(int(usuario_id))
        if not usuario:
            return {"exito": False, "mensaje": "Usuario no encontrado"}, 404

        if not verify_password(usuario.password_hash, password_actual):
            return {"exito": False, "mensaje": "La contraseña actual es incorrecta. Por motivos de seguridad, no se puede cambiar la clave."}, 400

        usuario.password_hash = hash_password(password_nueva)
        usuario.sesion_version = (getattr(usuario, "sesion_version", 1) or 1) + 1
        usuario.update()

        return {"exito": True, "mensaje": "Contraseña actualizada exitosamente."}, 200

    @staticmethod
    def solicitar_recuperacion(identificador):
        """
        Genera token seguro y código OTP de 6 dígitos persistidos en base de datos (`TokensSeguridad`).
        - Evita enumeración de usuarios/correos devolviendo siempre respuesta genérica 200.
        - Nunca expone el código OTP ni el token en la respuesta HTTP de producción ni en logs de producción.
        """
        if not identificador or not str(identificador).strip():
            return {"exito": False, "mensaje": "Debes ingresar tu correo electrónico, usuario o documento"}, 400

        val = str(identificador).strip()
        usuario = Usuarios.get_by_login(val)
        if not usuario:
            usuario = session.query(Usuarios).filter(Usuarios.documento == val).first()

        mensaje_generico = (
            "Si los datos ingresados corresponden a una cuenta activa, hemos enviado las instrucciones "
            "y el código de verificación al correo electrónico registrado."
        )

        if not usuario or (usuario.estado and usuario.estado.lower() in ("inactivo", "eliminado")):
            return {
                "exito": True,
                "mensaje": mensaje_generico,
                "email_enmascarado": "co***@registrado"
            }, 200

        token = secrets.token_urlsafe(32)
        otp_codigo = f"{secrets.randbelow(900000) + 100000}"

        TokensSeguridad.crear_token(
            tipo="password_recovery",
            identidad_tipo="usuario",
            identidad_id=usuario.id,
            codigo=otp_codigo,
            token=token,
            minutos_expiracion=30,
            max_intentos=5
        )

        fe_base_url = os.environ.get("FRONTEND_ADMIN_URL", "http://127.0.0.1:5001").rstrip("/")
        link_recuperacion = f"{fe_base_url}/recuperar_password?token={token}"
        email_enmascarado = _enmascarar_email(usuario.email)
        nombre_completo = f"{usuario.nombre} {usuario.apellido}".strip()

        enviado_smtp = Mailer.enviar_codigo_recuperacion(
            destinatario=usuario.email,
            nombre=nombre_completo,
            otp_codigo=otp_codigo,
            link_recuperacion=link_recuperacion
        )

        return {
            "exito": True,
            "mensaje": mensaje_generico,
            "email_enmascarado": email_enmascarado,
            "enviado_smtp": bool(enviado_smtp)
        }, 200

    @staticmethod
    def confirmar_recuperacion(token_o_codigo, password_nueva, identificador=None):
        """Restablece la contraseña validando el token o código OTP persistido en base de datos."""
        if not token_o_codigo:
            return {"exito": False, "mensaje": "Se requiere el código o token de verificación"}, 400

        valida_pol, msg_pol = validar_politica_password(password_nueva)
        if not valida_pol:
            return {"exito": False, "mensaje": msg_pol}, 400

        clave = str(token_o_codigo).strip()
        uid_filtro = None
        if identificador:
            u_cand = Usuarios.get_by_login(str(identificador).strip())
            if not u_cand:
                u_cand = session.query(Usuarios).filter(Usuarios.documento == str(identificador).strip()).first()
            if u_cand:
                uid_filtro = u_cand.id

        if len(clave) > 12:
            reg, err = TokensSeguridad.validar_y_consumir(
                tipo="password_recovery",
                identidad_tipo="usuario",
                token=clave
            )
        else:
            reg, err = TokensSeguridad.validar_y_consumir(
                tipo="password_recovery",
                identidad_tipo="usuario",
                identidad_id=uid_filtro,
                codigo=clave
            )

        if err or not reg:
            return {"exito": False, "mensaje": err or "El código o enlace es inválido o ha expirado."}, 400

        usuario = Usuarios.get_by_id(reg.identidad_id)
        if not usuario:
            return {"exito": False, "mensaje": "Usuario no encontrado"}, 404

        usuario.password_hash = hash_password(password_nueva)
        usuario.sesion_version = (getattr(usuario, "sesion_version", 1) or 1) + 1
        usuario.update()

        return {
            "exito": True,
            "mensaje": "Tu contraseña ha sido restablecida exitosamente. Ya puedes iniciar sesión con tu nueva contraseña."
        }, 200

    @staticmethod
    def solicitar_eliminacion_cuenta(usuario_id, password_actual):
        """Paso 1 de verificación en 2 pasos para eliminar cuenta: valida contraseña y persiste código OTP en BD."""
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
        TokensSeguridad.crear_token(
            tipo="account_deletion",
            identidad_tipo="usuario",
            identidad_id=int(usuario.id),
            codigo=otp_codigo,
            minutos_expiracion=10,
            max_intentos=5
        )

        email_enmascarado = _enmascarar_email(usuario.email)
        nombre_completo = f"{usuario.nombre} {usuario.apellido}".strip()
        enviado_smtp = Mailer.enviar_codigo_eliminacion(
            destinatario=usuario.email,
            nombre=nombre_completo,
            otp_codigo=otp_codigo
        )

        return {
            "exito": True,
            "mensaje": f"Paso 1 verificado. Se envió un código de 6 dígitos a {email_enmascarado} para confirmar la eliminación.",
            "email_enmascarado": email_enmascarado,
            "enviado_smtp": bool(enviado_smtp)
        }, 200

    @staticmethod
    def confirmar_eliminacion_cuenta(usuario_id, codigo_otp):
        """Paso 2 de verificación en 2 pasos: verifica el código OTP en BD y elimina/anonimiza la cuenta."""
        if not usuario_id:
            return {"exito": False, "mensaje": "Usuario no identificado."}, 400
        if not codigo_otp or not str(codigo_otp).strip():
            return {"exito": False, "mensaje": "Debes ingresar el código de verificación de 6 dígitos del segundo paso."}, 400

        uid = int(usuario_id)
        reg, err = TokensSeguridad.validar_y_consumir(
            tipo="account_deletion",
            identidad_tipo="usuario",
            identidad_id=uid,
            codigo=str(codigo_otp).strip()
        )
        if err or not reg:
            return {"exito": False, "mensaje": err or "Código de verificación inválido."}, 400

        usuario = Usuarios.get_by_id(uid)
        if not usuario:
            return {"exito": False, "mensaje": "Usuario no encontrado."}, 404

        try:
            session.query(UsuarioEmpresas).filter(UsuarioEmpresas.usuario_id == uid).delete()
            session.flush()
            session.delete(usuario)
            session.commit()
        except Exception:
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
