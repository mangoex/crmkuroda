import sys

file_path = r'c:\Users\Miguel Gonzalez\Downloads\CRMK\crmkuroda\static\index.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

menu_item_target = '<a href="#" class="menu-item" data-section="promociones">'
menu_item_replacement = '''<a href="#" class="menu-item" data-section="inventario-abcf">
                    <i class="fa-solid fa-boxes-stacked"></i> <span>Inventario ABC+F</span>
                </a>
                <a href="#" class="menu-item" data-section="promociones">'''

if menu_item_target in content and 'data-section="inventario-abcf"' not in content:
    content = content.replace(menu_item_target, menu_item_replacement)

section_target = '<!-- Section 3: Promociones -->'
section_replacement = '''<!-- Section Inventario ABC+F -->
                <section id="section-inventario-abcf" class="dashboard-section hidden animate-fade-in">
                    <div class="panel-header" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                        <h2>Inventario ABC+F</h2>
                        <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
                            <form id="upload-inventario-abcf-form" onsubmit="event.preventDefault();" style="display: flex; gap: 10px; align-items: center; margin: 0;">
                                <label for="file-inventario-abcf" class="btn btn-secondary btn-sm" style="cursor: pointer; display: flex; align-items: center; gap: 8px; margin: 0; padding: 0.5rem 1rem;">
                                    <i class="fa-solid fa-file-excel"></i> <span id="file-inv-name">Seleccionar Archivo</span>
                                </label>
                                <input type="file" id="file-inventario-abcf" accept=".xlsx,.XLSX" required style="display: none;" onchange="document.getElementById('file-inv-name').textContent = this.files[0] ? this.files[0].name : 'Seleccionar Archivo';">
                                <button type="submit" class="btn btn-primary btn-sm"><i class="fa-solid fa-upload"></i> Subir Inventario</button>
                            </form>
                        </div>
                    </div>

                    <!-- Upload and Filter panel -->
                    <div class="glass-card filters-card margin-bottom" style="padding: 20px;">
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 20px; align-items: end;">
                            <div class="input-group">
                                <label for="filter-inv-sucursal" style="font-size: 0.85rem; color: hsl(var(--text-secondary));">Sucursal / Centro</label>
                                <select id="filter-inv-sucursal" class="form-control" style="width: 100%;">
                                    <option value="todos">Todos</option>
                                </select>
                            </div>
                            <div class="input-group">
                                <label for="filter-inv-abcf" style="font-size: 0.85rem; color: hsl(var(--text-secondary));">ABC+F</label>
                                <select id="filter-inv-abcf" class="form-control" style="width: 100%;">
                                    <option value="todos">Todos</option>
                                </select>
                            </div>
                            <div style="display: flex; flex-direction: column; gap: 6px; grid-column: 1 / -1;">
                                <label for="filter-inv-search" style="font-size: 0.85rem; color: hsl(var(--text-secondary));"><i class="fa-solid fa-magnifying-glass"></i> Buscar Material</label>
                                <div style="display: flex; gap: 10px;">
                                    <input type="text" id="filter-inv-search" class="form-control" placeholder="Código o Descripción..." style="flex-grow: 1;">
                                    <button type="button" id="btn-clear-inv-filters" class="btn btn-secondary" title="Limpiar Filtros" style="display: flex; align-items: center; gap: 8px;">
                                        <i class="fa-solid fa-filter-circle-xmark"></i> Limpiar Filtros
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Inventario Table -->
                    <div class="glass-card table-container" style="overflow-x: auto;">
                        <table class="data-table" id="table-inventario-abcf" style="min-width: 1200px;">
                            <thead>
                                <tr>
                                    <th>Centro</th>
                                    <th>Almacén</th>
                                    <th>ABC+F</th>
                                    <th>Código</th>
                                    <th>Descripción</th>
                                    <th>Cant Propia</th>
                                    <th>Inv. Consig.</th>
                                    <th>Precio Prom.</th>
                                    <th>Importe Inv.</th>
                                    <th>Ubicación</th>
                                </tr>
                            </thead>
                            <tbody>
                                <!-- Loaded dynamically -->
                            </tbody>
                        </table>
                        <div class="table-pagination" id="pag-inventario-abcf">
                            <!-- Loaded dynamically -->
                        </div>
                    </div>
                </section>

                <!-- Section 3: Promociones -->'''

if section_target in content and 'id="section-inventario-abcf"' not in content:
    content = content.replace(section_target, section_replacement)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Injected successfully')
