from src.models.productos import Productos
from src.utils.pagination import paginate_query

import uuid

class ProductosController:

    @staticmethod
    def get():
        return Productos.get()

    @staticmethod
    def get_paginated(page=1, per_page=10):
        return paginate_query(Productos.get_query(), page, per_page)

    @staticmethod
    def get_by_id(id):
        producto = Productos.get_by_id(id)

        if producto is None:
            return "Producto no encontrado"
        
        return producto


    @staticmethod
    def create(data):
        producto = Productos()
        producto.nombre = data.get("nombre", "")
        producto.descripcion = data.get("descripcion", "")
        producto.precio = float(data.get("precio", 0))
        producto.stock = int(data.get("stock", 0))
        
        # Asignar categoría válida o categoría 1 por defecto
        cat_id = data.get("id_categoria")
        producto.id_categoria = int(cat_id) if cat_id else 1
        
        # Generar código único si no se proporcionó uno
        cod = data.get("codigo")
        producto.codigo = str(cod) if cod else f"PROD-{uuid.uuid4().hex[:6].upper()}"
        producto.unidad_medida = data.get("unidad_medida", "UND")
        
        producto.create()
        return producto

    @staticmethod
    def update(id, data):
        producto = Productos.get_by_id(id)
        if producto is None:
            return None
        producto.nombre = data.get("nombre", producto.nombre)
        producto.descripcion = data.get("descripcion", producto.descripcion)
        producto.precio = float(data.get("precio", producto.precio))
        producto.stock = int(data.get("stock", producto.stock))
        producto.id_categoria = data.get("id_categoria", producto.id_categoria)
        if "codigo" in data:
            producto.codigo = data["codigo"]
        if "unidad_medida" in data:
            producto.unidad_medida = data["unidad_medida"]
        producto.update()
        return producto


    @staticmethod
    def delete(id):

        producto = Productos.get_by_id(id)
        if producto is None:
            return "Producto no encontrado"
        producto.delete()

        return True and "Producto eliminado correctamente"