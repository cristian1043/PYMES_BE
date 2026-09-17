from src.models import session
from src.models.facturas import Facturas
from src.models.clientes import Clientes
from src.models.productos import Productos

class ReportesController:
    """
    Controlador encargado de procesar toda la lógica de negocio y cálculo
    de reportes estadísticos y financieros en el Backend.
    """

    @staticmethod
    def get_reporte_ventas(empresa_id=None):
        """Calcula los agregados financieros de las facturas válidas registradas (excluye canceladas)."""
        try:
            query = session.query(Facturas)
            if empresa_id:
                query = query.filter(Facturas.id_empresa == int(empresa_id))
            facturas = query.all()
            if not facturas:
                return {
                    'total_ventas': 0.0,
                    'subtotal': 0.0,
                    'iva': 0.0,
                    'descuento': 0.0,
                    'cantidad_facturas': 0,
                    'promedio_venta': 0.0,
                    'facturas': []
                }

            facturas_validas = [f for f in facturas if getattr(f, 'estado', 'Emitida') != 'Cancelada']

            total_ventas = sum(f.total for f in facturas_validas)
            subtotal = sum(f.subtotal for f in facturas_validas)
            iva = sum(f.iva for f in facturas_validas)
            descuento = sum(f.descuento for f in facturas_validas)
            cantidad = len(facturas_validas)
            promedio = (total_ventas / cantidad) if cantidad > 0 else 0.0

            return {
                'total_ventas': total_ventas,
                'subtotal': subtotal,
                'iva': iva,
                'descuento': descuento,
                'cantidad_facturas': cantidad,
                'promedio_venta': promedio,
                'facturas': [f.to_dict() for f in facturas]
            }
        except Exception as e:
            session.rollback()
            print(f"Error en get_reporte_ventas: {str(e)}")
            return {
                'total_ventas': 0.0,
                'subtotal': 0.0,
                'iva': 0.0,
                'descuento': 0.0,
                'cantidad_facturas': 0,
                'promedio_venta': 0.0,
                'facturas': []
            }

    @staticmethod
    def get_reporte_clientes(empresa_id=None):
        """Procesa el ranking de compras agrupado por cliente (excluye facturas canceladas)."""
        try:
            cli_query = session.query(Clientes)
            fac_query = session.query(Facturas)
            if empresa_id:
                cli_query = cli_query.filter(Clientes.id_empresa == int(empresa_id))
                fac_query = fac_query.filter(Facturas.id_empresa == int(empresa_id))

            clientes = cli_query.all()
            facturas = fac_query.all()

            resultado = []
            for cli in clientes:
                facturas_cli = [f for f in facturas if f.id_cliente and str(f.id_cliente) == str(cli.id) and getattr(f, 'estado', 'Emitida') != 'Cancelada']
                total_comprado = sum(float(f.total or 0.0) for f in facturas_cli)
                num_facturas = len(facturas_cli)

                apell = getattr(cli, 'apellido', '') or ''
                nombre_comp = f"{cli.nombre} {apell}".strip()

                resultado.append({
                    'id': cli.id,
                    'nombre': nombre_comp,
                    'email': cli.email or 'Sin correo',
                    'telefono': cli.telefono or 'Sin teléfono',
                    'num_facturas': num_facturas,
                    'total_comprado': total_comprado
                })

            resultado.sort(key=lambda x: x['total_comprado'], reverse=True)
            return resultado
        except Exception as e:
            session.rollback()
            print(f"Error en get_reporte_clientes: {str(e)}")
            return []

    @staticmethod
    def get_reporte_inventario(empresa_id=None):
        """Calcula la valoración total del stock e identifica productos críticos."""
        try:
            query = session.query(Productos)
            if empresa_id:
                query = query.filter(Productos.id_empresa == int(empresa_id))
            productos = query.all()
            if not productos:
                return {
                    'valor_total_inventario': 0.0,
                    'total_productos': 0,
                    'productos_bajo_stock': 0,
                    'productos': []
                }

            valor_total = sum(p.precio * p.stock for p in productos)
            total_prods = len(productos)
            bajo_stock = [p for p in productos if (p.stock or 0) <= 10]

            return {
                'valor_total_inventario': valor_total,
                'total_productos': total_prods,
                'productos_bajo_stock': len(bajo_stock),
                'productos': [p.to_dict() for p in productos]
            }
        except Exception as e:
            session.rollback()
            print(f"Error en get_reporte_inventario: {str(e)}")
            return {
                'valor_total_inventario': 0.0,
                'total_productos': 0,
                'productos_bajo_stock': 0,
                'productos': []
            }

    @staticmethod
    def get_reporte_top_productos(empresa_id=None):
        """Calcula el ranking de productos más vendidos según el historial de facturación."""
        try:
            from src.models.detalle_facturas import DetalleFacturas
            prod_query = session.query(Productos)
            if empresa_id:
                prod_query = prod_query.filter(Productos.id_empresa == int(empresa_id))
            productos = prod_query.all()
            prod_ids = {p.id for p in productos}

            detalles_all = session.query(DetalleFacturas).all()
            detalles = [d for d in detalles_all if d.id_producto in prod_ids]

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
                    'precio': float(p.precio),
                    'stock': p.stock,
                    'cantidad_vendida': stats['cantidad_vendida'],
                    'total_recaudado': stats['total_recaudado']
                })

            resultado.sort(key=lambda x: (x['cantidad_vendida'], x['total_recaudado']), reverse=True)
            return resultado
        except Exception as e:
            session.rollback()
            print(f"Error en get_reporte_top_productos: {str(e)}")
            return []

