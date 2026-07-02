import sys

f = open('c:/Users/Miguel Gonzalez/Downloads/CRMK/crmkuroda/static/index.html', encoding='utf-8')
content = f.read()
start = content.find('id="section-asignacion"')
if start != -1:
    end = content.find('</section>', start)
    print(content[end-20:end+100])
else:
    print("Not found")
