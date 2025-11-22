# 🏥 PharmaFlow Solutions

Sistema de Gestión de Inventario y Cadena de Suministro para una Farmacéutica.

## 📋 Descripción

PharmaFlow Solutions es un sistema robusto que integra múltiples bases de datos (MySQL, MongoDB, Redis, Neo4j) para gestionar:

- **Inventario y Transacciones** (MySQL) - Control de concurrencia optimista
- **Ensayos Clínicos** (MongoDB) - Documentos flexibles
- **Cache y Sesiones** (Redis) - Datos volátiles
- **Interacciones Medicamentosas** (Neo4j) - Grafos de relaciones

## 🏗️ Arquitectura

```
├── MySQL (Puerto 3307)        - Inventario, usuarios, transacciones
├── MongoDB (Puerto 27017)     - Ensayos clínicos
├── Redis (Puerto 6379)        - Sesiones y cache
├── Neo4j (Puerto 7474/7687)   - Relaciones entre medicamentos
└── Flask API (Puerto 5000)    - Backend REST API
```

## 🚀 Instalación Rápida

### Prerequisitos

- Docker y Docker Compose
- Python 3.9+
- Git

### 1. Clonar el repositorio

```bash
git clone https://github.com/TU_USUARIO/pharmaflow-project.git
cd pharmaflow-project
```

### 2. Iniciar contenedores Docker

```bash
docker-compose up -d
```

Espera 1-2 minutos para que todas las bases de datos inicialicen.

### 3. Configurar entorno Python

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copia el archivo `.env.example` a `.env`:

```bash
cp .env.example .env
```

### 5. Ejecutar la aplicación

```bash
python run.py
```

La API estará disponible en: **http://localhost:5000**

## 🧪 Verificar instalación

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

## 📚 Documentación API

### Autenticación

- `POST /api/auth/register` - Registrar usuario
- `POST /api/auth/login` - Iniciar sesión
- `GET /api/auth/me` - Obtener usuario actual

### Inventario

- `GET /api/inventario/productos` - Listar productos
- `POST /api/inventario/productos` - Crear producto
- `GET /api/inventario/lotes` - Listar lotes
- `POST /api/inventario/transacciones/venta` - Registrar venta (con concurrencia)

### Ensayos Clínicos

- `GET /api/ensayos/` - Listar ensayos
- `POST /api/ensayos/` - Crear ensayo
- `GET /api/ensayos/estadisticas` - Estadísticas

### Interacciones

- `GET /api/interacciones/medicamentos` - Listar medicamentos
- `POST /api/interacciones/verificar-interacciones` - Verificar interacciones

## 🔐 Usuarios de Prueba

| Usuario | Password | Rol |
|---------|----------|-----|
| gerente1 | (configurar) | Gerente |
| farma1 | (configurar) | Farmacéutico |
| invest1 | (configurar) | Investigador |

## 🛠️ Tecnologías

- **Backend:** Flask, SQLAlchemy, PyMongo
- **Bases de Datos:** MySQL, MongoDB, Redis, Neo4j
- **Autenticación:** JWT (Flask-JWT-Extended)
- **Contenedores:** Docker, Docker Compose

## 📦 Estructura del Proyecto

```
pharmaflow-project/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── models/
│   ├── routes/
│   ├── middleware/
│   └── services/
├── sql-scripts/
├── mongo-scripts/
├── neo4j-scripts/
├── docker-compose.yml
├── requirements.txt
└── run.py
```

## 🎯 Características Principales

### ✅ Control de Concurrencia Optimista

Sistema que previene sobreventa cuando múltiples usuarios intentan modificar el mismo lote simultáneamente.

```python
# Ejemplo de uso
{
  "lote_id": 1,
  "cantidad": 50,
  "version": 0,  # Versión del lote
  "referencia": "VENTA-001"
}
```

### ✅ Sistema de Roles

- **Gerente:** Acceso completo
- **Farmacéutico:** Modificar inventario, registrar ventas
- **Investigador:** Solo consulta

### ✅ Base de Datos Flexible (MongoDB)

Almacenamiento de ensayos clínicos con estructura variable.

### ✅ Grafos de Relaciones (Neo4j)

Mapeo de interacciones medicamentosas y trazabilidad de compuestos.

## 🐛 Solución de Problemas

### Puerto 3306 ocupado

El proyecto usa el puerto 3307 para MySQL. Verifica en `docker-compose.yml`.

### Error "Module not found"

```bash
pip install -r requirements.txt --force-reinstall
```

### Bases de datos vacías

```bash
docker-compose down -v
docker-compose up -d
```

## 👥 Equipo

- Carlos A.
- Arturo M.

