from src.models import session
from src.models.usuario_empresas import UsuarioEmpresas
from src.models.usuarios import Usuarios

class UsuarioEmpresasController:

    @staticmethod
    def get():
        return UsuarioEmpresas.get()

    @staticmethod
    def get_by_usuario_empresa(usuario_id, empresa_id):
        vinculacion = UsuarioEmpresas.get_by_usuario_empresa(usuario_id, empresa_id)
        if not vinculacion:
            usuario = Usuarios.get_by_id(usuario_id)
            rol_defecto = usuario.id_rol if usuario else 2
            return {
                "usuario_id": usuario_id,
                "empresa_id": empresa_id,
                "rol_id": rol_defecto,
                "estado": "No Vinculado"
            }
        return vinculacion.to_dict()

    @staticmethod
    def actualizar_vinculacion(usuario_id, empresa_id, estado=None, rol_id=None):
        vinculacion = UsuarioEmpresas.get_by_usuario_empresa(usuario_id, empresa_id)
        if not vinculacion:
            usuario = Usuarios.get_by_id(usuario_id)
            rol_defecto = usuario.id_rol if usuario else 2

            vinculacion = UsuarioEmpresas()
            vinculacion.usuario_id = usuario_id
            vinculacion.empresa_id = empresa_id
            vinculacion.rol_id = int(rol_id) if rol_id is not None else rol_defecto
            vinculacion.estado = estado if estado is not None else "Activo"
            session.add(vinculacion)
            session.commit()
        else:
            if estado is not None:
                vinculacion.estado = str(estado)
            if rol_id is not None:
                vinculacion.rol_id = int(rol_id)
            session.add(vinculacion)
            session.commit()

        return vinculacion.to_dict()
