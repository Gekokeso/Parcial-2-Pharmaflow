from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
from app.models.mysql_models import db, Usuario
from app import get_redis_client

bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@bp.route('/register', methods=['POST'])
def register():
    """
    Registrar un nuevo usuario.
    
    Body:
    {
        "username": "string",
        "email": "string", 
        "password": "string",
        "rol": "gerente|farmaceutico|investigador"
    }
    """
    try:
        data = request.get_json()
        
        # Verificar que data no sea None
        if not data:
            return jsonify({'error': 'No se proporcionó JSON en el body'}), 400
        
        # Validaciones
        if not all(k in data for k in ('username', 'email', 'password', 'rol')):
            return jsonify({'error': 'Faltan campos requeridos: username, email, password, rol'}), 400
        
        # Validar que los campos no estén vacíos
        if not data['username'] or not data['email'] or not data['password'] or not data['rol']:
            return jsonify({'error': 'Los campos no pueden estar vacíos'}), 400
        
        if data['rol'] not in ['gerente', 'farmaceutico', 'investigador']:
            return jsonify({'error': 'Rol inválido. Debe ser: gerente, farmaceutico o investigador'}), 400
        
        # Verificar si el usuario ya existe
        if Usuario.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'El usuario ya existe'}), 409
        
        if Usuario.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'El email ya está registrado'}), 409
        
        # Crear nuevo usuario
        nuevo_usuario = Usuario(
            username=data['username'],
            email=data['email'],
            rol=data['rol']
        )
        nuevo_usuario.set_password(data['password'])
        
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Usuario registrado exitosamente',
            'usuario': nuevo_usuario.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/login', methods=['POST'])
def login():
    """
    Iniciar sesión y obtener token JWT.
    
    Body:
    {
        "username": "string",
        "password": "string"
    }
    """
    try:
        data = request.get_json()
        
        if not all(k in data for k in ('username', 'password')):
            return jsonify({'error': 'Faltan username o password'}), 400
        
        # Buscar usuario
        usuario = Usuario.query.filter_by(username=data['username']).first()
        
        if not usuario or not usuario.check_password(data['password']):
            return jsonify({'error': 'Credenciales inválidas'}), 401
        
        if not usuario.activo:
            return jsonify({'error': 'Usuario inactivo'}), 403
        
        # Crear token JWT
        access_token = create_access_token(
            identity=usuario.id,
            expires_delta=timedelta(hours=8),
            additional_claims={'rol': usuario.rol}
        )
        
        # Guardar sesión en Redis
        redis_client = get_redis_client()
        session_key = f"session:{usuario.id}"
        redis_client.setex(
            session_key,
            timedelta(hours=8),
            usuario.username
        )
        
        return jsonify({
            'mensaje': 'Login exitoso',
            'access_token': access_token,
            'usuario': usuario.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Cerrar sesión (eliminar de Redis).
    """
    try:
        usuario_id = get_jwt_identity()
        
        # Eliminar sesión de Redis
        redis_client = get_redis_client()
        session_key = f"session:{usuario_id}"
        redis_client.delete(session_key)
        
        return jsonify({'mensaje': 'Logout exitoso'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Obtener información del usuario actual.
    """
    try:
        usuario_id = get_jwt_identity()
        usuario = Usuario.query.get(usuario_id)
        
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        return jsonify(usuario.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/usuarios', methods=['GET'])
@jwt_required()
def listar_usuarios():
    """
    Listar todos los usuarios (solo para gerentes).
    """
    try:
        usuario_id = get_jwt_identity()
        usuario_actual = Usuario.query.get(usuario_id)
        
        if usuario_actual.rol != 'gerente':
            return jsonify({'error': 'No autorizado'}), 403
        
        usuarios = Usuario.query.all()
        return jsonify([u.to_dict() for u in usuarios]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500