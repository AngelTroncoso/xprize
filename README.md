# Super_Profesor

Super_Profesor es un entorno educativo hiperpersonalizado e impulsado por una arquitectura multi-agente que adapta el aprendizaje a los ritmos y estilos del estudiante.

## Arquitectura

El sistema utiliza una topología **Master-Agent** coordinando tres roles especializados:
1. **Agente Evaluador (Gemini 3.5 Flash)**: Realiza diagnósticos y mapas de debilidades en tiempo real.
2. **Agente Pedagógico (Gemini 3.1 Pro)**: Adapta el plan de estudio y crea analogías personalizadas.
3. **Agente Validador (Gemini 3.5 Flash)**: Evalúa el código y ejercicios entregados por el alumno de forma instantánea.

## Estructura del Proyecto

* `/frontend`: Aplicación en Next.js (App Router) con interfaz premium (Tailwind CSS, Monaco Editor, Recharts, Framer Motion).
* `/backend`: API en FastAPI (Python) para la gestión del flujo multi-agente y la API de Gemini.
* `/supabase`: Migraciones y configuración de base de datos.
