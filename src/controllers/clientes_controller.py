from src.models.clientes import Clientes
from src.models import session
from src.utils.pagination import paginate_query

class ClientesController:

    @staticmethod
    def get(empresa_id=None):
        query = Clientes.get_query()
        if empresa_id:
            eid = int(empresa_id)
            if eid == 1:
                query = query.filter((Clientes.id_empresa == eid) | (Clientes.id_empresa == None))
            else:
                query = query.filter(Clientes.id_empresa == eid)
        else:
            return []
        return query.all()

    @staticmethod
    def get_paginated(page=1, per_page=10, empresa_id=None):
        query = Clientes.get_query()
        if empresa_id:
            eid = int(empresa_id)
            if eid == 1:
                query = query.filter((Clientes.id_empresa == eid) | (Clientes.id_empresa == None))
            else:
                query = query.filter(Clientes.id_empresa == eid)
        else:
            return paginate_query(query.filter(Clientes.id_empresa == -1), page, per_page)
        return paginate_query(query, page, per_page)

    @staticmethod
    def get_by_id(id):
        return Clientes.get_by_id(id)

    @staticmethod
    def create(data):
        doc_input = str(data.get("documento", "")).strip()
        emp_id = data.get("id_empresa") or data.get("empresa_id") or 1
        eid = int(emp_id)

        # Si ya existe un cliente con este documento, actualizarlo y vincularlo a la empresa activa
        if doc_input:
            cliente_existente = session.query(Clientes).filter(Clientes.documento == doc_input).first()
            if cliente_existente:
                cliente_existente.nombre = data.get("nombre") or cliente_existente.nombre
                if hasattr(cliente_existente, 'apellido') and data.get("apellido"):
                    cliente_existente.apellido = data.get("apellido")
                cliente_existente.direccion = data.get("direccion") or cliente_existente.direccion
                cliente_existente.telefono = data.get("telefono") or cliente_existente.telefono
                if data.get("email"):
                    cliente_existente.email = data.get("email")
                cliente_existente.tipo_documento = data.get("tipo_documento", getattr(cliente_existente, 'tipo_documento', 'CC'))
                cliente_existente.id_empresa = eid
                cliente_existente.estado = "Activo"
                cliente_existente.update()
                return cliente_existente

        cliente = Clientes()
        cliente.documento = doc_input
        cliente.nombre = data.get("nombre", "")
        if hasattr(cliente, 'apellido'):
            cliente.apellido = data.get("apellido", "")
        cliente.direccion = data.get("direccion", "")
        cliente.telefono = data.get("telefono", "")
        email_cand = data.get("email", "")
        if not email_cand:
            email_cand = f"cli_{doc_input}_{eid}@correo.com"
        cliente.email = email_cand
        cliente.tipo_documento = data.get("tipo_documento", "CC")
        cliente.estado = data.get("estado", "Activo")
        cliente.id_empresa = eid
        
        # Generar código correlativo por empresa CLI-E{empresa_id}-{consecutivo:03d}
        if data.get("codigo"):
            cliente.codigo = data.get("codigo")
        else:
            count = session.query(Clientes).filter(Clientes.id_empresa == eid).count()
            cliente.codigo = f"CLI-E{eid}-{count + 1:03d}"
        
        cliente.tiene_tarjeta = data.get("tiene_tarjeta", "No")
        cliente.tipo_tarjeta = data.get("tipo_tarjeta")
        cliente.banco_tarjeta = data.get("banco_tarjeta")
        cliente.franquicia_tarjeta = data.get("franquicia_tarjeta")
        # Por seguridad PCI-DSS, nunca guardar número completo ni CVC. Extraer únicamente últimos 4 dígitos.
        raw_card = str(data.get("numero_tarjeta") or data.get("ultimos_digitos_tarjeta") or "").strip()
        cliente.ultimos_digitos_tarjeta = raw_card[-4:] if len(raw_card) >= 4 else raw_card
        cliente.numero_tarjeta = None
        cliente.titular_tarjeta = data.get("titular_tarjeta")
        cliente.fecha_expiracion = None
        cliente.cvc_tarjeta = None

        from datetime import datetime
        try:
            cliente.save()
        except Exception:
            session.rollback()
            cliente.email = f"cli_{doc_input}_{eid}_{int(datetime.now().timestamp())}@correo.com"
            cliente.save()

        return cliente

    @staticmethod
    def update(id, data):
        cliente = Clientes.get_by_id(id)

        if cliente is None:
            return None

        cliente.documento = data.get("documento", cliente.documento)
        cliente.nombre = data.get("nombre", cliente.nombre)
        if hasattr(cliente, 'apellido'):
            cliente.apellido = data.get("apellido", getattr(cliente, 'apellido', ''))
        cliente.direccion = data.get("direccion", cliente.direccion)
        cliente.telefono = data.get("telefono", cliente.telefono)
        cliente.email = data.get("email", cliente.email)
        if "tipo_documento" in data:
            cliente.tipo_documento = data["tipo_documento"]
        if "estado" in data:
            cliente.estado = data["estado"]
        
        if "tiene_tarjeta" in data:
            cliente.tiene_tarjeta = data["tiene_tarjeta"]
        if "tipo_tarjeta" in data:
            cliente.tipo_tarjeta = data["tipo_tarjeta"]
        if "banco_tarjeta" in data:
            cliente.banco_tarjeta = data["banco_tarjeta"]
        if "franquicia_tarjeta" in data:
            cliente.franquicia_tarjeta = data["franquicia_tarjeta"]
        if "ultimos_digitos_tarjeta" in data or "numero_tarjeta" in data:
            raw_c = str(data.get("numero_tarjeta") or data.get("ultimos_digitos_tarjeta") or "").strip()
            cliente.ultimos_digitos_tarjeta = raw_c[-4:] if len(raw_c) >= 4 else raw_c
            cliente.numero_tarjeta = None
        if "titular_tarjeta" in data:
            cliente.titular_tarjeta = data["titular_tarjeta"]
        cliente.cvc_tarjeta = None
        cliente.fecha_expiracion = None

        cliente.update()
        return cliente

    @staticmethod
    def desactivar(id, estado="Inactivo"):
        cliente = Clientes.get_by_id(id)
        if cliente is None:
            return None
        cliente.estado = estado
        cliente.update()
        return cliente

    @staticmethod
    def buscar_por_documento(documento, empresa_id=None):
        return Clientes.get_by_documento(documento, empresa_id=empresa_id)

    @staticmethod
    def delete(id):
        cliente = Clientes.get_by_id(id)
        if cliente is None:
            return False
        # Desactivación lógica (Soft-Delete) para proteger facturas e histórico
        cliente.estado = "Inactivo"
        cliente.update()
        return True

