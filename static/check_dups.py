import sys

html_path = 'c:/Users/Miguel Gonzalez/Downloads/CRMK/crmkuroda/static/index.html'

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

print("filter-promo-status count:", html.count('id="filter-promo-status"'))
print("filter-promo-proveedor count:", html.count('id="filter-promo-proveedor"'))
print("filter-promo-search count:", html.count('id="filter-promo-search"'))
print("filter-promo-sort count:", html.count('id="filter-promo-sort"'))
