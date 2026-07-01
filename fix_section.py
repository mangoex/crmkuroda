with open("static/index.html", "r", encoding="utf-8") as f:
    html = f.read()

# remove from wrong location
wrong_section = """        <!-- SECTION: CONEXION -->
        <section id="section-conexion" class="dashboard-section hidden animate-fade-in">
            <div class="section-header">
                <h2>Conexión de Datos (CSV a BD)</h2>
                <p>Configura la sincronización de cotizaciones desde un archivo CSV de Google Drive.</p>
            </div>
            
            <div class="card glass-panel" style="max-width: 800px;">
                <div class="card-header">
                    <h3><i class="fa-solid fa-link text-primary"></i> Enlace a Google Drive</h3>
                </div>
                <div class="card-body">
                    <p class="text-sm" style="color: hsl(var(--text-secondary)); margin-bottom: 20px;">
                        Pega aquí el enlace directo de exportación CSV de tu Google Sheet.
                        Ejemplo: <code>https://docs.google.com/spreadsheets/d/TU_ID_AQUI/export?format=csv</code>
                    </p>
                    <div class="form-group">
                        <label for="csv-drive-url">URL del Archivo CSV:</label>
                        <input type="url" id="csv-drive-url" class="form-control" placeholder="https://docs.google.com/spreadsheets/...">
                    </div>
                    
                    <div style="display: flex; gap: 10px; margin-top: 20px;">
                        <button id="btn-save-csv-url" class="btn btn-primary">
                            <i class="fa-solid fa-floppy-disk"></i> Guardar URL
                        </button>
                        <button id="btn-sync-csv" class="btn btn-success">
                            <i class="fa-solid fa-rotate"></i> Sincronizar Cotizaciones Ahora
                        </button>
                    </div>
                </div>
            </div>
        </section>
"""

html = html.replace(wrong_section, "")

# find end of section-asignacion
start_idx = html.find('<section id="section-asignacion"')
if start_idx != -1:
    end_idx = html.find('</section>', start_idx)
    if end_idx != -1:
        # insert right after </section>
        insert_pos = end_idx + len('</section>')
        html = html[:insert_pos] + "\n" + wrong_section + html[insert_pos:]

with open("static/index.html", "w", encoding="utf-8") as f:
    f.write(html)
