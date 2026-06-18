/* ==========================================================================
   APPLICATION LOGIC - CRM KURODA SPA
   ========================================================================== */

// Global Application State
const state = {
    token: localStorage.getItem("crm_token") || null,
    user: JSON.parse(localStorage.getItem("crm_user")) || null,
    currentSection: "summary",
    vendedores: [],
    metas: [],
    cotizaciones: [],
    salesChart: null,
    goalsChart: null,
    quotesCurrentPage: 1,
    quotesPageSize: 15
};

// UI Selectors
const DOM = {
    authContainer: document.getElementById("auth-container"),
    dashboardContainer: document.getElementById("dashboard-container"),
    loginForm: document.getElementById("login-form"),
    loginEmail: document.getElementById("login-email"),
    loginPassword: document.getElementById("login-password"),
    userDisplayName: document.getElementById("user-display-name"),
    userRoleBadge: document.getElementById("user-role-badge"),
    logoutBtn: document.getElementById("logout-btn"),
    menuItems: document.querySelectorAll(".menu-item"),
    sections: document.querySelectorAll(".dashboard-section"),
    toastContainer: document.getElementById("toast-container"),
    
    // Summary Metrics
    kpiTotalSales: document.getElementById("kpi-total-sales"),
    kpiActiveGoals: document.getElementById("kpi-active-goals"),
    kpiTotalQuotes: document.getElementById("kpi-total-quotes"),
    kpiTotalSellers: document.getElementById("kpi-total-sellers"),
    
    // Vendedores Section
    menuVendedores: document.getElementById("menu-vendedores"),
    btnAddSeller: document.getElementById("btn-add-seller"),
    sellerFormWrapper: document.getElementById("seller-form-wrapper"),
    sellerForm: document.getElementById("seller-form"),
    btnCancelSeller: document.getElementById("btn-cancel-seller"),
    btnCloseSellerForm: document.getElementById("btn-close-seller-form"),
    tableVendedores: document.querySelector("#table-vendedores tbody"),
    
    // Metas Section
    btnGenerateGoalsModal: document.getElementById("btn-generate-goals-modal"),
    aiGoalsWrapper: document.getElementById("ai-goals-wrapper"),
    aiGoalsForm: document.getElementById("ai-goals-form"),
    aiGoalsVendedor: document.getElementById("ai-goals-vendedor"),
    aiGoalsGlobal: document.getElementById("ai-goals-global"),
    btnSubmitAiGoals: document.getElementById("btn-submit-ai-goals"),
    btnCancelAiGoals: document.getElementById("btn-cancel-ai-goals"),
    btnCloseAiGoals: document.getElementById("btn-close-ai-goals"),
    filterGoalStatus: document.getElementById("filter-goal-status"),
    tableMetas: document.querySelector("#table-metas tbody"),
    
    // Cotizaciones Section
    btnGenerateQuoteModal: document.getElementById("btn-generate-quote-modal"),
    aiQuoteWrapper: document.getElementById("ai-quote-wrapper"),
    aiQuoteForm: document.getElementById("ai-quote-form"),
    quoteClientName: document.getElementById("quote-client-name"),
    quoteClientEmail: document.getElementById("quote-client-email"),
    quoteClientPhone: document.getElementById("quote-client-phone"),
    quoteItemsList: document.getElementById("quote-items-list"),
    btnAddItemRow: document.getElementById("btn-add-item-row"),
    quoteExtraReqs: document.getElementById("quote-extra-reqs"),
    btnSubmitAiQuote: document.getElementById("btn-submit-ai-quote"),
    btnCancelAiQuote: document.getElementById("btn-cancel-ai-quote"),
    btnCloseAiQuote: document.getElementById("btn-close-ai-quote"),
    searchQuoteClient: document.getElementById("search-quote-client"),
    filterQuoteSeller: document.getElementById("filter-quote-seller"),
    filterQuoteDays: document.getElementById("filter-quote-days"),
    tableCotizaciones: document.querySelector("#table-cotizaciones tbody"),
    pagCotizaciones: document.getElementById("pag-cotizaciones"),
    
    // Proposal Modal
    proposalModal: document.getElementById("proposal-modal"),
    modalProposalTitle: document.getElementById("modal-proposal-title"),
    modalProposalBody: document.getElementById("modal-proposal-body"),
    btnCopyProposal: document.getElementById("btn-copy-proposal"),
    btnCloseProposalModal: document.getElementById("btn-close-proposal-modal"),
    btnCloseProposal: document.getElementById("btn-close-proposal")
};

