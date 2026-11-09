from datetime import datetime
from src.models import session
from src.models.compras import Compras
from src.models.proveedores import Proveedores
from src.models.usuarios import Usuarios
from src.models.productos import Productos
from src.models.detalle_compras import DetalleCompras
from src.models.metodos_pago import MetodosPago
from src.utils.pagination import paginate_query


class ComprasController:

    @staticmethod
    def get(empresa_id=None):
        if not empresa_id:
            return []
        return Compras.get_query().filter(Compras.id_empresa == int(empresa_id)).all()

    @staticmethod
    def get_paginated(page=1, per_page=10, empresa_id=None):
        query = Compras.get_query()
        if empresa_id:
            query = query.filter(Compras.id_empresa == int(empresa_id))
        else:
            return paginate_query(query.filter(Compras.id_empresa == -1), page, per_page)
        return paginate_query(query, page, per_page)

    @staticmethod
    def get_by_id(id):
        compra = Compras.get_by_id(id)
        if compra is None:
            return None

        c_dict = compra.to_dict()

        prov = Proveedores.get_by_id(compra.id_proveedor)
        c_dict['proveedor'] = prov.to_dict() if prov else None

        usr = Usuarios.get_by_id(compra.id_usuario)
        c_dict['usuario'] = usr.to_safe_dict() if usr else None

        id_mp = getattr(compra, 'id_metodo_pago', None)
        mp_obj = MetodosPago.get_by_id(id_mp) if id_mp else None
        c_dict['metodo_pago_detalle'] = mp_obj.to_dict() if mp_obj else None
        if not c_dict.get('metodo_pago'):
            c_dict['metodo_pago'] = mp_obj.nombre if mp_obj else 'Efectivo'
        c_dict['referencia_pago'] = getattr(compra, 'referencia_pago', None)

        detalles_db = session.query(DetalleCompras).filter_by(id_compra=id).all()
        items_list = []
        for det in detalles_db:
            prod = Productos.get_by_id(det.id_producto)
            items_list.append({
                'id': det.id,
                'id_producto': det.id_producto,
                'codigo': prod.codigo if prod else f"PROD-{det.id_producto:03d}",
                'nombre_producto': prod.nombre if prod else "Insumo / Producto",
                'unidad_medida': prod.unidad_medida if prod else "UND",
                'cantidad': det.cantidad,
                'costo_unitario': det.costo_unitario,
                'subtotal': det.subtotal
            })

        c_dict['detalles'] = items_list

        if isinstance(c_dict.get('fecha'), datetime):
            c_dict['fecha'] = c_dict['fecha'].strftime('%Y-%m-%d %H:%M:%S')

        return c_dict

    @staticmethod
    def obtener_siguiente_numero(empresa_id=None):
        eid = int(empresa_id) if empresa_id else 1
        prefix = f"COMP-E{eid}-"
        compras = Compras.get_query().filter(Compras.id_empresa == eid).all()
        max_num = 0
        for c in compras:
            if c.numero:
                if c.numero.startswith(prefix):
                    try:
                        num_part = int(c.numero.replace(prefix, "").strip())
                        if num_part > max_num:
                            max_num = num_part
                    except ValueError:
                        pass
                elif c.numero.startswith("COMP-"):
                    try:
                        num_part = int(c.numero.split("-")[-1].strip())
                        if num_part > max_num:
                            max_num = num_part
                    except ValueError:
                        pass
        siguiente = max_num + 1
        return f"{prefix}{siguiente:03d}"

    @staticmethod
    def create(data):
        emp_id = data.get("id_empresa") or data.get("empresa_id")
        if not emp_id:
            raise ValueError("El identificador de empresa ('id_empresa') es obligatorio para registrar una compra.")
        id_empresa_val = int(emp_id)

        id_prov = data.get("id_proveedor")
        if not id_prov:
            raise ValueError("Debes especificar un proveedor válido para registrar la compra.")
        prov_obj = Proveedores.get_by_id(int(id_prov))
        if not prov_obj or (prov_obj.id_empresa and int(prov_obj.id_empresa) != id_empresa_val):
            raise ValueError("El proveedor especificado no existe o no pertenece a la empresa activa.")

        subtotal = float(data.get("subtotal", 0))
        iva = float(data.get("iva", 0))
        descuento = float(data.get("descuento", 0))

        num = data.get("numero")
        if not num or num == "COMP-AUTO" or str(num).strip() == "":
            num = ComprasController.obtener_siguiente_numero(id_empresa_val)

        detalles = data.get("detalles") or data.get("items") or []
        if not detalles and subtotal <= 0:
            raise ValueError("La orden de compra debe contener al menos un producto o ítem en el detalle.")

        items_validados = []
        subtotal_items = 0.0
        for item in detalles:
            id_prod = int(item.get("id_producto"))
            cant = int(item.get("cantidad", 1))
            if cant <= 0:
                raise ValueError("La cantidad de cada producto comprado debe ser mayor a cero.")
            prod = Productos.get_by_id(id_prod)
            if not prod:
                raise ValueError(f"El producto con ID {id_prod} no existe.")
            if getattr(prod, "id_empresa", None) is None or int(prod.id_empresa) != id_empresa_val:
                raise ValueError(f"El producto '{prod.nombre}' no pertenece a la empresa activa.")

            costo_u = float(item.get("costo_unitario", item.get("precio_unitario", 0)))
            if costo_u < 0:
                raise ValueError("El costo unitario no puede ser negativo.")
            subt_item = round(cant * costo_u, 2)
            subtotal_items += subt_item
            items_validados.append((prod, cant, costo_u, subt_item))

        if items_validados:
            subtotal = subtotal_items
        total = round(subtotal + iva - descuento, 2)
        if total < 0:
            raise ValueError("El total de la compra no puede ser negativo.")

        id_mp_raw = data.get("id_metodo_pago")
        nombre_mp_raw = (data.get("metodo_pago") or "").strip()
        id_mp_val = None
        nombre_mp_val = nombre_mp_raw

        if id_mp_raw is not None and str(id_mp_raw).strip() != "":
            try:
                id_mp_val = int(id_mp_raw)
                mp_obj = MetodosPago.get_by_id(id_mp_val)
                if mp_obj and getattr(mp_obj, "nombre", None) and not nombre_mp_val:
                    nombre_mp_val = mp_obj.nombre
            except ValueError:
                if not nombre_mp_val:
                    nombre_mp_val = str(id_mp_raw).strip()

        if not nombre_mp_val:
            nombre_mp_val = "Efectivo"
        if not id_mp_val:
            id_mp_val = 1

        try:
            compra = Compras()
            compra.numero = num
            compra.subtotal = subtotal
            compra.iva = iva
            compra.descuento = descuento
            compra.total = total
            compra.estado = data.get("estado", "Completada")
            compra.id_proveedor = int(id_prov)
            compra.id_usuario = int(data.get("id_usuario") or 1)
            compra.id_metodo_pago = id_mp_val
            compra.metodo_pago = nombre_mp_val
            compra.referencia_pago = (data.get("referencia_pago") or "").strip() or None
            compra.id_empresa = id_empresa_val

            session.add(compra)
            session.flush()

            from src.models.movimiento_inventario import MovimientosInventario
            for prod, cant, costo_u, subt_item in items_validados:
                det_compra = DetalleCompras()
                det_compra.id_compra = compra.id
                det_compra.id_producto = prod.id
                det_compra.cantidad = cant
                det_compra.costo_unitario = costo_u
                det_compra.subtotal = subt_item
                session.add(det_compra)

                prod.stock = (prod.stock or 0) + cant
                if costo_u > 0:
                    prod.costo = costo_u
                session.add(prod)

                mov = MovimientosInventario(
                    tipo_movimiento="ENTRADA",
                    cantidad=cant,
                    observacion=f"Ingreso por Compra {compra.numero}",
                    id_producto=prod.id,
                    id_usuario=compra.id_usuario or 1,
                    id_empresa=compra.id_empresa
                )
                session.add(mov)

            session.commit()
            return compra
        except Exception:
            session.rollback()
            raise

    @staticmethod
    def cancelar(id):
        compra = Compras.get_by_id(id)
        if compra is None:
            return None

        if compra.estado == "Cancelada":
            return compra

        try:
            compra.estado = "Cancelada"
            from src.models.movimiento_inventario import MovimientosInventario
            detalles = session.query(DetalleCompras).filter_by(id_compra=id).all()
            for det in detalles:
                prod = Productos.get_by_id(det.id_producto)
                if prod:
                    prod.stock = max(0, (prod.stock or 0) - det.cantidad)
                    session.add(prod)
                    mov = MovimientosInventario(
                        tipo_movimiento="SALIDA",
                        cantidad=det.cantidad,
                        observacion=f"Reverso por cancelación de Compra {compra.numero}",
                        id_producto=prod.id,
                        id_usuario=compra.id_usuario or 1,
                        id_empresa=compra.id_empresa
                    )
                    session.add(mov)

            session.commit()
            return compra
        except Exception:
            session.rollback()
            raise

    @staticmethod
    def update(id, data):
        compra = Compras.get_by_id(id)
        if compra is None:
            return None

        subtotal = float(data.get("subtotal", compra.subtotal))
        iva = float(data.get("iva", compra.iva))
        descuento = float(data.get("descuento", compra.descuento))
        total = round(subtotal + iva - descuento, 2)

        compra.numero = data.get("numero", compra.numero)
        compra.subtotal = subtotal
        compra.iva = iva
        compra.descuento = descuento
        compra.total = total
        if "id_proveedor" in data and data["id_proveedor"]:
            prov_cand = Proveedores.get_by_id(int(data["id_proveedor"]))
            if not prov_cand or (compra.id_empresa and prov_cand.id_empresa != compra.id_empresa):
                raise ValueError("El proveedor seleccionado no pertenece a la empresa de la compra.")
            compra.id_proveedor = int(data["id_proveedor"])
        compra.id_usuario = int(data.get("id_usuario", compra.id_usuario))
        if "id_metodo_pago" in data and data.get("id_metodo_pago"):
            try:
                compra.id_metodo_pago = int(data.get("id_metodo_pago"))
                mp_obj = MetodosPago.get_by_id(compra.id_metodo_pago)
                if mp_obj and getattr(mp_obj, "nombre", None) and not data.get("metodo_pago"):
                    compra.metodo_pago = mp_obj.nombre
            except ValueError:
                pass
        if "metodo_pago" in data and data.get("metodo_pago"):
            compra.metodo_pago = str(data.get("metodo_pago")).strip()
        if "referencia_pago" in data:
            compra.referencia_pago = (data.get("referencia_pago") or "").strip() or None

        compra.update()
        return compra

    @staticmethod
    def delete(id):
        compra = Compras.get_by_id(id)
        if compra is None:
            return False
        session.query(DetalleCompras).filter_by(id_compra=id).delete()
        compra.delete()
        return True
