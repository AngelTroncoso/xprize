-- 1. Habilitar extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Crear tabla de inquilinos (Tenants) para el modelo B2B SaaS
CREATE TABLE tenants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  settings JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Tabla de perfiles que extiende auth.users
CREATE TABLE profiles (
  id UUID PRIMARY KEY, -- Se vincula a auth.users(id)
  tenant_id UUID REFERENCES tenants(id) ON DELETE SET NULL,
  role TEXT NOT NULL CHECK (role IN ('student', 'teacher', 'admin')),
  full_name TEXT,
  avatar_url TEXT,
  grade_level TEXT,
  preferred_language TEXT DEFAULT 'es',
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Cursos
CREATE TABLE courses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  description TEXT,
  subject TEXT,
  grade_level TEXT,
  instructor_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
  is_published BOOLEAN DEFAULT false,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Módulos de aprendizaje
CREATE TABLE modules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  description TEXT,
  position INTEGER NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. Lecciones individuales
CREATE TABLE lessons (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  module_id UUID NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  content JSONB NOT NULL, -- Contenido flexible de la lección
  lesson_type TEXT CHECK (lesson_type IN ('text', 'video', 'interactive', 'ai_tutor')),
  position INTEGER NOT NULL,
  duration_minutes INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. Rutas de aprendizaje adaptativas
CREATE TABLE learning_paths (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  description TEXT,
  is_adaptive BOOLEAN DEFAULT false,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. Relación entre rutas de aprendizaje y cursos
CREATE TABLE learning_path_courses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  learning_path_id UUID NOT NULL REFERENCES learning_paths(id) ON DELETE CASCADE,
  course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
  position INTEGER NOT NULL,
  is_required BOOLEAN DEFAULT true,
  UNIQUE(learning_path_id, course_id)
);

-- 9. Matriculaciones
CREATE TABLE enrollments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  course_id UUID REFERENCES courses(id) ON DELETE CASCADE,
  learning_path_id UUID REFERENCES learning_paths(id) ON DELETE CASCADE,
  status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'paused', 'dropped')),
  enrolled_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);

-- 10. Evaluaciones
CREATE TABLE assessments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lesson_id UUID REFERENCES lessons(id) ON DELETE CASCADE,
  course_id UUID REFERENCES courses(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  assessment_type TEXT CHECK (assessment_type IN ('quiz', 'exam', 'homework', 'project')),
  questions JSONB NOT NULL, -- Estructura de preguntas para el evaluador/pedagógico
  max_score NUMERIC DEFAULT 100,
  time_limit_minutes INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 11. Entregas de evaluaciones por estudiantes
CREATE TABLE submissions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assessment_id UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
  student_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  answers JSONB NOT NULL,
  score NUMERIC,
  status TEXT DEFAULT 'submitted' CHECK (status IN ('submitted', 'graded', 'reviewed')),
  feedback JSONB, -- Feedback estructurado del Agente Validador
  submitted_at TIMESTAMPTZ DEFAULT NOW(),
  graded_at TIMESTAMPTZ
);

-- 12. Progreso de lecciones y módulos
CREATE TABLE user_progress (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  content_type TEXT NOT NULL CHECK (content_type IN ('lesson', 'module', 'course', 'learning_path')),
  content_id UUID NOT NULL,
  status TEXT DEFAULT 'not_started' CHECK (status IN ('not_started', 'in_progress', 'completed')),
  progress_pct NUMERIC DEFAULT 0 CHECK (progress_pct >= 0 AND progress_pct <= 100),
  last_accessed TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  metadata JSONB DEFAULT '{}',
  UNIQUE(student_id, content_type, content_id)
);

-- 13. Sesiones de chat con el tutor de IA
CREATE TABLE chat_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  lesson_id UUID REFERENCES lessons(id) ON DELETE SET NULL,
  title TEXT,
  model_version TEXT DEFAULT 'gemini-3.5-flash',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  metadata JSONB DEFAULT '{}'
);

-- 14. Historial de mensajes de chat
CREATE TABLE chat_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'tool')),
  content JSONB NOT NULL,
  token_count INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices de rendimiento
CREATE INDEX idx_profiles_tenant ON profiles(tenant_id);
CREATE INDEX idx_courses_tenant ON courses(tenant_id);
CREATE INDEX idx_enrollments_student ON enrollments(student_id);
CREATE INDEX idx_progress_student ON user_progress(student_id);
CREATE INDEX idx_submissions_student ON submissions(student_id);
CREATE INDEX idx_chat_sessions_student ON chat_sessions(student_id);
CREATE INDEX idx_chat_messages_session ON chat_messages(session_id, created_at);

-- RLS (Row Level Security)
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE courses ENABLE ROW LEVEL SECURITY;
ALTER TABLE enrollments ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE submissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
