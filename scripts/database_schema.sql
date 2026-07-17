-- Ejecuta este código en el SQL Editor de tu panel de Supabase (https://app.supabase.com)

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS exercises (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_oa VARCHAR(255) NOT NULL,
    curso VARCHAR(50) NOT NULL,
    asignatura VARCHAR(100) NOT NULL,
    dificultad INT NOT NULL CHECK (dificultad >= 1 AND dificultad <= 10),
    contenido JSONB NOT NULL,
    feedback_inmediato JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índice para búsquedas ultra rápidas al buscar un ejercicio por subtema y nivel
CREATE INDEX IF NOT EXISTS idx_exercises_id_oa_dificultad ON exercises(id_oa, dificultad);
