from src.models.proveedores import Proveedores
from src.models import session
from src.utils.pagination import paginate_query


class ProveedoresController:

    @staticmethod
    def get(empresa_id=None):
        if not empresa_id:
            return []
        return Proveedores.get_query().filter(Proveedores.id_empresa == int(empresa_id)).all()

    @staticmethod
    def get_paginated(page=1, per_page=10, empresa_id=None):
        query = Proveedores.get_query()
        if empresa_id:
            query = query.filter(Proveedores.id_empresa == int(empresa_id))
        else:
            return paginate_query(query.filter(Proveedores.id_empresa == -1), page, per_page)
        return paginate_query(query, page, per_page)

    @staticmethod
    def get_by_id(id):
        return Proveedores.get_by_id(id)

    @staticmethod
    def obtener_siguiente_codigo(empresa_id=None):
        eid = int(empresa_id) if empresa_id else 1
        prefix = f"PROV-E{eid}-"
        proveedores = session.query(Proveedores).filter(Proveedores.id_empresa == eid).all()
        max_num = 0
        for p in proveedores:
            cod = getattr(p, "codigo", None)
            if cod:
                if cod.startswith(prefix):
                    try:
                        num = int(cod.replace(prefix, "").strip())
                        if num > max_num:
                            max_num = num
                    except ValueError:
                        pass
                elif "PROV-" in cod:
                    try:
                        num = int(cod.split("-")[-1].strip())
                        if num > max_num:
                            max_num = num
                    except ValueError:
                        pass
            elif p.id and p.id > max_num:
                max_num = p.id
        siguiente = max_num + 1
        return f"{prefix}{siguiente:03d}"

    @staticmethod
    def create(data):
        emp_id = data.get("id_empresa") or data.get("empresa_id")
        if not emp_id:
            raise ValueError("El identificador de empresa ('id_empresa') es obligatorio para registrar un proveedor.")
        eid = int(emp_id)

        nit = str(data.get("nit") or "").strip()
        if not nit:
            raise ValueError("El NIT del proveedor es obligatorio.")

        # Validar unicidad de NIT dentro de la misma empresa
        dup_nit = session.query(Proveedores).filter(
            Proveedores.id_empresa == eid,
            Proveedores.nit == nit
        ).first()
        if dup_nit:
            raise ValueError(f"Ya existe un proveedor con el NIT '{nit}' en esta empresa.")

        proveedor = Proveedores()
        proveedor.nit = nit
        proveedor.nombre = str(data.get("nombre") or "").strip()
        if not proveedor.nombre:
            raise ValueError("El nombre o razón social del proveedor es obligatorio.")
        proveedor.contacto = str(data.get("contacto") or "").strip()
        proveedor.telefono = str(data.get("telefono") or "").strip()
        proveedor.direccion = str(data.get("direccion") or "").strip()
        proveedor.email = str(data.get("email") or "").strip()
        proveedor.detalle_servicios = str(data.get("detalle_servicios") or "").strip()
        proveedor.estado = data.get("estado", "Activo")
        proveedor.id_empresa = eid

        if data.get("codigo"):
            proveedor.codigo = data.get("codigo")
        else:
            proveedor.codigo = ProveedoresController.obtener_siguiente_codigo(eid)

        proveedor.save()
        return proveedor

    @staticmethod
    def update(id, data):
        proveedor = Proveedores.get_by_id(id)
        if proveedor is None:
            return None

        if "nit" in data and str(data["nit"]).strip():
            nuevo_nit = str(data["nit"]).strip()
            if nuevo_nit != proveedor.nit and proveedor.id_empresa:
                dup = session.query(Proveedores).filter(
                    Proveedores.id_empresa == proveedor.id_empresa,
                    Proveedores.nit == nuevo_nit,
                    Proveedores.id != proveedor.id
                ).first()
                if dup:
                    raise ValueError(f"Ya existe otro proveedor con el NIT '{nuevo_nit}' en esta empresa.")
            proveedor.nit = nuevo_nit

        proveedor.nombre = data.get("nombre", proveedor.nombre)
        if hasattr(proveedor, 'contacto'):
            proveedor.contacto = data.get("contacto", getattr(proveedor, 'contacto', ''))
        proveedor.telefono = data.get("telefono", proveedor.telefono)
        proveedor.direccion = data.get("direccion", proveedor.direccion)
        proveedor.email = data.get("email", proveedor.email)
        proveedor.detalle_servicios = data.get("detalle_servicios", proveedor.detalle_servicios)
        if "estado" in data:
            proveedor.estado = data["estado"]
        proveedor.update()
        return proveedor

    @staticmethod
    def desactivar(id, estado="Inactivo"):
        proveedor = Proveedores.get_by_id(id)
        if proveedor is None:
            return None
        proveedor.estado = estado
        proveedor.update()
        return proveedor

    @staticmethod
    def delete(id):
        proveedor = Proveedores.get_by_id(id)
        if proveedor is None:
            return False
        proveedor.estado = "Inactivo"
        proveedor.update()
        return True
