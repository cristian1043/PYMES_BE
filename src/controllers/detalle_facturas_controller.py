from src.models.detalle_facturas import DetalleFacturas


class DetalleFacturasController:

    @staticmethod
    def get():
        return DetalleFacturas.get()

    @staticmethod
    def get_by_id(id):
        return DetalleFacturas.get_by_id(id)

    @staticmethod
    def create(data):
        detalle = DetalleFacturas()
        detalle.cantidad = int(data["cantidad"])
        detalle.precio_unitario = float(data["precio_unitario"])
        detalle.subtotal = float(data.get("subtotal", detalle.cantidad * detalle.precio_unitario))
        detalle.id_factura = int(data["id_factura"])
        detalle.id_producto = int(data["id_producto"])
        detalle.create()
        return detalle

    @staticmethod
    def update(id, data):
        detalle = DetalleFacturas.get_by_id(id)
        if detalle is None:
            return None
        if "cantidad" in data:
            detalle.cantidad = int(data["cantidad"])
        if "precio_unitario" in data:
            detalle.precio_unitario = float(data["precio_unitario"])
        detalle.subtotal = float(data.get("subtotal", detalle.cantidad * detalle.precio_unitario))
        if "id_factura" in data:
            detalle.id_factura = int(data["id_factura"])
        if "id_producto" in data:
            detalle.id_producto = int(data["id_producto"])
        detalle.update()
        return detalle

    @staticmethod
    def delete(id):
        detalle = DetalleFacturas.get_by_id(id)
        if detalle is None:
            return False
        detalle.delete()
        return True
