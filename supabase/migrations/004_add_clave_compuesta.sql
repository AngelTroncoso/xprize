-- 004_add_clave_compuesta.sql
-- Agrega campo clave_compuesta a curriculum_objectives para búsquedas rápidas
-- Formato: "{id_oa}|{curso}|{asignatura}"

ALTER TABLE public.curriculum_objectives 
    ADD COLUMN IF NOT EXISTS clave_compuesta text;

-- Generar las claves para registros existentes
UPDATE public.curriculum_objectives
SET clave_compuesta = id_oa || '|' || curso || '|' || asignatura
WHERE clave_compuesta IS NULL;

-- Hacer el campo único (junto con id_oa, curso, asignatura ya son únicos, pero clave_compuesta es la clave de búsqueda)
CREATE UNIQUE INDEX IF NOT EXISTS idx_curriculum_objectives_clave_compuesta
    ON public.curriculum_objectives (clave_compuesta);

-- Política RLS pública para lectura (heredada de las políticas existentes, pero explícita por claridad)
CREATE POLICY "Allow public read curriculum objectives clave" ON public.curriculum_objectives
    FOR SELECT
    USING (true);