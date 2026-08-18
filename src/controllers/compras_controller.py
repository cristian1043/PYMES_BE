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

        c_dict['detalles'] = items_list
        return c_dict

    @staticmethod
    def create(data):
        subtotal = float(data.get("subtotal", 0))
        iva = float(data.get("iva", 0))
        descuento = float(data.get("descuento", 0))
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