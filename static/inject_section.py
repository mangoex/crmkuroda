import sys

file_path = 'c:/Users/Miguel Gonzalez/Downloads/CRMK/crmkuroda/static/index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find('<section id="section-api"')
end = content.find('</section>', start) + len('</section>')

if start != -1 and end != -1:
    old_section = content[start:end]
    new_section = """<section id="section-api" class="dashboard-section hidden animate-fade-in">
                    <div class="card-header" style="margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h2><i class="fa-brands fa-whatsapp text-glow" style="margin-right: 8px; color: #25D366;"></i>Conectar WhatsApp</h2>
                            <p style="color: hsl(var(--text-secondary)); margin-top: 8px;">Positivala - Embedded Signup oficial de Meta.</p>
                        </div>
                        <span class="badge badge-primary" style="background: rgba(37, 211, 102, 0.2); color: #25D366; border: 1px solid #25D366;">LISTO PARA ABRIR EMBEDDED SIGNUP</span>
                    </div>

                    <div class="kpi-grid" style="grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 24px;">
                        
                        <!-- Columna 1: Embedded Signup -->
                        <div class="glass-card" style="display: flex; flex-direction: column;">
                            <div class="card-header" style="margin-bottom: 20px;">
                                <h3 style="font-size: 1.2rem;">Embedded Signup</h3>
                            </div>
                            <div style="color: hsl(var(--text-secondary)); font-size: 0.95rem; line-height: 1.6; margin-bottom: 20px;">
                                Usa este flujo cuando el cliente conecta su propio WABA/numero. El token se guarda cifrado como integracion <code style="background: rgba(0,0,0,0.3); padding: 2px 6px; border-radius: 4px;">whatsapp_cloud</code>.
                            </div>
                            
                            <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 20px;">
                                <button type="button" class="btn btn-primary" style="background: #0f766e; border-color: #0f766e; padding: 10px 15px;">Abrir Embedded Signup</button>
                                <button type="button" class="btn btn-secondary" style="padding: 10px 15px;">Diagnostico</button>
                                <button type="button" class="btn btn-secondary" style="padding: 10px 15px;">Enviar prueba</button>
                                <button type="button" class="btn btn-secondary" style="padding: 10px 15px;">Plantillas</button>
                            </div>
                            
                            <div style="margin-top: auto; color: hsl(var(--text-secondary)); font-size: 0.9rem;">
                                Esperando conexion.
                            </div>
                        </div>

                        <!-- Columna 2: Guardar conexion -->
                        <div class="glass-card">
                            <div class="card-header" style="margin-bottom: 20px;">
                                <h3 style="font-size: 1.2rem;">Guardar conexion</h3>
                            </div>
                            <form id="api-config-form" style="display: flex; flex-direction: column; gap: 16px;">
                                
                                <div class="input-group">
                                    <label style="font-size: 0.85rem; font-weight: 600; color: hsl(var(--text-primary));">Authorization code de Meta</label>
                                    <input type="text" placeholder="" style="background: transparent; border: 1px solid hsl(var(--border-color));">
                                </div>
                                
                                <div class="input-group">
                                    <label style="font-size: 0.85rem; font-weight: 600; color: hsl(var(--text-primary));">Access token temporal/manual</label>
                                    <div style="position: relative;">
                                        <input type="password" placeholder="" style="background: transparent; border: 1px solid hsl(var(--border-color)); width: 100%; padding-right: 40px;">
                                        <button type="button" style="position: absolute; right: 10px; top: 50%; transform: translateY(-50%); background: none; border: none; color: hsl(var(--text-secondary)); cursor: pointer;">
                                            <i class="fa-regular fa-eye"></i>
                                        </button>
                                    </div>
                                </div>
                                
                                <div class="input-group">
                                    <label style="font-size: 0.85rem; font-weight: 600; color: hsl(var(--text-primary));">Business ID</label>
                                    <input type="text" value="248668109015895" style="background: transparent; border: 1px solid hsl(var(--border-color));">
                                </div>
                                
                                <div class="input-group">
                                    <label style="font-size: 0.85rem; font-weight: 600; color: hsl(var(--text-primary));">WABA ID</label>
                                    <input type="text" value="1511483567038034" style="background: transparent; border: 1px solid hsl(var(--border-color));">
                                </div>
                                
                                <div class="input-group">
                                    <label style="font-size: 0.85rem; font-weight: 600; color: hsl(var(--text-primary));">Phone Number ID</label>
                                    <input type="text" value="1173938019132326" style="background: transparent; border: 1px solid hsl(var(--border-color));">
                                </div>
                                
                                <div class="input-group">
                                    <label style="font-size: 0.85rem; font-weight: 600; color: hsl(var(--text-primary));">Numero visible</label>
                                    <input type="text" value="+526869032840" style="background: transparent; border: 1px solid hsl(var(--border-color));">
                                </div>
                                
                                <div style="margin-top: 10px;">
                                    <button type="button" class="btn btn-primary" style="background: #0f172a; border: 1px solid #1e293b; color: white;">Guardar conexion cifrada</button>
                                </div>
                            </form>
                        </div>

                    </div>
                </section>"""
    
    content = content.replace(old_section, new_section)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Section replaced successfully.")
else:
    print("Could not find section-api")
