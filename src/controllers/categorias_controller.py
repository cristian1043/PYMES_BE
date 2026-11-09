from src.models.categorias import Categorias


class CategoriasController:
    @staticmethod
    def get(empresa_id=None, include_global=True):
        return Categorias.get(id_empresa=empresa_id, include_global=include_global)

    @staticmethod
    def get_by_id(id):
        return Categorias.get_by_id(id)

    @staticmethod
    def create(data):
        nombre = str(data.get("nombre") or "").strip()
        if not nombre:
            raise ValueError("El nombre de la categoría es obligatorio.")
        emp_id = data.get("id_empresa") or data.get("empresa_id")
        categoria = Categorias()
        categoria.nombre = nombre
        categoria.descripcion = str(data.get("descripcion") or "").strip()
        categoria.estado = data.get("estado", "Activo")
        categoria.id_empresa = int(emp_id) if emp_id else None
        categoria.create()
        return categoria

    @staticmethod
    def update(id, data):
        categoria = Categorias.get_by_id(id)
        if categoria is None:
            return None

        if "nombre" in data and str(data["nombre"]).strip():
            categoria.nombre = str(data["nombre"]).strip()
        if "descripcion" in data:
            categoria.descripcion = str(data["descripcion"] or "").strip()
        if "estado" in data:
            categoria.estado = data["estado"]
        categoria.update()
        return categoria

    @staticmethod
    def delete(id):
        categoria = Categorias.get_by_id(id)
        if categoria is None:
            return False
        categoria.delete()
        return True
