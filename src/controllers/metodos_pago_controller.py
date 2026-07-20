from src.models.metodos_pago import MetodosPago


class MetodosPagoController:

    @staticmethod
    def get():
        return MetodosPago.get()
 
    @staticmethod
    def get_by_id(id):
        return MetodosPago.get_by_id(id)

        if metodo_pago is None:
            return "Método de pago no encontrado"
        
        return metodo_pago
    
    @staticmethod
    def create(id, data):

        metodo_pago = MetodosPago()
        
        metodo_pago.nombre = data["nombre"]
        metodo_pago.descripcion = data.get("descripcion", None)
        
        metodo_pago.save()
        
        return metodo_pago

    @staticmethod
    def update(id, data):

        metodo_pago = MetodosPago.get_by_id(id)

        if metodo_pago is None:
            return "Método de pago no encontrado"

        metodo_pago.nombre = data["nombre"]
        metodo_pago.descripcion = data.get("descripcion", None)

        metodo_pago.update()

        return metodo_pago


    @staticmethod
    def delete(id):

        metodo_pago = MetodosPago.get_by_id(id)

        if metodo_pago is None:
            return "Método de pago no encontrado"
        
        metodo_pago.delete()
        return "Método de pago eliminado"