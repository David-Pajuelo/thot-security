-- Script SQL para agregar el rol "Jefe de Seguridad Suplente"
-- Este script puede ejecutarse directamente en la base de datos si la migración no se ha ejecutado aún

INSERT INTO roles (name, description, created_at, updated_at) 
VALUES 
('jefe_seguridad_suplente', 'Jefe de Seguridad Suplente', NOW(), NOW())
ON CONFLICT (name) DO NOTHING;

