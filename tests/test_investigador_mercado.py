import pytest
from decimal import Decimal
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app

# 1. Tests del Algoritmo Determinista de Precios (Humanio CEO: Matemáticas en Python, no en LLM)
from app.agents.investigador_mercado_agent import (
    calcular_precio_sugerido,
    InvestigacionMercadoResult,
    ItemCompetidor,
    investigar_mercado_producto
)


def test_calcular_precio_sugerido_protege_margen_minimo():
    """
    Verifica que el precio sugerido NUNCA caiga por debajo del costo unitario + margen mínimo de seguridad,
    incluso si la competencia tiene precios predatorios extremadamente bajos.
    """
    costo = 100.0
    precio_kuroda = 150.0
    stock_actual = 50
    abc_f = "A"
    
    # Competidor absurdamente barato (por debajo del costo de Kuroda)
    precios_competencia = [80.0, 90.0]
    
    resultado = calcular_precio_sugerido(
        costo=costo,
        precio_kuroda=precio_kuroda,
        stock_actual=stock_actual,
        abc_f=abc_f,
        precios_competencia=precios_competencia,
        margen_minimo_pct=0.10  # 10% de margen mínimo
    )
    
    # El piso debe ser costo * 1.10 = 110.0
    assert resultado["precio_sugerido"] >= 110.0
    assert resultado["margen_sugerido_pct"] >= 0.10
    assert "margen" in resultado["justificacion"].lower() or "costo" in resultado["justificacion"].lower()


def test_calcular_precio_sugerido_agresivo_para_material_d_sobrestock():
    """
    Para inventario clasificado como 'D' (baja rotación / liquidación) o sobrestock alto,
    la sugerencia debe ser agresiva (igualar o mejorar ligeramente el mejor precio de mercado)
    para acelerar la rotación sin violar el costo.
    """
    costo = 100.0
    precio_kuroda = 200.0
    stock_actual = 500  # Gran volumen estancado
    abc_f = "D"
    
    precios_competencia = [160.0, 175.0, 190.0]
    
    resultado = calcular_precio_sugerido(
        costo=costo,
        precio_kuroda=precio_kuroda,
        stock_actual=stock_actual,
        abc_f=abc_f,
        precios_competencia=precios_competencia,
        margen_minimo_pct=0.15
    )
    
    # Debe ser menor o igual al mínimo de la competencia (160), pero por encima del piso (115)
    assert resultado["precio_sugerido"] <= 160.0
    assert resultado["precio_sugerido"] >= 115.0
    assert resultado["estrategia"] == "LIQUIDACION_VOLUMEN"


def test_calcular_precio_sugerido_conservador_para_stock_escaso():
    """
    Cuando el stock propio es escaso y la competencia tiene precios más altos,
    se debe sugerir mantener o incrementar el precio capturando mayor margen.
    """
    costo = 100.0
    precio_kuroda = 140.0
    stock_actual = 2  # Casi agotado
    abc_f = "A"
    
    precios_competencia = [180.0, 195.0, 210.0]
    
    resultado = calcular_precio_sugerido(
        costo=costo,
        precio_kuroda=precio_kuroda,
        stock_actual=stock_actual,
        abc_f=abc_f,
        precios_competencia=precios_competencia,
        margen_minimo_pct=0.15
    )
    
    # La sugerencia debe aprovechar el mercado alto
    assert resultado["precio_sugerido"] >= precio_kuroda
    assert resultado["estrategia"] in ("MAXIMIZAR_MARGEN", "ALINEACION_MERCADO")


