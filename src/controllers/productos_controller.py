from src.models.productos import Productos
from src.models.proveedores import Proveedores
from src.models.categorias import Categorias
from src.utils.pagination import paginate_query


class ProductosController:

    @staticmethod
    def get(empresa_id=None):
        if not empresa_id:
            return []
        return Productos.get_query().filter(Productos.id_empresa == int(empresa_id)).all()

    @staticmethod
    def get_paginated(page=1, per_page=10, empresa_id=None):
        query = Productos.get_query()
        if empresa_id:
            query = query.filter(Productos.id_empresa == int(empresa_id))
        else:
            return paginate_query(query.filter(Productos.id_empresa == -1), page, per_page)
        return paginate_query(query, page, per_page)

    @staticmethod
    def get_by_id(id):
        return Productos.get_by_id(id)

    @staticmethod
    def obtener_siguiente_codigo(empresa_id=None):
        eid = int(empresa_id) if empresa_id else 1
        prefix = f"PROD-E{eid}-"
        productos = Productos.get_query().filter(Productos.id_empresa == eid).all()
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
        while Productos.get_query().filter_by(id_empresa=eid, codigo=cand).first() is not None:
            siguiente += 1
            cand = f"{prefix}{siguiente:03d}"
        return cand

    @staticmethod
    def create(data):
        emp_id = data.get("id_empresa") or data.get("empresa_id")
        if not emp_id:
            raise ValueError("El identificador de empresa ('id_empresa') es obligatorio para registrar un producto.")
        empresa_id_val = int(emp_id)

        nombre = str(data.get("nombre", "")).strip()
        if not nombre:
            raise ValueError("El nombre del producto es obligatorio.")

        precio = float(data.get("precio", 0))
        if precio < 0:
            raise ValueError("El precio del producto no puede ser negativo.")

        stock = int(data.get("stock", 0))
        if stock < 0:
            raise ValueError("El stock inicial no puede ser negativo.")

        producto = Productos()
        producto.id_empresa = empresa_id_val
        producto.nombre = nombre
        producto.descripcion = str(data.get("descripcion", "")).strip()
        producto.precio = precio
        costo_val = float(data.get("costo", 0) or 0)
        producto.costo = costo_val if costo_val > 0 else round(producto.precio * 0.70, 2)
        producto.stock = stock

        cat_id = data.get("id_categoria")
        if cat_id:
            cat_obj = Categorias.get_by_id(int(cat_id))
            if cat_obj and cat_obj.id_empresa and int(cat_obj.id_empresa) != empresa_id_val:
                raise ValueError("La categoría seleccionada pertenece a otra empresa.")
            producto.id_categoria = int(cat_id)
        else:
            producto.id_categoria = 1

        prov_id = data.get("id_proveedor")
        if prov_id and str(prov_id).strip():
            prov_obj = Proveedores.get_by_id(int(prov_id))
            if not prov_obj or (prov_obj.id_empresa and int(prov_obj.id_empresa) != empresa_id_val):
                raise ValueError("El proveedor seleccionado no existe o pertenece a otra empresa.")
            producto.id_proveedor = int(prov_id)
        else:
            producto.id_proveedor = None

        codigo_enviado = (data.get("codigo") or "").strip()
        if codigo_enviado:
            existente = Productos.get_query().filter_by(id_empresa=empresa_id_val, codigo=codigo_enviado).first()
            if existente:
                producto.codigo = ProductosController.obtener_siguiente_codigo(empresa_id_val)
            else:
                producto.codigo = codigo_enviado
        else:
            producto.codigo = ProductosController.obtener_siguiente_codigo(empresa_id_val)

        producto.unidad_medida = data.get("unidad_medida", "UND")
        producto.estado = data.get("estado", "Activo")
        producto.imagen = data.get("imagen", None)

        # Campos del Portal de Clientes
        if "publicado_portal" in data:
            producto.publicado_portal = 1 if data["publicado_portal"] in (True, 1, "1", "true", "on", "si") else 0
        else:
            producto.publicado_portal = 1

        if "disponible_portal" in data:
            producto.disponible_portal = 1 if data["disponible_portal"] in (True, 1, "1", "true", "on", "si") else 0
        else:
            producto.disponible_portal = 1

        if "destacado" in data:
            producto.destacado = 1 if data["destacado"] in (True, 1, "1", "true", "on", "si") else 0
        else:
            producto.destacado = 0

        producto.descripcion_publica = str(data.get("descripcion_publica") or producto.descripcion).strip()
        producto.imagen_publica = data.get("imagen_publica") or producto.imagen
        if data.get("precio_publico") not in (None, ""):
            producto.precio_publico = float(data["precio_publico"])
        else:
            producto.precio_publico = producto.precio

        producto.create()
        return producto

    @staticmethod
    def update(id, data):
        producto = Productos.get_by_id(id)
        if producto is None:
            return None

        if "nombre" in data and str(data["nombre"]).strip():
            producto.nombre = str(data["nombre"]).strip()
        if "descripcion" in data:
            producto.descripcion = str(data["descripcion"]).strip()
        if "precio" in data and data["precio"] is not None:
            prec = float(data["precio"])
            if prec < 0:
                raise ValueError("El precio no puede ser negativo.")
            producto.precio = prec
        if "costo" in data and data["costo"] is not None:
            producto.costo = float(data["costo"])
        if "stock" in data and data["stock"] is not None:
            stk = int(data["stock"])
            if stk < 0:
                raise ValueError("El stock no puede ser negativo.")
            producto.stock = stk
        if "id_categoria" in data and data["id_categoria"]:
            cat_obj = Categorias.get_by_id(int(data["id_categoria"]))
            if cat_obj and cat_obj.id_empresa and producto.id_empresa and int(cat_obj.id_empresa) != int(producto.id_empresa):
                raise ValueError("La categoría seleccionada pertenece a otra empresa.")
            producto.id_categoria = int(data["id_categoria"])
        if "id_proveedor" in data:
            if data["id_proveedor"]:
                prov_obj = Proveedores.get_by_id(int(data["id_proveedor"]))
                if not prov_obj or (prov_obj.id_empresa and producto.id_empresa and int(prov_obj.id_empresa) != int(producto.id_empresa)):
                    raise ValueError("El proveedor seleccionado pertenece a otra empresa.")
                producto.id_proveedor = int(data["id_proveedor"])
            else:
                producto.id_proveedor = None
        if "unidad_medida" in data:
            producto.unidad_medida = data["unidad_medida"]
        if "estado" in data:
            producto.estado = data["estado"]
        if "imagen" in data:
            producto.imagen = data["imagen"]

        # Campos del Portal de Clientes
        if "publicado_portal" in data:
            producto.publicado_portal = 1 if data["publicado_portal"] in (True, 1, "1", "true", "on", "si") else 0
        if "disponible_portal" in data:
            producto.disponible_portal = 1 if data["disponible_portal"] in (True, 1, "1", "true", "on", "si") else 0
        if "destacado" in data:
            producto.destacado = 1 if data["destacado"] in (True, 1, "1", "true", "on", "si") else 0
        if "descripcion_publica" in data:
            producto.descripcion_publica = str(data["descripcion_publica"] or "").strip()
        if "imagen_publica" in data:
            producto.imagen_publica = data["imagen_publica"]
        if "precio_publico" in data:
            producto.precio_publico = float(data["precio_publico"]) if data["precio_publico"] not in (None, "") else producto.precio

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
        producto.estado = "Inactivo"
        producto.update()
        return True
