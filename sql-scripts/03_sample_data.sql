USE pharmaflow;

-- Insertar usuarios de ejemplo
INSERT INTO usuarios (username, email, password_hash, rol) VALUES
('gerente1', 'gerente@pharmaflow.com', '$2b$12$hashed_password_1', 'gerente'),
('farma1', 'farmaceutico@pharmaflow.com', '$2b$12$hashed_password_2', 'farmaceutico'),
('invest1', 'investigador@pharmaflow.com', '$2b$12$hashed_password_3', 'investigador');

-- Insertar proveedores
INSERT INTO proveedores (nombre, contacto, telefono, email) VALUES
('LabFarma S.A.', 'Juan Pérez', '+34 912 345 678', 'juan@labfarma.com'),
('MediSupply Corp', 'María García', '+34 913 456 789', 'maria@medisupply.com'),
('BioPharm Inc', 'Carlos López', '+34 914 567 890', 'carlos@biopharm.com');

-- Insertar productos
INSERT INTO productos (codigo_barras, nombre, descripcion, principio_activo, tipo_medicamento, precio_base, temperatura_almacenamiento, requiere_refrigeracion) VALUES
('8437001234567', 'Paracetamol 500mg', 'Analgésico y antipirético', 'Paracetamol', 'generico', 5.50, 25.0, FALSE),
('8437001234568', 'Ibuprofeno 600mg', 'Antiinflamatorio no esteroideo', 'Ibuprofeno', 'generico', 7.25, 25.0, FALSE),
('8437001234569', 'Amoxicilina 500mg', 'Antibiótico de amplio espectro', 'Amoxicilina', 'patentado', 12.80, 15.0, TRUE),
('8437001234570', 'Insulina Lantus', 'Análogo de insulina de acción prolongada', 'Insulina glargina', 'controlado', 45.90, 8.0, TRUE);

-- Insertar lotes
INSERT INTO lotes (producto_id, numero_lote, cantidad_inicial, cantidad_actual, fecha_fabricacion, fecha_caducidad, precio_compra, precio_venta, proveedor_id, ubicacion_almacen) VALUES
(1, 'LOTE-PARA-2024-001', 1000, 850, '2024-01-15', '2026-01-15', 3.50, 5.50, 1, 'Almacén A - Estante 1'),
(1, 'LOTE-PARA-2024-002', 800, 800, '2024-02-01', '2026-02-01', 3.60, 5.50, 1, 'Almacén A - Estante 1'),
(2, 'LOTE-IBU-2024-001', 500, 320, '2024-01-20', '2025-07-20', 5.00, 7.25, 2, 'Almacén A - Estante 2'),
(3, 'LOTE-AMOX-2024-001', 300, 150, '2024-03-01', '2025-09-01', 8.50, 12.80, 3, 'Cámara Frío 1'),
(4, 'LOTE-INSU-2024-001', 200, 75, '2024-01-10', '2024-10-10', 35.00, 45.90, 3, 'Cámara Frío 2');

-- Insertar transacciones de ejemplo
INSERT INTO transacciones (lote_id, usuario_id, tipo_transaccion, cantidad, motivo, referencia) VALUES
(1, 2, 'salida', 50, 'Venta a cliente', 'VENTA-001'),
(1, 2, 'salida', 100, 'Venta a hospital', 'VENTA-002'),
(3, 2, 'salida', 80, 'Venta a farmacia', 'VENTA-003'),
(4, 2, 'salida', 50, 'Venta a clínica', 'VENTA-004'),
(5, 2, 'salida', 25, 'Venta a paciente', 'VENTA-005');

-- Insertar interacciones medicamentosas
INSERT INTO interacciones_medicamentosas (medicamento_a_id, medicamento_b_id, tipo_interaccion, descripcion, recomendaciones) VALUES
(1, 2, 'leve', 'Puede aumentar el riesgo de daño hepático', 'Monitorizar función hepática'),
(2, 3, 'moderada', 'Puede reducir la efectividad del antibiótico', 'Separar la administración por 2 horas'),
(1, 3, 'leve', 'Interacción mínima documentada', 'No se requieren ajustes significativos');