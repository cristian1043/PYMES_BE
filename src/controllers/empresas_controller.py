from datetime import datetime, timedelta
from src.models import session
from src.models.empresas import Empresas, PRECIO_MEMBRESIA_COP, DIAS_MEMBRESIA_CICLO, PLAN_MEMBRESIA_DEFAULT

class EmpresasController:

    @staticmethod
    def get():
        empresas = Empresas.get()
        if not empresas:
            ahora = datetime.now()
            venc = ahora + timedelta(days=DIAS_MEMBRESIA_CICLO)

            emp1 = Empresas()
            emp1.nombre = "Empresa Chaneques S.A.S."
            emp1.nit = "900.123.456-1"
            emp1.direccion = "Calle 10 #20-30"
            emp1.telefono = "+57 300 1234567"
            emp1.email = "contacto@chaneques.com"
            emp1.estado = "Activo"
            emp1.plan_membresia = PLAN_MEMBRESIA_DEFAULT
            emp1.precio_membresia = PRECIO_MEMBRESIA_COP
            emp1.estado_membresia = "Activa"
            emp1.fecha_inicio_membresia = ahora
            emp1.fecha_vencimiento_membresia = venc
            emp1.auto_renovacion = 1
            emp1.save()

            emp2 = Empresas()
            emp2.nombre = "Empresa La Vainilla S.A.S."
            emp2.nit = "900.654.321-2"
            emp2.direccion = "Carrera 45 #12-34"
            emp2.telefono = "+57 315 9876543"
            emp2.email = "contacto@lavainilla.com"
            emp2.estado = "Activo"
            emp2.plan_membresia = PLAN_MEMBRESIA_DEFAULT
            emp2.precio_membresia = PRECIO_MEMBRESIA_COP
            emp2.estado_membresia = "Activa"
            emp2.fecha_inicio_membresia = ahora
            emp2.fecha_vencimiento_membresia = venc
            emp2.auto_renovacion = 1
            emp2.save()

            empresas = [emp1, emp2]
        return empresas

    @staticmethod
    def get_by_id(id):
        return Empresas.get_by_id(id)

    @staticmethod
    def create(data):
        nit = data.get("nit")
        if nit and session.query(Empresas).filter_by(nit=nit).first():
            raise Exception(f"Ya existe una empresa registrada con el NIT '{nit}'.")

        ahora = datetime.now()
        empresa = Empresas()
        empresa.nombre = data["nombre"]
        empresa.nit = nit
        empresa.direccion = data.get("direccion", "")
        empresa.telefono = data.get("telefono", "")
        empresa.email = data.get("email", "")
        empresa.estado = data.get("estado", "Activo")
        empresa.plan_membresia = data.get("plan_membresia") or PLAN_MEMBRESIA_DEFAULT
        empresa.precio_membresia = PRECIO_MEMBRESIA_COP
        empresa.estado_membresia = data.get("estado_membresia") or "Activa"
        empresa.fecha_inicio_membresia = ahora
        empresa.fecha_vencimiento_membresia = ahora + timedelta(days=DIAS_MEMBRESIA_CICLO)
        empresa.auto_renovacion = 1 if data.get("auto_renovacion", True) else 0
        empresa.save()

        usuario_id = data.get("usuario_id")
        if usuario_id:
            from src.models.usuario_empresas import UsuarioEmpresas
            v = UsuarioEmpresas.get_by_usuario_empresa(int(usuario_id), empresa.id)
            if not v:
                v = UsuarioEmpresas()
                v.usuario_id = int(usuario_id)
                v.empresa_id = empresa.id
                v.rol_id = 1
                v.estado = "Activo"
                v.save()

        return empresa

    @staticmethod
    def update(id, data):
        empresa = Empresas.get_by_id(id)
        if not empresa:
            return None

        if "nombre" in data:
            empresa.nombre = data["nombre"]
        if "nit" in data:
            empresa.nit = data["nit"]
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
