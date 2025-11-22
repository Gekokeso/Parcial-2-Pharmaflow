from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_
from datetime import datetime, date
from app.models.mysql_models import db, Producto, Lote, Transaccion, Usuario
from app.middleware.auth_middleware import gerente_o_farmaceutico, cualquier_usuario_autenticado, solo_gerente
from app.middleware.concurrency import OptimisticLockManager, ConcurrencyException

bp = Blueprint('inventario', __name__, url_prefix='/api/inventario')


# ============================================
# PRODUCTOS
# ============================================

@bp.route('/productos', methods=['GET'])
@cualquier_usuario_autenticado
def listar_productos(usuario):
    """
    Listar todos los productos.
    Query params: activo (true/false), buscar (texto)
    """
    try:
        query = Producto.query
        
        # Filtros opcionales
        if request.args.get('activo'):
            activo = request.args.get('activo').lower() == 'true'
            query = query.filter_by(activo=activo)
        
        if request.args.get('buscar'):
            buscar = f"%{request.args.get('buscar')}%"
            query = query.filter(
                or_(
                    Producto.nombre.like(buscar),
                    Producto.codigo_barras.like(buscar),
                    Producto.principio_activo.like(buscar)
                )
            )
        
        productos = query.all()
        return jsonify([p.to_dict() for p in productos]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/productos/<int:id>', methods=['GET'])
@cualquier_usuario_autenticado
def obtener_producto(usuario, id):
    """Obtener un producto por ID"""
    try:
        producto = Producto.query.get(id)
        
        if not producto:
            return jsonify({'error': 'Producto no encontrado'}), 404
        
        return jsonify(producto.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/productos', methods=['POST'])
@gerente_o_farmaceutico
def crear_producto(usuario):
    """
    Crear un nuevo producto.
    
    Body:
    {
        "codigo_barras": "string",
        "nombre": "string",
        "descripcion": "string",
        "principio_activo": "string",
        "tipo_medicamento": "generico|patentado|controlado",
        "precio_base": float,
        "temperatura_almacenamiento": float,
        "requiere_refrigeracion": boolean
    }
    """
    try:
        data = request.get_json()
        
        # Validaciones básicas
        campos_requeridos = ['codigo_barras', 'nombre', 'tipo_medicamento', 'precio_base']
        if not all(k in data for k in campos_requeridos):
            return jsonify({'error': 'Faltan campos requeridos'}), 400
        
        # Verificar si el código de barras ya existe
        if Producto.query.filter_by(codigo_barras=data['codigo_barras']).first():
            return jsonify({'error': 'El código de barras ya existe'}), 409
        
        # Crear producto
        producto = Producto(
            codigo_barras=data['codigo_barras'],
            nombre=data['nombre'],
            descripcion=data.get('descripcion'),
            principio_activo=data.get('principio_activo'),
            tipo_medicamento=data['tipo_medicamento'],
            precio_base=data['precio_base'],
            temperatura_almacenamiento=data.get('temperatura_almacenamiento'),
            requiere_refrigeracion=data.get('requiere_refrigeracion', False)
        )
        
        db.session.add(producto)
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Producto creado exitosamente',
            'producto': producto.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================
# LOTES
# ============================================

@bp.route('/lotes', methods=['GET'])
@cualquier_usuario_autenticado
def listar_lotes(usuario):
    """
    Listar todos los lotes.
    Query params: producto_id, caducidad_proxima (dias)
    """
    try:
        query = Lote.query
        
        # Filtrar por producto
        if request.args.get('producto_id'):
            query = query.filter_by(producto_id=request.args.get('producto_id'))
        
        # Filtrar por caducidad próxima
        if request.args.get('caducidad_proxima'):
            dias = int(request.args.get('caducidad_proxima'))
            fecha_limite = date.today() + timedelta(days=dias)
            query = query.filter(Lote.fecha_caducidad <= fecha_limite)
        
        # Solo lotes con cantidad > 0
        if request.args.get('disponible') == 'true':
            query = query.filter(Lote.cantidad_actual > 0)
        
        lotes = query.all()
        return jsonify([l.to_dict() for l in lotes]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/lotes/<int:id>', methods=['GET'])
@cualquier_usuario_autenticado
def obtener_lote(usuario, id):
    """Obtener un lote por ID"""
    try:
        lote = Lote.query.get(id)
        
        if not lote:
            return jsonify({'error': 'Lote no encontrado'}), 404
        
        return jsonify(lote.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/lotes', methods=['POST'])
@gerente_o_farmaceutico
def crear_lote(usuario):
    """
    Crear un nuevo lote de producto.
    
    Body:
    {
        "producto_id": int,
        "numero_lote": "string",
        "cantidad_inicial": int,
        "fecha_fabricacion": "YYYY-MM-DD",
        "fecha_caducidad": "YYYY-MM-DD",
        "precio_compra": float,
        "precio_venta": float,
        "proveedor_id": int,
        "ubicacion_almacen": "string"
    }
    """
    try:
        data = request.get_json()
        
        # Validaciones
        campos_requeridos = ['producto_id', 'numero_lote', 'cantidad_inicial', 
                           'fecha_fabricacion', 'fecha_caducidad', 'precio_compra', 'precio_venta']
        if not all(k in data for k in campos_requeridos):
            return jsonify({'error': 'Faltan campos requeridos'}), 400
        
        # Verificar si el lote ya existe
        if Lote.query.filter_by(numero_lote=data['numero_lote']).first():
            return jsonify({'error': 'El número de lote ya existe'}), 409
        
        # Crear lote
        lote = Lote(
            producto_id=data['producto_id'],
            numero_lote=data['numero_lote'],
            cantidad_inicial=data['cantidad_inicial'],
            cantidad_actual=data['cantidad_inicial'],
            fecha_fabricacion=datetime.strptime(data['fecha_fabricacion'], '%Y-%m-%d').date(),
            fecha_caducidad=datetime.strptime(data['fecha_caducidad'], '%Y-%m-%d').date(),
            precio_compra=data['precio_compra'],
            precio_venta=data['precio_venta'],
            proveedor_id=data.get('proveedor_id'),
            ubicacion_almacen=data.get('ubicacion_almacen')
        )
        
        db.session.add(lote)
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Lote creado exitosamente',
            'lote': lote.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================
# TRANSACCIONES CON CONTROL DE CONCURRENCIA
# ============================================

@bp.route('/transacciones/venta', methods=['POST'])
@gerente_o_farmaceutico
def registrar_venta(usuario):
    """
    Registrar una venta con CONTROL DE CONCURRENCIA OPTIMISTA.
    
    Body:
    {
        "lote_id": int,
        "cantidad": int,
        "referencia": "string",
        "version": int  // Versión del lote que el usuario vio
    }
    
    IMPORTANTE: El campo 'version' es crítico para evitar conflictos.
    """
    try:
        data = request.get_json()
        
        # Validaciones
        if not all(k in data for k in ('lote_id', 'cantidad', 'version')):
            return jsonify({'error': 'Faltan campos requeridos (lote_id, cantidad, version)'}), 400
        
        if data['cantidad'] <= 0:
            return jsonify({'error': 'La cantidad debe ser mayor a 0'}), 400
        
        # Ejecutar venta con control de concurrencia
        resultado = OptimisticLockManager.vender_producto(
            lote_id=data['lote_id'],
            cantidad=data['cantidad'],
            usuario_id=usuario.id,
            referencia_venta=data.get('referencia', f'VENTA-{datetime.now().strftime("%Y%m%d%H%M%S")}'),
            version_esperada=data['version']
        )
        
        return jsonify(resultado), 200
        
    except ConcurrencyException as e:
        return jsonify({
            'error': 'Conflicto de concurrencia',
            'mensaje': str(e),
            'tipo': 'concurrency_conflict'
        }), 409
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Error inesperado: {str(e)}'}), 500


@bp.route('/transacciones/entrada', methods=['POST'])
@gerente_o_farmaceutico
def registrar_entrada(usuario):
    """
    Registrar entrada de inventario con control de concurrencia.
    
    Body:
    {
        "lote_id": int,
        "cantidad": int,
        "referencia": "string",
        "version": int
    }
    """
    try:
        data = request.get_json()
        
        if not all(k in data for k in ('lote_id', 'cantidad', 'version')):
            return jsonify({'error': 'Faltan campos requeridos'}), 400
        
        if data['cantidad'] <= 0:
            return jsonify({'error': 'La cantidad debe ser mayor a 0'}), 400
        
        resultado = OptimisticLockManager.agregar_inventario(
            lote_id=data['lote_id'],
            cantidad=data['cantidad'],
            usuario_id=usuario.id,
            referencia_compra=data.get('referencia', f'ENTRADA-{datetime.now().strftime("%Y%m%d%H%M%S")}'),
            version_esperada=data['version']
        )
        
        return jsonify(resultado), 200
        
    except ConcurrencyException as e:
        return jsonify({
            'error': 'Conflicto de concurrencia',
            'mensaje': str(e),
            'tipo': 'concurrency_conflict'
        }), 409
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Error inesperado: {str(e)}'}), 500


@bp.route('/transacciones', methods=['GET'])
@cualquier_usuario_autenticado
def listar_transacciones(usuario):
    """
    Listar transacciones.
    Query params: lote_id, tipo, fecha_desde, fecha_hasta
    """
    try:
        query = Transaccion.query
        
        if request.args.get('lote_id'):
            query = query.filter_by(lote_id=request.args.get('lote_id'))
        
        if request.args.get('tipo'):
            query = query.filter_by(tipo_transaccion=request.args.get('tipo'))
        
        transacciones = query.order_by(Transaccion.fecha_transaccion.desc()).limit(100).all()
        return jsonify([t.to_dict() for t in transacciones]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# REPORTES Y ESTADÍSTICAS
# ============================================

@bp.route('/reportes/stock-bajo', methods=['GET'])
@gerente_o_farmaceutico
def reporte_stock_bajo(usuario):
    """Productos con stock bajo (menos de 50 unidades)"""
    try:
        lotes_bajo_stock = Lote.query.filter(
            Lote.cantidad_actual < 50,
            Lote.cantidad_actual > 0
        ).all()
        
        return jsonify([l.to_dict() for l in lotes_bajo_stock]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/reportes/proximos-vencer', methods=['GET'])
@gerente_o_farmaceutico
def reporte_proximos_vencer(usuario):
    """Lotes próximos a vencer (30 días)"""
    try:
        from datetime import timedelta
        fecha_limite = date.today() + timedelta(days=30)
        
        lotes_vencer = Lote.query.filter(
            Lote.fecha_caducidad <= fecha_limite,
            Lote.fecha_caducidad >= date.today(),
            Lote.cantidad_actual > 0
        ).order_by(Lote.fecha_caducidad).all()
        
        return jsonify([l.to_dict() for l in lotes_vencer]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500