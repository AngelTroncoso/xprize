import sys
sys.path.insert(0, 'xprize/backend')
from app.services.curriculum_manager import CurriculumManager

cm = CurriculumManager()
print(f"Loaded {len(cm.curriculum_data)} units")
print(f"Index size: {len(cm._oa_index)}")

results = cm.search_oa_by_course_and_subject('5° Básico', 'Matemática')
print(f'\nSearch "5° Básico" + "Matemática": {len(results)} results')
for r in results[:5]:
    print(f"  {r.get('id_oa')} | {r.get('curso')} | {r.get('asignatura')}")

# Try without accent
results2 = cm.search_oa_by_course_and_subject('5° Basico', 'Matematica')
print(f'\nSearch "5° Basico" + "Matematica": {len(results2)} results')