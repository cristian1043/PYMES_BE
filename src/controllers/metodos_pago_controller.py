from src.models.metodos_pago import metodosPago


class MetodosPagoController:

    @staticmethod
    def get():
        return metodosPago.get()
 
    @staticmethod
    def get_by_id(id):
        return metodosPago.get_by_id(id)

        if metodosPago is None:
            return "Método de pago no encontrado"
        
        return metodosPago
    
    @staticmethod
    def save(id, data):

        metodosPago = metodosPago()
        
        metodosPago.nombre = data["nombre"]
        metodosPago.descripcion = data.get("descripcion", None)
        
        metodosPago.save()
        
        return metodosPago

    @staticmethod
    def update(id, data):

        metodosPago = metodosPago.get_by_id(id)

        if metodosPago is None:
            return "Método de pago no encontrado"

        metodosPago.nombre = data["nombre"]
        metodosPago.descripcion = data.get("descripcion", None)

        metodosPago.update()

        return metodosPago


    @staticmethod
    def delete(id):

        metodosPago = metodosPago.get_by_id(id)

        if metodosPago is None:
            return "Método de pago no encontrado"
        
        metodosPago.delete()
        return "Método de pago eliminado"