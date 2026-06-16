-- 002_student_oa_progress.sql
-- Migración: tabla para rastrear progreso por OA por estudiante

-- Requiere la extensión pgcrypto para gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pgcrypto;

BEGIN;

CREATE TABLE IF NOT EXISTS public.student_oa_progress (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id text NOT NULL,
    id_oa text NOT NULL,
    mastery_level text NOT NULL CHECK (mastery_level IN ('not_started','in_progress','partial','mastered')),
    last_evaluation timestamptz DEFAULT now(),
    evaluation_history jsonb DEFAULT '[]'::jsonb,
    aligned_resources text[] DEFAULT '{}',
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
    CONSTRAINT student_oa_unique UNIQUE (student_id, id_oa)
);

CREATE INDEX IF NOT EXISTS idx_student_oa_progress_student ON public.student_oa_progress (student_id);
CREATE INDEX IF NOT EXISTS idx_student_oa_progress_oa ON public.student_oa_progress (id_oa);

COMMIT;