/* ==========================================================================
   TOAST NOTIFICATION ENGINE
   ========================================================================== */

function showToast(message, type = "success") {
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    
    let iconClass = "fa-circle-check";
    if (type === "error") iconClass = "fa-circle-exclamation";
    if (type === "info") iconClass = "fa-circle-info";
    
    toast.innerHTML = `
        <i class="fa-solid ${iconClass}"></i>
        <span>${message}</span>
    `;
    
    DOM.toastContainer.appendChild(toast);
    
    // Remove toast after 4 seconds
    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(50px)";
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

/* ==========================================================================
   JWT PARSER & SESSION MANAGEMENT
   ========================================================================== */

function parseJwt(token) {
    try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(window.atob(base64).split('').map(function(c) {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));
        return JSON.parse(jsonPayload);
    } catch (e) {
        return null;
    }
}

function initSession() {
    if (state.token && state.user) {
        // Hide login, show dashboard
        DOM.authContainer.classList.add("hidden");
        DOM.dashboardContainer.classList.remove("hidden");
        
        // Set user badge
        DOM.userDisplayName.textContent = state.user.email.split("@")[0].toUpperCase();
        DOM.userRoleBadge.textContent = state.user.rol;
        
        // Manage visible menu entries based on role (vendedores is admin/gerente only)
        if (state.user.rol === "vendedor") {
            DOM.menuVendedores.classList.add("hidden");
            DOM.btnGenerateGoalsModal.classList.add("hidden");
        } else {
            DOM.menuVendedores.classList.remove("hidden");
            DOM.btnGenerateGoalsModal.classList.remove("hidden");
        }
        
        // Go to initial summary view
        switchSection("summary");
    } else {
        DOM.authContainer.classList.remove("hidden");
        DOM.dashboardContainer.classList.add("hidden");
    }
}

/* ==========================================================================
   API REQUEST WRAPPER
   ========================================================================== */

async function apiRequest(endpoint, options = {}) {
    const url = endpoint;
    const headers = {
        "Content-Type": "application/json",
        ...options.headers
    };
    
    if (state.token) {
        headers["Authorization"] = `Bearer ${state.token}`;
    }
    
    const config = {
        ...options,
        headers
    };
    
    try {
        const response = await fetch(url, config);
        const data = await response.json();
        
        if (!response.ok) {
            // Check for unauthorized access
            if (response.status === 401) {
                logout();
                throw new Error("Sesión expirada. Por favor inicia sesión nuevamente.");
            }
            throw new Error(data.message || "Error al realizar la solicitud.");
        }
        return data;
    } catch (error) {
        loggerError(error.message);
        throw error;
    }
}

function loggerError(msg) {
    console.error("API Error:", msg);
}

function logout() {
    state.token = null;
    state.user = null;
    localStorage.removeItem("crm_token");
    localStorage.removeItem("crm_user");
    initSession();
    showToast("Sesión cerrada correctamente", "info");
}

/* ==========================================================================
   ROUTING & VIEW SWITCHER
   ========================================================================== */

function switchSection(sectionId) {
    state.currentSection = sectionId;
    
    // Toggle active sidebar items
    DOM.menuItems.forEach(item => {
        if (item.getAttribute("data-section") === sectionId) {
            item.classList.add("active");
        } else {
            item.classList.remove("active");
        }
    });
    
    // Toggle active sections in viewport
    DOM.sections.forEach(sec => {
        if (sec.id === `section-${sectionId}`) {
            sec.classList.remove("hidden");
        } else {
            sec.classList.add("hidden");
        }
    });
    
    // Load fresh data for the section
    loadSectionData(sectionId);
}

async function loadSectionData(sectionId) {
    try {
        if (sectionId === "summary") {
            await loadSummaryData();
        } else if (sectionId === "vendedores") {
            await loadVendedoresData();
        } else if (sectionId === "metas") {
            await loadMetasData();
        } else if (sectionId === "cotizaciones") {
            await loadCotizacionesData();
        }
    } catch (e) {
        showToast(e.message, "error");
    }
}

/* ==========================================================================
   API LOADING HANDLERS
   ========================================================================== */

async function loadSummaryData() {
    // In summary, we load sellers, metas, and quotes to compute metrics and draw charts
    let sellers = [];
    if (state.user.rol !== "vendedor") {
        const sellersRes = await apiRequest("/api/v1/vendedores/?limit=100");
        sellers = sellersRes.data || [];
    }
    
    const metasRes = await apiRequest("/api/v1/metas/?limit=100");
    const metas = metasRes.data || [];
    
    const quotesRes = await apiRequest("/api/v1/cotizaciones/?limit=3000");
    const quotes = quotesRes.data || [];
    
    state.vendedores = sellers;
    state.metas = metas;
    state.cotizaciones = quotes;
    
    // Calculate totals
    const totalCotizado = quotes.reduce((acc, q) => acc + q.total, 0);
    const completedMetas = metas.filter(m => m.estado === "completada").length;
    
    // Update KPI UI
    DOM.kpiTotalSales.textContent = `$${totalCotizado.toLocaleString('es-MX', { minimumFractionDigits: 2 })}`;
    DOM.kpiActiveGoals.textContent = `${completedMetas} / ${metas.length}`;
    DOM.kpiTotalQuotes.textContent = quotes.length;
    DOM.kpiTotalSellers.textContent = state.user.rol === "vendedor" ? 1 : sellers.length;
    
    // Render Charts
    renderSalesChart(quotes);
    renderGoalsChart(metas, quotes, sellers);
}

async function loadVendedoresData() {
    if (state.user.rol === "vendedor") return;
    
    const res = await apiRequest("/api/v1/vendedores/?limit=50");
    const sellers = res.data || [];
    state.vendedores = sellers;
    
    DOM.tableVendedores.innerHTML = "";
    if (sellers.length === 0) {
        DOM.tableVendedores.innerHTML = `<tr><td colspan="5" style="text-align: center;">No hay vendedores registrados.</td></tr>`;
        return;
    }
    
    sellers.forEach(v => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><strong>${v.email}</strong></td>
            <td><code>${v.id}</code></td>
            <td>${v.telefono_whatsapp || '<span class="text-muted">No asignado</span>'}</td>
            <td><span class="status-pill status-rol">${v.rol}</span></td>
            <td>
                <button class="btn btn-secondary btn-sm edit-phone-btn" data-id="${v.id}" data-phone="${v.telefono_whatsapp || ''}">
                    <i class="fa-solid fa-phone"></i> Editar Teléfono
                </button>
            </td>
        `;
        DOM.tableVendedores.appendChild(tr);
    });
    
    // Attach event listeners to Edit Phone buttons
    document.querySelectorAll(".edit-phone-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            const id = btn.getAttribute("data-id");
            const phone = btn.getAttribute("data-phone");
            promptEditPhone(id, phone);
        });
    });
}

async function promptEditPhone(id, currentPhone) {
    const newPhone = prompt("Ingrese el nuevo número de WhatsApp (incluya prefijo de país sin símbolos, ej: 521XXXXXXXXXX):", currentPhone);
    if (newPhone === null) return; // user cancelled
    
    try {
        await apiRequest(`/api/v1/vendedores/${id}`, {
            method: "PUT",
            body: JSON.stringify({ telefono_whatsapp: newPhone })
        });
        showToast("Número de WhatsApp actualizado correctamente");
        loadVendedoresData();
    } catch (e) {
        showToast(e.message, "error");
    }
}

async function loadMetasData() {
    const statusFilter = DOM.filterGoalStatus.value;
    let endpoint = "/api/v1/metas/?limit=50";
    
    const res = await apiRequest(endpoint);
    let metas = res.data || [];
    
    // Apply client-side status filter
    if (statusFilter) {
        metas = metas.filter(m => m.estado === statusFilter);
    }
    
    state.metas = metas;
    
    DOM.tableMetas.innerHTML = "";
    if (metas.length === 0) {
        DOM.tableMetas.innerHTML = `<tr><td colspan="7" style="text-align: center;">No se encontraron metas de venta.</td></tr>`;
        return;
    }
    
    // Populate select values in AI Form if admin/gerente
    if (state.user.rol !== "vendedor" && state.vendedores.length === 0) {
        const sellersRes = await apiRequest("/api/v1/vendedores/?limit=100");
        state.vendedores = sellersRes.data || [];
    }
    
    metas.forEach(m => {
        // Find seller email
        const sellerEmail = m.vendedor_id === state.user.id ? state.user.email : (state.vendedores.find(v => v.id === m.vendedor_id)?.email || m.vendedor_id);
        const tr = document.createElement("tr");
        
        let stateSelect = "";
        if (m.vendedor_id === state.user.id || state.user.rol !== "vendedor") {
            stateSelect = `
                <select class="goal-status-select" data-id="${m.id}">
                    <option value="pendiente" ${m.estado === "pendiente" ? "selected" : ""}>Pendiente</option>
                    <option value="en_progreso" ${m.estado === "en_progreso" ? "selected" : ""}>En Progreso</option>
                    <option value="completada" ${m.estado === "completada" ? "selected" : ""}>Completada</option>
                </select>
            `;
        } else {
            stateSelect = `<span class="status-pill status-${m.estado.replace('_', '-')}">${m.estado}</span>`;
        }
        
        tr.innerHTML = `
            <td>${sellerEmail}</td>
            <td>${m.descripcion}</td>
            <td><strong>$${m.monto_objetivo.toLocaleString('es-MX', { minimumFractionDigits: 2 })}</strong></td>
            <td>${m.fecha_inicio}</td>
            <td>${m.fecha_limite}</td>
            <td>${stateSelect}</td>
            <td>
                <span class="text-muted">-</span>
            </td>
        `;
        DOM.tableMetas.appendChild(tr);
    });
    
    // Attach change handlers to goal status select dropdowns
    document.querySelectorAll(".goal-status-select").forEach(sel => {
        sel.addEventListener("change", async (e) => {
            const id = sel.getAttribute("data-id");
            const newStatus = sel.value;
            try {
                await apiRequest(`/api/v1/metas/${id}`, {
                    method: "PUT",
                    body: JSON.stringify({ estado: newStatus })
                });
                showToast("Estado de la meta actualizado");
                loadMetasData();
            } catch (e) {
                showToast(e.message, "error");
                // Reset select value on failure
                loadMetasData();
            }
        });
    });
}

async function loadCotizacionesData(forceRefresh = true) {
    // Make sure vendedores are loaded so we can resolve emails and populate the dropdown filter
    if (state.user.rol !== "vendedor" && state.vendedores.length === 0) {
        const sellersRes = await apiRequest("/api/v1/vendedores/?limit=100");
        state.vendedores = sellersRes.data || [];
    }
    
    // Dynamically populate the sellers select if it hasn't been populated yet (or has only the default option)
    if (DOM.filterQuoteSeller && DOM.filterQuoteSeller.options.length <= 1) {
        state.vendedores.forEach(v => {
            const opt = document.createElement("option");
            opt.value = v.id;
            opt.textContent = v.email;
            DOM.filterQuoteSeller.appendChild(opt);
        });
    }

    if (forceRefresh || state.cotizaciones.length === 0) {
        let endpoint = "/api/v1/cotizaciones/?limit=3000";
        const res = await apiRequest(endpoint);
        state.cotizaciones = res.data || [];
    }
    
    // Reset current page when loading fresh section
    state.quotesCurrentPage = 1;
    
    renderQuotesTableFiltered();
}

function renderQuotesTableFiltered() {
    const searchVal = DOM.searchQuoteClient.value.toLowerCase();
    const sellerVal = DOM.filterQuoteSeller.value;
    const daysVal = DOM.filterQuoteDays.value;
    
    let filteredQuotes = state.cotizaciones;
    
    // 1. Filter by Client Search
    if (searchVal) {
        filteredQuotes = filteredQuotes.filter(q => q.cliente_nombre.toLowerCase().includes(searchVal));
    }
    
    // 2. Filter by Seller
    if (sellerVal) {
        filteredQuotes = filteredQuotes.filter(q => q.vendedor_id === sellerVal);
    }
    
    // 3. Filter by Vencimiento / Antigüedad
    if (daysVal) {
        const daysLimit = parseInt(daysVal);
        const refDate = new Date("2026-06-18T12:00:00Z");
        filteredQuotes = filteredQuotes.filter(q => {
            if (!q.fecha_registro) return false;
            const quoteDate = new Date(`${q.fecha_registro}T12:00:00Z`);
            const diffTime = refDate - quoteDate;
            const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
            return diffDays >= 0 && diffDays <= daysLimit;
        });
    }
    
    // Set up pagination
    const totalItems = filteredQuotes.length;
    const pageSize = state.quotesPageSize || 15;
    const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
    
    // Correct current page if out of bounds
    if (state.quotesCurrentPage > totalPages) {
        state.quotesCurrentPage = totalPages;
    }
    if (state.quotesCurrentPage < 1) {
        state.quotesCurrentPage = 1;
    }
    
    const startIndex = (state.quotesCurrentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    const pageQuotes = filteredQuotes.slice(startIndex, endIndex);
    
    DOM.tableCotizaciones.innerHTML = "";
    if (pageQuotes.length === 0) {
        DOM.tableCotizaciones.innerHTML = `<tr><td colspan="10" style="text-align: center;">No hay cotizaciones registradas con los filtros seleccionados.</td></tr>`;
        renderPagination(totalPages);
        return;
    }
    
    pageQuotes.forEach(c => {
        const sellerEmail = c.vendedor_id === state.user.id ? state.user.email : (state.vendedores.find(v => v.id === c.vendedor_id)?.email || c.vendedor_id);
        const contactInfo = `Email: ${c.datos_contacto.email || '-'}<br>Tel: ${c.datos_contacto.telefono || '-'}`;
        const itemsSummary = c.items.map(i => `${i.producto} (${i.cantidad})`).join(", ");
        
        const dateStr = c.fecha_registro || '-';
        const quoteNum = c.numero_cotizacion || '-';
        const canal = c.canal || '-';
        const lossPill = c.venta_perdida === "Si" ? 
            `<span class="status-pill status-pendiente">Si</span>` : 
            `<span class="status-pill status-completada">No</span>`;
            
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><code>${quoteNum}</code></td>
            <td>${dateStr}</td>
            <td><strong>${c.cliente_nombre}</strong></td>
            <td>${contactInfo}</td>
            <td>${canal}</td>
            <td><strong>$${c.total.toLocaleString('es-MX', { minimumFractionDigits: 2 })}</strong></td>
            <td>${sellerEmail}</td>
            <td>${lossPill}</td>
            <td><span class="text-muted" title="${itemsSummary}">${itemsSummary.length > 35 ? itemsSummary.slice(0, 35) + "..." : itemsSummary}</span></td>
            <td>
                <button class="btn btn-secondary btn-sm view-proposal-btn" data-id="${c.id}">
                    <i class="fa-regular fa-file-lines"></i> Ver Propuesta
                </button>
            </td>
        `;
        DOM.tableCotizaciones.appendChild(tr);
    });
    
    // Attach click events to View Proposal buttons
    document.querySelectorAll(".view-proposal-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const id = btn.getAttribute("data-id");
            const quote = state.cotizaciones.find(q => q.id === id);
            if (quote) {
                showProposalModal(quote);
            }
        });
    });
    
    renderPagination(totalPages);
}

