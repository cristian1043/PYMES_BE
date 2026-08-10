from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token, get_jwt
from src.controllers.auth_controller import AuthController

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
        claims = get_jwt()
        
        nuevo_access_token = create_access_token(
            identity=identity,
            additional_claims={
                "usuario_id": claims.get("usuario_id"),
                "username": claims.get("username"),
                "email": claims.get("email"),
                "rol": claims.get("rol"),
                "id_rol": claims.get("id_rol"),
                "empresas": claims.get("empresas", [])
            }
        )
        return jsonify({"access_token": nuevo_access_token}), 200
    except Exception as e:
        return jsonify({"mensaje": f"No se pudo refrescar el token: {str(e)}"}), 400

@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    try:
        current_user_id = get_jwt_identity()
        resultado, status_code = AuthController.get_user_profile(current_user_id)
        return jsonify(resultado), status_code
    except Exception as e:
        return jsonify({"mensaje": f"Error al obtener perfil: {str(e)}"}), 500
