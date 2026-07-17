import urllib.request
import re

html = urllib.request.urlopen('https://superprofesor-frontend-253925950091.us-central1.run.app/').read().decode('utf-8')
js_files = re.findall(r'href="(/_build/assets/[^\"]+\.js)"', html)
if not js_files:
    js_files = re.findall(r'src="(/_build/assets/[^\"]+\.js)"', html)
if not js_files:
    js_files = re.findall(r'href="(/assets/[^\"]+\.js)"', html)
if not js_files:
    js_files = re.findall(r'src="(/assets/[^\"]+\.js)"', html)

print('Found JS files:', js_files)
found = False
for js_file in js_files:
    js_url = 'https://superprofesor-frontend-253925950091.us-central1.run.app' + js_file
    js_code = urllib.request.urlopen(js_url).read().decode('utf-8', errors='ignore')
    if 'Volver al Cat' in js_code:
        print(f'Found "Volver al Cat" in {js_file}!')
        found = True

if not found:
    print('Did not find the text in any JS bundle.')
