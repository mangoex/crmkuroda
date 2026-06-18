import { useState, useEffect } from 'react'
import axios from 'axios'
import './App.css'

function App() {
  const [resumen, setResumen] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const fetchResumen = async () => {
    setLoading(true)
    try {
      const response = await axios.get('/api/v1/analisis/resumen')
      setResumen(response.data.resumen_ejecutivo)
    } catch (error) {
      console.error("Error fetching resumen", error)
      setResumen("Error al obtener el resumen. Asegúrate de que el backend esté corriendo y la API Key de OpenRouter sea válida.")
    }
    setLoading(false)
  }

  return (
    <div className="dashboard-container">
      <header className="header">
        <h1>CRM Kuroda - Dashboard Inteligente</h1>
        <p>Gestión Agéntica con IA</p>
      </header>

      <main className="main-content">
        <section className="card">
          <h2>Agente Analista (Business Insights)</h2>
          <p>Genera un resumen ejecutivo sobre el desempeño de ventas mensual.</p>
          <button onClick={fetchResumen} disabled={loading} className="btn-primary">
            {loading ? 'Analizando...' : 'Generar Resumen Ejecutivo'}
          </button>
          
          {resumen && (
            <div className="resumen-box">
              <h3>Resumen Generado:</h3>
              <pre>{resumen}</pre>
            </div>
          )}
        </section>

        <section className="card">
          <h2>Seguimiento Diario (Enlaces de WhatsApp)</h2>
          <p>
            El sistema genera automáticamente los enlaces a las 8:00 AM mediante <strong>APScheduler</strong>.
            Puedes ver la lista de vendedores y dar clic en "Enviar" para abrir WhatsApp Web con el mensaje pre-redactado.
          </p>
          <div className="table-placeholder">
            <p><em>La tabla de vendedores aparecerá aquí. (Simulado)</em></p>
            <ul>
              <li>
                Vendedor: Juan Pérez - 
                <a href="https://wa.me/1234567890?text=Hola%20Juan%20como%20vas" target="_blank" rel="noreferrer" className="btn-whatsapp">
                  Enviar Mensaje
                </a>
              </li>
            </ul>
          </div>
        </section>
      </main>
    </div>
  )
}

export default App