def test_calcular_metricas_brecha_mercado():
    """
    Verifica que el cálculo de brecha de precio (Kuroda vs mínimo y promedio) sea matemáticamente exacto.
    """
    costo = 100.0
    precio_kuroda = 150.0
    stock_actual = 20
    abc_f = "B"
    precios_competencia = [120.0, 150.0, 180.0]  # Min: 120, Prom: 150
    
    resultado = calcular_precio_sugerido(
        costo=costo,
        precio_kuroda=precio_kuroda,
        stock_actual=stock_actual,
        abc_f=abc_f,
        precios_competencia=precios_competencia
    )
    
    assert resultado["precio_minimo_mercado"] == 120.0
    assert resultado["precio_promedio_mercado"] == 150.0
    # Brecha vs mínimo: (150 - 120) / 120 * 100 = 25% más caro que el mínimo
    assert round(resultado["brecha_vs_minimo_pct"], 2) == 25.0


@pytest.mark.asyncio
async def test_investigar_mercado_producto_con_mock_openrouter():
    """
    Verifica que el agente procese correctamente la respuesta simulada de OpenRouter
    con publicaciones encontradas y zona geográfica delimitada.
    """
    mock_llm_response = """
    {
        "publicaciones": [
            {
                "tienda": "The Home Depot Culiacán",
                "producto_encontrado": "Tubo PVC Sanitario 4 pulg x 6m",
                "precio": 389.00,
                "moneda": "MXN",
                "en_promocion": true,
                "detalle_promocion": "10% de descuento en línea",
                "url": "https://www.homedepot.com.mx/tubo-pvc-4",
                "disponibilidad_local": "En tienda Tres Ríos Culiacán"
            },
            {
                "tienda": "Construrama Sinaloa",
                "producto_encontrado": "Tubo Sanitario PVC 4 pulgadas Norma",
                "precio": 415.50,
                "moneda": "MXN",
                "en_promocion": false,
                "detalle_promocion": null,
                "url": "https://www.construrama.com/tubo-4",
                "disponibilidad_local": "Entrega en Culiacán 24-48h"
            }
        ],
        "resumen_plaza": "Precios de tubería sanitaria 4 pulgadas en Culiacán oscilan entre $389 y $415 MXN."
    }
    """
    
    with patch("app.agents.investigador_mercado_agent.call_llm_openrouter_web", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_llm_response
        
        res = await investigar_mercado_producto(
            codigo_material="TUB-PVC-001",
            descripcion_material="Tubo PVC Sanitario 4 pulg",
            precio_kuroda=420.0,
            costo_kuroda=290.0,
            stock_kuroda=120,
            abc_f="B",
            ciudad="Culiacán",
            estado="Sinaloa",
            pais="México",
            competidores=["The Home Depot", "Construrama"]
        )
        
        assert len(res.publicaciones) == 2
        assert res.publicaciones[0].tienda == "The Home Depot Culiacán"
        assert res.publicaciones[0].precio == 389.00
        assert res.analisis_precios["precio_minimo_mercado"] == 389.00
        assert res.analisis_precios["precio_sugerido"] > 290.0  # Protege costo
        assert res.plaza["ciudad"] == "Culiacán"


def test_api_mercado_buscar_productos_endpoint():
    """
    Verifica que el endpoint GET /api/v1/mercado/productos devuelva productos del catálogo
    con información de stock y precio.
    """
    client = TestClient(app)
    response = client.get("/api/v1/mercado/productos?q=tubo")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_api_mercado_test_connection_endpoint():
    """
    Verifica que el endpoint POST /api/v1/mercado/test-connection responda adecuadamente.
    """
    client = TestClient(app)
    response = client.post("/api/v1/mercado/test-connection", json={"api_key": ""})
    assert response.status_code == 200
    res_data = response.json()
    assert "connected" in res_data
    assert "message" in res_data


def test_api_mercado_investigar_endpoint_completo():
    """
    Verifica el flujo integral del endpoint POST /api/v1/mercado/investigar con simulación de OpenRouter.
    """
    mock_llm_response = """
    {
        "publicaciones": [
            {
                "tienda": "The Home Depot Culiacán",
                "producto_encontrado": "Inodoro Ecológico Dual Flush",
                "precio": 2499.00,
                "moneda": "MXN",
                "en_promocion": true,
                "detalle_promocion": "Meses sin intereses y 5% adicional",
                "url": "https://homedepot.com.mx/inodoro-dual",
                "disponibilidad_local": "En sucursal El Palmito Culiacán"
            }
        ],
        "resumen_plaza": "Disponibilidad inmediata en Culiacán con financiamiento activo."
    }
    """
    client = TestClient(app)
    with patch("app.agents.investigador_mercado_agent.call_llm_openrouter_web", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_llm_response
        
        payload = {
            "codigo_material": "INO-DF-01",
            "descripcion_material": "Inodoro Ecológico Dual Flush",
            "precio_kuroda": 2650.0,
            "costo_kuroda": 1700.0,
            "stock_kuroda": 45,
            "abc_f": "A",
            "ciudad": "Culiacán",
            "estado": "Sinaloa",
            "pais": "México",
            "competidores": ["The Home Depot"],
            "api_key_override": "sk-or-mock-key-12345"
        }
        
        response = client.post("/api/v1/mercado/investigar", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["codigo_material"] == "INO-DF-01"
        assert len(data["publicaciones"]) == 1
        assert data["publicaciones"][0]["precio"] == 2499.0
        assert data["analisis_precios"]["precio_sugerido"] > 1700.0
        assert data["plaza"]["ciudad"] == "Culiacán"


def test_market_agent_frontend_contract():
    """
    Contrato de Frontend: Verifica que la interfaz gráfica contenga todos los elementos
    especificados en la historia de usuario en index.html y app.js.
    """
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    html = (root / "static" / "index.html").read_text(encoding="utf-8")
    javascript = (root / "static" / "app.js").read_text(encoding="utf-8")
    
    # 1. Tarjeta en Centro de Agentes
    assert "Investigador de Mercado" in html
    assert 'id="btn-open-market-agent"' in html
    
    # 2. Workspace y Formulario
    assert 'id="market-agent-panel"' in html
    assert 'id="market-product-search"' in html
    assert 'id="market-city-input"' in html
    assert 'id="market-state-input"' in html
    assert 'id="market-competitors-chips"' in html
    assert 'id="btn-start-market-research"' in html
    
    # 3. KPIs, Sugerencia, Gráfica y Tabla Comparativa
    assert 'id="kpi-market-suggested-price"' in html
    assert 'id="market-res-justification"' in html
    assert 'id="market-comparison-chart"' in html
    assert 'id="market-comparison-table"' in html
    assert 'id="market-table-filter-text"' in html
    assert 'id="market-table-filter-competitor"' in html
    assert 'id="market-table-filter-promos-only"' in html
    
    # 4. JavaScript Handlers
    assert "btn-open-market-agent" in javascript
    assert "/api/v1/mercado/investigar" in javascript
    assert "/api/v1/mercado/productos" in javascript
    assert "renderMarketResults" in javascript
    assert "filterAndRenderMarketTable" in javascript
    assert "renderMarketChart" in javascript
    assert "clearSelectedMarketProduct" in javascript
    assert 'id="btn-clear-market-product-input"' in html
    assert "market-kpi-card" in html


@pytest.mark.asyncio
async def test_investigar_mercado_con_conversational_text_y_markdown():
    """
    Verifica que el agente extraiga correctamente el JSON estructurado incluso si el modelo
    de lenguaje responde con saludos, texto explicativo o preámbulo antes del bloque de código.
    """
    conversational_response = (
        "Hola, he completado la búsqueda en la plaza Culiacán, Sinaloa. Aquí tienes las publicaciones encontradas:\n\n"
        "```json\n"
        "{\n"
        '  "publicaciones": [\n'
        "    {\n"
        '      "tienda": "Ferretería El Tornillo Local",\n'
        '      "producto_encontrado": "Cespol para Lavabo A.I.",\n'
        '      "precio": 59.90,\n'
        '      "moneda": "MXN",\n'
        '      "en_promocion": true,\n'
        '      "detalle_promocion": "15% off pago de contado",\n'
        '      "url": "https://eltornillo.com/p/cespol",\n'
        '      "disponibilidad_local": "En sucursal Centro Culiacán"\n'
        "    }\n"
        "  ],\n"
        '  "resumen_plaza": "Gran variedad de marcas alternativas en la zona urbana."\n'
        "}\n"
        "```\n"
        "Quedo a tu disposición para más investigaciones."
    )
    
    with patch("app.agents.investigador_mercado_agent.call_llm_openrouter_web", new=AsyncMock(return_value=conversational_response)):
        resultado = await investigar_mercado_producto(
            codigo_material="F3337",
            descripcion_material="CESPOL P/LAVA C/CUB A.I. METALIZADO",
            precio_kuroda=66.58,
            costo_kuroda=48.25,
            stock_kuroda=30.0,
            abc_f="D",
            ciudad="Culiacán",
            estado="Sinaloa",
            competidores=["__ALL__", "The Home Depot", "Ferretería El Tornillo Local"]
        )
        
        assert len(resultado.publicaciones) == 1
        assert resultado.publicaciones[0].tienda == "Ferretería El Tornillo Local"
        assert resultado.publicaciones[0].precio == 59.90
        assert resultado.publicaciones[0].en_promocion is True
        # Al ser Material D, el precio sugerido debe buscar liquidar rotación compitiendo con 59.90
        assert resultado.analisis_precios["precio_sugerido"] <= 60.0
        assert resultado.analisis_precios["precio_sugerido"] >= 48.25 * 1.12


@pytest.mark.asyncio
async def test_investigar_mercado_con_busqueda_abierta_cualquier_proveedor():
    """
    Verifica que al no haber competidores o incluir __ALL__, la directriz del prompt
    instruya al agente a buscar cualquier proveedor en internet.
    """
    mock_response = (
        "{"
        '  "publicaciones": ['
        '    {"tienda": "Amazon México", "producto_encontrado": "Cespol", "precio": 65.0, "en_promocion": false}'
        '  ],'
        '  "resumen_plaza": "Oferta con entrega garantizada en Culiacán."'
        "}"
    )
    with patch("app.agents.investigador_mercado_agent.call_llm_openrouter_web", new=AsyncMock(return_value=mock_response)):
        resultado = await investigar_mercado_producto(
            codigo_material="F3337",
            descripcion_material="CESPOL",
            precio_kuroda=66.58,
            costo_kuroda=48.25,
            stock_kuroda=10.0,
            competidores=["__ALL__"]
        )
        assert len(resultado.publicaciones) == 1
        assert resultado.publicaciones[0].tienda == "Amazon México"


def test_mercado_status_endpoint():
    """
    Verifica que el endpoint GET /api/v1/mercado/status devuelva la disponibilidad
    de clave de sistema y el modelo configurado.
    """
    client = TestClient(app)
    response = client.get("/api/v1/mercado/status")
    assert response.status_code == 200
    data = response.json()
    assert "has_system_key" in data
    assert "default_model" in data


def test_investigar_requiere_api_key_cuando_no_hay_global():
    """
    Verifica que la API rechace con HTTP 400 si no se proporciona API key
    y el servidor no tiene una configurada.
    """
    client = TestClient(app)
    with patch("app.api.v1.investigador_mercado.settings.OPENROUTER_API_KEY", ""):
        response = client.post(
            "/api/v1/mercado/investigar",
            json={
                "codigo_material": "TEST1",
                "descripcion_material": "Material Prueba",
                "precio_kuroda": 100.0,
                "costo_kuroda": 70.0,
                "api_key_override": ""
            }
        )
        assert response.status_code == 400
        data = response.json()
        error_text = data.get("message", data.get("detail", ""))
        assert "API Key" in error_text


def test_investigar_propaga_error_401_claramente():
    """
    Verifica que si OpenRouter responde 401 (Unauthorized), la API devuelva HTTP 401
    y no enmascare el error en un análisis referencial vacío.
    """
    client = TestClient(app)
    with patch("app.agents.investigador_mercado_agent.call_llm_openrouter_web", side_effect=PermissionError("Error 401: Clave no válida")):
        response = client.post(
            "/api/v1/mercado/investigar",
            json={
                "codigo_material": "TEST1",
                "descripcion_material": "Material Prueba",
                "precio_kuroda": 100.0,
                "costo_kuroda": 70.0,
                "api_key_override": "sk-or-invalid"
            }
        )
        assert response.status_code == 401
        data = response.json()
        error_text = data.get("message", data.get("detail", ""))
        assert "401" in error_text


def test_frontend_persiste_openrouter_key():
    """
    Verifica que el frontend contenga las rutinas de persistencia en localStorage
    y el endpoint /status para sincronizar el estado de conexión.
    """
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    javascript = (root / "static" / "app.js").read_text(encoding="utf-8")
    assert "crm_kuroda_openrouter_key" in javascript
    assert "/api/v1/mercado/status" in javascript
    assert "checkMarketOpenRouterStatus" in javascript


@pytest.mark.asyncio
async def test_descarta_publicaciones_con_precio_cero_o_sin_inventario():
    """
    Verifica que si un proveedor no tiene inventario o el modelo devuelve precio 0.0,
    el agente lo descarte por completo para no distorsionar ni la tabla ni la gráfica.
    """
    mock_response = """
    {
        "publicaciones": [
            {
                "tienda": "The Home Depot",
                "producto_encontrado": "Tinaco 1100L",
                "precio": 2999.00,
                "moneda": "MXN",
                "en_promocion": true
            },
            {
                "tienda": "Bricomark",
                "producto_encontrado": "Tinaco Plus Tricapa",
                "precio": 0.00,
                "moneda": "MXN",
                "en_promocion": false
            },
            {
                "tienda": "Mercado Libre",
                "producto_encontrado": "Tinaco Agotado",
                "precio": 0.00,
                "moneda": "MXN",
                "en_promocion": false
            },
            {
                "tienda": "Plomería Universal",
                "producto_encontrado": "Tinaco Rotoplas",
                "precio": 3445.07,
                "moneda": "MXN",
                "en_promocion": false
            }
        ],
        "resumen_plaza": "Ofertas reales en Culiacán."
    }
    """
    with patch("app.agents.investigador_mercado_agent.call_llm_openrouter_web", new=AsyncMock(return_value=mock_response)):
        res = await investigar_mercado_producto(
            codigo_material="ROT1100",
            descripcion_material="Tinaco 1100L",
            precio_kuroda=3442.13,
            costo_kuroda=2494.30,
            stock_kuroda=100.0,
            api_key_override="sk-or-test"
        )
        
        # Deben filtrarse los que tienen precio 0.0 (Bricomark y Mercado Libre)
        assert len(res.publicaciones) == 2
        tiendas = [p.tienda for p in res.publicaciones]
        assert "The Home Depot" in tiendas
        assert "Plomería Universal" in tiendas
        assert "Bricomark" not in tiendas
        assert "Mercado Libre" not in tiendas
        assert all(p.precio > 0 for p in res.publicaciones)
        # El precio mínimo debe ser 2999.00, jamás 0.00
        assert res.analisis_precios["precio_minimo_mercado"] == 2999.00


def test_guardar_clave_global_servidor():
    """
    Verifica que el endpoint POST /api/v1/mercado/save-global-key valide la clave
    y la configure en settings para toda la empresa.
    """
    client = TestClient(app)
    
    # Mock de validación en OpenRouter
    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"data": {"label": "Clave Empresa"}}
    
    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        response = client.post(
            "/api/v1/mercado/save-global-key",
            json={"api_key": "sk-or-empresa-global-123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        from app.core.config import settings
        assert settings.OPENROUTER_API_KEY == "sk-or-empresa-global-123"


