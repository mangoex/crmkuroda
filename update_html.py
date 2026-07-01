with open("static/index.html", "r", encoding="utf-8") as f:
    html = f.read()

old_section = """        <!-- SECTION: CONEXION -->
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
        </section>"""

# Sometimes the accents are messed up in Python due to encoding
import re

# We will just replace everything between <!-- SECTION: CONEXION --> and </section> after it.
start = html.find("<!-- SECTION: CONEXION -->")
end = html.find("</section>", start) + 10

if start != -1:
    new_section = """        <!-- SECTION: CONEXION -->
        <section id="section-conexion" class="dashboard-section hidden animate-fade-in">
            <div class="panel-header" style="margin-bottom: 24px;">
                <h2>Conexión de Datos (CSV a BD)</h2>
                <p style="font-size: 13px; color: hsl(var(--text-secondary)); margin-top: 4px;">Configura la sincronización de cotizaciones desde un archivo CSV de Google Drive.</p>
            </div>
            
            <div class="glass-card" style="padding: 24px; max-width: 800px;">
                <h3 style="margin: 0 0 16px 0; font-size: 16px;"><i class="fa-solid fa-link" style="color: #3b82f6; margin-right: 8px;"></i> Enlace a Google Drive</h3>
                <p style="font-size: 13px; color: hsl(var(--text-secondary)); margin-bottom: 20px;">
                    Pega aquí el enlace directo de exportación CSV de tu Google Sheet. Ejemplo: <code>https://docs.google.com/spreadsheets/d/TU_ID_AQUI/export?format=csv</code>
                </p>
                <div class="input-group">
                    <label for="csv-drive-url">URL del Archivo CSV</label>
                    <input type="url" id="csv-drive-url" placeholder="https://docs.google.com/spreadsheets/.../export?format=csv">
                </div>
                
                <div style="display: flex; gap: 12px; margin-top: 24px;">
                    <button id="btn-save-csv-url" class="btn btn-glow">
                        <i class="fa-solid fa-floppy-disk"></i> Guardar URL
                    </button>
                    <button id="btn-sync-csv" class="btn btn-secondary" style="background: hsl(var(--success)/10%); color: hsl(var(--success)); border-color: hsl(var(--success)/20%);">
                        <i class="fa-solid fa-rotate"></i> Sincronizar Ahora
                    </button>
                </div>
            </div>
        </section>"""
    html = html[:start] + new_section + html[end:]
    with open("static/index.html", "w", encoding="utf-8") as f:
        f.write(html)
