from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token, get_jwt
from src.controllers.auth_controller import AuthController
from src.models.usuarios import Usuarios
from src.models.roles import Roles
from src.models.usuario_empresas import UsuarioEmpresas
from datetime import timedelta

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json() or {}
        email_or_username = data.get("email") or data.get("username")
        password = data.get("password")

        resultado, status_code = AuthController.login(email_or_username, password)
        return jsonify(resultado), status_code
    except Exception as e:
        print(f"Error en /api/auth/login: {str(e)}")
        return jsonify({"exito": False, "mensaje": f"Error interno en el servidor: {str(e)}"}), 500

@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    try:
        identity = get_jwt_identity()
        claims = get_jwt() or {}
        
        user_id = int(identity) if identity else None
        usuario = Usuarios.get_by_id(user_id) if user_id else None
        
        if usuario:
            rol = Roles.get_by_id(usuario.id_rol)
            nombre_rol = rol.nombre if rol else "Usuario"
            relaciones_empresa = UsuarioEmpresas.get_by_usuario_id(usuario.id)
            empresas_ids = [rel.empresa_id for rel in relaciones_empresa]

            user_claims = {
                "usuario_id": usuario.id,
                "username": usuario.username,
                "email": usuario.email,
                "rol": nombre_rol,
                "id_rol": usuario.id_rol,
                "empresas": empresas_ids
            }
        else:
            user_claims = {
                "usuario_id": claims.get("usuario_id"),
                "username": claims.get("username"),
                "email": claims.get("email"),
                "rol": claims.get("rol"),
                "id_rol": claims.get("id_rol"),
                "empresas": claims.get("empresas", [])
            }
        
        nuevo_access_token = create_access_token(
            identity=str(identity),
            additional_claims=user_claims,
            expires_delta=timedelta(hours=2)
        )
        return jsonify({"exito": True, "access_token": nuevo_access_token}), 200
    except Exception as e:
        return jsonify({"exito": False, "mensaje": f"No se pudo refrescar el token: {str(e)}"}), 400

@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    try:
        current_user_id = get_jwt_identity()
        resultado, status_code = AuthController.get_user_profile(current_user_id)
        return jsonify(resultado), status_code
    except Exception as e:
        return jsonify({"mensaje": f"Error al obtener perfil: {str(e)}"}), 500