function renderPagination(totalPages) {
    if (!DOM.pagCotizaciones) return;
    
    DOM.pagCotizaciones.innerHTML = `
        <div class="pag-info">
            Mostrando página <span>${state.quotesCurrentPage}</span> de <span>${totalPages}</span>
        </div>
        <div class="pag-controls">
            <button class="btn btn-secondary btn-sm" id="btn-quote-prev" ${state.quotesCurrentPage === 1 ? 'disabled' : ''}>
                <i class="fa-solid fa-chevron-left"></i> Anterior
            </button>
            <button class="btn btn-secondary btn-sm" id="btn-quote-next" ${state.quotesCurrentPage === totalPages ? 'disabled' : ''}>
                Siguiente <i class="fa-solid fa-chevron-right"></i>
            </button>
        </div>
    `;
    
    const prevBtn = DOM.pagCotizaciones.querySelector("#btn-quote-prev");
    const nextBtn = DOM.pagCotizaciones.querySelector("#btn-quote-next");
    
    if (prevBtn) {
        prevBtn.addEventListener("click", () => {
            if (state.quotesCurrentPage > 1) {
                state.quotesCurrentPage--;
                renderQuotesTableFiltered();
            }
        });
    }
    
    if (nextBtn) {
        nextBtn.addEventListener("click", () => {
            if (state.quotesCurrentPage < totalPages) {
                state.quotesCurrentPage++;
                renderQuotesTableFiltered();
            }
        });
    }
}

