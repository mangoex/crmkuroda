with open("static/app.js", "r", encoding="utf-8") as f:
    js = f.read()

import re

# Fix btnSaveCsvUrl logic
pattern = r"if \(btnSaveCsvUrl\).*?hideLoading\(\);\s*\}\s*\}\);\s*\}"

new_logic = """if (btnSaveCsvUrl) {
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

js = re.sub(pattern, new_logic, js, flags=re.DOTALL)

with open("static/app.js", "w", encoding="utf-8") as f:
    f.write(js)
