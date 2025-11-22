-- 02_security_roles.sql
-- Crear usuarios y roles
CREATE ROLE IF NOT EXISTS 'gerente_role';
CREATE ROLE IF NOT EXISTS 'farmaceutico_role'; 
CREATE ROLE IF NOT EXISTS 'investigador_role';

-- Privilegios para gerente (acceso total)
GRANT ALL PRIVILEGES ON pharmaflow.* TO 'gerente_role';

-- Privilegios para farmacéutico
GRANT SELECT, INSERT, UPDATE ON pharmaflow.productos TO 'farmaceutico_role';
GRANT SELECT, INSERT, UPDATE ON pharmaflow.lotes TO 'farmaceutico_role';
GRANT SELECT, INSERT ON pharmaflow.transacciones TO 'farmaceutico_role';
GRANT SELECT ON pharmaflow.usuarios TO 'farmaceutico_role';

-- Privilegios para investigador (solo consulta)
GRANT SELECT ON pharmaflow.productos TO 'investigador_role';
GRANT SELECT ON pharmaflow.lotes TO 'investigador_role';

-- Crear usuarios específicos
CREATE USER 'gerente_main'@'%' IDENTIFIED BY 'securepassword1';
CREATE USER 'farmaceutico_juan'@'%' IDENTIFIED BY 'securepassword2';
CREATE USER 'investigador_maria'@'%' IDENTIFIED BY 'securepassword3';

-- Asignar roles a usuarios
GRANT 'gerente_role' TO 'gerente_main'@'%';
GRANT 'farmaceutico_role' TO 'farmaceutico_juan'@'%';
GRANT 'investigador_role' TO 'investigador_maria'@'%';

-- Activar roles por defecto
SET DEFAULT ROLE ALL TO 'gerente_main'@'%';
SET DEFAULT ROLE ALL TO 'farmaceutico_juan'@'%';
SET DEFAULT ROLE ALL TO 'investigador_maria'@'%';

FLUSH PRIVILEGES;