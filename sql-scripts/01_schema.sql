-- 01_schema.sql
CREATE DATABASE IF NOT EXISTS pharmaflow;
USE pharmaflow;

-- Tabla de usuarios
CREATE TABLE usuarios (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol ENUM('gerente', 'farmaceutico', 'investigador') NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de proveedores (debe crearse antes que productos)
CREATE TABLE proveedores (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(200) NOT NULL,
    contacto VARCHAR(100),
    telefono VARCHAR(20),
    email VARCHAR(100),
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de productos
CREATE TABLE productos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    codigo_barras VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,
    principio_activo VARCHAR(100),
    tipo_medicamento ENUM('generico', 'patentado', 'controlado'),
    precio_base DECIMAL(10,2) NOT NULL,
    temperatura_almacenamiento DECIMAL(3,1),
    requiere_refrigeracion BOOLEAN DEFAULT FALSE,
    activo BOOLEAN DEFAULT TRUE
);

-- Tabla de lotes (con control de concurrencia)
CREATE TABLE lotes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    producto_id INT NOT NULL,
    numero_lote VARCHAR(50) UNIQUE NOT NULL,
    cantidad_inicial INT NOT NULL,
    cantidad_actual INT NOT NULL,
    fecha_fabricacion DATE NOT NULL,
    fecha_caducidad DATE NOT NULL,
    precio_compra DECIMAL(10,2) NOT NULL,
    precio_venta DECIMAL(10,2) NOT NULL,
    proveedor_id INT,
    ubicacion_almacen VARCHAR(100),
    version INT DEFAULT 0, -- Para control de concurrencia optimista
    FOREIGN KEY (producto_id) REFERENCES productos(id),
    FOREIGN KEY (proveedor_id) REFERENCES proveedores(id)
);

-- Tabla de transacciones
CREATE TABLE transacciones (
    id INT PRIMARY KEY AUTO_INCREMENT,
    lote_id INT NOT NULL,
    usuario_id INT NOT NULL,
    tipo_transaccion ENUM('entrada', 'salida', 'ajuste') NOT NULL,
    cantidad INT NOT NULL,
    fecha_transaccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    motivo VARCHAR(200),
    referencia VARCHAR(100),
    FOREIGN KEY (lote_id) REFERENCES lotes(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Tabla de interacciones medicamentosas
CREATE TABLE interacciones_medicamentosas (
    id INT PRIMARY KEY AUTO_INCREMENT,
    medicamento_a_id INT NOT NULL,
    medicamento_b_id INT NOT NULL,
    tipo_interaccion ENUM('leve', 'moderada', 'grave') NOT NULL,
    descripcion TEXT,
    recomendaciones TEXT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (medicamento_a_id) REFERENCES productos(id),
    FOREIGN KEY (medicamento_b_id) REFERENCES productos(id)
);

-- Índices para optimización
CREATE INDEX idx_lotes_producto ON lotes(producto_id);
CREATE INDEX idx_lotes_caducidad ON lotes(fecha_caducidad);
CREATE INDEX idx_lotes_cantidad ON lotes(cantidad_actual);
CREATE INDEX idx_transacciones_fecha ON transacciones(fecha_transaccion);
CREATE INDEX idx_transacciones_lote ON transacciones(lote_id);
CREATE INDEX idx_transacciones_usuario ON transacciones(usuario_id);
CREATE INDEX idx_productos_codigo ON productos(codigo_barras);
CREATE INDEX idx_productos_activo ON productos(activo);