import sys

file_path = 'c:/Users/Miguel Gonzalez/Downloads/CRMK/crmkuroda/static/index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find('<section id="section-api"')
end = content.find('</section>', start) + len('</section>')

if start != -1 and end != -1:
    old_section = content[start:end]
    new_section = """<section id="section-api" class="dashboard-section hidden animate-fade-in">
                    <div class="card-header" style="margin-bottom: 24px;">
                        <h2><i class="fa-brands fa-whatsapp text-glow" style="margin-right: 8px; color: #25D366;"></i>Conexión con WhatsApp</h2>
                        <p style="color: hsl(var(--text-secondary)); margin-top: 8px;">Vincula tu cuenta de WhatsApp Business para habilitar la interacción agéntica.</p>
                    </div>

                    <div class="glass-card" style="max-width: 600px; margin: 0 auto; text-align: center; padding: 40px 20px;">
                        
                        <!-- Estado Desconectado -->
                        <div id="wa-status-disconnected">
                            <div style="width: 80px; height: 80px; background: rgba(37, 211, 102, 0.1); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 20px;">
                                <i class="fa-brands fa-whatsapp" style="font-size: 40px; color: #25D366;"></i>
                            </div>
                            
                            <h3 style="margin-bottom: 10px;">No estás conectado</h3>
                            <p style="color: hsl(var(--text-secondary)); font-size: 0.95rem; line-height: 1.6; margin-bottom: 30px;">
                                Para comenzar a recibir solicitudes de tus vendedores a través de WhatsApp, necesitas conectar tu cuenta de WhatsApp Business oficial usando Facebook.
                            </p>
                            
                            <button type="button" class="btn btn-primary" style="background: #1877F2; border-color: #1877F2; font-size: 1.1rem; padding: 12px 24px; display: inline-flex; align-items: center; gap: 10px; width: 100%; max-width: 300px; justify-content: center;">
                                <i class="fa-brands fa-facebook"></i> Conectar con Meta
                            </button>
                            
                            <div style="margin-top: 30px; text-align: left; background: rgba(0,0,0,0.2); padding: 15px; border-radius: 8px; font-size: 0.85rem;">
                                <strong style="color: hsl(var(--text-primary));">¿Cómo funciona?</strong>
                                <ol style="margin-top: 10px; padding-left: 20px; color: hsl(var(--text-secondary)); line-height: 1.5;">
                                    <li>Haz clic en "Conectar con Meta".</li>
                                    <li>Inicia sesión con tu cuenta de Facebook (administrador de Business Manager).</li>
                                    <li>Selecciona o crea tu cuenta de WhatsApp Business y tu número.</li>
                                    <li>Autoriza los permisos y ¡listo!</li>
                                </ol>
                            </div>
                        </div>
                        
                        <!-- Estado Conectado (Oculto por defecto) -->
                        <div id="wa-status-connected" class="hidden">
                            <div style="width: 80px; height: 80px; background: rgba(37, 211, 102, 0.2); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 20px; border: 2px solid #25D366;">
                                <i class="fa-solid fa-check" style="font-size: 35px; color: #25D366;"></i>
                            </div>
                            
                            <h3 style="margin-bottom: 10px; color: #25D366;">¡Conexión Exitosa!</h3>
                            <p style="color: hsl(var(--text-secondary)); font-size: 0.95rem; line-height: 1.6; margin-bottom: 30px;">
                                Tu sistema ahora está escuchando mensajes de WhatsApp.
                            </p>
                            
                            <div style="background: rgba(0,0,0,0.2); padding: 20px; border-radius: 8px; text-align: left; margin-bottom: 30px;">
                                <div style="display: flex; justify-content: space-between; border-bottom: 1px solid hsl(var(--border-color)); padding-bottom: 10px; margin-bottom: 10px;">
                                    <span style="color: hsl(var(--text-secondary));">Número Asociado:</span>
                                    <strong style="color: hsl(var(--text-primary));">+52 686 903 2840</strong>
                                </div>
                                <div style="display: flex; justify-content: space-between; border-bottom: 1px solid hsl(var(--border-color)); padding-bottom: 10px; margin-bottom: 10px;">
                                    <span style="color: hsl(var(--text-secondary));">WABA ID:</span>
                                    <strong style="color: hsl(var(--text-primary));">1511483567038034</strong>
                                </div>
                                <div style="display: flex; justify-content: space-between;">
                                    <span style="color: hsl(var(--text-secondary));">Business ID:</span>
                                    <strong style="color: hsl(var(--text-primary));">248668109015895</strong>
                                </div>
                            </div>
                            
                            <button type="button" class="btn btn-danger" style="background: transparent; border: 1px solid #ef4444; color: #ef4444;">
                                Revocar Acceso
                            </button>
                        </div>

                    </div>
                </section>"""
    
    content = content.replace(old_section, new_section)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Section replaced successfully (Client UI).")
else:
    print("Could not find section-api")
