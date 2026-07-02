import sys

css_path = 'c:/Users/Miguel Gonzalez/Downloads/CRMK/crmkuroda/static/style.css'
with open(css_path, 'r', encoding='utf-8') as f:
    css = f.read()

import re
matches = re.findall(r'(\.[a-zA-Z0-9_-]+)\s*\{', css)
print("Classes:", set(matches))
