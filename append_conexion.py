with open("static/app.js", "r", encoding="utf-8") as f:
    js = f.read()

append_code = """
// --- CONEXION TAB LOGIC ---
document.addEventListener("DOMContentLoaded", () => {
    const menuConexion = document.getElementById("menu-conexion");
    const csvDriveUrl = document.getElementById("csv-drive-url");
    const btnSaveCsvUrl = document.getElementById("btn-save-csv-url");
    const btnSyncCsv = document.getElementById("btn-sync-csv");
    
    // Auth Check for menu (runs when state.currentUser is updated, but we can hook into renderSummary or login)
    // A quick hack is to check state periodically or monkey-patch
    
    const originalRenderSummary = window.renderSummary;
    if (typeof renderSummary !== "undefined") {
        window.renderSummary = function() {
            if (menuConexion && state.currentUser) {
                menuConexion.style.display = (state.currentUser.rol === "admin" || state.currentUser.rol === "gerente") ? "flex" : "none";
            }
            if (csvDriveUrl && state.csv_drive_url !== undefined) {
                csvDriveUrl.value = state.csv_drive_url;
            }
            originalRenderSummary();
        };
    }

    if (btnSaveCsvUrl) {
        btnSaveCsvUrl.addEventListener("click", async () => {
            const url = csvDriveUrl.value.trim();
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

    if (btnSyncCsv) {
        btnSyncCsv.addEventListener("click", async () => {
            try {
                showLoading();
                const res = await apiRequest("/api/v1/cotizaciones/sync-csv", { method: "POST" });
                showToast(res.message || "Sincronización exitosa", "success");
                await loadDashboardData(true);
            } catch (e) {
                console.error(e);
                showToast(e.message || "Fallo al sincronizar CSV", "error");
            } finally {
                hideLoading();
            }
        });
    }
});

// Monkey patch loadDashboardData to capture csv_drive_url
const originalLoadDashboardData = window.loadDashboardData;
if (typeof loadDashboardData !== "undefined") {
    window.loadDashboardData = async function(force = false) {
        await originalLoadDashboardData(force);
        try {
            const res = await apiRequest("/api/v1/companies/kuroda/dashboard");
            state.csv_drive_url = res.data.csv_drive_url;
            if (document.getElementById("csv-drive-url") && state.csv_drive_url) {
                document.getElementById("csv-drive-url").value = state.csv_drive_url;
            }
            if (document.getElementById("menu-conexion") && state.currentUser) {
                document.getElementById("menu-conexion").style.display = (state.currentUser.rol === "admin" || state.currentUser.rol === "gerente") ? "flex" : "none";
            }
        } catch(e) {}
    };
}
"""

with open("static/app.js", "w", encoding="utf-8") as f:
    f.write(js + "\n" + append_code)
