from src.models.empresas import Empresas

class EmpresasController:

    @staticmethod
    def get():
        empresas = Empresas.get()
        if not empresas:
            emp1 = Empresas()
            emp1.nombre = "Empresa Chaneques S.A.S."
            emp1.nit = "900.123.456-1"
            emp1.direccion = "Calle 10 #20-30"
            emp1.telefono = "+57 300 1234567"
            emp1.email = "contacto@chaneques.com"
            emp1.save()

            emp2 = Empresas()
            emp2.nombre = "Empresa La Vainilla S.A.S."
            emp2.nit = "900.654.321-2"
            emp2.direccion = "Carrera 45 #12-34"
            emp2.telefono = "+57 315 9876543"
            emp2.email = "contacto@lavainilla.com"
            emp2.save()

            empresas = [emp1, emp2]
        return empresas

    @staticmethod
    def get_by_id(id):
        return Empresas.get_by_id(id)

    @staticmethod
    def create(data):
        empresa = Empresas()
        empresa.nombre = data["nombre"]
        empresa.nit = data["nit"]
        empresa.direccion = data.get("direccion", "")
        empresa.telefono = data.get("telefono", "")
        empresa.email = data.get("email", "")
        empresa.save()
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

        empresa.update()
        return empresa
