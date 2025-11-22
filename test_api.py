"""
Tests automatizados para PharmaFlow API
Ejecutar con: pytest tests/test_api.py -v
"""
import pytest
import json
from app import create_app, db
from app.models.mysql_models import Usuario, Producto, Lote


@pytest.fixture
def client():
    """Fixture para crear un cliente de prueba"""
    app = create_app('testing')
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()


@pytest.fixture
def auth_token(client):
    """Fixture para obtener token de autenticación"""
    # Registrar usuario de prueba
    client.post('/api/auth/register', json={
        'username': 'test_user',
        'email': 'test@test.com',
        'password': 'password123',
        'rol': 'farmaceutico'
    })
    
    # Login
    response = client.post('/api/auth/login', json={
        'username': 'test_user',
        'password': 'password123'
    })
    
    data = json.loads(response.data)
    return data['access_token']


# ============================================
# TESTS DE AUTENTICACIÓN
# ============================================

def test_health_check(client):
    """Test: Verificar que el servidor está funcionando"""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'ok'


def test_register_usuario(client):
    """Test: Registrar un nuevo usuario"""
    response = client.post('/api/auth/register', json={
        'username': 'nuevo_usuario',
        'email': 'nuevo@test.com',
        'password': 'password123',
        'rol': 'investigador'
    })
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['usuario']['username'] == 'nuevo_usuario'
    assert data['usuario']['rol'] == 'investigador'


def test_login_exitoso(client):
    """Test: Login con credenciales correctas"""
    # Primero registrar
    client.post('/api/auth/register', json={
        'username': 'login_test',
        'email': 'login@test.com',
        'password': 'password123',
        'rol': 'gerente'
    })
    
    # Luego login
    response = client.post('/api/auth/login', json={
        'username': 'login_test',
        'password': 'password123'
    })
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'access_token' in data
    assert data['usuario']['username'] == 'login_test'


def test_login_fallido(client):
    """Test: Login con credenciales incorrectas"""
    response = client.post('/api/auth/login', json={
        'username': 'no_existe',
        'password': 'wrong_password'
    })
    
    assert response.status_code == 401


# ============================================
# TESTS DE INVENTARIO
# ============================================

def test_crear_producto(client, auth_token):
    """Test: Crear un nuevo producto"""
    response = client.post('/api/inventario/productos',
        headers={'Authorization': f'Bearer {auth_token}'},
        json={
            'codigo_barras': '1234567890',
            'nombre': 'Producto Test',
            'tipo_medicamento': 'generico',
            'precio_base': 10.50
        }
    )
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['producto']['nombre'] == 'Producto Test'


def test_listar_productos(client, auth_token):
    """Test: Listar todos los productos"""
    # Crear un producto primero
    client.post('/api/inventario/productos',
        headers={'Authorization': f'Bearer {auth_token}'},
        json={
            'codigo_barras': '9876543210',
            'nombre': 'Otro Producto',
            'tipo_medicamento': 'patentado',
            'precio_base': 25.00
        }
    )
    
    # Listar productos
    response = client.get('/api/inventario/productos',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) > 0


# ============================================
# TESTS DE CONTROL DE CONCURRENCIA
# ============================================