function showProposalModal(quote) {
    DOM.modalProposalTitle.textContent = `Propuesta Comercial - ${quote.cliente_nombre}`;
    DOM.modalProposalBody.textContent = quote.texto_propuesta || "Esta cotización no contiene propuesta detallada.";
    DOM.proposalModal.classList.remove("hidden");
}

/* ==========================================================================
   CHARTS RENDERING ENGINE
   ========================================================================== */

function renderSalesChart(quotes) {
    if (state.salesChart) {
        state.salesChart.destroy();
    }
    
    // Group quotes total by client name
    const grouped = {};
    quotes.forEach(q => {
        grouped[q.cliente_nombre] = (grouped[q.cliente_nombre] || 0) + q.total;
    });
    
    const labels = Object.keys(grouped);
    const data = Object.values(grouped);
    
    const ctx = document.getElementById("salesChart").getContext("2d");
    state.salesChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Monto Cotizado ($)',
                data,
                backgroundColor: 'rgba(93, 95, 239, 0.4)',
                borderColor: '#5d5fef',
                borderWidth: 2,
                borderRadius: 6,
                hoverBackgroundColor: 'rgba(0, 242, 254, 0.5)',
                hoverBorderColor: '#00f2fe'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#abb2bf' } }
            },
            scales: {
                x: { ticks: { color: '#abb2bf' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                y: { ticks: { color: '#abb2bf' }, grid: { color: 'rgba(255,255,255,0.05)' } }
            }
        }
    });
}

