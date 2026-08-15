    if (DOM.sellerPerformanceChart && typeof Chart !== "undefined") {
        if (state.sellerPerformanceChart) state.sellerPerformanceChart.destroy();
        const labels = state.sellerGoalPeriod === "day" ? ["Hoy"] : state.sellerGoalPeriod === "week" ? ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"] : ["Sem 1", "Sem 2", "Sem 3", "Sem 4"];
        const progress = Array(labels.length).fill(0);
        const span = Math.max(1, period.end.getTime() - period.start.getTime());

        quotes.filter(q => q.numero_factura).forEach(quote => {
            const quoteDate = parseLocalDate(quote.fecha_registro || quote.fecha_factura);
            if (!quoteDate || quoteDate < period.start || quoteDate > period.end) return;
            const ratio = Math.max(0, Math.min(0.999, (quoteDate.getTime() - period.start.getTime()) / span));
            const index = Math.min(labels.length - 1, Math.floor(ratio * labels.length));
            progress[index] += getInvoiceAmount(quote);
        });

        let running = 0;
        const cumulative = progress.map(amount => (running += amount));
        const target = labels.map((_, index) => periodGoal * ((index + 1) / labels.length));
        const isLightMode = document.body.classList.contains("light-mode");
        const tickColor = isLightMode ? "#64748b" : "#a6b0c4";
        const gridColor = isLightMode ? "rgba(15, 23, 42, 0.08)" : "rgba(148, 163, 184, 0.12)";
        state.sellerPerformanceChart = new Chart(DOM.sellerPerformanceChart.getContext("2d"), {
            type: "line",
            data: {
                labels,
                datasets: [
                    { label: "Meta", data: target, borderColor: "#8b5cf6", borderDash: [5, 5], borderWidth: 1.5, pointRadius: 0, tension: 0.35 },
                    { label: "Avance", data: cumulative, borderColor: "#22c55e", backgroundColor: "rgba(34, 197, 94, 0.08)", fill: true, borderWidth: 2, pointRadius: 2, pointBackgroundColor: "#4ade80", tension: 0.35 }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: tickColor, boxWidth: 12, usePointStyle: true, font: { size: 11 } } } },
                scales: {
                    x: { ticks: { color: tickColor, font: { size: 10 } }, grid: { display: false } },
                    y: { display: false, beginAtZero: true, suggestedMax: Math.max(periodGoal || 0, ...cumulative, 1000), grid: { color: gridColor } }
                }
            }
        });
    }
