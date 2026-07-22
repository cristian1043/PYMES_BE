from src.models.detalle_facturas import DetalleFacturas
 

class DetalleFacturasController:

    @staticmethod
    def get():
        return DetalleFacturas.get()


    @staticmethod
    def get_by_id(id):
        return DetalleFacturas.get_by_id(id)
    
        if detalle is None:
            return "Detalle de factura no encontrado"
        
        return detalle
     
    @staticmethod
    def create(data):
        detalle = DetalleFacturas()
        
        detalle.cantidad = data["cantidad"]
        detalle.precio_unitario = data["precio_unitario"]
        detalle.subtotal = data["subtotal"]
        detalle.id_factura = data["id_factura"]
        detalle.id_producto = data["id_producto"]
        
        detalle.create()
        
        return detalle

    @staticmethod
    def update(id, data):

        detalle = DetalleFacturas.get_by_id(id)

        if detalle is None:
            return "Detalle de factura no encontrado"

        detalle.cantidad = data["cantidad"]
        detalle.precio_unitario = data["precio_unitario"]
        detalle.subtotal = data["subtotal"]
        detalle.id_factura = data["id_factura"]
        detalle.id_producto = data["id_producto"]
        
        detalle.update()
        
        return detalle

    @staticmethod
    def delete(id):

        detalle = DetalleFacturas.get_by_id(id)

        if detalle is None:
            return "Detalle de factura no encontrado"

        detalle.delete()

        return True and "Detalle de factura eliminado correctamente"

      