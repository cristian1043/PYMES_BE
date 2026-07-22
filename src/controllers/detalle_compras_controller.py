from src.models.detalle_compras import DetalleCompras


class DetalleComprasController:

    @staticmethod
    def get():
        return DetalleCompras.get()

    @staticmethod
    def get_by_id(id):
        detalle = DetalleCompras.get_by_id(id)

        if detalle is None:
            return None

        return detalle

    @staticmethod
    def create(data):

        detalle = DetalleCompras()

        detalle.cantidad = data["cantidad"]
        detalle.costo_unitario = data["costo_unitario"]
        detalle.subtotal = data["subtotal"]
        detalle.id_compra = data["id_compra"]
        detalle.id_producto = data["id_producto"]

        detalle.save()

        return detalle

    @staticmethod
    def update(id, data):

        detalle = DetalleCompras.get_by_id(id)

        if detalle is None:
            return None

        detalle.cantidad = data["cantidad"]
        detalle.costo_unitario = data["costo_unitario"]
        detalle.subtotal = data["subtotal"]
        detalle.id_compra = data["id_compra"]
        detalle.id_producto = data["id_producto"]

        detalle.update()

        return detalle

    @staticmethod
    def delete(id):

        detalle = DetalleCompras.get_by_id(id)

        if detalle is None:
            return False

        detalle.delete()

        return True