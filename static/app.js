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
    quotesPageSize: 15,
    quotesSortOrder: null, // 'asc', 'desc', or null
    kanbanSortOrders: {
        propuesta: null,
        cotizado: null,
        vendido: null,
        vencido: null
    }
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
    
    // Kanban board elements
    kanbanSearchClient: document.getElementById("kanban-search-client"),
    kanbanFilterSeller: document.getElementById("kanban-filter-seller"),
    kanbanFilterDays: document.getElementById("kanban-filter-days"),
    kanbanPropuesta: document.getElementById("kanban-propuesta"),
    kanbanCotizado: document.getElementById("kanban-cotizado"),
    kanbanVendido: document.getElementById("kanban-vendido"),
    kanbanVencido: document.getElementById("kanban-vencido"),
    countKanbanPropuesta: document.getElementById("count-kanban-propuesta"),
    countKanbanCotizado: document.getElementById("count-kanban-cotizado"),
    countKanbanVendido: document.getElementById("count-kanban-vendido"),
    countKanbanVencido: document.getElementById("count-kanban-vencido"),
    
    // Proposal Modal
    proposalModal: document.getElementById("proposal-modal"),
    modalProposalTitle: document.getElementById("modal-proposal-title"),
    modalProposalBody: document.getElementById("modal-proposal-body"),
    btnCopyProposal: document.getElementById("btn-copy-proposal"),
    btnCloseProposalModal: document.getElementById("btn-close-proposal-modal"),
    btnCloseProposal: document.getElementById("btn-close-proposal"),
    
    // Sidebar Collapse & Profile Edit
    btnToggleSidebar: document.getElementById("btn-toggle-sidebar"),
    sidebar: document.querySelector(".sidebar-container"),
    userAvatarBtn: document.getElementById("user-avatar-btn"),
    userAvatarImg: document.getElementById("user-avatar-img"),
    userAvatarPlaceholder: document.getElementById("user-avatar-placeholder"),
    profileModal: document.getElementById("profile-modal"),
    btnCloseProfileModal: document.getElementById("btn-close-profile-modal"),
    btnCancelProfile: document.getElementById("btn-cancel-profile"),
    profileForm: document.getElementById("profile-form"),
    profileFullname: document.getElementById("profile-fullname"),
    profileEmail: document.getElementById("profile-email"),
    profilePhone: document.getElementById("profile-phone"),
    profilePassword: document.getElementById("profile-password"),
    inputProfileAvatar: document.getElementById("input-profile-avatar"),
    profileAvatarPreview: document.getElementById("profile-avatar-preview"),
    profileAvatarPlaceholder: document.getElementById("profile-avatar-placeholder"),
    profileAvatarUploader: document.getElementById("profile-avatar-uploader"),
    
    // Sort Controls
    sortQuotesAsc: document.getElementById("sort-quotes-asc"),
    sortQuotesDesc: document.getElementById("sort-quotes-desc"),
    
    // Theme Toggle
    themeToggleBtn: document.getElementById("theme-toggle-btn"),
    themeToggleIcon: document.getElementById("theme-toggle-icon")
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

