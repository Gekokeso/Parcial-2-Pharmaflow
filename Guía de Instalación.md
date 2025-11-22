# 🚀 PharmaFlow Solutions - Guía de Instalación

## 📋 Prerequisitos

- Python 3.9 o superior
- Docker y Docker Compose
- pip (gestor de paquetes de Python)

---

## 🔧 Paso 1: Levantar la infraestructura Docker

```bash
# Asegúrate de estar en la carpeta del proyecto
cd pharmaflow-project

# Iniciar todos los contenedores
docker-compose up -d

# Verificar que todo esté corriendo
docker-compose ps
```

---

## 📦 Paso 2: Instalar dependencias Python

```bash
# Crear entorno virtual (recomendado)
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

---

## ⚙️ Paso 3: Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto con el contenido del artifact proporcionado, o copia el ejemplo:

```bash
cp .env.example .env
```

---

## 🏃 Paso 4: Ejecutar la aplicación

```bash
# Ejecutar el servidor Flask
python run.py
```

La aplicación estará disponible en: **http://localhost:5000**

---

## 🧪 Paso 5: Probar la API

### 1. Verificar que todo funciona

```bash
curl http://localhost:5000/health
```

Deberías ver:
```json
{
  "status": "ok",
  "mysql": "connected",
  "mongodb": "connected",
  "redis": "connected",
  "neo4j": "connected"
}
```

### 2. Login con usuario de prueba

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "gerente1",
    "password": "$2b$12$hashed_password_1"
  }'
```

---

## 📚 Endpoints Disponibles

### **Autenticación (`/api/auth`)**
- `POST /register` - Registrar usuario
- `POST /login` - Iniciar sesión
- `POST /logout` - Cerrar sesión
- `GET /me` - Obtener usuario actual
- `GET /usuarios` - Listar usuarios (solo gerente)

### **Inventario (`/api/inventario`)**
- `GET /productos` - Listar productos
- `POST /productos` - Crear producto
- `GET /lotes` - Listar lotes
- `POST /lotes` - Crear lote
- `POST /transacciones/venta` - Registrar venta (CON CONCURRENCIA)
- `POST /transacciones/entrada` - Registrar entrada
- `GET /reportes/stock-bajo` - Reporte de stock bajo
- `GET /reportes/proximos-vencer` - Lotes próximos a vencer

### **Ensayos Clínicos (`/api/ensayos`)**
- `GET /` - Listar ensayos
- `POST /` - Crear ensayo
- `GET /<id>` - Obtener ensayo específico
- `PUT /<id>` - Actualizar ensayo
- `POST /<id>/efectos-secundarios` - Agregar efecto secundario
- `POST /busqueda/avanzada` - Búsqueda avanzada
- `GET /estadisticas` - Estadísticas

### **Interacciones (`/api/interacciones`)**
- `GET /medicamentos` - Listar medicamentos
- `GET /medicamentos/<id>/interacciones` - Interacciones de un medicamento
- `POST /verificar-interacciones` - Verificar múltiples medicamentos
- `GET /principios-activos` - Listar principios activos
- `GET /compuestos/<id>/cadena` - Cadena de compuesto a medicamento
- `GET /estadisticas/grafo` - Estadísticas del grafo

---

## 🔐 Sistema de Roles

| Rol | Permisos |
|-----|----------|
| **Gerente** | Acceso total: crear, modificar, eliminar |
| **Farmacéutico** | Modificar inventario, registrar ventas |
| **Investigador** | Solo consulta (lectura) |

---

## 🐛 Solución de Problemas

### Error de conexión a MySQL
```bash
# Verificar que el puerto correcto está en .env
MYSQL_PORT=3307
```

### Error "Module not found"
```bash
# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall
```

### Error de autenticación en bases de datos
```bash
# Verificar que las credenciales en .env coincidan con docker-compose.yml
```

---

## 📖 Ejemplo Completo de Uso

### 1. Registrar un usuario
```python
import requests

response = requests.post('http://localhost:5000/api/auth/register', json={
    'username': 'test_user',
    'email': 'test@pharmaflow.com',
    'password': 'password123',
    'rol': 'farmaceutico'
})
print(response.json())
```

### 2. Login y obtener token
```python
response = requests.post('http://localhost:5000/api/auth/login', json={
    'username': 'test_user',
    'password': 'password123'
})
token = response.json()['access_token']
```

### 3. Registrar una venta CON control de concurrencia
```python
headers = {'Authorization': f'Bearer {token}'}

response = requests.post(
    'http://localhost:5000/api/inventario/transacciones/venta',
    headers=headers,
    json={
        'lote_id': 1,
        'cantidad': 10,
        'version': 0,  # Versión actual del lote
        'referencia': 'VENTA-001'
    }
)
print(response.json())
```

---

## 🎯 Próximos Pasos

1. ✅ Probar todos los endpoints con Postman o curl
2. ✅ Simular concurrencia con múltiples usuarios
3. ✅ Crear el video demo mostrando funcionalidades
4. ✅ Escribir la reflexión individual del proyecto

---

## 📞 Soporte

Si tienes problemas, verifica:
1. Docker está corriendo
2. Todas las dependencias están instaladas
3. El archivo `.env` está configurado correctamente
4. Los puertos no están en conflicto