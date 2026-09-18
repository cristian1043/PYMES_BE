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

        # 3. Enriquecer Método de Pago por Nombre
        metodo = MetodosPago.get_by_id(factura.id_metodo_pago)
        f_dict['metodo_pago'] = metodo.to_dict() if metodo else {'nombre': 'No especificado'}

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
            raise ValueError("El identificador de empresa ('id_empresa') es obligatorio para emitir la factura.")
        id_empresa_val = int(emp_id)

        numero = data.get("numero")
        if not numero or not str(numero).strip():
            numero = FacturasController.obtener_siguiente_numero(id_empresa_val)

        subtotal = float(data.get("subtotal", 0))
        iva = float(data.get("iva", 0))
        descuento = float(data.get("descuento", 0))
        total = subtotal + iva - descuento

        fecha_factura = data.get("fecha")
        if not fecha_factura:
            fecha_factura = datetime.now()

        # Resolver o autovincular cliente
        id_cliente = data.get("id_cliente") or data.get("cliente_id")
        if not id_cliente:
            doc_cliente = data.get("documento_cliente") or data.get("documento")
            nom_cliente = data.get("cliente_nombre") or data.get("nombre_cliente")
            tipo_doc = data.get("tipo_documento") or "CC"
            if doc_cliente and str(doc_cliente).strip():
                doc_clean = str(doc_cliente).strip()
                cliente_existente = Clientes.get_by_documento(doc_clean, empresa_id=id_empresa_val)
                if not cliente_existente:
                    cliente_existente = Clientes.get_by_documento(doc_clean)
                if cliente_existente:
                    id_cliente = cliente_existente.id
                else:
                    # Crear nuevo cliente para la empresa
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
                    nuevo_cliente.direccion = data.get("direccion_cliente", "Dirección Comercial")
                    nuevo_cliente.telefono = data.get("telefono_cliente", "3000000000")
                    nuevo_cliente.email = data.get("email_cliente", f"cliente_{doc_clean}@correo.com")
                    nuevo_cliente.estado = "Activo"
                    nuevo_cliente.id_empresa = id_empresa_val
                    nuevo_cliente.save()
                    id_cliente = nuevo_cliente.id
            elif nom_cliente and str(nom_cliente).strip():
                nom_full = str(nom_cliente).strip()
                parts = nom_full.split(" ", 1)
                first_name = parts[0]
                last_name = parts[1] if len(parts) > 1 else ""

                count_cli = session.query(Clientes).filter(Clientes.id_empresa == id_empresa_val).count()
                cod_cli = f"CLI-E{id_empresa_val}-{count_cli + 1:03d}"

                nuevo_cliente = Clientes()
                nuevo_cliente.codigo = cod_cli
                nuevo_cliente.documento = f"CC-{int(datetime.now().timestamp())}"
                nuevo_cliente.tipo_documento = tipo_doc
                nuevo_cliente.nombre = first_name
                nuevo_cliente.apellido = last_name
                nuevo_cliente.direccion = data.get("direccion_cliente", "Dirección Comercial")
                nuevo_cliente.telefono = data.get("telefono_cliente", "3000000000")
                nuevo_cliente.email = data.get("email_cliente", f"cli_{int(datetime.now().timestamp())}@correo.com")
                nuevo_cliente.estado = "Activo"
                nuevo_cliente.id_empresa = id_empresa_val
                nuevo_cliente.save()
                id_cliente = nuevo_cliente.id
            else:
                raise ValueError("Se requiere especificar el cliente para emitir la factura.")

        # Resolver id_metodo_pago
        id_metodo = data.get("id_metodo_pago")
        if id_metodo:
            try:
                id_metodo = int(id_metodo)
            except (ValueError, TypeError):
                id_metodo = 1
        elif data.get("metodo_pago"):
            nom_mp = str(data.get("metodo_pago")).strip()
            from src.models.metodos_pago import MetodosPago
            metodos_disponibles = MetodosPago.get_query().filter(
                (MetodosPago.id_empresa == None) | (MetodosPago.id_empresa == id_empresa_val)
            ).all()
            match = next((m for m in metodos_disponibles if m.nombre.lower() == nom_mp.lower()), None)
            if match:
                id_metodo = match.id
            elif "tarjet" in nom_mp.lower():
                id_metodo = 2
            elif "transf" in nom_mp.lower() or "nequi" in nom_mp.lower() or "davi" in nom_mp.lower():
                id_metodo = 3
            else:
                id_metodo = 1
        else:
            id_metodo = 1

        factura = Facturas()
        factura.numero = str(numero).strip()
        factura.fecha = fecha_factura
        factura.subtotal = subtotal
        factura.iva = iva
        factura.descuento = descuento
        factura.total = data.get("total", total)
        factura.estado = data.get("estado", "Emitida")
        factura.id_cliente = int(id_cliente)
        factura.id_usuario = int(data.get("id_usuario") or 1)
        factura.id_metodo_pago = int(id_metodo or 1)
        factura.id_empresa = id_empresa_val
        factura.pasarela = data.get("pasarela")
        factura.referencia_pago = data.get("referencia_pago")
        
        factura.create()

        # Guardar ítems de DetalleFacturas y descontar stock si vienen en la petición
        detalles = data.get("detalles") or data.get("items") or []
        for item in detalles:
            try:
                id_prod = int(item.get("id_producto"))
                cant = int(item.get("cantidad", 1))
                prec = float(item.get("precio_unitario", 0))
                sub_item = float(item.get("subtotal", cant * prec))

                det = DetalleFacturas()
                det.id_factura = factura.id
                det.id_producto = id_prod
                det.cantidad = cant
                det.precio_unitario = prec
                det.subtotal = sub_item
                session.add(det)

                # Actualizar stock de inventario
                prod = Productos.get_by_id(id_prod)
                if prod:
                    prod.stock = max(0, (prod.stock or 0) - cant)
                    session.add(prod)
            except Exception as e:
                print(f"Error al guardar detalle de factura o actualizar stock: {str(e)}")

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
        if "estado" in data:
            factura.estado = data["estado"]
        factura.subtotal = subtotal
        factura.iva = iva
        factura.descuento = descuento
        factura.total = data.get("total", total)
        factura.id_cliente = int(data.get("id_cliente", factura.id_cliente))
        factura.id_usuario = int(data.get("id_usuario", factura.id_usuario))
        factura.id_metodo_pago = int(data.get("id_metodo_pago", factura.id_metodo_pago))
        if "pasarela" in data:
            factura.pasarela = data["pasarela"]
        if "referencia_pago" in data:
            factura.referencia_pago = data["referencia_pago"]
        
        factura.update()
        return factura

    @staticmethod
    def registrar_pago_pasarela(id, pasarela="wompi", referencia_pago=None, id_metodo_pago=None):
        factura = Facturas.get_by_id(id)
        if not factura:
            return None
        factura.estado = "Pagada"
        factura.pasarela = str(pasarela or "wompi")
        factura.referencia_pago = str(referencia_pago or f"TXN-{int(datetime.now().timestamp())}")
        if id_metodo_pago:
            factura.id_metodo_pago = int(id_metodo_pago)
        factura.update()
        return factura

    @staticmethod
    def cancelar(id):
        """Cancela la factura emitida y restaura el stock de productos vendidos."""
        factura = Facturas.get_by_id(id)
        if not factura:
            return None

        factura.estado = "Cancelada"
        
        # Revertir stock de productos
        detalles_db = session.query(DetalleFacturas).filter_by(id_factura=id).all()
        for det in detalles_db:
            prod = Productos.get_by_id(det.id_producto)
            if prod:
                prod.stock = (prod.stock or 0) + det.cantidad
                session.add(prod)

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