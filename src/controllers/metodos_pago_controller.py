from src.models.metodos_pago import metodos_Pago


class MetodosPagoController:

    @staticmethod
    def get():
        return metodos_Pago.get()
 
    @staticmethod
    def get_by_id(id):
        return metodos_Pago.get_by_id(id)

        if metodo_pago is None:
            return "Método de pago no encontrado"
        
        return metodo_pago
    
    @staticmethod
    def create(id, data):

        metodos_pago = metodos_Pago()
        
        metodos_pago.nombre = data["nombre"]
        metodos_pago.descripcion = data.get("descripcion", None)
        
        metodos_pago.save()
        
        return metodos_pago

    @staticmethod
    def update(id, data):

        metodos_pago = metodos_Pago.get_by_id(id)

        if metodos_pago is None:
            return "Método de pago no encontrado"

        metodos_pago.nombre = data["nombre"]
        metodos_pago.descripcion = data.get("descripcion", None)

        metodos_pago.update()

        return metodos_pago


    @staticmethod
    def delete(id):

        metodos_pago = metodos_Pago.get_by_id(id)

        if metodos_pago is None:
            return "Método de pago no encontrado"
        
        metodos_pago.delete()
        return "Método de pago eliminado"