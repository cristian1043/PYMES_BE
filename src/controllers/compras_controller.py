from src.models.categorias import Categorias
from src.models.compras import Compras

 
class ComprasController:
    @staticmethod
    def get():
        return Compras.get()

    @staticmethod
    def get_by_id(id):
        compra = Compras.get_by_id(id)

        if compra:
            return compra.to_dict()

        return None

    @staticmethod
    def create(data):

        compra = Compras()

        compra.numero = data["numero"]
        compra.subtotal = data["subtotal"]
        compra.iva = data["iva"]
        compra.descuento = data["descuento"]
        compra.total = data["total"]
        compra.id_proveedor = data["id_proveedor"]
        compra.id_usuario = data["id_usuario"]

        compra.save()

        return compra

    @staticmethod
    def update(id, data):

        compra = Compras.get_by_id(id)

        if compra is None:
            return None

        compra.numero = data["numero"]
        compra.subtotal = data["subtotal"]
        compra.iva = data["iva"]
        compra.descuento = data["descuento"]
        compra.total = data["total"]
        compra.id_proveedor = data["id_proveedor"]
        compra.id_usuario = data["id_usuario"]

        compra.update()

        return compra.to_dict()

    @staticmethod
    def delete(id):

        compra = Compras.get_by_id(id)

        if compra is None:
            return False

        compra.delete()

        return True