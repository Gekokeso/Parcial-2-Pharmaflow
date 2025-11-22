from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from bson import ObjectId
from datetime import datetime
from app import get_mongo_db
from app.middleware.auth_middleware import cualquier_usuario_autenticado, gerente_o_farmaceutico

bp = Blueprint('ensayos', __name__, url_prefix='/api/ensayos')


def serialize_mongo_doc(doc):
    """Convierte ObjectId a string para JSON"""
    if doc:
        doc['_id'] = str(doc['_id'])
        # Convertir fechas a ISO format
        for key, value in doc.items():
            if isinstance(value, datetime):
                doc[key] = value.isoformat()
            elif isinstance(value, list):
                doc[key] = [serialize_mongo_doc(item) if isinstance(item, dict) else item for item in value]
            elif isinstance(value, dict):
                doc[key] = serialize_mongo_doc(value)
    return doc


@bp.route('/', methods=['GET'])
@cualquier_usuario_autenticado
def listar_ensayos(usuario):
    """
    Listar todos los ensayos clínicos.
    
    Query params:
    - fase: Filtrar por fase (1, 2, 3)
    - estado: Filtrar por estado (en_curso, reclutamiento, completado)
    - farmaco: Buscar por nombre de fármaco
    """
    try:
        mongo_db = get_mongo_db()
        collection = mongo_db.ensayos_clinicos
        
        # Construir filtro
        filtro = {}
        
        if request.args.get('fase'):
            filtro['fase'] = int(request.args.get('fase'))
        
        if request.args.get('estado'):
            filtro['estado'] = request.args.get('estado')
        
        if request.args.get('farmaco'):
            filtro['farmaco'] = {'$regex': request.args.get('farmaco'), '$options': 'i'}
        
        # Ejecutar consulta
        ensayos = list(collection.find(filtro))
        
        # Serializar resultados
        ensayos_serializados = [serialize_mongo_doc(e) for e in ensayos]
        
        return jsonify({
            'total': len(ensayos_serializados),
            'ensayos': ensayos_serializados
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<ensayo_id>', methods=['GET'])
@cualquier_usuario_autenticado
def obtener_ensayo(usuario, ensayo_id):
    """Obtener un ensayo clínico por ID"""
    try:
        mongo_db = get_mongo_db()
        collection = mongo_db.ensayos_clinicos
        
        ensayo = collection.find_one({'_id': ObjectId(ensayo_id)})
        
        if not ensayo:
            return jsonify({'error': 'Ensayo no encontrado'}), 404
        
        return jsonify(serialize_mongo_doc(ensayo)), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/', methods=['POST'])
@gerente_o_farmaceutico
def crear_ensayo(usuario):
    """
    Crear un nuevo ensayo clínico.
    
    Body: (ejemplo simplificado)
    {
        "codigo_ensayo": "string",
        "farmaco": "string",
        "principio_activo": "string",
        "fase": int,
        "fecha_inicio": "ISO date",
        "fecha_fin_estimada": "ISO date",
        "estado": "string",
        "objetivo_principal": "string",
        "criterios_inclusion": {...},
        "centros_participantes": [...],
        "resultados_intermedios": {...}
    }
    """
    try:
        data = request.get_json()
        
        # Validaciones básicas
        campos_requeridos = ['codigo_ensayo', 'farmaco', 'fase', 'estado']
        if not all(k in data for k in campos_requeridos):
            return jsonify({'error': 'Faltan campos requeridos'}), 400
        
        # Agregar metadata
        data['metadata'] = {
            'creado_por': usuario.username,
            'fecha_creacion': datetime.utcnow(),
            'ultima_modificacion': datetime.utcnow(),
            'version_documento': 1
        }
        
        # Convertir fechas string a datetime
        if 'fecha_inicio' in data:
            data['fecha_inicio'] = datetime.fromisoformat(data['fecha_inicio'].replace('Z', '+00:00'))
        if 'fecha_fin_estimada' in data:
            data['fecha_fin_estimada'] = datetime.fromisoformat(data['fecha_fin_estimada'].replace('Z', '+00:00'))
        
        # Insertar en MongoDB
        mongo_db = get_mongo_db()
        collection = mongo_db.ensayos_clinicos
        
        resultado = collection.insert_one(data)
        
        # Recuperar el documento insertado
        ensayo_creado = collection.find_one({'_id': resultado.inserted_id})
        
        return jsonify({
            'mensaje': 'Ensayo clínico creado exitosamente',
            'ensayo': serialize_mongo_doc(ensayo_creado)
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<ensayo_id>', methods=['PUT'])
@gerente_o_farmaceutico
def actualizar_ensayo(usuario, ensayo_id):
    """
    Actualizar un ensayo clínico existente.
    
    Body: Campos a actualizar
    """
    try:
        data = request.get_json()
        
        # Actualizar metadata
        data['metadata.ultima_modificacion'] = datetime.utcnow()
        data['metadata.modificado_por'] = usuario.username
        
        mongo_db = get_mongo_db()
        collection = mongo_db.ensayos_clinicos
        
        # Actualizar documento
        resultado = collection.update_one(
            {'_id': ObjectId(ensayo_id)},
            {'$set': data, '$inc': {'metadata.version_documento': 1}}
        )
        
        if resultado.matched_count == 0:
            return jsonify({'error': 'Ensayo no encontrado'}), 404
        
        # Recuperar documento actualizado
        ensayo_actualizado = collection.find_one({'_id': ObjectId(ensayo_id)})
        
        return jsonify({
            'mensaje': 'Ensayo actualizado exitosamente',
            'ensayo': serialize_mongo_doc(ensayo_actualizado)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<ensayo_id>', methods=['DELETE'])
@gerente_o_farmaceutico
def eliminar_ensayo(usuario, ensayo_id):
    """Eliminar (archivar) un ensayo clínico"""
    try:
        mongo_db = get_mongo_db()
        collection = mongo_db.ensayos_clinicos
        
        # En lugar de eliminar, marcar como archivado
        resultado = collection.update_one(
            {'_id': ObjectId(ensayo_id)},
            {'$set': {
                'estado': 'archivado',
                'metadata.archivado_por': usuario.username,
                'metadata.fecha_archivado': datetime.utcnow()
            }}
        )
        
        if resultado.matched_count == 0:
            return jsonify({'error': 'Ensayo no encontrado'}), 404
        
        return jsonify({'mensaje': 'Ensayo archivado exitosamente'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<ensayo_id>/efectos-secundarios', methods=['POST'])
@gerente_o_farmaceutico
def agregar_efecto_secundario(usuario, ensayo_id):
    """
    Agregar un efecto secundario a un ensayo.
    
    Body:
    {
        "tipo": "string",
        "frecuencia": "string",
        "severidad": "string",
        "duracion_promedio": "string"
    }
    """
    try:
        data = request.get_json()
        
        mongo_db = get_mongo_db()
        collection = mongo_db.ensayos_clinicos
        
        resultado = collection.update_one(
            {'_id': ObjectId(ensayo_id)},
            {
                '$push': {
                    'resultados_intermedios.efectos_secundarios_frecuentes': data
                },
                '$set': {
                    'metadata.ultima_modificacion': datetime.utcnow()
                }
            }
        )
        
        if resultado.matched_count == 0:
            return jsonify({'error': 'Ensayo no encontrado'}), 404
        
        return jsonify({'mensaje': 'Efecto secundario agregado'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/busqueda/avanzada', methods=['POST'])
@cualquier_usuario_autenticado
def busqueda_avanzada(usuario):
    """
    Búsqueda avanzada con múltiples criterios.
    
    Body:
    {
        "fase": [1, 2, 3],
        "estado": ["en_curso", "reclutamiento"],
        "edad_minima": int,
        "edad_maxima": int,
        "condiciones": ["hipertension", "diabetes"]
    }
    """
    try:
        criterios = request.get_json()
        
        mongo_db = get_mongo_db()
        collection = mongo_db.ensayos_clinicos
        
        # Construir query compleja
        query = {}
        
        if 'fase' in criterios:
            query['fase'] = {'$in': criterios['fase']}
        
        if 'estado' in criterios:
            query['estado'] = {'$in': criterios['estado']}
        
        if 'edad_minima' in criterios:
            query['criterios_inclusion.edad_minima'] = {'$lte': criterios['edad_minima']}
        
        if 'condiciones' in criterios:
            query['criterios_inclusion.condiciones_medicas'] = {
                '$in': criterios['condiciones']
            }
        
        resultados = list(collection.find(query))
        
        return jsonify({
            'total': len(resultados),
            'ensayos': [serialize_mongo_doc(e) for e in resultados]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/estadisticas', methods=['GET'])
@cualquier_usuario_autenticado
def estadisticas_ensayos(usuario):
    """Estadísticas generales de ensayos clínicos"""
    try:
        mongo_db = get_mongo_db()
        collection = mongo_db.ensayos_clinicos
        
        # Agregación con pipeline
        pipeline = [
            {
                '$group': {
                    '_id': '$estado',
                    'total': {'$sum': 1},
                    'fase_promedio': {'$avg': '$fase'}
                }
            }
        ]
        
        estadisticas = list(collection.aggregate(pipeline))
        
        # Total general
        total_ensayos = collection.count_documents({})
        
        return jsonify({
            'total_ensayos': total_ensayos,
            'por_estado': estadisticas
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500