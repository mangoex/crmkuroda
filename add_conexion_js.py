import os

with open("static/app.js", "r", encoding="utf-8") as f:
    js = f.read()

# Add DOM elements
dom_add = """    menuConexion: document.getElementById("menu-conexion"),
    csvDriveUrl: document.getElementById("csv-drive-url"),
    btnSaveCsvUrl: document.getElementById("btn-save-csv-url"),
    btnSyncCsv: document.getElementById("btn-sync-csv"),"""

js = js.replace('menuAsignacion: document.getElementById("menu-asignacion"),', 'menuAsignacion: document.getElementById("menu-asignacion"),\n' + dom_add)

# Hide tab if not admin/gerente
auth_add = """            
            if (DOM.menuConexion) {
                DOM.menuConexion.style.display = (data.rol === "admin" || data.rol === "gerente") ? "flex" : "none";
            }"""
js = js.replace('DOM.menuAsignacion.style.display = (data.rol === "admin" || data.rol === "gerente") ? "flex" : "none";', 'DOM.menuAsignacion.style.display = (data.rol === "admin" || data.rol === "gerente") ? "flex" : "none";' + auth_add)

# Populate URL on load
populate_add = """        
        if (DOM.csvDriveUrl && res.data.csv_drive_url) {
            DOM.csvDriveUrl.value = res.data.csv_drive_url;
        }"""
js = js.replace('state.vendedores = res.data.sellers || [];', 'state.vendedores = res.data.sellers || [];' + populate_add)

# Add event listeners
listeners = """
    if (DOM.btnSaveCsvUrl) {
        DOM.btnSaveCsvUrl.addEventListener("click", async () => {
            const url = DOM.csvDriveUrl.value.trim();
            try {
                showLoading();
                await apiRequest("/api/v1/companies/kuroda/dashboard/target", {
                    method: "POST",
                    body: JSON.stringify({
                        global_sales_target: state.global_sales_target || 0,
                        global_goals: state.global_goals || "",
                        csv_drive_url: url
                    })
                });
                showToast("URL de CSV guardada exitosamente", "success");
            } catch (e) {
                console.error(e);
                showToast("Fallo al guardar URL del CSV", "error");
            } finally {
                hideLoading();
            }
        });
    }

    if (DOM.btnSyncCsv) {
        DOM.btnSyncCsv.addEventListener("click", async () => {
            try {
                showLoading();
                const res = await apiRequest("/api/v1/cotizaciones/sync-csv", { method: "POST" });
                showToast(res.message || "Sincronización exitosa", "success");
                // Reload data
                await loadDashboardData(true);
            } catch (e) {
                console.error(e);
                showToast(e.message || "Fallo al sincronizar CSV", "error");
            } finally {
                hideLoading();
            }
        });
    }
"""

js = js.replace('// Eventos Globales y UI', '// Eventos Globales y UI' + listeners)

with open("static/app.js", "w", encoding="utf-8") as f:
    f.write(js)