function renderGoalsChart(metas, quotes, sellers) {
    if (state.goalsChart) {
        state.goalsChart.destroy();
    }
    
    // Group target goals and actual quotes totals by seller
    const goalsBySeller = {};
    const actualsBySeller = {};
    
    // Seed maps
    metas.forEach(m => {
        goalsBySeller[m.vendedor_id] = (goalsBySeller[m.vendedor_id] || 0) + m.monto_objetivo;
    });
    
    quotes.forEach(q => {
        actualsBySeller[q.vendedor_id] = (actualsBySeller[q.vendedor_id] || 0) + q.total;
    });
    
    const sellerIds = Array.from(new Set([...Object.keys(goalsBySeller), ...Object.keys(actualsBySeller)]));
    const labels = sellerIds.map(sid => {
        if (sid === state.user.id) return state.user.email.split("@")[0];
        return (sellers.find(s => s.id === sid)?.email || sid).split("@")[0];
    });
    
    const targetData = sellerIds.map(sid => goalsBySeller[sid] || 0);
    const actualData = sellerIds.map(sid => actualsBySeller[sid] || 0);
    
    const ctx = document.getElementById("goalsChart").getContext("2d");
    state.goalsChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: labels.length ? labels : ["Sin Datos"],
            datasets: [
                {
                    label: 'Monto Meta ($)',
                    data: targetData.length ? targetData : [0],
                    backgroundColor: 'rgba(139, 92, 246, 0.2)',
                    borderColor: '#8b5cf6',
                    pointBackgroundColor: '#8b5cf6',
                    borderWidth: 2
                },
                {
                    label: 'Real Cotizado ($)',
                    data: actualData.length ? actualData : [0],
                    backgroundColor: 'rgba(16, 185, 129, 0.2)',
                    borderColor: '#10b981',
                    pointBackgroundColor: '#10b981',
                    borderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#abb2bf' } }
            },
            scales: {
                r: {
                    angleLines: { color: 'rgba(255,255,255,0.05)' },
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    pointLabels: { color: '#abb2bf' },
                    ticks: { backdropColor: 'transparent', color: '#abb2bf' }
                }
            }
        }
    });
}

