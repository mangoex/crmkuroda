import { useState, useEffect } from 'react'
import axios from 'axios'
import './App.css'

interface Vendedor {
  id: string;
  email: string;
  nombre_completo: string | null;
  telefono_whatsapp: string | null;
  codigo_vendedor: string | null;
}

function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'))
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)

  const [resumen, setResumen] = useState<string | null>(null)
  const [loadingResumen, setLoadingResumen] = useState(false)

  const [vendedores, setVendedores] = useState<Vendedor[]>([])
  const [loadingVendedores, setLoadingVendedores] = useState(false)

  const [editingVendedor, setEditingVendedor] = useState<Vendedor | null>(null)

  // Configure axios to always send the token if available
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchVendedores();
    } else {
      delete axios.defaults.headers.common['Authorization'];
    }
  }, [token])

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const params = new URLSearchParams();
      params.append('username', username);
      params.append('password', password);

      const response = await axios.post('/api/auth/login', params, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      const access_token = response.data.access_token;
      localStorage.setItem('token', access_token);
      setToken(access_token);
    } catch (error) {
      alert("Error al iniciar sesión. Revisa tus credenciales.");
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setVendedores([]);
  }

  const fetchResumen = async () => {
    setLoadingResumen(true)
    try {
      const response = await axios.get('/api/v1/analisis/resumen')
      setResumen(response.data.resumen_ejecutivo)
    } catch (error) {
      console.error("Error fetching resumen", error)
      setResumen("Error al obtener el resumen. Asegúrate de que el backend esté corriendo y la API Key sea válida.")
    }
    setLoadingResumen(false)
  }

  const fetchVendedores = async () => {
    setLoadingVendedores(true)
    try {
      const response = await axios.get('/api/v1/vendedores/?limit=100')
      if (response.data.status === 'success') {
        setVendedores(response.data.data)
      }
    } catch (error) {
      console.error("Error fetching vendedores", error)
    }
    setLoadingVendedores(false)
  }

  const handleEditChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (editingVendedor) {
      setEditingVendedor({
        ...editingVendedor,
        [e.target.name]: e.target.value
      });
    }
  }

  const saveVendedor = async () => {
    if (!editingVendedor) return;
    try {
      await axios.put(`/api/v1/vendedores/${editingVendedor.id}`, {
        nombre_completo: editingVendedor.nombre_completo,
        email: editingVendedor.email,
        telefono_whatsapp: editingVendedor.telefono_whatsapp,
        codigo_vendedor: editingVendedor.codigo_vendedor
      });
      setEditingVendedor(null);
      fetchVendedores(); // reload
    } catch (error) {
      alert("Error al actualizar vendedor");
      console.error(error);
    }
  }

  if (!token) {
    return (
      <div className="login-container">
        <form onSubmit={handleLogin} className="login-card">
          <h2>CRM Kuroda - Iniciar Sesión</h2>
          <input 
            type="email" 
            placeholder="Correo Electrónico (admin@kuroda.com)" 
            value={username} 
            onChange={e => setUsername(e.target.value)} 
            required 
          />
          <div className="password-wrapper">
            <input 
              type={showPassword ? "text" : "password"} 
              placeholder="Contraseña (admin123)" 
              value={password} 
              onChange={e => setPassword(e.target.value)} 
              required 
            />
            <button 
              type="button" 
              className="btn-toggle-password" 
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? "Ocultar" : "👁️"}
            </button>
          </div>
          <button type="submit" className="btn-primary">Entrar</button>
        </form>
      </div>
    )
  }

  return (
    <div className="dashboard-container">
      <header className="header">
        <h1>CRM Kuroda - Dashboard Inteligente</h1>
        <p>Gestión Agéntica y Panel de Control <button onClick={handleLogout} className="btn-logout">Cerrar Sesión</button></p>
      </header>

      <main className="main-content">
        
        {/* Panel de Vendedores */}
        <section className="card">
          <h2>Gestión de Vendedores</h2>
          <p>Edita los datos de los vendedores registrados en la base de datos.</p>
          
          {loadingVendedores ? <p>Cargando vendedores...</p> : (
            <div className="table-responsive">
              <table className="vendedores-table">
                <thead>
                  <tr>
                    <th>Código</th>
                    <th>Nombre</th>
                    <th>Email</th>
                    <th>WhatsApp</th>
                    <th>Acción</th>
                  </tr>
                </thead>
                <tbody>
                  {vendedores.map(v => (
                    <tr key={v.id}>
                      <td>{v.codigo_vendedor || '-'}</td>
                      <td>{v.nombre_completo || 'Sin nombre'}</td>
                      <td>{v.email}</td>
                      <td>{v.telefono_whatsapp || 'No registrado'}</td>
                      <td>
                        <button onClick={() => setEditingVendedor(v)} className="btn-secondary">Editar</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* Modal de Edición */}
        {editingVendedor && (
          <div className="modal-overlay">
            <div className="modal">
              <h3>Editar Vendedor</h3>
              <div className="form-group">
                <label>Nombre Completo</label>
                <input name="nombre_completo" value={editingVendedor.nombre_completo || ''} onChange={handleEditChange} />
              </div>
              <div className="form-group">
                <label>Correo Electrónico</label>
                <input name="email" value={editingVendedor.email || ''} onChange={handleEditChange} />
              </div>
              <div className="form-group">
                <label>Teléfono (WhatsApp)</label>
                <input name="telefono_whatsapp" value={editingVendedor.telefono_whatsapp || ''} onChange={handleEditChange} />
              </div>
              <div className="form-group">
                <label>Código de Vendedor</label>
                <input name="codigo_vendedor" value={editingVendedor.codigo_vendedor || ''} onChange={handleEditChange} />
              </div>
              <div className="modal-actions">
                <button onClick={() => setEditingVendedor(null)} className="btn-secondary">Cancelar</button>
                <button onClick={saveVendedor} className="btn-primary">Guardar Cambios</button>
              </div>
            </div>
          </div>
        )}

        {/* Business Insights */}
        <section className="card">
          <h2>Agente Analista (Business Insights)</h2>
          <p>Genera un resumen ejecutivo sobre el desempeño de ventas mensual.</p>
          <button onClick={fetchResumen} disabled={loadingResumen} className="btn-primary">
            {loadingResumen ? 'Analizando...' : 'Generar Resumen Ejecutivo'}
          </button>
          
          {resumen && (
            <div className="resumen-box">
              <h3>Resumen Generado:</h3>
              <pre>{resumen}</pre>
            </div>
          )}
        </section>
      </main>
    </div>
  )
}

export default App
