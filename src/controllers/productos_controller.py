from src.models.productos import Productos
from src.utils.pagination import paginate_query

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
        producto.nombre = data["nombre"]
        producto.descripcion = data["descripcion"]
        producto.precio = data["precio"]
        producto.stock = data["stock"]
        producto.id_categoria = data["id_categoria"]
        producto.codigo = data["codigo"]
        producto.unidad_medida = data["unidad_medida"]
        producto.create()
        return producto

    @staticmethod
    def update(id, data):
        producto = Productos.get_by_id(id)
        if producto is None:
            return "Producto no encontrado"
        producto.nombre = data["nombre"]
        producto.descripcion = data["descripcion"]
        producto.precio = data["precio"]
        producto.stock = data["stock"]
        producto.id_categoria = data["id_categoria"]
        producto.codigo = data["codigo"]
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