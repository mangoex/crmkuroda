import sys

file_path = 'c:/Users/Miguel Gonzalez/Downloads/CRMK/crmkuroda/static/index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find('<section id="section-api"')
end = content.find('</section>', start) + len('</section>')

if start != -1 and end != -1:
    old_section = content[start:end]
    new_section = """<section id="section-api" class="dashboard-section hidden animate-fade-in" style="max-width: 800px; margin: 0 auto; color: #e2e8f0;">
                    <div class="card-header" style="margin-bottom: 30px;">
                        <h2 style="font-size: 2rem; color: #ffffff; font-weight: 700;">Configuración de Empresa</h2>
                        <p style="color: hsl(var(--text-secondary)); margin-top: 8px;">Administración del Tech Provider y credenciales de WhatsApp</p>
                    </div>

                    <!-- Bloque 1: Integración con Asistto -->
                    <div class="glass-card" style="margin-bottom: 30px; padding: 30px; border: 1px solid rgba(255,255,255,0.05); background: rgba(15, 23, 42, 0.6);">
                        <h3 style="display: flex; align-items: center; font-size: 1.3rem; color: #ffffff; margin-bottom: 20px;">
                            <i class="fa-solid fa-plug" style="color: #a855f7; margin-right: 12px; font-size: 1.1rem;"></i> Integración con Asistto (Tech Provider)
                        </h3>
                        
                        <p style="font-size: 0.95rem; margin-bottom: 25px;">Para conectar tu <strong>Coach-Agent</strong> con tu número actual de Asistto, sigue estos pasos:</p>
                        
                        <div style="margin-bottom: 25px;">
                            <h4 style="color: #ffffff; margin-bottom: 10px; font-size: 1rem;">Paso 1: Enviar mensajes (Coach-Agent -> Vendedor)</h4>
                            <p style="font-size: 0.9rem; color: #cbd5e1; line-height: 1.6;">
                                Copia el <strong>Phone Number ID</strong> y el <strong>Access Token</strong> desde la pantalla "Meta Embedded Signup" de Asistto y pégalos en la sección de abajo. Esto nos permitirá enviar las plantillas directo desde Meta.
                            </p>
                        </div>
                        
                        <div style="margin-bottom: 25px;">
                            <h4 style="color: #ffffff; margin-bottom: 10px; font-size: 1rem;">Paso 2: Recibir mensajes (Vendedor -> Coach-Agent)</h4>
                            <p style="font-size: 0.9rem; color: #cbd5e1; line-height: 1.6; margin-bottom: 15px;">
                                Envía un correo o mensaje a soporte de Asistto pidiendo que redirijan los mensajes entrantes de tu equipo a nuestra URL usando su función de <code>WEBHOOK_POST</code>.
                            </p>
                            
                            <div style="background: rgba(0,0,0,0.4); border-radius: 8px; padding: 15px; display: flex; flex-direction: column; gap: 10px; margin-bottom: 15px;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <span style="font-weight: 600; color: #ffffff; font-size: 0.9rem;">Tu URL de Webhook:</span>
                                    <button class="btn btn-secondary btn-sm" style="background: rgba(255,255,255,0.1); border: none; padding: 5px 10px;"><i class="fa-regular fa-copy"></i> Copiar</button>
                                </div>
                                <code style="color: #06b6d4; font-family: monospace; font-size: 0.9rem; word-break: break-all;">https://crmkuroda.railway.app/api/whatsapp/webhook/asistto</code>
                            </div>
                            
                            <div style="background: rgba(255,255,255,0.05); border-left: 3px solid #64748b; padding: 15px; border-radius: 4px; font-style: italic; color: #94a3b8; font-size: 0.9rem;">
                                "Hola equipo de Asistto. Necesito que los mensajes de WhatsApp provenientes de los números de mis vendedores sean ignorados por su bot y reenviados mediante WEBHOOK_POST (con payload {'phone': '+52...', 'message': '...'}) a esta URL."
                            </div>
                        </div>
                    </div>

                    <!-- Bloque 2: Credenciales de la Empresa -->
                    <div class="glass-card" style="padding: 30px; border: 1px solid rgba(255,255,255,0.05); background: rgba(15, 23, 42, 0.6);">
                        <h3 style="display: flex; align-items: center; font-size: 1.3rem; color: #ffffff; margin-bottom: 25px;">
                            <i class="fa-regular fa-building" style="color: #8b5cf6; margin-right: 12px;"></i> Credenciales de la Empresa
                        </h3>
                        
                        <form id="empresa-credentials-form" style="display: flex; flex-direction: column; gap: 20px;">
                            
                            <div class="input-group">
                                <label style="font-size: 0.8rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; display: block;">Código de Empresa</label>
                                <input type="text" placeholder="MOB-B21EE7" style="background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); color: #f8fafc; padding: 12px; border-radius: 6px; width: 100%;">
                            </div>
                            
                            <div class="input-group">
                                <label style="font-size: 0.8rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; display: block;">WhatsApp Phone Number ID</label>
                                <input type="text" placeholder="El ID del número destino de la WABA" style="background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); color: #f8fafc; padding: 12px; border-radius: 6px; width: 100%;">
                            </div>
                            
                            <div class="input-group">
                                <label style="font-size: 0.8rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; display: block;">WhatsApp Access Token</label>
                                <input type="password" placeholder="Pega aquí tu token permanente" style="background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); color: #f8fafc; padding: 12px; border-radius: 6px; width: 100%;">
                                <div style="font-size: 0.8rem; color: #ef4444; margin-top: 8px;">Estado: Sin Token configurado</div>
                            </div>
                            
                            <div style="margin-top: 15px;">
                                <button type="button" class="btn btn-primary" style="background: #8b5cf6; border: none; font-weight: 600; padding: 12px 24px; border-radius: 6px; display: inline-flex; align-items: center; gap: 8px; color: white;">
                                    <i class="fa-solid fa-floppy-disk"></i> Guardar Empresa
                                </button>
                            </div>
                        </form>
                    </div>

                </section>"""
    
    content = content.replace(old_section, new_section)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Section replaced successfully (Asistto UI).")
else:
    print("Could not find section-api")
