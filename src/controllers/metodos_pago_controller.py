from src.models.metodos_pago import MetodosPago
from src.models import session

class MetodosPagoController:

    @staticmethod
    def get(empresa_id=None):
        query = MetodosPago.get_query().filter(MetodosPago.estado == 'Activo')
        if empresa_id:
            # Retorna métodos base globales (id_empresa is None) MÁS los exclusivos de la empresa solicitada
            query = query.filter((MetodosPago.id_empresa == None) | (MetodosPago.id_empresa == int(empresa_id)))
        else:
            # Si no se especifica empresa, solo los métodos globales estándar
            query = query.filter(MetodosPago.id_empresa == None)
        return query.all()

    @staticmethod
    def get_by_id(id):
        return MetodosPago.get_by_id(id)

    @staticmethod
    def create(data):
        nombre = str(data.get("nombre", "")).strip()
        if not nombre:
            raise ValueError("El nombre del método de pago es obligatorio.")

        metodo = MetodosPago()
        metodo.nombre = nombre
        metodo.descripcion = data.get("descripcion")
        metodo.tipo = data.get("tipo", "Efectivo")
        metodo.banco = data.get("banco")
        metodo.numero_cuenta = data.get("numero_cuenta")
        metodo.titular = data.get("titular")
        
        emp_id = data.get("id_empresa") or data.get("empresa_id")
        metodo.id_empresa = int(emp_id) if emp_id else None
        metodo.estado = data.get("estado", "Activo")
        
        # Parámetros de pasarela de pago (Wompi, MercadoPago, Stripe, Bold, etc.)
        metodo.pasarela = data.get("pasarela", "ninguna")
        metodo.api_key_publica = data.get("api_key_publica")
        metodo.api_key_privada = data.get("api_key_privada")
        metodo.webhook_secret = data.get("webhook_secret")
        metodo.modo = data.get("modo", "sandbox")

        metodo.create()
        return metodo

    @staticmethod
    def update(id, data):
        metodo = MetodosPago.get_by_id(id)
        if metodo is None:
            return None

        if "nombre" in data and data["nombre"]:
            metodo.nombre = str(data["nombre"]).strip()
        if "descripcion" in data:
            metodo.descripcion = data["descripcion"]
        if "tipo" in data:
            metodo.tipo = data["tipo"]
        if "banco" in data:
            metodo.banco = data["banco"]
        if "numero_cuenta" in data:
            metodo.numero_cuenta = data["numero_cuenta"]
        if "titular" in data:
            metodo.titular = data["titular"]
        if "estado" in data:
            metodo.estado = data["estado"]
            
        # Actualización de pasarela
        if "pasarela" in data:
            metodo.pasarela = data["pasarela"]
        if "api_key_publica" in data:
            metodo.api_key_publica = data["api_key_publica"]
        if "api_key_privada" in data and data["api_key_privada"]:
            metodo.api_key_privada = data["api_key_privada"]
        if "webhook_secret" in data and data["webhook_secret"]:
            metodo.webhook_secret = data["webhook_secret"]
        if "modo" in data:
            metodo.modo = data["modo"]

        metodo.update()
        return metodo

    @staticmethod
    def delete(id):
        metodo = MetodosPago.get_by_id(id)
        if metodo is None:
            return False

        # Si es un método base global del sistema, no permitir borrarlo físicamente
        if metodo.id_empresa is None:
            return False

        # Desactivación lógica para proteger historial de facturación
        metodo.estado = "Inactivo"
        metodo.update()
        return True