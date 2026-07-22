from src.models.categorias import Categorias


class CategoriasController:
    @staticmethod
    def get():
        return Categorias.get()

    @staticmethod
    def get_by_id(id):
        return Categorias.get_by_id(id)

    @staticmethod
    def create(data):
        categoria = Categorias()
        categoria.nombre = data["nombre"]
        categoria.create()
        return categoria

    @staticmethod
    def update(id, data):
        categoria = Categorias.get_by_id(id)

        if categoria is None:
            return None

        categoria.nombre = data["nombre"]
        categoria.update()

        return categoria

    @staticmethod
    def delete(id):
        categoria = Categorias.get_by_id(id)

        if categoria is None:
            return False

        categoria.delete()
        return True