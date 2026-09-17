from src.models.productos import Productos
from src.utils.pagination import paginate_query

import uuid

class ProductosController:

    @staticmethod
    def get(empresa_id=None):
        query = Productos.get_query()
        if empresa_id:
            query = query.filter(Productos.id_empresa == int(empresa_id))
        else:
            return []
        return query.all()

    @staticmethod
    def get_paginated(page=1, per_page=10, empresa_id=None):
        query = Productos.get_query()
        if empresa_id:
            query = query.filter(Productos.id_empresa == int(empresa_id))
        else:
            # Aislamiento estricto: sin empresa_id especificada, no mezclar productos entre empresas
            return paginate_query(query.filter(Productos.id_empresa == -1), page, per_page)
        return paginate_query(query, page, per_page)

    @staticmethod
    def get_by_id(id):
        return Productos.get_by_id(id)

    @staticmethod
    def obtener_siguiente_codigo(empresa_id=None):
        prefix = f"PROD-E{empresa_id}-" if empresa_id else "PROD-"
        query = Productos.get_query()
        if empresa_id:
            query = query.filter(Productos.id_empresa == int(empresa_id))
        productos = query.all()
        max_num = 0
        for p in productos:
            if p.codigo and prefix in p.codigo:
                num_part = p.codigo.replace(prefix, "").strip()
                if num_part.isdigit():
                    max_num = max(max_num, int(num_part))
            elif p.codigo and p.codigo.startswith("PROD-"):
                num_part = p.codigo.replace("PROD-", "").strip()
                if num_part.isdigit():
                    max_num = max(max_num, int(num_part))
        
        siguiente = max_num + 1
        cand = f"{prefix}{siguiente:03d}"
        while Productos.get_query().filter_by(codigo=cand).first() is not None:
            siguiente += 1
            cand = f"{prefix}{siguiente:03d}"
        return cand

    @staticmethod
    def create(data):
        emp_id = data.get("id_empresa") or data.get("empresa_id")
        if not emp_id:
            raise ValueError("El identificador de empresa ('id_empresa') es obligatorio para registrar un producto.")
        empresa_id_val = int(emp_id)

        producto = Productos()
        producto.id_empresa = empresa_id_val
        producto.nombre = str(data.get("nombre", "")).strip()
        producto.descripcion = str(data.get("descripcion", "")).strip()
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

        # Asignar o generar código correlativo propio garantizado sin colisiones
        codigo_enviado = (data.get("codigo") or "").strip()
        if codigo_enviado:
            existente = Productos.get_query().filter_by(codigo=codigo_enviado).first()
            if existente:
                producto.codigo = ProductosController.obtener_siguiente_codigo(empresa_id_val)
            else:
                producto.codigo = codigo_enviado
        else:
            producto.codigo = ProductosController.obtener_siguiente_codigo(empresa_id_val)

        producto.unidad_medida = data.get("unidad_medida", "UND")
        producto.estado = data.get("estado", "Activo")
        producto.imagen = data.get("imagen", None)
        
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
        if "unidad_medida" in data:
            producto.unidad_medida = data["unidad_medida"]
        if "estado" in data:
            producto.estado = data["estado"]
        if "imagen" in data:
            producto.imagen = data["imagen"]
        producto.update()
        return producto

    @staticmethod
    def desactivar(id, estado="Inactivo"):
        producto = Productos.get_by_id(id)
        if producto is None:
            return None
        producto.estado = estado
        producto.update()
        return producto

    @staticmethod
    def delete(id):
        producto = Productos.get_by_id(id)
        if producto is None:
            return False
        # Desactivación lógica (Soft-Delete) para proteger integridad referencial de compras y facturas
        producto.estado = "Inactivo"
        producto.update()
        return True