/* ==========================================================================
   EVENT LISTENERS & FORM SUBMISSIONS
   ========================================================================== */

// Handle Auth Form Submission
DOM.loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = DOM.loginEmail.value;
    const password = DOM.loginPassword.value;
    
    try {
        const formData = new FormData();
        formData.append("username", email);
        formData.append("password", password);
        
        const response = await fetch("/api/auth/login", {
            method: "POST",
            body: formData
        });
        
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "Fallo en el inicio de sesión");
        }
        
        // Save token and parse user details
        state.token = data.access_token;
        const decoded = parseJwt(data.access_token);
        state.user = {
            email: decoded.sub,
            rol: decoded.rol,
            id: decoded.sub // fallback as ID, or we fetch from JWT payload
        };
        
        // Fetch actual user ID via email lookup or decode payload
        // We will assign it cleanly
        const userDetailsRes = await apiRequest("/api/v1/vendedores/?limit=100");
        const match = (userDetailsRes.data || []).find(v => v.email === state.user.email);
        if (match) {
            state.user.id = match.id;
        }
        
        localStorage.setItem("crm_token", state.token);
        localStorage.setItem("crm_user", JSON.stringify(state.user));
        
        showToast("¡Inicio de sesión exitoso!");
        initSession();
    } catch (e) {
        showToast(e.message, "error");
    }
});

