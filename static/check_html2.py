import sys
html_path = 'c:/Users/Miguel Gonzalez/Downloads/CRMK/crmkuroda/static/index.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

start = html.find('class="glass-card filters-card')
print(html[max(0, start-100):start+1500])
