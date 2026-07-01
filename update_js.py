with open("static/app.js", "r", encoding="utf-8") as f:
    js = f.read()

# Replace showLoading/hideLoading with inline button logic
old_save_logic = """    if (btnSaveCsvUrl) {
        btnSaveCsvUrl.addEventListener("click", async () => {
            const url = csvDriveUrl.value.trim();
            try {
                showLoading();
                await apiRequest("/api/v1/companies/kuroda/dashboard/target", {
                    method: "POST",
                    body: JSON.stringify({
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
    }"""

new_save_logic = """    if (btnSaveCsvUrl) {
        btnSaveCsvUrl.addEventListener("click", async () => {
            const url = csvDriveUrl.value.trim();
            try {
                btnSaveCsvUrl.disabled = true;
                const originalHtml = btnSaveCsvUrl.innerHTML;
                btnSaveCsvUrl.innerHTML = 'Guardando... <i class="fa-solid fa-spinner animate-spin"></i>';
                await apiRequest("/api/v1/companies/kuroda/dashboard/target", {
                    method: "POST",
                    body: JSON.stringify({
                        csv_drive_url: url
                    })
                });
                showToast("URL de CSV guardada exitosamente", "success");
                btnSaveCsvUrl.innerHTML = originalHtml;
            } catch (e) {
                console.error(e);
                showToast("Fallo al guardar URL del CSV", "error");
                btnSaveCsvUrl.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> Guardar URL';
            } finally {
                btnSaveCsvUrl.disabled = false;
            }
        });
    }"""

old_sync_logic = """    if (btnSyncCsv) {
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
    }"""

new_sync_logic = """    if (btnSyncCsv) {
        btnSyncCsv.addEventListener("click", async () => {
            try {
                btnSyncCsv.disabled = true;
                const originalHtml = btnSyncCsv.innerHTML;
                btnSyncCsv.innerHTML = 'Sincronizando... <i class="fa-solid fa-spinner animate-spin"></i>';
                const res = await apiRequest("/api/v1/cotizaciones/sync-csv", { method: "POST" });
                showToast(res.message || "Sincronización exitosa", "success");
                await loadDashboardData(true);
                btnSyncCsv.innerHTML = originalHtml;
            } catch (e) {
                console.error(e);
                showToast(e.message || "Fallo al sincronizar CSV", "error");
                btnSyncCsv.innerHTML = '<i class="fa-solid fa-rotate"></i> Sincronizar Ahora';
            } finally {
                btnSyncCsv.disabled = false;
            }
        });
    }"""

js = js.replace(old_save_logic, new_save_logic)
js = js.replace(old_sync_logic, new_sync_logic)

with open("static/app.js", "w", encoding="utf-8") as f:
    f.write(js)
