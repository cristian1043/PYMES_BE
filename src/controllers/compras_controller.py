from src.models.compras import Compras
from src.utils.pagination import paginate_query

class ComprasController:
    
    @staticmethod
    def get():
        return Compras.get()

    @staticmethod
    def get_paginated(page=1, per_page=10):
        return paginate_query(Compras.get_query(), page, per_page)

    @staticmethod
    def get_by_id(id):
        compra = Compras.get_by_id(id)
        if compra is None:
            return None
        return compra

    @staticmethod
    def create(data):
        subtotal = float(data.get("subtotal", 0))
        iva = float(data.get("iva", 0))
        descuento = float(data.get("descuento", 0))
        # Cálculo automático del total en la lógica de negocios del Backend
        total = subtotal + iva - descuento

        compra = Compras()
        compra.numero = data["numero"]
        compra.subtotal = subtotal
        compra.iva = iva
        compra.descuento = descuento
        compra.total = data.get("total", total)
        compra.id_proveedor = int(data["id_proveedor"])
        compra.id_usuario = int(data.get("id_usuario", 1))
        
        compra.save()
        return compra

    @staticmethod
    def update(id, data):
        compra = Compras.get_by_id(id)
        if compra is None:
            return None
            
        subtotal = float(data.get("subtotal", compra.subtotal))
        iva = float(data.get("iva", compra.iva))
        descuento = float(data.get("descuento", compra.descuento))
        total = subtotal + iva - descuento

        compra.numero = data.get("numero", compra.numero)
        compra.subtotal = subtotal
        compra.iva = iva
        compra.descuento = descuento
        compra.total = data.get("total", total)
        compra.id_proveedor = int(data.get("id_proveedor", compra.id_proveedor))
        compra.id_usuario = int(data.get("id_usuario", compra.id_usuario))
        
        compra.update()
        return compra

    @staticmethod
    def delete(id):
        compra = Compras.get_by_id(id)
        if compra is None:
            return False
        compra.delete()
        return True