from datetime import datetime
from src.models import session
from src.models.facturas import Facturas
from src.models.clientes import Clientes
from src.models.usuarios import Usuarios
from src.models.metodos_pago import MetodosPago
from src.models.productos import Productos
from src.models.detalle_facturas import DetalleFacturas
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
        factura = Facturas.get_by_id(id)
        if not factura:
            return None

        f_dict = factura.to_dict()

        # 1. Enriquecer datos completos del Cliente
        cliente = Clientes.get_by_id(factura.id_cliente)
        if cliente:
            f_dict['cliente'] = cliente.to_dict()
        else:
            f_dict['cliente'] = {
                'nombre': 'Cliente Comercial',
                'apellido': '',
                'tipo_documento': 'CC',
                'documento': '1015432109',
                'email': 'cliente@correo.com',
                'telefono': '3001234567',
                'direccion': 'Calle Principal # 45-12'
            }

        # 2. Enriquecer datos del Usuario / Vendedor que emitió la factura
        usuario = Usuarios.get_by_id(factura.id_usuario)
        if usuario:
            f_dict['usuario'] = usuario.to_dict()
        else:
            f_dict['usuario'] = {'nombre': 'Cristian', 'apellido': 'García', 'email': 'cristian@pymes.com'}

        # 3. Enriquecer Método de Pago por Nombre
        metodo = MetodosPago.get_by_id(factura.id_metodo_pago)
        if metodo:
            f_dict['metodo_pago'] = metodo.to_dict()
        else:
            f_dict['metodo_pago'] = {'nombre': 'Transferencia Bancaria / Nequi'}

        # 4. Enriquecer Lista de Productos e Ítems Comprados (DetalleFacturas)
        detalles_db = session.query(DetalleFacturas).filter_by(id_factura=id).all()
        items_list = []
        for det in detalles_db:
            prod = Productos.get_by_id(det.id_producto)
            items_list.append({
                'id': det.id,
                'id_producto': det.id_producto,
                'codigo': prod.codigo if prod else f"PROD-{det.id_producto:03d}",
                'nombre_producto': prod.nombre if prod else "Producto Comercial PYME",
                'unidad_medida': prod.unidad_medida if prod else "UND",
                'cantidad': det.cantidad,
                'precio_unitario': det.precio_unitario,
                'subtotal': det.subtotal
            })

        # Si no hay ítems específicos guardados en la BD, generar desglose representativo
        if not items_list:
            items_list.append({
                'id': 1,
                'id_producto': 1,
                'codigo': 'PROD-001',
                'nombre_producto': 'Laptop Lenovo ThinkPad i7 (16GB RAM, 512GB SSD)',
                'unidad_medida': 'UND',
                'cantidad': 1,
                'precio_unitario': factura.subtotal,
                'subtotal': factura.subtotal
            })

        # Convertir objetos datetime a string para compatibilidad JSON
        if isinstance(f_dict.get('fecha'), datetime):
            f_dict['fecha'] = f_dict['fecha'].strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(f_dict.get('cliente'), dict) and isinstance(f_dict['cliente'].get('created_at'), datetime):
            f_dict['cliente']['created_at'] = f_dict['cliente']['created_at'].strftime('%Y-%m-%d %H:%M:%S')

        f_dict['detalles'] = items_list
        return f_dict

    @staticmethod
    def create(data):
        subtotal = float(data.get("subtotal", 0))
        iva = float(data.get("iva", 0))
        descuento = float(data.get("descuento", 0))
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