def test_concurrencia_venta_exitosa(client, auth_token):
    """Test: Venta con versión correcta debe funcionar"""
    # Crear producto
    prod_response = client.post('/api/inventario/productos',
        headers={'Authorization': f'Bearer {auth_token}'},
        json={
            'codigo_barras': 'CONC001',
            'nombre': 'Producto Concurrencia',
            'tipo_medicamento': 'generico',
            'precio_base': 15.00
        }
    )
    producto_id = json.loads(prod_response.data)['producto']['id']
    
    # Crear lote
    lote_response = client.post('/api/inventario/lotes',
        headers={'Authorization': f'Bearer {auth_token}'},
        json={
            'producto_id': producto_id,
            'numero_lote': 'LOTE-CONC-001',
            'cantidad_inicial': 100,
            'fecha_fabricacion': '2024-01-01',
            'fecha_caducidad': '2026-01-01',
            'precio_compra': 10.00,
            'precio_venta': 15.00
        }
    )
    lote_id = json.loads(lote_response.data)['lote']['id']
    
    # Registrar venta con versión correcta
    response = client.post('/api/inventario/transacciones/venta',
        headers={'Authorization': f'Bearer {auth_token}'},
        json={
            'lote_id': lote_id,
            'cantidad': 20,
            'version': 0,
            'referencia': 'VENTA-TEST-001'
        }
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    assert data['lote']['cantidad_actual'] == 80
    assert data['lote']['version'] == 1


def test_concurrencia_conflicto_version(client, auth_token):
    """Test: Venta con versión obsoleta debe fallar"""
    # Crear producto y lote (similar al test anterior)
    prod_response = client.post('/api/inventario/productos',
        headers={'Authorization': f'Bearer {auth_token}'},
        json={
            'codigo_barras': 'CONC002',
            'nombre': 'Producto Conflicto',
            'tipo_medicamento': 'generico',
            'precio_base': 15.00
        }
    )
    producto_id = json.loads(prod_response.data)['producto']['id']
    
    lote_response = client.post('/api/inventario/lotes',
        headers={'Authorization': f'Bearer {auth_token}'},
        json={
            'producto_id': producto_id,
            'numero_lote': 'LOTE-CONC-002',
            'cantidad_inicial': 100,
            'fecha_fabricacion': '2024-01-01',
            'fecha_caducidad': '2026-01-01',
            'precio_compra': 10.00,
            'precio_venta': 15.00
        }
    )
    lote_id = json.loads(lote_response.data)['lote']['id']
    
    # Primera venta exitosa
    client.post('/api/inventario/transacciones/venta',
        headers={'Authorization': f'Bearer {auth_token}'},
        json={
            'lote_id': lote_id,
            'cantidad': 20,
            'version': 0,
            'referencia': 'VENTA-1'
        }
    )
    
    # Segunda venta con versión obsoleta (debería fallar)
    response = client.post('/api/inventario/transacciones/venta',
        headers={'Authorization': f'Bearer {auth_token}'},
        json={
            'lote_id': lote_id,
            'cantidad': 30,
            'version': 0,  # Versión obsoleta
            'referencia': 'VENTA-2'
        }
    )
    
    assert response.status_code == 409  # Conflict
    data = json.loads(response.data)
    assert 'concurrency' in data['mensaje'].lower()


def test_concurrencia_inventario_insuficiente(client, auth_token):
    """Test: Venta que excede inventario debe fallar"""
    # Crear producto y lote con poca cantidad
    prod_response = client.post('/api/inventario/productos',
        headers={'Authorization': f'Bearer {auth_token}'},
        json={
            'codigo_barras': 'CONC003',
            'nombre': 'Producto Limitado',
            'tipo_medicamento': 'generico',
            'precio_base': 15.00
        }
    )
    producto_id = json.loads(prod_response.data)['producto']['id']
    
    lote_response = client.post('/api/inventario/lotes',
        headers={'Authorization': f'Bearer {auth_token}'},
        json={
            'producto_id': producto_id,
            'numero_lote': 'LOTE-LIMIT-001',
            'cantidad_inicial': 10,
            'fecha_fabricacion': '2024-01-01',
            'fecha_caducidad': '2026-01-01',
            'precio_compra': 10.00,
            'precio_venta': 15.00
        }
    )
    lote_id = json.loads(lote_response.data)['lote']['id']
    
    # Intentar vender más de lo disponible
    response = client.post('/api/inventario/transacciones/venta',
        headers={'Authorization': f'Bearer {auth_token}'},
        json={
            'lote_id': lote_id,
            'cantidad': 50,  # Más de lo disponible
            'version': 0,
            'referencia': 'VENTA-EXCESO'
        }
    )
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'insuficiente' in data['error'].lower()


# ============================================
# TESTS DE AUTORIZACIÓN POR ROL
# ============================================

def test_investigador_no_puede_crear_producto(client):
    """Test: Investigador no puede crear productos"""
    # Registrar investigador
    client.post('/api/auth/register', json={
        'username': 'investigador_test',
        'email': 'invest@test.com',
        'password': 'password123',
        'rol': 'investigador'
    })
    
    # Login
    response = client.post('/api/auth/login', json={
        'username': 'investigador_test',
        'password': 'password123'
    })
    token = json.loads(response.data)['access_token']
    
    # Intentar crear producto (debería fallar)
    response = client.post('/api/inventario/productos',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'codigo_barras': 'TEST001',
            'nombre': 'Producto Test',
            'tipo_medicamento': 'generico',
            'precio_base': 10.00
        }
    )
    
    assert response.status_code == 403  # Forbidden


# ============================================
# RESUMEN DE TESTS
# ============================================

"""
Para ejecutar todos los tests:
    pytest tests/test_api.py -v

Para ejecutar un test específico:
    pytest tests/test_api.py::test_concurrencia_conflicto_version -v

Para ver cobertura:
    pytest tests/test_api.py --cov=app --cov-report=html
"""