from src.models.empresas import Empresas
from src.utils.migrations import DatabaseMigrations

class EmpresasController:

    @staticmethod
    def get():
        DatabaseMigrations.ejecutar_migraciones()
        empresas = Empresas.get()
        if not empresas:
            emp1 = Empresas()
            emp1.nombre = "Empresa Chaneques S.A.S."
            emp1.nit = "900.123.456-1"
            emp1.direccion = "Calle 10 #20-30"
            emp1.telefono = "+57 300 1234567"
            emp1.email = "contacto@chaneques.com"
            emp1.estado = "Activo"
            emp1.save()

            emp2 = Empresas()
            emp2.nombre = "Empresa La Vainilla S.A.S."
            emp2.nit = "900.654.321-2"
            emp2.direccion = "Carrera 45 #12-34"
            emp2.telefono = "+57 315 9876543"
            emp2.email = "contacto@lavainilla.com"
            emp2.estado = "Activo"
            emp2.save()

            empresas = [emp1, emp2]
        return empresas

    @staticmethod
    def get_by_id(id):
        DatabaseMigrations.ejecutar_migraciones()
        return Empresas.get_by_id(id)

    @staticmethod
    def create(data):
        DatabaseMigrations.ejecutar_migraciones()
        nit = data.get("nit")
        if nit and session.query(Empresas).filter_by(nit=nit).first():
            raise Exception(f"Ya existe una empresa registrada con el NIT '{nit}'.")

        empresa = Empresas()
        empresa.nombre = data["nombre"]
        empresa.nit = nit
        empresa.direccion = data.get("direccion", "")
        empresa.telefono = data.get("telefono", "")
        empresa.email = data.get("email", "")
        empresa.estado = data.get("estado", "Activo")
        empresa.save()
        return empresa

    @staticmethod
    def update(id, data):
        DatabaseMigrations.ejecutar_migraciones()
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

        empresa.update()
        return empresa
