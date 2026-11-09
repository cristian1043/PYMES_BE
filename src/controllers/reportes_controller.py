from src.models import session
from src.models.facturas import Facturas
from src.models.clientes import Clientes
from src.models.productos import Productos


class ReportesController:
    """
    Controlador encargado de procesar toda la lógica de negocio y cálculo
    de reportes estadísticos y financieros en el Backend con aislamiento estricto por empresa.
    """

    @staticmethod
    def get_reporte_ventas(empresa_id=None):
        """Calcula los agregados financieros de las facturas válidas registradas (excluye canceladas)."""
        empty_res = {
            'total_ventas': 0.0,
            'subtotal': 0.0,
            'iva': 0.0,
            'descuento': 0.0,
            'cantidad_facturas': 0,
            'promedio_venta': 0.0,
            'facturas': []
        }
        if not empresa_id:
            return empty_res
        try:
            eid = int(empresa_id)
            facturas = session.query(Facturas).filter(Facturas.id_empresa == eid).all()
            if not facturas:
                return empty_res

            facturas_validas = [f for f in facturas if getattr(f, 'estado', 'Emitida') != 'Cancelada']

            total_ventas = sum(float(f.total or 0.0) for f in facturas_validas)
            subtotal = sum(float(f.subtotal or 0.0) for f in facturas_validas)
            iva = sum(float(f.iva or 0.0) for f in facturas_validas)
            descuento = sum(float(f.descuento or 0.0) for f in facturas_validas)
            cantidad = len(facturas_validas)
            promedio = (total_ventas / cantidad) if cantidad > 0 else 0.0

            return {
                'total_ventas': round(total_ventas, 2),
                'subtotal': round(subtotal, 2),
                'iva': round(iva, 2),
                'descuento': round(descuento, 2),
                'cantidad_facturas': cantidad,
                'promedio_venta': round(promedio, 2),
                'facturas': [f.to_dict() for f in facturas]
            }
        except Exception:
            session.rollback()
            return empty_res

    @staticmethod
    def get_reporte_clientes(empresa_id=None):
        """Procesa el ranking de compras agrupado por cliente (excluye facturas canceladas)."""
        if not empresa_id:
            return []
        try:
            eid = int(empresa_id)
            clientes = session.query(Clientes).filter(Clientes.id_empresa == eid).all()
            facturas = session.query(Facturas).filter(Facturas.id_empresa == eid).all()

            resultado = []
            for cli in clientes:
                facturas_cli = [
                    f for f in facturas
                    if f.id_cliente and str(f.id_cliente) == str(cli.id) and getattr(f, 'estado', 'Emitida') != 'Cancelada'
                ]
                total_comprado = sum(float(f.total or 0.0) for f in facturas_cli)
                num_facturas = len(facturas_cli)

                apell = getattr(cli, 'apellido', '') or ''
                nombre_comp = f"{cli.nombre} {apell}".strip()

                resultado.append({
                    'id': cli.id,
                    'nombre': nombre_comp,
                    'tipo_documento': getattr(cli, 'tipo_documento', 'CC') or 'CC',
                    'documento': (getattr(cli, 'documento', '') or 'Sin documento').split("#E")[0],
                    'direccion': getattr(cli, 'direccion', '') or 'Sin dirección registrada',
                    'email': cli.email or 'Sin correo',
                    'telefono': cli.telefono or 'Sin teléfono',
                    'num_facturas': num_facturas,
                    'total_comprado': round(total_comprado, 2)
                })

            resultado.sort(key=lambda x: x['total_comprado'], reverse=True)
            return resultado
        except Exception:
            session.rollback()
            return []

    @staticmethod
    def get_reporte_inventario(empresa_id=None):
        """Calcula la valoración total del stock e identifica productos críticos."""
        empty_inv = {
            'valor_total_inventario': 0.0,
            'total_productos': 0,
            'productos_bajo_stock': 0,
            'productos': []
        }
        if not empresa_id:
            return empty_inv
        try:
            eid = int(empresa_id)
            productos = session.query(Productos).filter(Productos.id_empresa == eid).all()
            if not productos:
                return empty_inv

            valor_total = sum(float(p.precio or 0.0) * int(p.stock or 0) for p in productos)
            total_prods = len(productos)
            bajo_stock = [p for p in productos if (p.stock or 0) <= 10]

            return {
                'valor_total_inventario': round(valor_total, 2),
                'total_productos': total_prods,
                'productos_bajo_stock': len(bajo_stock),
                'productos': [p.to_dict() for p in productos]
            }
        except Exception:
            session.rollback()
            return empty_inv

    @staticmethod
    def get_reporte_top_productos(empresa_id=None):
        """Calcula el ranking de productos más vendidos según el historial de facturación válida."""
        if not empresa_id:
            return []
        try:
            from src.models.detalle_facturas import DetalleFacturas
            eid = int(empresa_id)
            productos = session.query(Productos).filter(Productos.id_empresa == eid).all()
            if not productos:
                return []
            prod_ids = [p.id for p in productos]

            facturas_validas_ids = [
                f.id for f in session.query(Facturas).filter(Facturas.id_empresa == eid).all()
                if getattr(f, 'estado', 'Emitida') != 'Cancelada'
            ]

            detalles = []
            if prod_ids and facturas_validas_ids:
                detalles = session.query(DetalleFacturas).filter(
                    DetalleFacturas.id_producto.in_(prod_ids),
                    DetalleFacturas.id_factura.in_(facturas_validas_ids)
                ).all()

            ventas_prod = {}
            for d in detalles:
                pid = d.id_producto
                cant = d.cantidad or 0
                subt = (d.subtotal if hasattr(d, 'subtotal') and d.subtotal else (cant * (d.precio_unitario or 0)))
                if pid not in ventas_prod:
                    ventas_prod[pid] = {'cantidad_vendida': 0, 'total_recaudado': 0.0}
                ventas_prod[pid]['cantidad_vendida'] += cant
                ventas_prod[pid]['total_recaudado'] += float(subt)

            resultado = []
            for p in productos:
                stats = ventas_prod.get(p.id, {'cantidad_vendida': 0, 'total_recaudado': 0.0})
                resultado.append({
                    'id': p.id,
                    'codigo': getattr(p, 'codigo', f'PROD-{p.id}'),
                    'nombre': p.nombre,
                    'precio': float(p.precio or 0.0),
                    'stock': p.stock,
                    'cantidad_vendida': stats['cantidad_vendida'],
                    'total_recaudado': round(stats['total_recaudado'], 2)
                })

            resultado.sort(key=lambda x: (x['cantidad_vendida'], x['total_recaudado']), reverse=True)
            return resultado
        except Exception:
            session.rollback()
            return []
