from datetime import datetime, timedelta
from src.models import session
from src.models.empresas import Empresas, PRECIO_MEMBRESIA_COP, DIAS_MEMBRESIA_CICLO, PLAN_MEMBRESIA_DEFAULT
from src.models.usuario_empresas import UsuarioEmpresas
from src.models.portal_config import ConfiguracionPortal


class EmpresasController:

    @staticmethod
    def get(user_id=None, es_super_admin=False):
        """
        Retorna las empresas autorizadas para el usuario consultante.
        - Nunca crea empresas ficticias automáticamente durante consultas normales.
        - Un usuario normal o administrador de empresa solo ve las empresas a las que está vinculado activamente.
        - Solo un Super Administrador global (`es_super_admin=True`) puede listar todas las empresas.
        """
        if es_super_admin:
            return Empresas.get()

        if not user_id or not str(user_id).isdigit():
            return []

        vinculaciones = UsuarioEmpresas.get_by_usuario(int(user_id))
        ids_autorizados = [int(v.empresa_id) for v in vinculaciones if v.estado == "Activo" and v.empresa_id is not None]
        if not ids_autorizados:
            return []

        return session.query(Empresas).filter(Empresas.id.in_(ids_autorizados)).all()

    @staticmethod
    def get_by_id(id):
        return Empresas.get_by_id(id)

    @staticmethod
    def create(data):
        nombre = str(data.get("nombre") or "").strip()
        if not nombre:
            raise ValueError("El nombre comercial de la empresa es obligatorio.")

        nit = str(data.get("nit") or "").strip()
        if not nit:
            raise ValueError("El NIT o identificación tributaria es obligatorio.")

        if session.query(Empresas).filter_by(nit=nit).first():
            raise ValueError(f"Ya existe una empresa registrada con el NIT '{nit}'.")

        ahora = datetime.now()
        empresa = Empresas()
        empresa.nombre = nombre
        empresa.razon_social = str(data.get("razon_social") or nombre).strip()
        empresa.nit = nit
        empresa.direccion = str(data.get("direccion") or "").strip()
        empresa.telefono = str(data.get("telefono") or "").strip()
        empresa.email = str(data.get("email") or "").strip()
        empresa.estado = data.get("estado", "Activo")
        empresa.created_at = ahora
        empresa.plan_membresia = data.get("plan_membresia") or PLAN_MEMBRESIA_DEFAULT
        empresa.precio_membresia = PRECIO_MEMBRESIA_COP
        empresa.estado_membresia = data.get("estado_membresia") or "Activa"
        empresa.fecha_inicio_membresia = ahora
        empresa.fecha_vencimiento_membresia = ahora + timedelta(days=DIAS_MEMBRESIA_CICLO)
        empresa.auto_renovacion = 1 if data.get("auto_renovacion", True) else 0
        empresa.save()

        usuario_id = data.get("usuario_id")
        if usuario_id and str(usuario_id).isdigit():
            v = UsuarioEmpresas.get_by_usuario_empresa(int(usuario_id), empresa.id)
            if not v:
                v = UsuarioEmpresas()
                v.usuario_id = int(usuario_id)
                v.empresa_id = empresa.id
                v.rol_id = 1
                v.estado = "Activo"
                v.save()

        # Inicializar configuración del Portal de Clientes para la nueva empresa
        try:
            ConfiguracionPortal.get_or_create_for_empresa(empresa)
        except Exception:
            pass

        return empresa

    @staticmethod
    def update(id, data):
        empresa = Empresas.get_by_id(id)
        if not empresa:
            return None

        if "nombre" in data and str(data["nombre"]).strip():
            empresa.nombre = str(data["nombre"]).strip()
        if "razon_social" in data:
            empresa.razon_social = str(data["razon_social"] or empresa.nombre).strip()
        if "nit" in data and str(data["nit"]).strip():
            nuevo_nit = str(data["nit"]).strip()
            if nuevo_nit != empresa.nit:
                existente = session.query(Empresas).filter(Empresas.nit == nuevo_nit, Empresas.id != empresa.id).first()
                if existente:
                    raise ValueError(f"Ya existe otra empresa registrada con el NIT '{nuevo_nit}'.")
            empresa.nit = nuevo_nit
        if "direccion" in data:
            empresa.direccion = data["direccion"]
        if "telefono" in data:
            empresa.telefono = data["telefono"]
        if "email" in data:
            empresa.email = data["email"]
        if "estado" in data:
            empresa.estado = data["estado"]
        if "plan_membresia" in data:
            empresa.plan_membresia = data["plan_membresia"]
        if "estado_membresia" in data:
            empresa.estado_membresia = data["estado_membresia"]
        if "auto_renovacion" in data:
            empresa.auto_renovacion = 1 if data["auto_renovacion"] else 0

        empresa.update()
        return empresa
