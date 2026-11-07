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
    def get(empresa_id=None):
        query = Facturas.get_query()
        if empresa_id:
            query = query.filter(Facturas.id_empresa == int(empresa_id))
        return query.all()

    @staticmethod
    def get_paginated(page=1, per_page=10, empresa_id=None):
        query = Facturas.get_query()
        if empresa_id:
            query = query.filter(Facturas.id_empresa == int(empresa_id))
        return paginate_query(query, page, per_page)

    @staticmethod
    def get_by_id(id):
        factura = Facturas.get_by_id(id)
        if not factura:
            return None

        f_dict = factura.to_dict()

        # 1. Enriquecer datos del Cliente si existe
        cliente = Clientes.get_by_id(factura.id_cliente)
        f_dict['cliente'] = cliente.to_dict() if cliente else None

        # 2. Enriquecer datos del Usuario que emitió la factura
        usuario = Usuarios.get_by_id(factura.id_usuario)
        f_dict['usuario'] = usuario.to_dict() if usuario else None

        # 3. Enriquecer Método de Pago por Nombre y Detalle
        metodo = MetodosPago.get_by_id(factura.id_metodo_pago)
        f_dict['metodo_pago_detalle'] = metodo.to_dict() if metodo else {'nombre': 'Efectivo', 'pasarela': 'ninguna', 'integrado': False}
        f_dict['metodo_pago'] = metodo.nombre if metodo else 'Efectivo'

        # 4. Enriquecer Lista de Productos e Ítems Comprados (DetalleFacturas)
        detalles_db = session.query(DetalleFacturas).filter_by(id_factura=id).all()
        items_list = []
        for det in detalles_db:
            prod = Productos.get_by_id(det.id_producto)
            items_list.append({
                'id': det.id,
                'id_producto': det.id_producto,
                'codigo': prod.codigo if prod else f"PROD-{det.id_producto:03d}",
                'nombre_producto': prod.nombre if prod else "Producto",
                'unidad_medida': prod.unidad_medida if prod else "UND",
                'cantidad': det.cantidad,
                'precio_unitario': det.precio_unitario,
                'subtotal': det.subtotal
            })

        f_dict['detalles'] = items_list

        # Convertir objetos datetime a string para compatibilidad JSON
        if isinstance(f_dict.get('fecha'), datetime):
            f_dict['fecha'] = f_dict['fecha'].strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(f_dict.get('cliente'), dict) and isinstance(f_dict['cliente'].get('created_at'), datetime):
            f_dict['cliente']['created_at'] = f_dict['cliente']['created_at'].strftime('%Y-%m-%d %H:%M:%S')

        f_dict['detalles'] = items_list
        return f_dict

    @staticmethod
    def obtener_siguiente_numero(empresa_id=None):
        prefix = f"FAC-E{empresa_id}-" if empresa_id else "FAC-"
        query = Facturas.get_query()
        if empresa_id:
            query = query.filter(Facturas.id_empresa == int(empresa_id))
        facturas = query.all()
        max_num = 0
        for f in facturas:
            if f.numero:
                if f.numero.startswith(prefix):
                    try:
                        num_part = int(f.numero.replace(prefix, "").strip())
                        if num_part > max_num:
                            max_num = num_part
                    except ValueError:
                        pass
                elif f.numero.startswith("FAC-"):
                    try:
                        num_part = int(f.numero.split("-")[-1].strip())
                        if num_part > max_num:
                            max_num = num_part
                    except ValueError:
                        pass
        siguiente = max_num + 1
        return f"{prefix}{siguiente:03d}"

    @staticmethod
    def create(data):
        # Resolver o autovincular empresa primero para el consecutivo
        emp_id = data.get("id_empresa") or data.get("empresa_id")
        if not emp_id:
            id_cli_cand = data.get("id_cliente") or data.get("cliente_id")
            if id_cli_cand:
                try:
                    cli_obj = Clientes.get_by_id(int(id_cli_cand))
                    if cli_obj and getattr(cli_obj, "id_empresa", None):
                        emp_id = cli_obj.id_empresa
                except Exception:
                    pass
        if not emp_id:
            emp_id = 1
        id_empresa_val = int(emp_id)

        try:
            from src.utils.migrations import DatabaseMigrations
            DatabaseMigrations.asegurar_esquema_y_datos(empresa_id=id_empresa_val)
        except Exception:
            pass

        # Prevalidar detalles y stock disponible antes de crear la factura
        detalles = data.get("detalles") or data.get("items") or []
        items_validados = []
        subtotal_items = 0.0
        for item in detalles:
            id_prod = int(item.get("id_producto"))
            cant = int(item.get("cantidad", 1))
            if cant <= 0:
                raise ValueError("La cantidad de cada producto en la factura debe ser mayor a cero.")
            prod = Productos.get_by_id(id_prod)
            if not prod:
                raise ValueError(f"El producto con ID {id_prod} no existe.")
            if getattr(prod, "id_empresa", None) and int(prod.id_empresa) != id_empresa_val:
                raise ValueError(f"El producto '{prod.nombre}' no pertenece a la empresa activa.")
            if (prod.stock or 0) < cant:
                raise ValueError(f"Stock insuficiente para '{prod.nombre}' (disponible: {prod.stock or 0}, solicitado: {cant}).")
            prec = float(item.get("precio_unitario", prod.precio or 0))
            if prec < 0:
                raise ValueError("El precio unitario no puede ser negativo.")
            sub_item = round(cant * prec, 2)
            subtotal_items += sub_item
            items_validados.append((prod, cant, prec, sub_item))

        numero = data.get("numero")
        if not numero or not str(numero).strip():
            numero = FacturasController.obtener_siguiente_numero(id_empresa_val)

        subtotal = float(data.get("subtotal", 0))
        if items_validados and subtotal <= 0:
            subtotal = subtotal_items
        iva = float(data.get("iva", 0))
        descuento = float(data.get("descuento", 0))
        if subtotal < 0 or iva < 0 or descuento < 0:
            raise ValueError("Los valores de subtotal, IVA y descuento no pueden ser negativos.")
        total = subtotal + iva - descuento
        if total < 0:
            raise ValueError("El total de la factura no puede ser negativo.")

        fecha_factura = data.get("fecha")
        if not fecha_factura:
            fecha_factura = datetime.now()

        # Resolver o autovincular cliente (respetando aislamiento multiempresa)
        id_cliente = data.get("id_cliente") or data.get("cliente_id")
        if not id_cliente:
            doc_cliente = data.get("documento_cliente") or data.get("documento")
            nom_cliente = data.get("cliente_nombre") or data.get("nombre_cliente")
            tipo_doc = data.get("tipo_documento") or "CC"
            if doc_cliente and str(doc_cliente).strip():
                doc_clean = str(doc_cliente).strip()
                cliente_existente = Clientes.get_by_documento(doc_clean, empresa_id=id_empresa_val)
                if cliente_existente:
                    id_cliente = cliente_existente.id
                    cliente_existente.id_empresa = id_empresa_val
                    cliente_existente.estado = "Activo"
                    if nom_cliente and str(nom_cliente).strip():
                        parts = str(nom_cliente).strip().split(" ", 1)
                        cliente_existente.nombre = parts[0]
                        if len(parts) > 1 and hasattr(cliente_existente, 'apellido'):
                            cliente_existente.apellido = parts[1]
                    if data.get("telefono_cliente"):
                        cliente_existente.telefono = str(data.get("telefono_cliente")).strip()
                    if data.get("direccion_cliente"):
                        cliente_existente.direccion = str(data.get("direccion_cliente")).strip()
                    cliente_existente.update()
                else:
                    # Crear nuevo cliente para la empresa sin sobrescribir clientes de otras empresas
                    nom_full = str(nom_cliente or f"Cliente {doc_clean}").strip()
                    parts = nom_full.split(" ", 1)
                    first_name = parts[0]
                    last_name = parts[1] if len(parts) > 1 else ""

                    count_cli = session.query(Clientes).filter(Clientes.id_empresa == id_empresa_val).count()
                    cod_cli = f"CLI-E{id_empresa_val}-{count_cli + 1:03d}"

                    nuevo_cliente = Clientes()
                    nuevo_cliente.codigo = cod_cli
                    nuevo_cliente.documento = doc_clean
                    nuevo_cliente.tipo_documento = tipo_doc
                    nuevo_cliente.nombre = first_name
                    nuevo_cliente.apellido = last_name
                    nuevo_cliente.direccion = data.get("direccion_cliente") or "Dirección Comercial"
                    nuevo_cliente.telefono = data.get("telefono_cliente") or "3000000000"
                    
                    email_cand = data.get("email_cliente")
                    if not email_cand or not str(email_cand).strip():
                        email_cand = f"cli_{doc_clean}_{id_empresa_val}@correo.com"
                    nuevo_cliente.email = str(email_cand).strip()
                    nuevo_cliente.estado = "Activo"
                    nuevo_cliente.id_empresa = id_empresa_val
                    
                    try:
                        nuevo_cliente.save()
                        id_cliente = nuevo_cliente.id
                    except Exception:
                        session.rollback()
                        nuevo_cliente.documento = f"{doc_clean}#E{id_empresa_val}"
                        nuevo_cliente.email = f"cli_{doc_clean}_{id_empresa_val}_{int(datetime.now().timestamp())}@correo.com"
                        nuevo_cliente.save()
                        id_cliente = nuevo_cliente.id
            elif nom_cliente and str(nom_cliente).strip():
                nom_full = str(nom_cliente).strip()
                parts = nom_full.split(" ", 1)
                first_name = parts[0]
                last_name = parts[1] if len(parts) > 1 else ""

                count_cli = session.query(Clientes).filter(Clientes.id_empresa == id_empresa_val).count()
                cod_cli = f"CLI-E{id_empresa_val}-{count_cli + 1:03d}"

                ts_suffix = int(datetime.now().timestamp())
                nuevo_cliente = Clientes()
                nuevo_cliente.codigo = cod_cli
                nuevo_cliente.documento = f"CC-{ts_suffix}"
                nuevo_cliente.tipo_documento = tipo_doc
                nuevo_cliente.nombre = first_name
                nuevo_cliente.apellido = last_name
                nuevo_cliente.direccion = data.get("direccion_cliente") or "Dirección Comercial"
                nuevo_cliente.telefono = data.get("telefono_cliente") or "3000000000"
                nuevo_cliente.email = data.get("email_cliente") or f"cli_{ts_suffix}@correo.com"
                nuevo_cliente.estado = "Activo"
                nuevo_cliente.id_empresa = id_empresa_val
                try:
                    nuevo_cliente.save()
                    id_cliente = nuevo_cliente.id
                except Exception:
                    session.rollback()
                    nuevo_cliente.email = f"cli_{ts_suffix}_{id_empresa_val}@correo.com"
                    nuevo_cliente.save()
                    id_cliente = nuevo_cliente.id
            else:
                raise ValueError("Se requiere especificar el cliente para emitir la factura.")

        if id_cliente:
            cli_asoc = Clientes.get_by_id(id_cliente)
            if cli_asoc and not getattr(cli_asoc, 'id_empresa', None):
                cli_asoc.id_empresa = id_empresa_val
                cli_asoc.estado = "Activo"
                cli_asoc.update()

        # Resolver id_metodo_pago garantizando que exista en la tabla metodos_pago (FK segura)
        id_metodo = data.get("id_metodo_pago")
        nom_mp = str(data.get("metodo_pago") or "").strip()
        metodo_sel = None

        if id_metodo and str(id_metodo).isdigit():
            metodo_sel = MetodosPago.get_by_id(int(id_metodo))

        if not metodo_sel:
            todos_metodos = MetodosPago.get_query().all()
            if not todos_metodos:
                nuevo_mp = MetodosPago(
                    nombre="Efectivo",
                    descripcion="Pago en efectivo en caja",
                    tipo="Efectivo",
                    pasarela="ninguna",
                    modo="sandbox",
                    estado="Activo",
                    id_empresa=None
                )
                session.add(nuevo_mp)
                session.commit()
                todos_metodos = [nuevo_mp]

            if nom_mp:
                nom_low = nom_mp.lower()
                metodo_sel = next((m for m in todos_metodos if (m.nombre or "").lower() == nom_low), None)
                if not metodo_sel:
                    if "bold" in nom_low or "datafono" in nom_low or "datáfono" in nom_low or "tarjet" in nom_low:
                        metodo_sel = next((m for m in todos_metodos if (m.tipo or "").lower() == "tarjeta" or "bold" in (m.nombre or "").lower()), None)
                    elif "wompi" in nom_low or "pse" in nom_low or "link" in nom_low:
                        metodo_sel = next((m for m in todos_metodos if (m.tipo or "").lower() == "pasarela" or "wompi" in (m.nombre or "").lower()), None)
                    elif "transf" in nom_low or "nequi" in nom_low or "davi" in nom_low:
                        metodo_sel = next((m for m in todos_metodos if (m.tipo or "").lower() == "transferencia" or "transf" in (m.nombre or "").lower()), None)

            if not metodo_sel and str(id_metodo or "") == "2":
                metodo_sel = next((m for m in todos_metodos if (m.tipo or "").lower() == "tarjeta" or (m.tipo or "").lower() == "transferencia"), None)
            elif not metodo_sel and str(id_metodo or "") == "3":
                metodo_sel = next((m for m in todos_metodos if (m.tipo or "").lower() == "transferencia" or (m.tipo or "").lower() == "tarjeta"), None)

            if not metodo_sel:
                metodo_sel = todos_metodos[0]

        id_metodo = metodo_sel.id

        factura = Facturas()
        factura.numero = str(numero).strip()
        factura.fecha = fecha_factura
        factura.subtotal = subtotal
        factura.iva = iva
        factura.descuento = descuento
        # El total siempre se calcula en el servidor (no se confía en el valor enviado por el cliente)
        factura.total = total
        factura.id_cliente = int(id_cliente)
        factura.id_usuario = int(data.get("id_usuario") or 1)
        factura.id_metodo_pago = int(id_metodo)
        factura.id_empresa = id_empresa_val

        # Si es un método de pago directo (Efectivo, Transferencia, etc.), liquidar como Pagada de inmediato
        if metodo_sel is not None and metodo_sel.integrado and not data.get("aprobar_inmediato"):
            factura.estado = "Emitida"
            factura.pasarela = None
            factura.referencia_pago = None
        else:
            factura.estado = data.get("estado") or "Pagada"
            if factura.estado == "Emitida" and not (metodo_sel and metodo_sel.integrado):
                factura.estado = "Pagada"
            factura.pasarela = data.get("pasarela") or (metodo_sel.pasarela if (metodo_sel and metodo_sel.pasarela != "ninguna") else "caja")
            factura.referencia_pago = data.get("referencia_pago") or f"PAGO-{int(datetime.now().timestamp())}"
        
        factura.create()

        # Guardar ítems prevalidados de DetalleFacturas, descontar stock y registrar Kardex
        from src.models.movimiento_inventario import MovimientosInventario
        for prod, cant, prec, sub_item in items_validados:
            det = DetalleFacturas()
            det.id_factura = factura.id
            det.id_producto = prod.id
            det.cantidad = cant
            det.precio_unitario = prec
            det.subtotal = sub_item
            session.add(det)

            prod.stock = (prod.stock or 0) - cant
            session.add(prod)

            mov = MovimientosInventario(
                tipo_movimiento="SALIDA",
                cantidad=cant,
                observacion=f"Venta Factura {factura.numero}",
                id_producto=prod.id,
                id_usuario=factura.id_usuario,
                id_empresa=factura.id_empresa
            )
            session.add(mov)

        session.commit()
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

        # Con pasarela integrada, el estado 'Pagada', la pasarela y la referencia solo los fija la confirmación del cobro
        metodo_destino = MetodosPago.get_by_id(int(data.get("id_metodo_pago", factura.id_metodo_pago)))
        protegido = metodo_destino is not None and metodo_destino.integrado
        if protegido:
            from src.services.pagos.cobros_service import CobrosService
            protegido = not CobrosService.pago_confirmado(factura.id)

        if "estado" in data:
            if not (protegido and data["estado"] == "Pagada"):
                factura.estado = data["estado"]
        factura.subtotal = subtotal
        factura.iva = iva
        factura.descuento = descuento
        factura.total = total
        factura.id_cliente = int(data.get("id_cliente", factura.id_cliente))
        factura.id_usuario = int(data.get("id_usuario", factura.id_usuario))
        factura.id_metodo_pago = int(data.get("id_metodo_pago", factura.id_metodo_pago))
        if "pasarela" in data and not protegido:
            factura.pasarela = data["pasarela"]
        if "referencia_pago" in data and not protegido:
            factura.referencia_pago = data["referencia_pago"]
        
        factura.update()
        return factura

    @staticmethod
    def registrar_pago_pasarela(id, pasarela="manual", referencia_pago=None, id_metodo_pago=None):
        """Registro directo de pago en caja (efectivo, transferencia o confirmación manual)."""
        factura = Facturas.get_by_id(id)
        if not factura:
            return None
        if id_metodo_pago and str(id_metodo_pago).isdigit():
            metodo = MetodosPago.get_by_id(int(id_metodo_pago))
            if metodo:
                factura.id_metodo_pago = metodo.id
        factura.estado = "Pagada"
        factura.pasarela = str(pasarela or "caja")
        factura.referencia_pago = str(referencia_pago or f"CAJA-{int(datetime.now().timestamp())}")
        factura.update()
        return factura

    @staticmethod
    def cancelar(id):
        """Cancela la factura emitida y restaura el stock de productos vendidos (idempotente)."""
        factura = Facturas.get_by_id(id)
        if not factura:
            return None

        if factura.estado == "Cancelada":
            return factura

        factura.estado = "Cancelada"
        
        # Revertir stock de productos y registrar entrada en Kardex
        from src.models.movimiento_inventario import MovimientosInventario
        detalles_db = session.query(DetalleFacturas).filter_by(id_factura=id).all()
        for det in detalles_db:
            prod = Productos.get_by_id(det.id_producto)
            if prod:
                prod.stock = (prod.stock or 0) + det.cantidad
                session.add(prod)
                mov = MovimientosInventario(
                    tipo_movimiento="ENTRADA",
                    cantidad=det.cantidad,
                    observacion=f"Reverso por cancelación de Factura {factura.numero}",
                    id_producto=prod.id,
                    id_usuario=factura.id_usuario or 1,
                    id_empresa=factura.id_empresa
                )
                session.add(mov)

        session.commit()
        return factura

    @staticmethod
    def delete(id):
        factura = Facturas.get_by_id(id)
        if factura is None:
            return False
        # Eliminar detalles asociados
        session.query(DetalleFacturas).filter_by(id_factura=id).delete()
        factura.delete()
        return True