async function initSession() {
    if (state.token) {
        try {
            // Fetch fresh user profile
            const profileRes = await apiRequest("/api/auth/me");
            if (profileRes.status === "success" && profileRes.data) {
                state.user = profileRes.data;
                localStorage.setItem("crm_user", JSON.stringify(state.user));
            }
        } catch (e) {
            console.error("Fallo al validar sesión:", e);
            logout();
            return;
        }

        // Hide login, show dashboard
        DOM.authContainer.classList.add("hidden");
        DOM.dashboardContainer.classList.remove("hidden");
        
        // Set user badge
        const displayName = state.user.nombre_completo || state.user.email.split("@")[0].toUpperCase();
        DOM.userDisplayName.textContent = displayName;
        DOM.userRoleBadge.textContent = state.user.rol.toUpperCase();
        
        // Show avatar image if exists
        if (state.user.avatar) {
            DOM.userAvatarImg.src = state.user.avatar;
            DOM.userAvatarImg.classList.remove("hidden");
            DOM.userAvatarPlaceholder.classList.add("hidden");
        } else {
            DOM.userAvatarImg.src = "";
            DOM.userAvatarImg.classList.add("hidden");
            DOM.userAvatarPlaceholder.classList.remove("hidden");
        }
        
        // Manage visible menu entries based on role (vendedores is admin/gerente only)
        if (state.user.rol === "vendedor") {
            DOM.menuVendedores.classList.add("hidden");
            DOM.btnGenerateGoalsModal.classList.add("hidden");
        } else {
            DOM.menuVendedores.classList.remove("hidden");
            DOM.btnGenerateGoalsModal.classList.remove("hidden");
        }
        
        // Go to initial summary view
        switchSection(state.currentSection || "summary");
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
        } else if (sectionId === "seguimiento") {
            await loadKanbanData();
        } else if (sectionId === "agentes") {
            await loadAgentesSectionData();
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
    renderQuotesHeatmap(quotes);
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
            <td><strong>${v.nombre_completo || 'Sin nombre'}</strong></td>
            <td>${v.email}</td>
            <td>${v.telefono_whatsapp || '<span class="text-muted">No asignado</span>'}</td>
            <td><span class="status-pill status-rol">${v.rol}</span></td>
            <td>
                <button class="btn btn-secondary btn-sm edit-seller-btn" data-id="${v.id}">
                    <i class="fa-solid fa-pen"></i> Editar Datos
                </button>
            </td>
        `;
        DOM.tableVendedores.appendChild(tr);
    });
    
    // Attach event listeners to Edit buttons
    document.querySelectorAll(".edit-seller-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            const id = btn.getAttribute("data-id");
            const seller = state.vendedores.find(s => s.id === id);
            if (seller) {
                openEditSellerModal(seller);
            }
        });
    });
}

function openEditSellerModal(seller) {
    document.getElementById("edit-seller-id").value = seller.id;
    document.getElementById("edit-seller-name").value = seller.nombre_completo || "";
    document.getElementById("edit-seller-email").value = seller.email || "";
    document.getElementById("edit-seller-phone").value = seller.telefono_whatsapp || "";
    
    document.getElementById("edit-seller-modal").classList.remove("hidden");
}

function closeEditSellerModal() {
    document.getElementById("edit-seller-modal").classList.add("hidden");
}

document.addEventListener("DOMContentLoaded", () => {
    // Add close events for edit seller modal
    const closeBtn = document.getElementById("btn-close-edit-seller-modal");
    const cancelBtn = document.getElementById("btn-cancel-edit-seller");
    if (closeBtn) closeBtn.addEventListener("click", closeEditSellerModal);
    if (cancelBtn) cancelBtn.addEventListener("click", closeEditSellerModal);
    
    // Submit Edit Seller
    const editForm = document.getElementById("edit-seller-form");
    if (editForm) {
        editForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const id = document.getElementById("edit-seller-id").value;
            const payload = {
                nombre_completo: document.getElementById("edit-seller-name").value,
                email: document.getElementById("edit-seller-email").value,
                telefono_whatsapp: document.getElementById("edit-seller-phone").value
            };
            
            try {
                await apiRequest(`/api/v1/vendedores/${id}`, {
                    method: "PUT",
                    body: JSON.stringify(payload)
                });
                showToast("Vendedor actualizado correctamente");
                closeEditSellerModal();
                loadVendedoresData();
            } catch (err) {
                showToast(err.message, "error");
            }
        });
    }
});

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
    
    // 4. Sort by Total
    if (state.quotesSortOrder) {
        if (state.quotesSortOrder === "asc") {
            filteredQuotes = [...filteredQuotes].sort((a, b) => Number(a.total) - Number(b.total));
        } else if (state.quotesSortOrder === "desc") {
            filteredQuotes = [...filteredQuotes].sort((a, b) => Number(b.total) - Number(a.total));
        }
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
   KANBAN BOARD MODULE
   ========================================================================== */

async function loadKanbanData(forceRefresh = false) {
    // Make sure vendedores are loaded
    if (state.user.rol !== "vendedor" && state.vendedores.length === 0) {
        const sellersRes = await apiRequest("/api/v1/vendedores/?limit=100");
        state.vendedores = sellersRes.data || [];
    }
    
    // Populate dropdown
    if (DOM.kanbanFilterSeller && DOM.kanbanFilterSeller.options.length <= 1) {
        state.vendedores.forEach(v => {
            const opt = document.createElement("option");
            opt.value = v.id;
            opt.textContent = v.email;
            DOM.kanbanFilterSeller.appendChild(opt);
        });
    }
    
    if (forceRefresh || state.cotizaciones.length === 0) {
        let endpoint = "/api/v1/cotizaciones/?limit=3000";
        const res = await apiRequest(endpoint);
        state.cotizaciones = res.data || [];
    }
    
    renderKanbanColumns();
}

function renderKanbanColumns() {
    const searchVal = DOM.kanbanSearchClient ? DOM.kanbanSearchClient.value.toLowerCase() : "";
    const sellerVal = DOM.kanbanFilterSeller ? DOM.kanbanFilterSeller.value : "";
    const daysVal = DOM.kanbanFilterDays ? DOM.kanbanFilterDays.value : "";
    
    let filteredQuotes = state.cotizaciones;
    
    // Apply filters
    if (searchVal) {
        filteredQuotes = filteredQuotes.filter(q => q.cliente_nombre.toLowerCase().includes(searchVal));
    }
    
    if (sellerVal) {
        filteredQuotes = filteredQuotes.filter(q => q.vendedor_id === sellerVal);
    }
    
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
    
    // Categorize quotes
    const stages = {
        propuesta: [],
        cotizado: [],
        vendido: [],
        vencido: []
    };
    
    const refDate = new Date("2026-06-18T12:00:00Z");
    
    filteredQuotes.forEach(q => {
        const hasInvoice = !!q.numero_factura;
        const isLost = q.venta_perdida === "Si";
        const hasQuoteNum = !!q.numero_cotizacion;
        
        let ageDays = 0;
        if (q.fecha_registro) {
            const qDate = new Date(`${q.fecha_registro}T12:00:00Z`);
            ageDays = Math.floor((refDate - qDate) / (1000 * 60 * 60 * 24));
        }
        
        if (hasInvoice) {
            stages.vendido.push(q);
        } else if (isLost || ageDays > 30) {
            stages.vencido.push(q);
        } else if (hasQuoteNum) {
            stages.cotizado.push(q);
        } else {
            stages.propuesta.push(q);
        }
    });
    
    // Sort columns if sort order is set
    const columns = ['propuesta', 'cotizado', 'vendido', 'vencido'];
    columns.forEach(col => {
        const order = state.kanbanSortOrders[col];
        if (order) {
            if (order === "asc") {
                stages[col].sort((a, b) => Number(a.total) - Number(b.total));
            } else if (order === "desc") {
                stages[col].sort((a, b) => Number(b.total) - Number(a.total));
            }
        }
    });
    
    // Render columns
    columns.forEach(col => {
        const container = DOM[`kanban${col.charAt(0).toUpperCase() + col.slice(1)}`];
        const countSpan = DOM[`countKanban${col.charAt(0).toUpperCase() + col.slice(1)}`];
        
        if (!container) return;
        
        container.innerHTML = "";
        if (countSpan) {
            countSpan.textContent = stages[col].length;
        }
        
        stages[col].forEach(q => {
            const card = document.createElement("div");
            card.className = "kanban-card";
            card.setAttribute("draggable", "true");
            card.setAttribute("data-id", q.id);
            
            const sellerEmail = q.vendedor_id === state.user.id ? state.user.email : (state.vendedores.find(v => v.id === q.vendedor_id)?.email || q.vendedor_id);
            const dateStr = q.fecha_registro || '-';
            const quoteNum = q.numero_cotizacion || '-';
            const totalStr = q.total.toLocaleString('es-MX', { minimumFractionDigits: 2 });
            
            let statusBadge = "";
            if (col === "vendido") {
                statusBadge = `<span class="kanban-card-badge kanban-card-badge-sold" title="Factura: ${q.numero_factura || ''}">Vendido</span>`;
            } else if (col === "vencido") {
                statusBadge = `<span class="kanban-card-badge kanban-card-badge-lost">${q.venta_perdida === "Si" ? 'Perdida' : 'Expirada'}</span>`;
            }
            
            card.innerHTML = `
                <div class="kanban-card-header">
                    <h4 class="kanban-card-client">${q.cliente_nombre}</h4>
                    <span class="kanban-card-num">${quoteNum !== '-' ? '#' + quoteNum : 'Sin #'}</span>
                </div>
                <div class="kanban-card-body">
                    <div class="kanban-card-date"><i class="fa-regular fa-calendar"></i> ${dateStr}</div>
                    <div class="kanban-card-seller" title="${sellerEmail}"><i class="fa-regular fa-user"></i> ${sellerEmail}</div>
                </div>
                <div class="kanban-card-footer">
                    <span class="kanban-card-total">$${totalStr}</span>
                    ${statusBadge}
                </div>
            `;
            
            // Drag listeners on card
            card.addEventListener("dragstart", (e) => {
                card.classList.add("dragging");
                e.dataTransfer.setData("text/plain", q.id);
                e.dataTransfer.effectAllowed = "move";
            });
            
            card.addEventListener("dragend", () => {
                card.classList.remove("dragging");
            });
            
            // Open proposal modal on click (if they don't drag)
            card.addEventListener("click", (e) => {
                if (e.target.closest(".kanban-card-actions") || card.classList.contains("dragging")) return;
                showProposalModal(q);
            });
            
            container.appendChild(card);
        });
    });
    
    setupKanbanDragAndDrop();
}

function setupKanbanDragAndDrop() {
    const columns = document.querySelectorAll(".kanban-column");
    
    columns.forEach(col => {
        // Dragover
        col.addEventListener("dragover", (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = "move";
        });
        
        // Dragenter
        col.addEventListener("dragenter", (e) => {
            e.preventDefault();
            col.classList.add("drag-over");
        });
        
        // Dragleave
        col.addEventListener("dragleave", () => {
            col.classList.remove("drag-over");
        });
        
        // Drop
        col.addEventListener("drop", async (e) => {
            e.preventDefault();
            col.classList.remove("drag-over");
            
            const quoteId = e.dataTransfer.getData("text/plain");
            const targetStage = col.getAttribute("data-stage");
            
            if (quoteId && targetStage) {
                await transitionQuoteStage(quoteId, targetStage);
            }
        });
    });
}

async function transitionQuoteStage(quoteId, targetStage) {
    const quote = state.cotizaciones.find(q => q.id === quoteId);
    if (!quote) return;
    
    let updatePayload = {};
    
    if (targetStage === "vendido") {
        // Prompt for invoice number
        const invoiceNum = prompt("Ingresa el número de factura para confirmar la venta:", quote.numero_factura || "");
        if (invoiceNum === null) return; // User cancelled
        if (invoiceNum.trim() === "") {
            showToast("Debes ingresar un número de factura válido.", "error");
            return;
        }
        updatePayload = {
            numero_factura: invoiceNum,
            venta_perdida: "No"
        };
    } else if (targetStage === "vencido") {
        // Prompt if sale lost
        const isLost = confirm("¿Marcar esta cotización como venta perdida oficialmente?\n(Presiona Cancelar para marcar como vencida/expirada ordinaria)");
        updatePayload = {
            venta_perdida: isLost ? "Si" : "No",
            numero_factura: null
        };
    } else if (targetStage === "cotizado") {
        // Prompt for quote number if empty
        let quoteNum = quote.numero_cotizacion;
        if (!quoteNum) {
            quoteNum = prompt("Ingresa el número de cotización oficial:", "");
            if (quoteNum === null) return; // cancelled
            if (quoteNum.trim() === "") {
                showToast("Debes ingresar un número de cotización.", "error");
                return;
            }
        }
        updatePayload = {
            numero_cotizacion: quoteNum,
            numero_factura: null,
            venta_perdida: "No"
        };
    } else if (targetStage === "propuesta") {
        // Reset to proposal
        const confirmReset = confirm("¿Estás seguro de regresar esta cotización al estado de Propuesta?\nSe eliminarán los números de cotización y factura asociados.");
        if (!confirmReset) return;
        updatePayload = {
            numero_cotizacion: null,
            numero_factura: null,
            venta_perdida: "No"
        };
    }
    
    try {
        const res = await apiRequest(`/api/v1/cotizaciones/${quoteId}`, {
            method: "PUT",
            body: JSON.stringify(updatePayload)
        });
        
        showToast("Estado de la cotización actualizado con éxito.");
        
        // Update local quote reference in state
        if (res.data) {
            const idx = state.cotizaciones.findIndex(q => q.id === quoteId);
            if (idx !== -1) {
                state.cotizaciones[idx] = res.data;
            }
        }
        
        renderKanbanColumns();
    } catch (e) {
        showToast(e.message, "error");
    }
}

/* ==========================================================================
   CHARTS RENDERING ENGINE
   ========================================================================== */

function renderSalesChart(quotes) {
    if (state.salesChart) {
        state.salesChart.destroy();
    }
    
    // Group quotes total by seller
    const grouped = {};
    quotes.forEach(q => {
        let sellerEmail = q.vendedor_id;
        if (q.vendedor_id === state.user.id) {
            sellerEmail = state.user.email;
        } else {
            const seller = state.vendedores.find(v => v.id === q.vendedor_id);
            if (seller && seller.email) {
                sellerEmail = seller.email;
            }
        }
        const label = sellerEmail.includes("@") ? sellerEmail.split("@")[0] : sellerEmail;
        grouped[label] = (grouped[label] || 0) + q.total;
    });
    
    // Convert to sorted array descending by total
    const sortedData = Object.keys(grouped).map(label => ({
        label: label,
        total: grouped[label]
    })).sort((a, b) => b.total - a.total);
    
    const labels = sortedData.map(item => item.label);
    const data = sortedData.map(item => item.total);
    
    // Determine dynamic styling based on active theme
    const isLightMode = document.body.classList.contains("light-mode");
    const tickColor = isLightMode ? '#333333' : '#abb2bf';
    const gridColor = isLightMode ? 'rgba(0, 0, 0, 0.08)' : 'rgba(255, 255, 255, 0.05)';
    
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
                hoverBorderColor: '#00f2fe',
                maxBarThickness: 50,
                barPercentage: 0.6,
                categoryPercentage: 0.8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: tickColor } }
            },
            scales: {
                x: { ticks: { color: tickColor }, grid: { color: gridColor } },
                y: { ticks: { color: tickColor }, grid: { color: gridColor } }
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
    
    // Determine dynamic styling based on active theme
    const isLightMode = document.body.classList.contains("light-mode");
    const tickColor = isLightMode ? '#333333' : '#abb2bf';
    const gridColor = isLightMode ? 'rgba(0, 0, 0, 0.08)' : 'rgba(255, 255, 255, 0.05)';
    
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
                legend: { labels: { color: tickColor } }
            },
            scales: {
                r: {
                    angleLines: { color: gridColor },
                    grid: { color: gridColor },
                    pointLabels: { color: tickColor },
                    ticks: { backdropColor: 'transparent', color: tickColor }
                }
            }
        }
    });
}

function renderQuotesHeatmap(quotes) {
    const gridEl = document.getElementById("heatmap-quotes-grid");
    if (!gridEl) return;
    gridEl.innerHTML = "";

    const xCategories = [
        { label: "0-7 días", minDays: 0, maxDays: 7 },
        { label: "8-15 días", minDays: 8, maxDays: 15 },
        { label: "16-30 días", minDays: 16, maxDays: 30 },
        { label: "30+ días", minDays: 31, maxDays: 99999 }
    ];

    const yCategories = [
        { label: "Bajo ($0-$10k)", minVal: 0, maxVal: 10000 },
        { label: "Medio ($10k-$50k)", minVal: 10000, maxVal: 50000 },
        { label: "Alto ($50k-$200k)", minVal: 50000, maxVal: 200000 },
        { label: "Premium ($200k+)", minVal: 200000, maxVal: Infinity }
    ];

    // Initialize matrix
    const matrix = Array(yCategories.length).fill(null).map(() => 
        Array(xCategories.length).fill(null).map(() => ({ count: 0, sum: 0 }))
    );

    const refDate = new Date("2026-06-18T12:00:00Z");

    quotes.forEach(q => {
        let ageDays = 0;
        if (q.fecha_registro) {
            const qDate = new Date(`${q.fecha_registro}T12:00:00Z`);
            ageDays = Math.floor((refDate - qDate) / (1000 * 60 * 60 * 24));
            if (ageDays < 0) ageDays = 0;
        } else {
            ageDays = 999;
        }

        const amt = Number(q.total);

        // Find Y category (quote amount)
        const yIdx = yCategories.findIndex(c => amt >= c.minVal && amt < c.maxVal);
        // Find X category (age days)
        const xIdx = xCategories.findIndex(c => ageDays >= c.minDays && ageDays <= c.maxDays);

        if (xIdx !== -1 && yIdx !== -1) {
            matrix[yIdx][xIdx].count++;
            matrix[yIdx][xIdx].sum += amt;
        }
    });

    // 1. Create Corner cell
    const corner = document.createElement("div");
    corner.style.visibility = "hidden";
    gridEl.appendChild(corner);

    // 2. Render X-Axis Headers (Age Categories)
    xCategories.forEach(cat => {
        const header = document.createElement("div");
        header.className = "heatmap-header-x";
        header.textContent = cat.label;
        gridEl.appendChild(header);
    });

    // 3. Render Matrix Rows (Y Headers + Cells)
    // Render YCategories in reverse order (Premium first, Bajo last) to place higher amounts on top
    for (let yIdx = yCategories.length - 1; yIdx >= 0; yIdx--) {
        const yCat = yCategories[yIdx];
        
        // Y Header
        const header = document.createElement("div");
        header.className = "heatmap-header-y";
        header.textContent = yCat.label;
        gridEl.appendChild(header);

        // Cells for this row
        xCategories.forEach((xCat, xIdx) => {
            const cellData = matrix[yIdx][xIdx];

            // Determine temperature class based on count
            let tempClass = "temp-0";
            if (cellData.count > 0) {
                if (cellData.count <= 2) tempClass = "temp-low";
                else if (cellData.count <= 5) tempClass = "temp-medium";
                else if (cellData.count <= 10) tempClass = "temp-high";
                else tempClass = "temp-extreme";
            }

            const cell = document.createElement("div");
            cell.className = `heatmap-cell ${tempClass}`;

            const sumStr = cellData.sum > 0 ? 
                `$${(cellData.sum / 1000).toFixed(1)}k` : 
                "$0";

            cell.innerHTML = `
                <span class="heatmap-cell-count">${cellData.count}</span>
                <span class="heatmap-cell-sum">${sumStr}</span>
                <div class="heatmap-cell-tooltip">
                    <strong>Monto:</strong> ${yCat.label}<br>
                    <strong>Edad:</strong> ${xCat.label}<br>
                    <strong>Cotizaciones:</strong> ${cellData.count}<br>
                    <strong>Total:</strong> $${cellData.sum.toLocaleString('es-MX', { maximumFractionDigits: 0 })}
                </div>
            `;
            gridEl.appendChild(cell);
        });
    }
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
        
        // Save token
        state.token = data.access_token;
        localStorage.setItem("crm_token", state.token);
        
        // initSession will fetch the fresh user profile via /api/auth/me
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

// Kanban Board event listeners
if (DOM.kanbanSearchClient) {
    DOM.kanbanSearchClient.addEventListener("input", () => {
        renderKanbanColumns();
    });
}
if (DOM.kanbanFilterSeller) {
    DOM.kanbanFilterSeller.addEventListener("change", () => {
        renderKanbanColumns();
    });
}
if (DOM.kanbanFilterDays) {
    DOM.kanbanFilterDays.addEventListener("change", () => {
        renderKanbanColumns();
    });
}

// Quotes Table Sorting listeners
if (DOM.sortQuotesAsc) {
    DOM.sortQuotesAsc.addEventListener("click", () => {
        if (state.quotesSortOrder === "asc") {
            state.quotesSortOrder = null;
            DOM.sortQuotesAsc.classList.remove("active");
        } else {
            state.quotesSortOrder = "asc";
            DOM.sortQuotesAsc.classList.add("active");
            if (DOM.sortQuotesDesc) DOM.sortQuotesDesc.classList.remove("active");
        }
        renderQuotesTableFiltered();
    });
}

if (DOM.sortQuotesDesc) {
    DOM.sortQuotesDesc.addEventListener("click", () => {
        if (state.quotesSortOrder === "desc") {
            state.quotesSortOrder = null;
            DOM.sortQuotesDesc.classList.remove("active");
        } else {
            state.quotesSortOrder = "desc";
            DOM.sortQuotesDesc.classList.add("active");
            if (DOM.sortQuotesAsc) DOM.sortQuotesAsc.classList.remove("active");
        }
        renderQuotesTableFiltered();
    });
}

// Kanban Column Sorting listeners
document.addEventListener("click", (e) => {
    const ascBtn = e.target.closest(".sort-kanban-column-asc");
    if (ascBtn) {
        const col = ascBtn.getAttribute("data-column");
        const header = ascBtn.closest(".kanban-column-header");
        const descBtn = header ? header.querySelector(".sort-kanban-column-desc") : null;
        
        if (state.kanbanSortOrders[col] === "asc") {
            state.kanbanSortOrders[col] = null;
            ascBtn.classList.remove("active");
        } else {
            state.kanbanSortOrders[col] = "asc";
            ascBtn.classList.add("active");
            if (descBtn) descBtn.classList.remove("active");
        }
        renderKanbanColumns();
        return;
    }
    
    const descBtn = e.target.closest(".sort-kanban-column-desc");
    if (descBtn) {
        const col = descBtn.getAttribute("data-column");
        const header = descBtn.closest(".kanban-column-header");
        const ascBtn = header ? header.querySelector(".sort-kanban-column-asc") : null;
        
        if (state.kanbanSortOrders[col] === "desc") {
            state.kanbanSortOrders[col] = null;
            descBtn.classList.remove("active");
        } else {
            state.kanbanSortOrders[col] = "desc";
            descBtn.classList.add("active");
            if (ascBtn) ascBtn.classList.remove("active");
        }
        renderKanbanColumns();
        return;
    }
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
   SIDEBAR COLLAPSE & PROFILE MANAGEMENT
   ========================================================================== */

// Sidebar collapse persistence on load
if (localStorage.getItem("sidebar_collapsed") === "true" && DOM.sidebar) {
    DOM.sidebar.classList.add("collapsed");
}

if (DOM.btnToggleSidebar) {
    DOM.btnToggleSidebar.addEventListener("click", () => {
        if (DOM.sidebar) {
            DOM.sidebar.classList.toggle("collapsed");
            const isCollapsed = DOM.sidebar.classList.contains("collapsed");
            localStorage.setItem("sidebar_collapsed", isCollapsed);
        }
    });
}

// Theme Toggle Handler
if (DOM.themeToggleBtn) {
    DOM.themeToggleBtn.addEventListener("click", () => {
        toggleTheme();
    });
}

// User Profile Modal Handlers
if (DOM.userAvatarBtn) {
    DOM.userAvatarBtn.addEventListener("click", () => {
        // Populate fields
        DOM.profileFullname.value = state.user.nombre_completo || "";
        DOM.profileEmail.value = state.user.email || "";
        DOM.profilePhone.value = state.user.telefono_whatsapp || "";
        DOM.profilePassword.value = "";
        profileAvatarBase64 = null;
        
        // Preview avatar
        if (state.user.avatar) {
            DOM.profileAvatarPreview.src = state.user.avatar;
            DOM.profileAvatarPreview.classList.remove("hidden");
            DOM.profileAvatarPlaceholder.classList.add("hidden");
        } else {
            DOM.profileAvatarPreview.src = "";
            DOM.profileAvatarPreview.classList.add("hidden");
            DOM.profileAvatarPlaceholder.classList.remove("hidden");
        }
        
        DOM.profileModal.classList.remove("hidden");
    });
}

function closeProfileModal() {
    DOM.profileModal.classList.add("hidden");
}

if (DOM.btnCloseProfileModal) DOM.btnCloseProfileModal.addEventListener("click", closeProfileModal);
if (DOM.btnCancelProfile) DOM.btnCancelProfile.addEventListener("click", closeProfileModal);
if (DOM.profileModal) {
    DOM.profileModal.addEventListener("click", (e) => {
        if (e.target === DOM.profileModal) closeProfileModal();
    });
}

// Click trigger for circular avatar uploader
if (DOM.profileAvatarUploader && DOM.inputProfileAvatar) {
    DOM.profileAvatarUploader.addEventListener("click", () => {
        DOM.inputProfileAvatar.click();
    });
}

// Convert uploaded photo to Base64
let profileAvatarBase64 = null;
if (DOM.inputProfileAvatar) {
    DOM.inputProfileAvatar.addEventListener("change", (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (event) => {
                profileAvatarBase64 = event.target.result;
                DOM.profileAvatarPreview.src = profileAvatarBase64;
                DOM.profileAvatarPreview.classList.remove("hidden");
                DOM.profileAvatarPlaceholder.classList.add("hidden");
            };
            reader.readAsDataURL(file);
        }
    });
}

// Handle profile update submit
if (DOM.profileForm) {
    DOM.profileForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const payload = {
            nombre_completo: DOM.profileFullname.value,
            email: DOM.profileEmail.value,
            telefono_whatsapp: DOM.profilePhone.value || null
        };
        
        if (DOM.profilePassword.value) {
            payload.password = DOM.profilePassword.value;
        }
        
        if (profileAvatarBase64) {
            payload.avatar = profileAvatarBase64;
        }
        
        try {
            const res = await apiRequest(`/api/v1/vendedores/${state.user.id}`, {
                method: "PUT",
                body: JSON.stringify(payload)
            });
            
            showToast("Perfil actualizado correctamente.");
            
            // Save updated user state
            state.user = res.data;
            localStorage.setItem("crm_user", JSON.stringify(state.user));
            
            closeProfileModal();
            
            // Re-render display
            const displayName = state.user.nombre_completo || state.user.email.split("@")[0].toUpperCase();
            DOM.userDisplayName.textContent = displayName;
            
            if (state.user.avatar) {
                DOM.userAvatarImg.src = state.user.avatar;
                DOM.userAvatarImg.classList.remove("hidden");
                DOM.userAvatarPlaceholder.classList.add("hidden");
            }
            
            profileAvatarBase64 = null;
        } catch (err) {
            showToast(err.message, "error");
        }
    });
}

/* ==========================================================================
   CENTRALIZED AGENTS HANDLERS (CEO, COACH, OUTREACH)
   ========================================================================== */

async function loadAgentesSectionData() {
    // We need sellers data to populate dropdowns. If state.vendedores is empty, fetch it.
    if (state.vendedores.length === 0) {
        if (state.user.rol !== "vendedor") {
            const res = await apiRequest("/api/v1/vendedores/?limit=100");
            state.vendedores = res.data || [];
        } else {
            state.vendedores = [state.user]; // Only themselves if they are a seller
        }
    }
    
    // Populate the dropdown selects
    const ceoSellerSel = document.getElementById("agent-ceo-seller");
    const coachSellerSel = document.getElementById("agent-coach-seller");
    
    if (ceoSellerSel) {
        ceoSellerSel.innerHTML = '<option value="">Selecciona un vendedor...</option>';
        state.vendedores.forEach(v => {
            const opt = document.createElement("option");
            opt.value = v.id;
            opt.textContent = v.nombre_completo || v.email;
            ceoSellerSel.appendChild(opt);
        });
    }
    
    if (coachSellerSel) {
        coachSellerSel.innerHTML = '<option value="">Selecciona un vendedor...</option>';
        state.vendedores.forEach(v => {
            const opt = document.createElement("option");
            opt.value = v.id;
            opt.textContent = v.nombre_completo || v.email;
            coachSellerSel.appendChild(opt);
        });
    }
}

// CEO Form Handler
const ceoForm = document.getElementById("agent-ceo-form");
if (ceoForm) {
    ceoForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const sellerId = document.getElementById("agent-ceo-seller").value;
        const objectives = document.getElementById("agent-ceo-objectives").value;
        const submitBtn = document.getElementById("btn-agent-ceo-submit");
        const resultContainer = document.getElementById("agent-ceo-result");
        
        if (!sellerId) return;
        
        submitBtn.disabled = true;
        submitBtn.innerHTML = 'Procesando... <i class="fa-solid fa-spinner animate-spin"></i>';
        resultContainer.classList.add("hidden");
        
        try {
            const res = await apiRequest(`/api/v1/metas/generate/${sellerId}`, {
                method: "POST",
                body: JSON.stringify({ objetivos_globales: objectives })
            });
            
            showToast("Metas generadas y asignadas con éxito.");
            
            // Populate results
            document.getElementById("ceo-res-monto").textContent = `$${res.data.monto_objetivo.toLocaleString('es-MX', { minimumFractionDigits: 2 })}`;
            document.getElementById("ceo-res-desc").textContent = res.data.descripcion;
            
            const kpisUl = document.getElementById("ceo-res-kpis");
            kpisUl.innerHTML = "";
            (res.data.kpis_clave || []).forEach(kpi => {
                const li = document.createElement("li");
                li.textContent = kpi;
                kpisUl.appendChild(li);
            });
            
            resultContainer.classList.remove("hidden");
        } catch (err) {
            showToast(err.message, "error");
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Generar y Asignar Metas <i class="fa-solid fa-wand-magic-sparkles" style="margin-left: 6px;"></i>';
        }
    });
}

// Coach Form Handler
const coachForm = document.getElementById("agent-coach-form");
if (coachForm) {
    coachForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const sellerId = document.getElementById("agent-coach-seller").value;
        const sendWa = document.getElementById("agent-coach-whatsapp").checked;
        const submitBtn = document.getElementById("btn-agent-coach-submit");
        const resultContainer = document.getElementById("agent-coach-result");
        
        if (!sellerId) return;
        
        submitBtn.disabled = true;
        submitBtn.innerHTML = 'Generando feedback... <i class="fa-solid fa-spinner animate-spin"></i>';
        resultContainer.classList.add("hidden");
        
        try {
            const res = await apiRequest(`/api/v1/metas/coach/${sellerId}`, {
                method: "POST",
                body: JSON.stringify({ send_whatsapp: sendWa })
            });
            
            showToast("Feedback generado con éxito.");
            
            // Populate results
            document.getElementById("coach-res-message").textContent = res.data.mensaje;
            
            const waStatus = document.getElementById("coach-wa-status");
            if (sendWa) {
                if (res.data.whatsapp_enviado) {
                    waStatus.innerHTML = `<a href="${res.data.whatsapp_enviado}" target="_blank" style="color: #10b981; text-decoration: none;">WhatsApp: Listo para enviar <i class="fa-solid fa-arrow-up-right-from-square"></i></a>`;
                    waStatus.style.background = "rgba(16, 185, 129, 0.15)";
                    waStatus.style.color = "#10b981";
                    
                    // Auto-open in new tab
                    window.open(res.data.whatsapp_enviado, "_blank");
                } else {
                    waStatus.textContent = "WhatsApp: Fallido/No Configurado";
                    waStatus.style.background = "rgba(239, 68, 68, 0.15)";
                    waStatus.style.color = "#ef4444";
                }
            } else {
                waStatus.textContent = "WhatsApp: No solicitado";
                waStatus.style.background = "rgba(255,255,255,0.05)";
                waStatus.style.color = "hsl(var(--text-secondary))";
            }
            
            resultContainer.classList.remove("hidden");
        } catch (err) {
            showToast(err.message, "error");
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Generar Feedback <i class="fa-solid fa-message" style="margin-left: 6px;"></i>';
        }
    });
}

// Outreach trigger handler
const outreachTrigger = document.getElementById("btn-agent-outreach-trigger");
if (outreachTrigger) {
    outreachTrigger.addEventListener("click", () => {
        switchSection("cotizaciones");
        const aiQuoteWrapper = document.getElementById("ai-quote-wrapper");
        if (aiQuoteWrapper) {
            aiQuoteWrapper.classList.remove("hidden");
            aiQuoteWrapper.scrollIntoView({ behavior: 'smooth' });
        }
    });
}

// Analyst Trigger handler
const analystTrigger = document.getElementById("btn-agent-analyst-trigger");
if (analystTrigger) {
    analystTrigger.addEventListener("click", async () => {
        const submitBtn = analystTrigger;
        const resultContainer = document.getElementById("agent-analyst-result");
        
        submitBtn.disabled = true;
        submitBtn.innerHTML = 'Analizando negocio... <i class="fa-solid fa-spinner animate-spin"></i>';
        resultContainer.classList.add("hidden");
        
        try {
            const res = await apiRequest(`/api/v1/analisis/resumen`);
            
            showToast("Análisis completado exitosamente.");
            
            document.getElementById("analyst-res-content").textContent = res.resumen_ejecutivo;
            resultContainer.classList.remove("hidden");
        } catch (err) {
            showToast(err.message, "error");
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Generar Resumen Ejecutivo <i class="fa-solid fa-brain" style="margin-left: 6px;"></i>';
        }
    });
}

/* ==========================================================================
   THEME MANAGER
   ========================================================================== */

function initTheme() {
    const savedTheme = localStorage.getItem("theme_mode");
    const themeIcon = DOM.themeToggleIcon || document.getElementById("theme-toggle-icon");
    if (savedTheme === "light") {
        document.body.classList.add("light-mode");
        if (themeIcon) {
            themeIcon.className = "fa-solid fa-moon";
        }
    } else {
        document.body.classList.remove("light-mode");
        if (themeIcon) {
            themeIcon.className = "fa-solid fa-sun";
        }
    }
}

function toggleTheme() {
    const isLight = document.body.classList.toggle("light-mode");
    localStorage.setItem("theme_mode", isLight ? "light" : "dark");
    
    // Update button icon
    const themeIcon = DOM.themeToggleIcon || document.getElementById("theme-toggle-icon");
    if (themeIcon) {
        if (isLight) {
            themeIcon.className = "fa-solid fa-moon";
        } else {
            themeIcon.className = "fa-solid fa-sun";
        }
    }
    
    // Re-render charts to update tick and grid colors dynamically
    if (state.cotizaciones && state.cotizaciones.length > 0) {
        renderSalesChart(state.cotizaciones);
    }
    if (state.metas && state.vendedores) {
        renderGoalsChart(state.metas, state.cotizaciones, state.vendedores);
    }
}

/* ==========================================================================
   INITIALIZATION
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    initSession();
    
    // Password toggle
    const btnTogglePassword = document.getElementById("btn-toggle-password");
    if (btnTogglePassword) {
        btnTogglePassword.addEventListener("click", () => {
            const pwdInput = document.getElementById("login-password");
            const icon = document.getElementById("icon-toggle-password");
            if (pwdInput.type === "password") {
                pwdInput.type = "text";
                icon.className = "fa-regular fa-eye-slash";
            } else {
                pwdInput.type = "password";
                icon.className = "fa-regular fa-eye";
            }
        });
    }
});
