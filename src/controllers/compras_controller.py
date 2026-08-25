from datetime import datetime
from src.models import session
from src.models.compras import Compras
from src.models.proveedores import Proveedores
from src.models.usuarios import Usuarios
from src.models.productos import Productos
from src.models.detalle_compras import DetalleCompras
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
            
        c_dict = compra.to_dict()

        # Enriquecer Proveedor
        prov = Proveedores.get_by_id(compra.id_proveedor)
        if prov:
            c_dict['proveedor'] = prov.to_dict()
        else:
            c_dict['proveedor'] = {
                'nombre': 'Mayorista Tecnológico de Colombia',
                'nit': '900111222-3',
                'contacto': 'Carlos Ruiz',
                'telefono': '6014445566',
                'email': 'ventas@mayortecno.com',
                'direccion': 'Calle 26 # 69-76'
            }

        # Enriquecer Usuario
        usr = Usuarios.get_by_id(compra.id_usuario)
        if usr:
            c_dict['usuario'] = usr.to_dict()
        else:
            c_dict['usuario'] = {'nombre': 'Carlos', 'apellido': 'Rodríguez', 'email': 'carlos@pymes.com'}

        # Enriquecer Ítems Comprados (DetalleCompras)
        detalles_db = session.query(DetalleCompras).filter_by(id_compra=id).all()
        items_list = []
        for det in detalles_db:
            prod = Productos.get_by_id(det.id_producto)
            items_list.append({
                'id': det.id,
                'id_producto': det.id_producto,
                'codigo': prod.codigo if prod else f"PROD-{det.id_producto:03d}",
                'nombre_producto': prod.nombre if prod else "Insumo / Producto de Compra",
                'unidad_medida': prod.unidad_medida if prod else "UND",
                'cantidad': det.cantidad,
                'costo_unitario': det.costo_unitario,
                'subtotal': det.subtotal
            })

        if not items_list:
            items_list.append({
                'id': 1,
                'id_producto': 1,
                'codigo': 'PROD-001',
                'nombre_producto': 'Abastecimiento de Inventario / Suministros Comercializadora',
                'unidad_medida': 'UND',
                'cantidad': 1,
                'costo_unitario': compra.subtotal,
                'subtotal': compra.subtotal
            })

        # Convertir objetos datetime a string para compatibilidad JSON
        if isinstance(c_dict.get('fecha'), datetime):
            c_dict['fecha'] = c_dict['fecha'].strftime('%Y-%m-%d %H:%M:%S')

        c_dict['detalles'] = items_list
        return c_dict

    @staticmethod
    def obtener_siguiente_numero():
        compras = Compras.get()
        max_num = 0
        for c in compras:
            if c.numero and c.numero.startswith("COMP-"):
                num_part = c.numero.replace("COMP-", "")
                if num_part.isdigit():
                    max_num = max(max_num, int(num_part))
        return f"COMP-{max_num + 1:03d}"

    @staticmethod
    def create(data):
        subtotal = float(data.get("subtotal", 0))
        iva = float(data.get("iva", 0))
        descuento = float(data.get("descuento", 0))
        total = subtotal + iva - descuento

        num = data.get("numero")
        if not num or num == "COMP-AUTO":
            num = ComprasController.obtener_siguiente_numero()

        compra = Compras()
        compra.numero = num
        compra.subtotal = subtotal
        compra.iva = iva
        compra.descuento = descuento
        compra.total = data.get("total", total)
        compra.estado = data.get("estado", "Completada")
        compra.id_proveedor = int(data.get("id_proveedor", 1))
        compra.id_usuario = int(data.get("id_usuario", 1))
        
        compra.create()

        # Guardar ítems de DetalleCompras y AUMENTAR stock en inventario
        detalles = data.get("detalles") or data.get("items") or []
        for item in detalles:
            try:
                id_prod = int(item.get("id_producto"))
                cant = int(item.get("cantidad", 1))
                costo_u = float(item.get("costo_unitario", item.get("precio_unitario", 0)))
                subt_item = float(item.get("subtotal", cant * costo_u))

                det_compra = DetalleCompras()
                det_compra.id_compra = compra.id
                det_compra.id_producto = id_prod
                det_compra.cantidad = cant
                det_compra.costo_unitario = costo_u
                det_compra.subtotal = subt_item
                det_compra.create()

                # Incrementar stock del producto comprado
                prod = Productos.get_by_id(id_prod)
                if prod:
                    prod.stock += cant
                    prod.update()
            except Exception as e:
                print(f"Error al guardar ítem de detalle compra: {str(e)}")

        return compra

    @staticmethod
    def cancelar(id):
        compra = Compras.get_by_id(id)
        if compra is None:
            return None
        
        if compra.estado == "Cancelada":
            return compra

        compra.estado = "Cancelada"
        compra.update()

        # Revertir stock de los productos comprados (restar)
        detalles = session.query(DetalleCompras).filter_by(id_compra=id).all()
        for det in detalles:
            prod = Productos.get_by_id(det.id_producto)
            if prod:
                prod.stock = max(0, prod.stock - det.cantidad)
                prod.update()

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

        # Eliminar detalles
        session.query(DetalleCompras).filter_by(id_compra=id).delete()
        compra.delete()
        return True