# 📚 GUÍA DE ALINEACIÓN CURRICULAR MINEDUC CHILE

## ESTRUCTURA INDEXADA

El sistema ha ingestado oficialmente el currículo de 3ro Básico - Matemática - Eje "Números y Operaciones". 

Todos los OA están indexados en `CurriculumManager` con acceso O(1).

```
curriculum_manager.get_oa_by_id("OA_04")
# Retorna:
{
  "id_oa": "OA_04",
  "curso": "3ro Basico",
  "asignatura": "Matematica",
  "eje_tematico": "Numeros y Operaciones",
  "descripcion": "Describir y aplicar estrategias de cálculo mental para las adiciones y sustracciones hasta 100.",
  "indicadores_evaluacion": [
    "Usan la descomposición de números.",
    "Completan sumas hasta la decena más cercana.",
    ...
  ],
  "conceptos_clave": ["calculo mental", "adicion", "sustraccion"]
}
```

---

## API DE CURRICULUM_MANAGER

### 1. **Consulta por ID de OA** (Agente Evaluador)
```python
oa_data = curriculum_manager.get_oa_by_id("OA_06")
```
**Retorna**: Dict con todos los datos del OA (descripción, indicadores, conceptos).

**Uso**: El Agente Evaluador debe SIEMPRE usar esto para obtener los criterios oficiales antes de evaluar.

---

### 2. **Obtener Indicadores de Evaluación** (Agente Evaluador)
```python
indicators = curriculum_manager.get_evaluation_indicators("OA_08")
# Retorna: ["Usan representaciones concretas y pictóricas.", "Expresan la multiplicación como suma...", ...]
```
**Uso**: Estos son los ÚNICOS criterios válidos. Una respuesta del alumno es "correcta" si demuestra **al menos uno** de estos indicadores.

---

### 3. **Obtener Conceptos Clave** (Agente Pedagógico)
```python
concepts = curriculum_manager.get_key_concepts("OA_04")
# Retorna: ["calculo mental", "adicion", "sustraccion"]
```
**Uso**: El Agente Pedagógico debe anclar analogías y ejercicios en estos conceptos exactos.

---

### 4. **Buscar OA por Curso y Asignatura** (Agente Orquestador)
```python
oas = curriculum_manager.search_oa_by_course_and_subject("3ro Basico", "Matematica")
# Retorna: Lista de 11 OA de 3ro Básico - Matemática
```
**Uso**: Para cargar el camino de aprendizaje completo de un estudiante.

---

### 5. **Buscar OA por Concepto Clave** (Agente Evaluador)
```python
oa_ids = curriculum_manager.search_oa_by_concept("multiplicacion")
# Retorna: ["OA_08", "OA_09"]
```
**Uso**: Cuando un alumno comete un error en un concepto, identificar rápidamente qué OA(s) necesita reforzar.

---

## PROTOCOLO PARA EVALUACIÓN

### Paso 1: Obtener OA Oficial
```python
oa_id = "OA_06"  # El OA siendo evaluado
oa_data = curriculum_manager.get_oa_by_id(oa_id)
indicators = oa_data["indicadores_evaluacion"]
```

### Paso 2: Validar Respuesta del Alumno
La respuesta es **"DOMINA"** si demuestra:
- ✅ Comprensión de **al menos 1** indicador de evaluación, O
- ✅ Aplicación correcta de **al menos 1** concepto clave

La respuesta es **"PARCIAL"** si:
- ⚠️ Demuestra 1 indicador pero con errores menores, O
- ⚠️ Demuestra comprensión de concepto pero no del indicador completo

La respuesta es **"NO DOMINA"** si:
- ❌ No demuestra ningún indicador, O
- ❌ No aplica ningún concepto clave correctamente

---

## PROTOCOLO PARA DISEÑO DE RUTAS DE APRENDIZAJE

### Paso 1: Cargar Currículo del Estudiante
```python
curso = "3ro Basico"
asignatura = "Matematica"
oas = curriculum_manager.search_oa_by_course_and_subject(curso, asignatura)
# Retorna: Lista ordenada de 11 OA (OA_01 → OA_11)
```

### Paso 2: Mapear Estado de Cada OA
Desde la BD de progreso:
```
{
  "OA_01": "mastered",
  "OA_02": "partial",
  "OA_03": "not_started",
  ...
}
```

### Paso 3: Generar Próximos Pasos
Prioridad:
1. **Completar**: OA en estado `partial` (reforzar)
2. **Iniciar**: Primer OA en estado `not_started` que tenga prereq dominados
3. **Expandir**: OA avanzados si hay tiempo

---

## CAMPOS CRÍTICOS DEL INDICE

| Campo | Descripción | Usado Por |
|-------|-------------|-----------|
| `id_oa` | Identificador único (OA_01, OA_02, ...) | Todos los agentes |
| `descripcion` | Enunciado oficial del OA | Agente Pedagógico (contexto) |
| `indicadores_evaluacion` | Criterios de evaluación | Agente Evaluador (validación) |
| `conceptos_clave` | Conceptos a dominar | Agente Pedagógico (analogías, ejercicios) |
| `curso` | Grado (3ro Basico, etc.) | Agente Orquestador |
| `asignatura` | Asignatura (Matematica, etc.) | Agente Orquestador |
| `eje_tematico` | Eje temático (Números y Operaciones) | Navegación |

---

## EJEMPLO COMPLETO: Evaluar OA_08 (Multiplicación)

```python
# 1. Obtener datos del OA
oa_id = "OA_08"
oa = curriculum_manager.get_oa_by_id(oa_id)

# 2. Alumno intenta resolver: "Dibuja 3 grupos de 4 puntos y escribe la multiplicación"
student_answer = """
●●●●
●●●●
●●●●

3 × 4 = 12
"""

# 3. Validar contra indicadores
indicators = oa["indicadores_evaluacion"]
# ["Usan representaciones concretas y pictóricas.",
#  "Expresan la multiplicación como suma de sumandos iguales.",
#  ...]

# 4. Conclusión: ✅ Demuestra "representaciones concretas y pictóricas"
# → Veredicto: MASTERED para OA_08
```

---

## NOTAS OPERACIONALES

- ⚡ **Velocidad**: El índice `_oa_index` permite búsquedas O(1) por `id_oa`
- 🔐 **Inmutabilidad**: El currículo JSON es de MINEDUC Chile oficial. No modificar manualmente.
- 📊 **Historial**: El estado de cada alumno en cada OA se guarda en `OAProgressRecord` de Supabase
- 🔄 **Retroalimentación**: Cada evaluación impacta automáticamente el estado del OA en el historial del estudiante