// Sidebar Menu Click Handlers
DOM.menuItems.forEach(item => {
    item.addEventListener("click", (e) => {
        e.preventDefault();
        const sectionId = item.getAttribute("data-section");
        switchSection(sectionId);
    });
});

// Logout Button Handler
DOM.logoutBtn.addEventListener("click", logout);

/* --- Vendedores Handlers --- */
DOM.btnAddSeller.addEventListener("click", () => {
    DOM.sellerFormWrapper.classList.remove("hidden");
});

DOM.btnCancelSeller.addEventListener("click", () => {
    DOM.sellerFormWrapper.classList.add("hidden");
});

DOM.btnCloseSellerForm.addEventListener("click", () => {
    DOM.sellerFormWrapper.classList.add("hidden");
});

DOM.sellerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("seller-email").value;
    const phone = document.getElementById("seller-phone").value;
    const password = document.getElementById("seller-password").value;
    
    try {
        await apiRequest("/api/v1/vendedores/", {
            method: "POST",
            body: JSON.stringify({
                email,
                rol: "vendedor",
                telefono_whatsapp: phone,
                password
            })
        });
        showToast("Vendedor registrado con éxito");
        DOM.sellerForm.reset();
        DOM.sellerFormWrapper.classList.add("hidden");
        loadVendedoresData();
    } catch (e) {
        showToast(e.message, "error");
    }
});

/* --- Metas Handlers --- */
DOM.btnGenerateGoalsModal.addEventListener("click", () => {
    DOM.aiGoalsWrapper.classList.remove("hidden");
    
    // Populate select elements
    DOM.aiGoalsVendedor.innerHTML = "";
    state.vendedores.forEach(v => {
        const opt = document.createElement("option");
        opt.value = v.id;
        opt.textContent = v.email;
        DOM.aiGoalsVendedor.appendChild(opt);
    });
});

DOM.btnCancelAiGoals.addEventListener("click", () => {
    DOM.aiGoalsWrapper.classList.add("hidden");
});

DOM.btnCloseAiGoals.addEventListener("click", () => {
    DOM.aiGoalsWrapper.classList.add("hidden");
});

DOM.aiGoalsForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const sellerId = DOM.aiGoalsVendedor.value;
    const globalGoals = DOM.aiGoalsGlobal.value;
    
    // Set loading state
    DOM.btnSubmitAiGoals.disabled = true;
    DOM.btnSubmitAiGoals.innerHTML = 'Generando Meta con IA... <i class="fa-solid fa-spinner fa-spin"></i>';
    
    try {
        await apiRequest(`/api/v1/metas/generate/${sellerId}`, {
            method: "POST",
            body: JSON.stringify({ objetivos_globales: globalGoals })
        });
        showToast("La IA ha generado y guardado la meta con éxito.");
        DOM.aiGoalsForm.reset();
        DOM.aiGoalsWrapper.classList.add("hidden");
        loadMetasData();
    } catch (e) {
        showToast(e.message, "error");
    } finally {
        DOM.btnSubmitAiGoals.disabled = false;
        DOM.btnSubmitAiGoals.innerHTML = 'Analizar y Generar Meta con IA <i class="fa-solid fa-sparkles">';
    }
});

DOM.filterGoalStatus.addEventListener("change", loadMetasData);

/* --- Cotizaciones Handlers --- */
DOM.btnGenerateQuoteModal.addEventListener("click", () => {
    DOM.aiQuoteWrapper.classList.remove("hidden");
});

DOM.btnCancelAiQuote.addEventListener("click", () => {
    DOM.aiQuoteWrapper.classList.add("hidden");
});

DOM.btnCloseAiQuote.addEventListener("click", () => {
    DOM.aiQuoteWrapper.classList.add("hidden");
});

DOM.btnAddItemRow.addEventListener("click", () => {
    const row = document.createElement("div");
    row.className = "item-row";
    row.innerHTML = `
        <input type="text" class="item-product" placeholder="Descripción del Producto/Servicio" required>
        <input type="number" class="item-qty" placeholder="Cant" min="1" required>
        <input type="number" class="item-price" placeholder="Precio Unitario" min="0" step="0.01" required>
        <button type="button" class="btn-remove-row btn-danger-icon"><i class="fa-solid fa-trash"></i></button>
    `;
    DOM.quoteItemsList.appendChild(row);
    
    // Attach delete handler to new row
    row.querySelector(".btn-remove-row").addEventListener("click", () => row.remove());
});

