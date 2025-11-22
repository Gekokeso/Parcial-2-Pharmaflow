from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import get_neo4j_driver
from app.middleware.auth_middleware import cualquier_usuario_autenticado

bp = Blueprint('interacciones', __name__, url_prefix='/api/interacciones')


def ejecutar_query_neo4j(query, parametros=None):
    """Ejecuta una consulta en Neo4j y retorna los resultados"""
    driver = get_neo4j_driver()
    
    with driver.session() as session:
        resultado = session.run(query, parametros or {})
        return [record.data() for record in resultado]


@bp.route('/medicamentos', methods=['GET'])
@cualquier_usuario_autenticado
def listar_medicamentos(usuario):
    """Listar todos los medicamentos del grafo"""
    try:
        query = """
        MATCH (m:Medicamento)
        RETURN m.id as id, m.nombre as nombre, m.nombre_comercial as nombre_comercial,
               m.dosis as dosis, m.laboratorio as laboratorio
        ORDER BY m.nombre
        """
        
        medicamentos = ejecutar_query_neo4j(query)
        
        return jsonify({
            'total': len(medicamentos),
            'medicamentos': medicamentos
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/medicamentos/<medicamento_id>', methods=['GET'])
@cualquier_usuario_autenticado
def obtener_medicamento_detalle(usuario, medicamento_id):
    """Obtener detalles completos de un medicamento con sus relaciones"""
    try:
        query = """
        MATCH (m:Medicamento {id: $medicamento_id})
        OPTIONAL MATCH (pa:PrincipioActivo)-[:COMPONE]->(m)
        OPTIONAL MATCH (c:Compuesto)-[:SE_TRANSFORMA_EN]->(pa)
        OPTIONAL MATCH (m)-[:PERTENECE_A]->(cat:Categoria)
        RETURN m, 
               collect(DISTINCT pa) as principios_activos,
               collect(DISTINCT c) as compuestos,
               collect(DISTINCT cat.nombre) as categorias
        """
        
        resultados = ejecutar_query_neo4j(query, {'medicamento_id': medicamento_id})
        
        if not resultados:
            return jsonify({'error': 'Medicamento no encontrado'}), 404
        
        return jsonify(resultados[0]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/medicamentos/<medicamento_id>/interacciones', methods=['GET'])
@cualquier_usuario_autenticado
def obtener_interacciones_medicamento(usuario, medicamento_id):
    """
    Obtener todas las interacciones de un medicamento específico.
    
    Query params:
    - severidad: Filtrar por severidad (leve, moderada, grave)
    """
    try:
        # Construir filtro de severidad
        filtro_severidad = ""
        if request.args.get('severidad'):
            filtro_severidad = f"AND r.severidad = '{request.args.get('severidad')}'"
        
        query = f"""
        MATCH (m1:Medicamento {{id: $medicamento_id}})-[r:INTERACCIONA_CON]-(m2:Medicamento)
        WHERE 1=1 {filtro_severidad}
        RETURN m1.nombre as medicamento_origen,
               m2.id as medicamento_interaccion_id,
               m2.nombre as medicamento_interaccion,
               m2.nombre_comercial as nombre_comercial,
               r.tipo as tipo_interaccion,
               r.severidad as severidad,
               r.descripcion as descripcion,
               r.recomendaciones as recomendaciones,
               r.nivel_evidencia as nivel_evidencia
        ORDER BY 
            CASE r.severidad 
                WHEN 'grave' THEN 1
                WHEN 'moderada' THEN 2
                WHEN 'leve' THEN 3
                ELSE 4
            END
        """
        
        interacciones = ejecutar_query_neo4j(query, {'medicamento_id': medicamento_id})
        
        return jsonify({
            'total': len(interacciones),
            'interacciones': interacciones
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/verificar-interacciones', methods=['POST'])
@cualquier_usuario_autenticado
def verificar_interacciones_multiples(usuario):
    """
    Verificar interacciones entre múltiples medicamentos.
    
    Body:
    {
        "medicamentos": ["MED001", "MED002", "MED003"]
    }
    """
    try:
        data = request.get_json()
        
        if 'medicamentos' not in data or len(data['medicamentos']) < 2:
            return jsonify({'error': 'Se requieren al menos 2 medicamentos'}), 400
        
        query = """
        MATCH (m1:Medicamento)-[r:INTERACCIONA_CON]-(m2:Medicamento)
        WHERE m1.id IN $medicamentos AND m2.id IN $medicamentos
        RETURN DISTINCT
            m1.id as medicamento_a_id,
            m1.nombre as medicamento_a,
            m2.id as medicamento_b_id,
            m2.nombre as medicamento_b,
            r.severidad as severidad,
            r.descripcion as descripcion,
            r.recomendaciones as recomendaciones
        ORDER BY 
            CASE r.severidad 
                WHEN 'grave' THEN 1
                WHEN 'moderada' THEN 2
                WHEN 'leve' THEN 3
            END
        """
        
        interacciones = ejecutar_query_neo4j(query, {'medicamentos': data['medicamentos']})
        
        # Clasificar por severidad
        interacciones_graves = [i for i in interacciones if i['severidad'] == 'grave']
        interacciones_moderadas = [i for i in interacciones if i['severidad'] == 'moderada']
        interacciones_leves = [i for i in interacciones if i['severidad'] == 'leve']
        
        return jsonify({
            'total_interacciones': len(interacciones),
            'tiene_interacciones_graves': len(interacciones_graves) > 0,
            'resumen': {
                'graves': len(interacciones_graves),
                'moderadas': len(interacciones_moderadas),
                'leves': len(interacciones_leves)
            },
            'interacciones_graves': interacciones_graves,
            'interacciones_moderadas': interacciones_moderadas,
            'interacciones_leves': interacciones_leves
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/principios-activos', methods=['GET'])
@cualquier_usuario_autenticado
def listar_principios_activos(usuario):
    """Listar todos los principios activos"""
    try:
        query = """
        MATCH (pa:PrincipioActivo)
        OPTIONAL MATCH (pa)-[:COMPONE]->(m:Medicamento)
        RETURN pa.id as id,
               pa.nombre as nombre,
               pa.mecanismo_accion as mecanismo_accion,
               pa.indicaciones as indicaciones,
               count(m) as cantidad_medicamentos
        ORDER BY pa.nombre
        """
        
        principios = ejecutar_query_neo4j(query)
        
        return jsonify({
            'total': len(principios),
            'principios_activos': principios
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/compuestos/<compuesto_id>/cadena', methods=['GET'])
@cualquier_usuario_autenticado
def obtener_cadena_compuesto(usuario, compuesto_id):
    """
    Obtener la cadena completa: Compuesto -> Principio Activo -> Medicamentos
    """
    try:
        query = """
        MATCH path = (c:Compuesto {id: $compuesto_id})-[:SE_TRANSFORMA_EN]->(pa:PrincipioActivo)-[:COMPONE]->(m:Medicamento)
        RETURN c.nombre as compuesto,
               c.formula_quimica as formula,
               pa.nombre as principio_activo,
               pa.mecanismo_accion as mecanismo,
               collect({
                   id: m.id,
                   nombre: m.nombre,
                   nombre_comercial: m.nombre_comercial,
                   laboratorio: m.laboratorio
               }) as medicamentos
        """
        
        resultados = ejecutar_query_neo4j(query, {'compuesto_id': compuesto_id})
        
        if not resultados:
            return jsonify({'error': 'Compuesto no encontrado'}), 404
        
        return jsonify(resultados[0]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/medicamentos/<medicamento_id>/ruta-completa', methods=['GET'])
@cualquier_usuario_autenticado
def obtener_ruta_completa_medicamento(usuario, medicamento_id):
    """
    Obtener la ruta completa desde compuestos hasta el medicamento.
    Útil para trazabilidad.
    """
    try:
        query = """
        MATCH path = (c:Compuesto)-[:SE_TRANSFORMA_EN]->(pa:PrincipioActivo)-[:COMPONE]->(m:Medicamento {id: $medicamento_id})
        RETURN c.nombre as compuesto,
               c.nombre_quimico as compuesto_quimico,
               c.formula_quimica as formula,
               pa.nombre as principio_activo,
               pa.mecanismo_accion as mecanismo_accion,
               m.nombre as medicamento,
               m.nombre_comercial as nombre_comercial,
               m.dosis as dosis,
               m.forma_farmaceutica as forma_farmaceutica
        """
        
        resultados = ejecutar_query_neo4j(query, {'medicamento_id': medicamento_id})
        
        if not resultados:
            return jsonify({'error': 'No se encontró la ruta completa para este medicamento'}), 404
        
        return jsonify({
            'medicamento_id': medicamento_id,
            'ruta': resultados
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/estadisticas/grafo', methods=['GET'])
@cualquier_usuario_autenticado
def estadisticas_grafo(usuario):
    """Obtener estadísticas generales del grafo"""
    try:
        query = """
        MATCH (n)
        WITH labels(n) as tipo, count(*) as cantidad
        RETURN tipo[0] as tipo_nodo, cantidad
        ORDER BY cantidad DESC
        """
        
        estadisticas_nodos = ejecutar_query_neo4j(query)
        
        query_relaciones = """
        MATCH ()-[r]->()
        RETURN type(r) as tipo_relacion, count(*) as cantidad
        ORDER BY cantidad DESC
        """
        
        estadisticas_relaciones = ejecutar_query_neo4j(query_relaciones)
        
        return jsonify({
            'nodos': estadisticas_nodos,
            'relaciones': estadisticas_relaciones
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/busqueda/medicamentos-por-categoria', methods=['GET'])
@cualquier_usuario_autenticado
def buscar_por_categoria(usuario):
    """
    Buscar medicamentos por categoría terapéutica.
    
    Query params:
    - categoria: Nombre de la categoría
    """
    try:
        categoria = request.args.get('categoria')
        
        if not categoria:
            return jsonify({'error': 'Parámetro categoria requerido'}), 400
        
        query = """
        MATCH (m:Medicamento)-[:PERTENECE_A]->(c:Categoria)
        WHERE c.nombre = $categoria
        RETURN m.id as id,
               m.nombre as nombre,
               m.nombre_comercial as nombre_comercial,
               m.dosis as dosis,
               m.laboratorio as laboratorio
        ORDER BY m.nombre
        """
        
        medicamentos = ejecutar_query_neo4j(query, {'categoria': categoria})
        
        return jsonify({
            'categoria': categoria,
            'total': len(medicamentos),
            'medicamentos': medicamentos
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500