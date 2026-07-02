import sys

file_path = 'c:/Users/Miguel Gonzalez/Downloads/CRMK/crmkuroda/static/index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add menu item
menu_target = '<a href="#" class="menu-item" data-section="asignacion" id="menu-asignacion">\n                    <i class="fa-solid fa-people-arrows"></i> <span>Asignación</span>\n                </a>'

menu_replacement = menu_target + '\n                <a href="#" class="menu-item" data-section="api" id="menu-api">\n                    <i class="fa-brands fa-whatsapp"></i> <span>API WhatsApp</span>\n                </a>'

if menu_target in content:
    content = content.replace(menu_target, menu_replacement)
    print("Menu replaced successfully.")
else:
    print("Menu target not found.")

# 2. Add section
section_api = """
                <!-- Section: API WhatsApp -->
                <section id="section-api" class="dashboard-section hidden animate-fade-in">
                    <div class="card-header" style="margin-bottom: 24px;">
                        <h2><i class="fa-brands fa-whatsapp text-glow" style="margin-right: 8px; color: #25D366;"></i>Integración API WhatsApp</h2>
                        <p style="color: hsl(var(--text-secondary)); margin-top: 8px;">Configuración y documentación para la interacción vía WhatsApp.</p>
                    </div>

                    <div class="kpi-grid" style="grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));">
                        <!-- Documentation Card -->
                        <div class="glass-card">
                            <div class="card-header" style="border-bottom: 1px solid hsl(var(--border-color)); padding-bottom: 15px; margin-bottom: 15px;">
                                <h3><i class="fa-solid fa-book"></i> Manual de Usuario</h3>
                            </div>
                            <div style="color: hsl(var(--text-secondary)); font-size: 0.95rem; line-height: 1.6;">
                                <p>Los vendedores pueden enviar mensajes al bot para consultar sus datos en tiempo real.</p>
                                <ul style="margin-top: 10px; margin-left: 20px;">
                                    <li><code>!mis ventas</code>: Resumen de ventas del mes.</li>
                                    <li><code>!cotizacion [ID]</code>: Descarga PDF de cotización.</li>
                                    <li><code>!metas</code>: Estado actual de las metas.</li>
                                </ul>
                                <div style="margin-top: 15px; padding: 10px; background: rgba(37, 211, 102, 0.1); border-left: 3px solid #25D366; border-radius: 4px;">
                                    <strong>Nota:</strong> El número de teléfono debe estar registrado en el perfil del vendedor.
                                </div>
                            </div>
                        </div>

                        <!-- Config Card -->
                        <div class="glass-card">
                            <div class="card-header" style="border-bottom: 1px solid hsl(var(--border-color)); padding-bottom: 15px; margin-bottom: 15px;">
                                <h3><i class="fa-solid fa-gears"></i> Datos de Conexión</h3>
                            </div>
                            <form id="api-config-form">
                                <div class="input-group" style="margin-bottom: 15px;">
                                    <label>URL del Webhook (Para Meta/Twilio)</label>
                                    <input type="text" value="https://crmkuroda.railway.app/api/webhook/whatsapp" readonly style="background: rgba(0,0,0,0.2);">
                                </div>
                                <div class="input-group" style="margin-bottom: 15px;">
                                    <label>Token de Acceso (API Key)</label>
                                    <input type="password" value="sk_test_1234567890abcdef" readonly style="background: rgba(0,0,0,0.2);">
                                </div>
                                <div class="input-group" style="margin-bottom: 15px;">
                                    <label>Proveedor Actual</label>
                                    <select disabled style="background: rgba(0,0,0,0.2);">
                                        <option>Meta Cloud API (Oficial)</option>
                                        <option>Twilio</option>
                                        <option>Gupshup</option>
                                    </select>
                                </div>
                                <button type="button" class="btn btn-secondary" style="width: 100%;"><i class="fa-solid fa-copy"></i> Copiar Credenciales</button>
                            </form>
                        </div>
                    </div>
                </section>
"""

section_target = '            </div>\n        </main>'

if section_target in content:
    content = content.replace(section_target, section_api + '\n' + section_target)
    print("Section inserted successfully.")
else:
    print("Section target not found.")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
