# 🤖 INTEGRACIÓN CURRICULAR PARA AGENTES

Cada agente en Super_Profesor debe consultar el currículo oficial de MINEDUC Chile antes de actuar.

---

## AGENTE EVALUADOR 🏆

**Responsabilidad**: Diagnosticar si un alumno domina un `id_oa` específico.

### Datos Críticos
```python
# 1. OBTENER INDICADORES (lo más importante)
indicators = curriculum_manager.get_evaluation_indicators("OA_06")
# Retorna: ["Usan estrategias personales con y sin material concreto.",
#           "Crean y resuelven problemas de adición y sustracción.",
#           "Aplican algoritmos con y sin reserva..."]

# 2. OBTENER CONCEPTOS (para validación secundaria)
concepts = curriculum_manager.get_key_concepts("OA_06")
# Retorna: ["adicion", "sustraccion", "algoritmos"]
```

### Protocolo de Evaluación

```
┌─────────────────────────────────────────────────────────────┐
│ 1. RECIBIR respuesta del alumno para OA_06                  │
├─────────────────────────────────────────────────────────────┤
│ 2. OBTENER indicadores → ["Usan estrategias...", ...]        │
├─────────────────────────────────────────────────────────────┤
│ 3. VALIDAR: ¿Demuestra ALGUNO de los indicadores?           │
│    ✅ SÍ → VEREDICTO: "MASTERED" o "PARTIAL"                │
│    ❌ NO → ¿Demuestra concepto? Si no → "NOT_MASTERED"      │
├─────────────────────────────────────────────────────────────┤
│ 4. REGISTRAR: Update student_oa_progress en Supabase        │
│    - mastery_level                                          │
│    - evaluation_history                                     │
│    - last_evaluation_date                                   │
└─────────────────────────────────────────────────────────────┘
```

### Reglas Estrictas

- ⛔ **NUNCA inventar criterios de evaluación**. Usar SOLO `indicadores_evaluacion` del OA.
- ⛔ **NUNCA cambiar el nivel de dominio sin evidencia clara**.
- ✅ **SIEMPRE incluir la cita del indicador** en la explicación al alumno.
- ✅ **SIEMPRE registrar el historial** en `evaluation_history`.

### Ejemplo

```
ALUMNO: "Resuelvo 45 + 28 usando descomposición: 45 + 20 = 65, 65 + 8 = 73"

AGENTE EVALUADOR:
1. Obtiene indicadores de OA_04:
   - "Usan la descomposición de números." ← MATCH
   - "Completan sumas hasta la decena más cercana."
   - ...

2. Conclusión: ✅ Demuestra "Usan la descomposición" claramente
3. Veredicto: MASTERED (OA_04)
4. Feedback: "Excelente. Usaste descomposición correctamente, que es 
             un indicador clave del OA_04. ¡Sigue así!"
```

---

## AGENTE PEDAGÓGICO 📚

**Responsabilidad**: Diseñar lecciones, analogías y ejercicios alineados con los `conceptos_clave`.

### Datos Críticos

```python
# 1. OBTENER CONCEPTOS DEL OA
concepts = curriculum_manager.get_key_concepts("OA_08")
# Retorna: ["multiplicacion", "tablas de multiplicar", "sumas repetidas"]

# 2. OBTENER DESCRIPCIÓN Y CONTEXTO
oa = curriculum_manager.get_oa_by_id("OA_08")
# Retorna: Descripción completa, curso, asignatura, eje temático
```

### Protocolo de Diseño de Lección

```
┌──────────────────────────────────────────────────────────────┐
│ 1. RECIBIR: Alumno quiere aprender OA_08                    │
├──────────────────────────────────────────────────────────────┤
│ 2. OBTENER conceptos_clave: ["multiplicacion", ...]          │
├──────────────────────────────────────────────────────────────┤
│ 3. DISEÑAR lección con:                                      │
│    - Analogía personalizad a interés del alumno              │
│    - Ejercicios que exploren cada concepto                   │
│    - Evaluación rápida que valide comprensión               │
├──────────────────────────────────────────────────────────────┤
│ 4. INCLUIR: Indicadores_evaluacion como punto de evaluación │
│    (para que Agente Evaluador sepa qué buscar)              │
└──────────────────────────────────────────────────────────────┘
```

### Reglas Estrictas

- ✅ **Toda analogía DEBE anclar en los `conceptos_clave`**.
  - ❌ MAL: "Piensa en multiplicación como... magia"
  - ✅ BIEN: "Multiplicación es suma repetida: 3×4 = 4+4+4"

- ✅ **Todo ejercicio DEBE validar UN concepto clave mínimo**.
- ✅ **Incluir indicadores_evaluacion en instrucciones** de ejercicio para claridad.
- ⛔ **NUNCA desviarse del currículo oficial** (no añadir OA extra).

### Ejemplo

```
ALUMNO: "Quiero aprender OA_08 (Tablas de multiplicar). Me gustan los videjuegos."

AGENTE PEDAGÓGICO:
1. Obtiene conceptos: ["multiplicacion", "tablas de multiplicar", "sumas repetidas"]
2. Diseña lección:
   ANALOGÍA: "En un videojuego de estrategia, tienes 3 grupos de enemigos.
             Cada grupo tiene 4 enemigos. 3×4 = 3+4+4+4 = 12 enemigos totales.
             Eso es multiplicación como suma repetida."
   
   EJERCICIO: "En tu juego, hay 5 torres de defensa. Cada una tiene 7 soldados.
              ¿Cuántos soldados en total? Dibuja y suma repetidamente."
   
   VALIDACIÓN: Busca evidencia de "sumas repetidas" (indicador oficial)
```

