"""Debug the search_oa_by_course_and_subject method."""
import json
import urllib.request
from urllib.parse import quote, unquote

# Test what FastAPI receives by checking the endpoint directly  
# First, check if "1° Básico" and "Matemática" match by making a direct call
# The issue is likely Unicode normalization (NFC vs NFD)

# Let's check the raw bytes from the server  
print("=" * 60)
print("Test: Direct call with URL encoding")
print("=" * 60)

url2 = "http://127.0.0.1:8000/api/curriculum/oas?curso=1%C2%B0%20B%C3%A1sico&asignatura=Matem%C3%A1tica"
print(f"URL: {url2}")

req = urllib.request.Request(url2)
with urllib.request.urlopen(req) as r:
    data = json.loads(r.read())
    print(f"Curso returned: {repr(data.get('curso'))}")
    print(f"Asignatura returned: {repr(data.get('asignatura'))}")
    print(f"Total count: {data.get('total_count')}")
    print(f"Data: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")

# Test 2: with unquoted URL
print("\n" + "=" * 60)
print("Test: Full list to see stored values")
print("=" * 60)

# Check what's stored for 1° Básico Matemática
url1 = "http://127.0.0.1:8000/api/curriculum/oas" 
with urllib.request.urlopen(url1) as r:
    data = json.loads(r.read())
    for unit in data.get('curriculum', []):
        if unit.get('curso') == "1° Básico" and unit.get('asignatura') == "Matemática":
            print(f"Found exact match - eje: {unit.get('eje_tematico')}, OAs: {len(unit.get('objetivos_aprendizaje', []))}")
            for oa in unit.get('objetivos_aprendizaje', []):
                print(f"  {oa['id_oa']}")
            # Direct debug of what search would match
            from urllib.parse import unquote
            curso_param = unquote("1%C2%B0%20B%C3%A1sico")
            asig_param = unquote("Matem%C3%A1tica")
            print(f"\nDecoded curso: {repr(curso_param)}")
            print(f"Decoded asignatura: {repr(asig_param)}")
            print(f"Stored curso: {repr(unit.get('curso'))}")
            print(f"Stored asig: {repr(unit.get('asignatura'))}")
            print(f"Match curso: {curso_param == unit.get('curso')}")
            print(f"Match asig: {asig_param == unit.get('asignatura')}")