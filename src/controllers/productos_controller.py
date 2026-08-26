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
    def obtener_siguiente_codigo():
        productos = Productos.get()
        max_num = 0
        for p in productos:
            if p.codigo and p.codigo.startswith("PROD-"):
                num_part = p.codigo.replace("PROD-", "")
                if num_part.isdigit():
                    max_num = max(max_num, int(num_part))
        return f"PROD-{max_num + 1:03d}"

    @staticmethod
    def create(data):
        producto = Productos()
        producto.nombre = data.get("nombre", "")
        producto.descripcion = data.get("descripcion", "")
        producto.precio = float(data.get("precio", 0))
        costo_val = float(data.get("costo", 0))
        producto.costo = costo_val if costo_val > 0 else round(producto.precio * 0.70, 2)
        producto.stock = int(data.get("stock", 0))
        
        # Asignar categoría válida o categoría 1 por defecto
        cat_id = data.get("id_categoria")
        producto.id_categoria = int(cat_id) if cat_id else 1
        
        # Asignar proveedor si fue proporcionado
        prov_id = data.get("id_proveedor")
        producto.id_proveedor = int(prov_id) if prov_id else None

        # Generar código único secuencial (PROD-001, PROD-002, etc)
        cod = data.get("codigo")
        producto.codigo = str(cod) if cod else ProductosController.obtener_siguiente_codigo()
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
        if "costo" in data and data["costo"] is not None:
            producto.costo = float(data["costo"])
        producto.stock = int(data.get("stock", producto.stock))
        if "id_categoria" in data:
            producto.id_categoria = int(data["id_categoria"]) if data["id_categoria"] else producto.id_categoria
        if "id_proveedor" in data:
            producto.id_proveedor = int(data["id_proveedor"]) if data["id_proveedor"] else None
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