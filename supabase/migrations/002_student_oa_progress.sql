-- 002_student_oa_progress.sql
-- Migración: tabla para rastrear progreso por OA por estudiante

-- Requiere la extensión pgcrypto para gen_random_uuid()
-- Habilita extensión para generación de UUIDs si no existe
CREATE EXTENSION IF NOT EXISTS pgcrypto;

BEGIN;

-- Tabla principal: student_oa_progress
CREATE TABLE IF NOT EXISTS public.student_oa_progress (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id uuid NOT NULL,
    curso text NOT NULL,
    asignatura text NOT NULL,
    id_oa text NOT NULL,
    nivel_logro text NOT NULL CHECK (nivel_logro IN ('not_started','in_progress','partial','mastered')),
    evaluation_history jsonb DEFAULT '[]'::jsonb,
    aligned_resources text[] DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT student_oa_unique UNIQUE (student_id, id_oa)
);

-- Índices para consultas rápidas desde frontend
CREATE INDEX IF NOT EXISTS idx_student_oa_progress_student ON public.student_oa_progress (student_id);
CREATE INDEX IF NOT EXISTS idx_student_oa_progress_oa ON public.student_oa_progress (id_oa);

-- Trigger para actualizar updated_at automáticamente en UPDATE
CREATE OR REPLACE FUNCTION public.trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_set_timestamp ON public.student_oa_progress;
CREATE TRIGGER trg_set_timestamp
BEFORE UPDATE ON public.student_oa_progress
FOR EACH ROW
EXECUTE FUNCTION public.trigger_set_timestamp();

-- Habilitar Row Level Security y políticas básicas
ALTER TABLE public.student_oa_progress ENABLE ROW LEVEL SECURITY;

-- Política: permitir que el usuario autenticado lea sólo sus registros
CREATE POLICY "Allow select own" ON public.student_oa_progress
    FOR SELECT
    USING (auth.uid()::uuid = student_id);

-- Política: permitir insert si el student_id coincide con auth.uid()
CREATE POLICY "Allow insert own" ON public.student_oa_progress
    FOR INSERT
    WITH CHECK (auth.uid()::uuid = student_id);

-- Política: permitir update sólo sobre los propios registros
CREATE POLICY "Allow update own" ON public.student_oa_progress
    FOR UPDATE
    USING (auth.uid()::uuid = student_id)
    WITH CHECK (auth.uid()::uuid = student_id);

-- Nota: si se desea que roles administrativos (service_role) puedan acceder,
-- se deben crear políticas adicionales que permitan accesos según rol.

COMMIT;