---

## AGENTE ORQUESTADOR 🎯

**Responsabilidad**: Coordinar el flujo de aprendizaje del alumno siguiendo el currículo.

### Datos Críticos

```python
# 1. OBTENER TODOS LOS OA DE UN CURSO
oas = curriculum_manager.search_oa_by_course_and_subject("3ro Basico", "Matematica")
# Retorna: Lista de 11 OA en orden [OA_01, OA_02, ..., OA_11]

# 2. OBTENER PROGRESO DEL ALUMNO
# (Consulta al frontend o a Supabase)
progress = {
  "OA_01": "mastered",
  "OA_02": "partial",
  "OA_03": "not_started",
  ...
}
```

### Protocolo de Orquestación

```
┌──────────────────────────────────────────────────────────────┐
│ 1. CARGAR currículo completo del alumno                      │
├──────────────────────────────────────────────────────────────┤
│ 2. MAPEAR estado actual vs. currículo                        │
├──────────────────────────────────────────────────────────────┤
│ 3. PRIORIZAR siguiente OA:                                   │
│    a) Si hay "partial" → REFORZAR primero                    │
│    b) Si hay "not_started" → INICIAR próximo                │
│    c) Si todo "mastered" → EXPANDIR (OA avanzados)          │
├──────────────────────────────────────────────────────────────┤
│ 4. ROTAR AGENTES en el orden correcto:                       │
│    Evaluador → Pedagógico → Validador → Registrar           │
└──────────────────────────────────────────────────────────────┘
```

### Reglas Estrictas

- ✅ **RESPETAR el orden curricular**: No saltar OA sin justificación.
- ✅ **PRIORIZAR refuerzo**: Antes que avanzar, dominar lo actual.
- ✅ **DOCUMENTAR decisiones**: Por qué se elige el próximo OA.
- ⛔ **NUNCA modificar indicadores_evaluacion ni conceptos_clave**.

### Ejemplo de Flujo

```
ALUMNO: Estudiante de 3ro Básico, sesión del día

ORQUESTADOR EJECUTA:
1. Carga currículo: 11 OA de Números y Operaciones
2. Verifica progreso:
   - OA_01, OA_02: MASTERED ✓
   - OA_03: PARTIAL ⚠️ (2 evaluaciones, errores en tabla posicional)
   - OA_04 a OA_11: NOT_STARTED

3. DECISIÓN: "OA_03 requiere refuerzo. Derivar a Pedagógico para lección de refuerzo."
   RATIONALE: El indicador "tabla posicional" no está completamente dominado.

4. FLUJO:
   Pedagógico → Diseña lección reforzada en "tabla posicional"
   ↓
   Alumno intenta ejercicio
   ↓
   Evaluador → Valida contra indicadores oficiales
   ↓
   Resultado: Si domina → pasar a OA_04. Si no → refuerzo adicional.
```

---

## 📊 RESUMEN: QUIÉN USA QUÉ

| Método | Agente Evaluador | Agente Pedagógico | Agente Orquestador |
|--------|-----------------|-------------------|-------------------|
| `get_oa_by_id()` | Contexto | Contexto | ✅ (carga) |
| `get_evaluation_indicators()` | ✅ (validación) | Secundario | - |
| `get_key_concepts()` | Secundario | ✅ (diseño) | - |
| `search_oa_by_course_and_subject()` | - | - | ✅ (carga) |
| `search_oa_by_concept()` | ✅ (diagnóstico) | - | - |

---

## 🔄 FLUJO COMPLETO INTEGRADO

```
ALUMNO RESPONDE A PREGUNTA
   ↓
AGENTE EVALUADOR:
  1. get_evaluation_indicators(oa_id)
  2. Valida respuesta contra indicadores
  3. Registra veredicto en student_oa_progress
   ↓
SI DOMINA:
  AGENTE ORQUESTADOR:
  1. search_oa_by_course_and_subject()
  2. Identifica próximo OA
   ↓
AGENTE PEDAGÓGICO:
  1. get_key_concepts(next_oa_id)
  2. Diseña lección nueva
   ↓
SI NO DOMINA:
  AGENTE PEDAGÓGICO:
  1. get_key_concepts(current_oa_id)
  2. Crea lección reforzada
  3. Enfatiza conceptos débiles
   ↓
FRONTEND:
  GET /api/curriculum/student/{id}/progress
  Grafica: [OA_01✓, OA_02✓, OA_03⚠️, OA_04□, ...]
```

---

## ⚙️ INICIALIZACIÓN EN CODE

Todos los agentes deben INICIALIZAR el curriculum_manager:

```python
from app.services.curriculum_manager import CurriculumManager

# En __init__ o setup del agente:
self.curriculum_manager = CurriculumManager()

# Ahora puede usar:
oa_data = self.curriculum_manager.get_oa_by_id("OA_04")
indicators = self.curriculum_manager.get_evaluation_indicators("OA_04")
```

---

## 🚨 CHECKLIST DE ALINEACIÓN

Antes de cada respuesta/acción del agente:

- [ ] ¿Consulté el currículo oficial (JSON)?
- [ ] ¿Usé SOLO indicadores/conceptos del OA?
- [ ] ¿Documenté la alineación curricular?
- [ ] ¿Registré el cambio de estado del alumno?
- [ ] ¿Validé que las analogías anclaron en conceptos_clave?
- [ ] ¿Respeto el orden y la jerarquía curricular?

✅ Si todas las respuestas son SÍ → Acción autorizada
❌ Si alguna es NO → REVISAR y CORREGIR
