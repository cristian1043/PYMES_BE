from datetime import datetime, timedelta
import hashlib
from sqlalchemy import Column, Integer, String, DateTime
from src.models import Base, session


class TokensSeguridad(Base):
    """
    Almacenamiento persistente en BD para tokens y códigos OTP de recuperación de contraseña,
    eliminación de cuenta (2FA) y verificación de vinculación de clientes.
    Reemplaza los diccionarios volátiles en memoria (PASSWORD_RECOVERY_TOKENS, etc.).
    """
    __tablename__ = "tokens_seguridad"

    id = Column(Integer, primary_key=True)
    tipo = Column(String(40), nullable=False, index=True)  # 'password_recovery', 'account_deletion', 'client_linking'
    identidad_tipo = Column(String(20), nullable=False, index=True)  # 'usuario' | 'cliente'
    identidad_id = Column(Integer, nullable=False, index=True)
    id_empresa = Column(Integer, nullable=True, index=True)
    codigo_hash = Column(String(128), nullable=True, index=True)
    token_hash = Column(String(128), nullable=True, index=True)
    intentos = Column(Integer, default=0, nullable=False)
    max_intentos = Column(Integer, default=5, nullable=False)
    usado = Column(Integer, default=0, nullable=False)
    expira_en = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    @staticmethod
    def hash_valor(valor):
        if not valor:
            return None
        return hashlib.sha256(str(valor).strip().encode("utf-8")).hexdigest()

    @classmethod
    def crear_token(cls, tipo, identidad_tipo, identidad_id, codigo=None, token=None,
                    minutos_expiracion=15, max_intentos=5, id_empresa=None):
        try:
            q = session.query(cls).filter_by(
                tipo=tipo,
                identidad_tipo=identidad_tipo,
                identidad_id=identidad_id,
                usado=0
            )
            if id_empresa is not None:
                q = q.filter_by(id_empresa=id_empresa)
            for prev in q.all():
                prev.usado = 1
        except Exception:
            session.rollback()

        nuevo = cls(
            tipo=tipo,
            identidad_tipo=identidad_tipo,
            identidad_id=identidad_id,
            id_empresa=id_empresa,
            codigo_hash=cls.hash_valor(codigo) if codigo else None,
            token_hash=cls.hash_valor(token) if token else None,
            intentos=0,
            max_intentos=max_intentos,
            usado=0,
            expira_en=datetime.now() + timedelta(minutes=minutos_expiracion),
            created_at=datetime.now()
        )
        session.add(nuevo)
        session.commit()
        return nuevo

    @classmethod
    def validar_y_consumir(cls, tipo, identidad_tipo, identidad_id=None, codigo=None, token=None, id_empresa=None):
        """
        Valida un código OTP o token contra la BD, controla expiración y límite de intentos.
        Retorna (registro, error_str). Si es válido, marca usado=1.
        """
        ahora = datetime.now()
        if token:
            t_hash = cls.hash_valor(token)
            reg = session.query(cls).filter_by(
                tipo=tipo,
                identidad_tipo=identidad_tipo,
                token_hash=t_hash
            ).order_by(cls.id.desc()).first()
            if not reg:
                return None, "El enlace o token de seguridad es inválido"
            if reg.usado:
                return None, "Este enlace de seguridad ya fue utilizado"
            if reg.expira_en < ahora:
                reg.usado = 1
                session.commit()
                return None, "El enlace de seguridad ha expirado"
            reg.usado = 1
            session.commit()
            return reg, None

        if codigo:
            c_hash = cls.hash_valor(codigo)
            q = session.query(cls).filter_by(
                tipo=tipo,
                identidad_tipo=identidad_tipo,
                usado=0
            )
            if identidad_id is not None:
                q = q.filter_by(identidad_id=identidad_id)
            if id_empresa is not None:
                q = q.filter_by(id_empresa=id_empresa)

            activos = q.order_by(cls.id.desc()).all()
            if not activos:
                return None, "No existe una solicitud activa o el código ya fue utilizado"

            # Buscar coincidencia entre los activos vigentes
            for reg in activos:
                if reg.expira_en < ahora:
                    reg.usado = 1
                    continue
                if reg.intentos >= (reg.max_intentos or 5):
                    reg.usado = 1
                    continue
                if reg.codigo_hash == c_hash or reg.token_hash == c_hash:
                    reg.usado = 1
                    session.commit()
                    return reg, None

            # Si no coincidió, registrar intento fallido en los tokens activos evaluados
            expirados_todos = True
            bloqueados_todos = True
            for reg in activos:
                if reg.expira_en >= ahora:
                    expirados_todos = False
                    reg.intentos = (reg.intentos or 0) + 1
                    if reg.intentos >= (reg.max_intentos or 5):
                        reg.usado = 1
                    else:
                        bloqueados_todos = False
            session.commit()

            if expirados_todos:
                return None, "El código de verificación ha expirado. Solicita uno nuevo"
            if bloqueados_todos:
                return None, "Se superó el número máximo de intentos permitidos. Solicita un nuevo código"
            return None, "El código de verificación ingresado es incorrecto"

        return None, "Datos de verificación incompletos"
