from datetime import datetime
from src.models.clientes import Clientes
from src.models import session
from src.utils.pagination import paginate_query


class ClientesController:

    @staticmethod
    def get(empresa_id=None):
        if not empresa_id:
            return []
        eid = int(empresa_id)
        return Clientes.get_query().filter(Clientes.id_empresa == eid).all()

    @staticmethod
    def get_paginated(page=1, per_page=10, empresa_id=None):
        query = Clientes.get_query()
        if empresa_id:
            eid = int(empresa_id)
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
        if not doc_input:
            raise ValueError("El documento del cliente es obligatorio.")

        emp_id = data.get("id_empresa") or data.get("empresa_id")
        if not emp_id:
            raise ValueError("El identificador de empresa ('id_empresa') es obligatorio para registrar un cliente.")
        eid = int(emp_id)

        cliente_existente = Clientes.get_by_documento(doc_input, empresa_id=eid)
        if cliente_existente:
            cliente_existente.nombre = data.get("nombre") or cliente_existente.nombre
            if hasattr(cliente_existente, 'apellido') and data.get("apellido") is not None:
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
        cliente.nombre = str(data.get("nombre") or "").strip()
        if not cliente.nombre:
            raise ValueError("El nombre del cliente es obligatorio.")
        cliente.apellido = str(data.get("apellido") or "").strip()
        cliente.direccion = str(data.get("direccion") or "").strip()
        cliente.telefono = str(data.get("telefono") or "").strip()
        email_cand = str(data.get("email") or "").strip()
        if not email_cand:
            email_cand = f"cli_{doc_input}_{eid}@correo.com"
        cliente.email = email_cand
        cliente.tipo_documento = data.get("tipo_documento", "CC")
        cliente.estado = data.get("estado", "Activo")
        cliente.id_empresa = eid

        if data.get("codigo"):
            cliente.codigo = data.get("codigo")
        else:
            count = session.query(Clientes).filter(Clientes.id_empresa == eid).count()
            cliente.codigo = f"CLI-E{eid}-{count + 1:03d}"

        try:
            cliente.save()
        except Exception:
            session.rollback()
            cliente.documento = f"{doc_input}#E{eid}"
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
        cliente.estado = "Inactivo"
        cliente.update()
        return True
