-- 003_curriculum_catalog.sql
-- Catalogo curricular MINEDUC para persistir las mallas locales en Supabase.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

BEGIN;

CREATE TABLE IF NOT EXISTS public.curriculum_units (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    curso text NOT NULL,
    asignatura text NOT NULL,
    eje_tematico text NOT NULL,
    source_file text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT curriculum_units_unique UNIQUE (curso, asignatura, eje_tematico)
);

CREATE TABLE IF NOT EXISTS public.curriculum_objectives (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    unit_id uuid NOT NULL REFERENCES public.curriculum_units(id) ON DELETE CASCADE,
    curso text NOT NULL,
    asignatura text NOT NULL,
    eje_tematico text NOT NULL,
    id_oa text NOT NULL,
    descripcion text NOT NULL,
    indicadores_evaluacion text[] DEFAULT '{}',
    conceptos_clave text[] DEFAULT '{}',
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT curriculum_objectives_unique UNIQUE (curso, asignatura, id_oa)
);

CREATE INDEX IF NOT EXISTS idx_curriculum_units_lookup
    ON public.curriculum_units (curso, asignatura);

CREATE INDEX IF NOT EXISTS idx_curriculum_objectives_lookup
    ON public.curriculum_objectives (curso, asignatura, id_oa);

CREATE OR REPLACE FUNCTION public.trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_curriculum_units_timestamp ON public.curriculum_units;
CREATE TRIGGER trg_curriculum_units_timestamp
BEFORE UPDATE ON public.curriculum_units
FOR EACH ROW
EXECUTE FUNCTION public.trigger_set_timestamp();

DROP TRIGGER IF EXISTS trg_curriculum_objectives_timestamp ON public.curriculum_objectives;
CREATE TRIGGER trg_curriculum_objectives_timestamp
BEFORE UPDATE ON public.curriculum_objectives
FOR EACH ROW
EXECUTE FUNCTION public.trigger_set_timestamp();

ALTER TABLE public.curriculum_units ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.curriculum_objectives ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read curriculum units" ON public.curriculum_units
    FOR SELECT
    USING (true);

CREATE POLICY "Allow public read curriculum objectives" ON public.curriculum_objectives
    FOR SELECT
    USING (true);

COMMIT;
