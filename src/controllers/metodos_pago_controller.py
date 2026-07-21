from src.models.metodos_pago import MetodosPago


class MetodosPagoController:

    @staticmethod
    def get():
        return MetodosPago.get()

    @staticmethod
    def get_by_id(id):
        return MetodosPago.get_by_id(id)

    @staticmethod
    def save(data):

        metodo = MetodosPago()

        metodo.nombre = data["nombre"]
        metodo.descripcion = data.get("descripcion")

        metodo.save()

        return metodo

    @staticmethod
    def update(id, data):

        metodo = MetodosPago.get_by_id(id)

        if metodo is None:
            return None

        metodo.nombre = data["nombre"]
        metodo.descripcion = data.get("descripcion")

        metodo.update()

        return metodo

    @staticmethod
    def delete(id):

        metodo = MetodosPago.get_by_id(id)

        if metodo is None:
            return False

        metodo.delete()

        return True