from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models.mysql_models import Usuario


def rol_requerido(*roles_permitidos):
    """
    Decorador para verificar que el usuario tenga uno de los roles permitidos.
    
    Uso:
        @bp.route('/inventario')
        @rol_requerido('gerente', 'farmaceutico')
        def ver_inventario():
            ...
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Verificar JWT
            verify_jwt_in_request()
            
            # Obtener identidad del usuario
            usuario_id = get_jwt_identity()
            
            # Buscar usuario en la base de datos
            usuario = Usuario.query.get(usuario_id)
            
            if not usuario:
                return jsonify({
                    'error': 'Usuario no encontrado'
                }), 404
            
            if not usuario.activo:
                return jsonify({
                    'error': 'Usuario inactivo'
                }), 403
            
            # Verificar rol
            if usuario.rol not in roles_permitidos:
                return jsonify({
                    'error': 'No tiene permisos para acceder a este recurso',
                    'rol_requerido': list(roles_permitidos),
                    'rol_actual': usuario.rol
                }), 403
            
            # Pasar el usuario a la función
            return fn(usuario=usuario, *args, **kwargs)
        
        return wrapper
    return decorator


# Decoradores específicos por rol
def solo_gerente(fn):
    """Solo gerentes pueden acceder"""
    return rol_requerido('gerente')(fn)


def gerente_o_farmaceutico(fn):
    """Gerentes y farmacéuticos pueden acceder"""
    return rol_requerido('gerente', 'farmaceutico')(fn)


def cualquier_usuario_autenticado(fn):
    """Cualquier usuario autenticado puede acceder"""
    return rol_requerido('gerente', 'farmaceutico', 'investigador')(fn)