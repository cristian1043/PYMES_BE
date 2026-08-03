from src.models.usuario_empresas import UsuarioEmpresas

class UsuarioEmpresasController:

    @staticmethod
    def get():
        return UsuarioEmpresas.get()

    @staticmethod
    def get_by_usuario_empresa(usuario_id, empresa_id):
        vinculacion = UsuarioEmpresas.get_by_usuario_empresa(usuario_id, empresa_id)
        if not vinculacion:
            # Si no existe registro aún en la base de datos, retornar vinculación activa por defecto
            return {
                "usuario_id": usuario_id,
                "empresa_id": empresa_id,
                "rol_id": 2,
                "estado": "Activo"
            }
        return vinculacion.to_dict()

    @staticmethod
    def actualizar_estado(usuario_id, empresa_id, estado, rol_id=None):
        vinculacion = UsuarioEmpresas.get_by_usuario_empresa(usuario_id, empresa_id)
        if not vinculacion:
            vinculacion = UsuarioEmpresas()
            vinculacion.usuario_id = usuario_id
            vinculacion.empresa_id = empresa_id
            vinculacion.rol_id = rol_id if rol_id else 2
            vinculacion.estado = estado
            vinculacion.save()
        else:
            vinculacion.estado = estado
            if rol_id:
                vinculacion.rol_id = rol_id
            vinculacion.update()
            
        return vinculacion.to_dict()
