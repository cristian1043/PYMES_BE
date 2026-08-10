from datetime import datetime
from src.models.facturas import Facturas
from src.utils.pagination import paginate_query

class FacturasController:

    @staticmethod
    def get():
        return Facturas.get()

    @staticmethod
    def get_paginated(page=1, per_page=10):
        return paginate_query(Facturas.get_query(), page, per_page)

    @staticmethod
    def get_by_id(id):
        return Facturas.get_by_id(id)

    @staticmethod
    def create(data):
        subtotal = float(data.get("subtotal", 0))
        iva = float(data.get("iva", 0))
        descuento = float(data.get("descuento", 0))
        # Cálculo automático del total en la lógica de negocios del Backend
        total = subtotal + iva - descuento

        fecha_factura = data.get("fecha")
        if not fecha_factura:
            fecha_factura = datetime.now()

        factura = Facturas()
        factura.numero = data["numero"]
        factura.fecha = fecha_factura
        factura.subtotal = subtotal
        factura.iva = iva
        factura.descuento = descuento
        factura.total = data.get("total", total)
        factura.id_cliente = int(data["id_cliente"])
        factura.id_usuario = int(data.get("id_usuario", 1))
        factura.id_metodo_pago = int(data.get("id_metodo_pago", 1))
        
        factura.save()
        return factura

    @staticmethod
    def update(id, data):
        factura = Facturas.get_by_id(id)
        if factura is None:
            return None

        subtotal = float(data.get("subtotal", factura.subtotal))
        iva = float(data.get("iva", factura.iva))
        descuento = float(data.get("descuento", factura.descuento))
        total = subtotal + iva - descuento

        factura.numero = data.get("numero", factura.numero)
        if "fecha" in data:
            factura.fecha = data["fecha"]
        factura.subtotal = subtotal
        factura.iva = iva
        factura.descuento = descuento
        factura.total = data.get("total", total)
        factura.id_cliente = int(data.get("id_cliente", factura.id_cliente))
        factura.id_usuario = int(data.get("id_usuario", factura.id_usuario))
        factura.id_metodo_pago = int(data.get("id_metodo_pago", factura.id_metodo_pago))
        
        factura.update()
        return factura

    @staticmethod
    def delete(id):
        factura = Facturas.get_by_id(id)
        if factura is None:
            return False
        factura.delete()
        return True