// Attach delete handler to initial default item row
document.querySelectorAll(".item-row .btn-remove-row").forEach(btn => {
    btn.addEventListener("click", (e) => {
        btn.closest(".item-row").remove();
    });
});

DOM.aiQuoteForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const clientName = DOM.quoteClientName.value;
    const clientEmail = DOM.quoteClientEmail.value;
    const clientPhone = DOM.quoteClientPhone.value;
    const extraReqs = DOM.quoteExtraReqs.value;
    
    // Parse items
    const items = [];
    const rows = document.querySelectorAll("#quote-items-list .item-row");
    rows.forEach(r => {
        items.push({
            producto: r.querySelector(".item-product").value,
            cantidad: parseInt(r.querySelector(".item-qty").value),
            precio_unitario: parseFloat(r.querySelector(".item-price").value)
        });
    });
    
    if (items.length === 0) {
        showToast("Debes agregar al menos un ítem a la cotización", "error");
        return;
    }
    
    // Set loading state
    DOM.btnSubmitAiQuote.disabled = true;
    DOM.btnSubmitAiQuote.innerHTML = 'Generando Cotización con IA... <i class="fa-solid fa-spinner fa-spin"></i>';
    
    try {
        const result = await apiRequest("/api/v1/cotizaciones/generate", {
            method: "POST",
            body: JSON.stringify({
                cliente_nombre: clientName,
                datos_contacto: {
                    email: clientEmail,
                    telefono: clientPhone
                },
                items,
                requerimientos_adicionales: extraReqs
            })
        });
        
        showToast("¡Propuesta y cotización creadas con éxito!");
        DOM.aiQuoteForm.reset();
        
        // Reset rows to single default
        DOM.quoteItemsList.innerHTML = `
            <div class="item-row">
                <input type="text" class="item-product" placeholder="Descripción del Producto/Servicio" required>
                <input type="number" class="item-qty" placeholder="Cant" min="1" required>
                <input type="number" class="item-price" placeholder="Precio Unitario" min="0" step="0.01" required>
                <button type="button" class="btn-remove-row btn-danger-icon"><i class="fa-solid fa-trash"></i></button>
            </div>
        `;
        DOM.quoteItemsList.querySelector(".btn-remove-row").addEventListener("click", (e) => {
            e.currentTarget.closest(".item-row").remove();
        });
        
        DOM.aiQuoteWrapper.classList.add("hidden");
        loadCotizacionesData();
        
        // Show the newly generated proposal modal automatically!
        if (result.data) {
            showProposalModal(result.data);
        }
    } catch (e) {
        showToast(e.message, "error");
    } finally {
        DOM.btnSubmitAiQuote.disabled = false;
        DOM.btnSubmitAiQuote.innerHTML = 'Generando Propuesta y Calcular Totales <i class="fa-solid fa-sparkles">';
    }
});

DOM.searchQuoteClient.addEventListener("input", () => {
    state.quotesCurrentPage = 1;
    renderQuotesTableFiltered();
});

DOM.filterQuoteSeller.addEventListener("change", () => {
    state.quotesCurrentPage = 1;
    renderQuotesTableFiltered();
});

DOM.filterQuoteDays.addEventListener("change", () => {
    state.quotesCurrentPage = 1;
    renderQuotesTableFiltered();
});

/* --- Proposal Modal Handlers --- */
function closeModal() {
    DOM.proposalModal.classList.add("hidden");
}

DOM.btnCloseProposalModal.addEventListener("click", closeModal);
DOM.btnCloseProposal.addEventListener("click", closeModal);
DOM.proposalModal.addEventListener("click", (e) => {
    if (e.target === DOM.proposalModal) closeModal();
});

DOM.btnCopyProposal.addEventListener("click", () => {
    const text = DOM.modalProposalBody.textContent;
    navigator.clipboard.writeText(text).then(() => {
        showToast("Copiado al portapapeles");
    }).catch(e => {
        showToast("Fallo al copiar texto", "error");
    });
});

/* ==========================================================================
   INITIALIZATION
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
    initSession();
});
