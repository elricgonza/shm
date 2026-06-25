-- ================================================================
-- MIGRACIÓN: Conversión de columnas DATE → TIMESTAMP
-- Sistema de Gestión Educativa SHALOM
-- Ejecutar como superusuario o propietario de la BD (uaded)
-- ================================================================
-- IMPORTANTE: Hacer backup de la base de datos antes de ejecutar.
-- Estas sentencias convierten las columnas existentes de tipo DATE
-- a TIMESTAMP, preservando los datos (la hora queda en 00:00:00).
-- ================================================================

-- ── Tabla: gestion ────────────────────────────────────────────
ALTER TABLE public.gestion
    ALTER COLUMN creado TYPE timestamp USING creado::timestamp,
    ALTER COLUMN act    TYPE timestamp USING act::timestamp;

-- ── Tabla: grado ──────────────────────────────────────────────
ALTER TABLE public.grado
    ALTER COLUMN creado TYPE timestamp USING creado::timestamp,
    ALTER COLUMN act    TYPE timestamp USING act::timestamp;

-- ── Tabla: materia ────────────────────────────────────────────
ALTER TABLE public.materia
    ALTER COLUMN creado TYPE timestamp USING creado::timestamp,
    ALTER COLUMN act    TYPE timestamp USING act::timestamp;

-- ── Tabla: profesor ───────────────────────────────────────────
ALTER TABLE public.profesor
    ALTER COLUMN creado TYPE timestamp USING creado::timestamp,
    ALTER COLUMN act    TYPE timestamp USING act::timestamp;

-- ── Tabla: curso ──────────────────────────────────────────────
ALTER TABLE public.curso
    ALTER COLUMN creado TYPE timestamp USING creado::timestamp,
    ALTER COLUMN act    TYPE timestamp USING act::timestamp;

-- ── Tabla: asignado ───────────────────────────────────────────
ALTER TABLE public.asignado
    ALTER COLUMN creado TYPE timestamp USING creado::timestamp,
    ALTER COLUMN act    TYPE timestamp USING act::timestamp;

-- ── Tabla: alumno ─────────────────────────────────────────────
ALTER TABLE public.alumno
    ALTER COLUMN creado TYPE timestamp USING creado::timestamp,
    ALTER COLUMN act    TYPE timestamp USING act::timestamp;

-- ── Tabla: inscrito ───────────────────────────────────────────
ALTER TABLE public.inscrito
    ALTER COLUMN creado TYPE timestamp USING creado::timestamp,
    ALTER COLUMN act    TYPE timestamp USING act::timestamp;

-- ── Tabla: nota ───────────────────────────────────────────────
ALTER TABLE public.nota
    ALTER COLUMN creado TYPE timestamp USING creado::timestamp,
    ALTER COLUMN act    TYPE timestamp USING act::timestamp;

-- ── Tabla: costo ──────────────────────────────────────────────
ALTER TABLE public.costo
    ALTER COLUMN creado TYPE timestamp USING creado::timestamp,
    ALTER COLUMN act    TYPE timestamp USING act::timestamp;

-- ── Tabla: pago ───────────────────────────────────────────────
ALTER TABLE public.pago
    ALTER COLUMN fecha_pago TYPE timestamp USING fecha_pago::timestamp,
    ALTER COLUMN creado     TYPE timestamp USING creado::timestamp,
    ALTER COLUMN act        TYPE timestamp USING act::timestamp;

-- ── Tabla: rol ────────────────────────────────────────────────
ALTER TABLE public.rol
    ALTER COLUMN act TYPE timestamp USING act::timestamp;

-- ================================================================
-- Verificación (opcional): listar tipos de columnas modificadas
-- ================================================================
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND column_name IN ('creado', 'act', 'fecha_pago')
ORDER BY table_name, column_name;
