/* ==========================================================================
   APPLICATION LOGIC - CRM KURODA SPA
   ========================================================================== */

// Global Application State

function escapeHTML(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

const state = {
    token: localStorage.getItem("crm_token") || null,
    user: JSON.parse(localStorage.getItem("crm_user")) || null,
    currentSection: "summary",
    vendedores: [],
    metas: [],
    promociones: [],
    cotizaciones: [],
    salesChart: null,
    goalsChart: null,
    chartQuoteStatus: null,
    chartQuoteSeller: null,
    chartQuoteTrend: null,
    chartQuoteChannel: null,
    quotesCurrentPage: 1,
    quotesPageSize: 15,
    quotesSortOrder: null, // 'asc', 'desc', or null
    kanbanSortOrders: {
        cotizado: null,
        promociones: null,
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
    menuApi: document.getElementById("menu-api"),
    btnAddSeller: document.getElementById("btn-add-seller"),
    sellerFormWrapper: document.getElementById("seller-form-wrapper"),
    sellerForm: document.getElementById("seller-form"),
    btnCancelSeller: document.getElementById("btn-cancel-seller"),
    btnCloseSellerForm: document.getElementById("btn-close-seller-form"),
    tableVendedores: document.querySelector("#table-vendedores tbody"),
    selectSortSellers: document.getElementById("select-sort-sellers"),
    sellerFullname: document.getElementById("seller-fullname"),
    sellerRole: document.getElementById("seller-role"),
    sellerCode: document.getElementById("seller-code"),
    sellerCodeGroup: document.getElementById("seller-code-group"),
    sellerEmail: document.getElementById("seller-email"),
    sellerPhone: document.getElementById("seller-phone"),
    sellerPassword: document.getElementById("seller-password"),
    sellerFormTitle: document.getElementById("seller-form-title"),
    sellerPasswordLabel: document.getElementById("seller-password-label"),
    btnSubmitSeller: document.getElementById("btn-submit-seller"),
    
    // Metas Section
    btnGenerateGoalsModal: document.getElementById("btn-generate-goals-modal"),
    aiGoalsWrapper: document.getElementById("ai-goals-wrapper"),
    promoKpiCategories: document.getElementById("promo-kpi-categories"),
    promoKpiCommissions: document.getElementById("promo-kpi-commissions"),
    aiGoalsForm: document.getElementById("ai-goals-form"),
    aiGoalsVendedor: document.getElementById("ai-goals-vendedor"),
    aiGoalsGlobal: document.getElementById("ai-goals-global"),
    btnSubmitAiGoals: document.getElementById("btn-submit-ai-goals"),
    btnCancelAiGoals: document.getElementById("btn-cancel-ai-goals"),
    btnCloseAiGoals: document.getElementById("btn-close-ai-goals"),
    filterPromoProveedor: document.getElementById("filter-promo-proveedor"),
    promoKpiProveedores: document.getElementById("promo-kpi-proveedores"),
    filterPromoSearch: document.getElementById("filter-promo-search"),
    thInvDisp: document.getElementById("th-inv-disp"),
    btnClearPromoFilters: document.getElementById("btn-clear-promo-filters"),
    filterPromoStatus: document.getElementById("filter-promo-status"),
    filterPromoSort: document.getElementById("filter-promo-sort"),
    tablePromociones: document.querySelector("#table-promociones tbody"),
    pagPromociones: document.getElementById("pag-promociones"),
    uploadPromocionesForm: document.getElementById("upload-promociones-form"),
    filePromociones: document.getElementById("file-promociones"),
    
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
    filterQuoteStartDate: document.getElementById("filter-quote-start-date"),
    filterQuoteEndDate: document.getElementById("filter-quote-end-date"),
    kpiQuotesTotalCount: document.getElementById("kpi-quotes-total-count"),
    kpiQuotesTotalAmount: document.getElementById("kpi-quotes-total-amount"),
    kpiQuotesSoldCount: document.getElementById("kpi-quotes-sold-count"),
    kpiQuotesSoldAmount: document.getElementById("kpi-quotes-sold-amount"),
    kpiQuotesPendingCount: document.getElementById("kpi-quotes-pending-count"),
    kpiQuotesPendingAmount: document.getElementById("kpi-quotes-pending-amount"),
    kpiQuotesExpiredCount: document.getElementById("kpi-quotes-expired-count"),
    kpiQuotesExpiredAmount: document.getElementById("kpi-quotes-expired-amount"),
    btnToggleQuotesDetails: document.getElementById("btn-toggle-quotes-details"),
    quotesDetailsToggleIcon: document.getElementById("quotes-details-toggle-icon"),
    quotesDetailsContent: document.getElementById("quotes-details-content"),
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
    themeToggleIcon: document.getElementById("theme-toggle-icon"),
    
    // Slight Edge Section
    slightEdgeSellerView: document.getElementById("slight-edge-seller-view"),
    slightEdgeDate: document.getElementById("slight-edge-date"),
    slightEdgePointsDesc: document.getElementById("slight-edge-points-desc"),
    slightEdgePointsCounter: document.getElementById("slight-edge-points-counter"),
    slightEdgeChecklistContainer: document.getElementById("slight-edge-checklist-container"),
    btnSaveSlightEdgeLog: document.getElementById("btn-save-slight-edge-log"),
    slightEdgeChatMessages: document.getElementById("slight-edge-chat-messages"),
    slightEdgeChatForm: document.getElementById("slight-edge-chat-form"),
    slightEdgeChatInput: document.getElementById("slight-edge-chat-input"),
    
    slightEdgeChatContainer: document.getElementById("slight-edge-chat-container"),
    slightEdgeDashboardContainer: document.getElementById("slight-edge-dashboard-container"),
    btnSlightEdgeBackToDashboard: document.getElementById("btn-slight-edge-back-to-dashboard"),
    btnSlightEdgeNewTask: document.getElementById("btn-slight-edge-new-task"),
    btnSlightEdgeAdjustCoach: document.getElementById("btn-slight-edge-adjust-coach"),
    btnSlightEdgeAdjustWeights: document.getElementById("btn-slight-edge-adjust-weights"),
    
    funnelTargetIncome: document.getElementById("funnel-target-income"),
    funnelTicketAvg: document.getElementById("funnel-ticket-avg"),
    funnelConvRate: document.getElementById("funnel-conv-rate"),
    funnelCalcSales: document.getElementById("funnel-calc-sales"),
    funnelCalcQuotes: document.getElementById("funnel-calc-quotes"),
    funnelCalcMeetings: document.getElementById("funnel-calc-meetings"),
    funnelCalcCalls: document.getElementById("funnel-calc-calls"),
    toggleFunnelReal: document.getElementById("toggle-funnel-real"),
    labelFunnelTargetIncome: document.getElementById("label-funnel-target-income"),
    labelFunnelTicketAvg: document.getElementById("label-funnel-ticket-avg"),
    labelFunnelConvRate: document.getElementById("label-funnel-conv-rate"),
    subtitleFunnelHeader: document.getElementById("subtitle-funnel-header"),
    labelFunnelSales: document.getElementById("label-funnel-sales"),
    labelFunnelQuotes: document.getElementById("label-funnel-quotes"),
    labelFunnelMeetings: document.getElementById("label-funnel-meetings"),
    labelFunnelCalls: document.getElementById("label-funnel-calls"),
    
    slightEdgeSummaryCard: document.getElementById("slight-edge-summary-card"),
    btnSlightEdgeSummaryCoach: document.getElementById("btn-slight-edge-summary-coach"),
    btnSlightEdgeSummaryGo: document.getElementById("btn-slight-edge-summary-go"),
    summaryPointsToday: document.getElementById("summary-points-today"),
    summaryPointsWeek: document.getElementById("summary-points-week"),
    summaryCompletedTodayText: document.getElementById("summary-completed-today-text"),
    summaryKpiCalls: document.getElementById("summary-kpi-calls"),
    summaryKpiMeetings: document.getElementById("summary-kpi-meetings"),
    summaryKpiQuotes: document.getElementById("summary-kpi-quotes"),
    summaryKpiSales: document.getElementById("summary-kpi-sales"),
    summaryConversionReal: document.getElementById("summary-conversion-real"),
    summaryConversionPlan: document.getElementById("summary-conversion-plan"),
    summaryConversionEfficiency: document.getElementById("summary-conversion-efficiency"),
    
    slightEdgeCoordinatorView: document.getElementById("slight-edge-coordinator-view"),
    coordinatorAlignmentAlert: document.getElementById("coordinator-alignment-alert"),
    alignmentIcon: document.getElementById("alignment_icon"),
    alignmentStatusTitle: document.getElementById("alignment_status_title"),
    alignmentStatusDesc: document.getElementById("alignment_status_desc"),
    alignmentDiffVal: document.getElementById("alignment_diff_val"),
    companySettingsForm: document.getElementById("company-settings-form"),
    coordinatorGlobalTarget: document.getElementById("coordinator-global-target"),
    coordinatorGlobalGoals: document.getElementById("coordinator-global-goals"),
    tableSlightEdgePerformance: document.querySelector("#table-slight-edge-performance tbody"),
    slightEdgeAiRecommendationCard: document.getElementById("slight-edge-ai-recommendation-card"),
    btnCloseSlightEdgeAi: document.getElementById("btn-close-slight-edge-ai"),
    slightEdgeAiContent: document.getElementById("slight-edge-ai-content")
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
            if (DOM.menuApi) DOM.menuApi.classList.add("hidden");
        } else {
            DOM.menuVendedores.classList.remove("hidden");
            DOM.btnGenerateGoalsModal.classList.remove("hidden");
            if (DOM.menuApi) DOM.menuApi.classList.remove("hidden");
        }

        // Show/hide conexion menu based on role
        
        // Go to initial summary view (default to slight-edge on mobile)
        const isMobile = window.innerWidth <= 768;
        if (isMobile) {
            switchSection("slight-edge");
        } else {
            switchSection(state.currentSection || "summary");
        }
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

    // Toggle active mobile bottom nav items
    document.querySelectorAll(".mobile-nav-item").forEach(item => {
        if (item.getAttribute("data-mobile-section") === sectionId) {
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
        } else if (sectionId === "promociones") {
            await loadPromocionesData();
        } else if (sectionId === "cotizaciones") {
            await loadCotizacionesData();
        } else if (sectionId === "seguimiento") {
            await loadKanbanData();
        } else if (sectionId === "agentes") {
            await loadAgentesSectionData();
        } else if (sectionId === "slight-edge") {
            await loadSlightEdgeData();
        } else if (sectionId === "asignacion") {
            await loadAsignacionData();
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
    
    const quotesRes = await apiRequest("/api/v1/cotizaciones/?limit=20000");
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
    
    // Load Slight Edge summary tracking card
    await loadSlightEdgeSummaryWidget();
}

async function loadVendedoresData() {
    if (state.user.rol === "vendedor") return;
    
    // Fetch sellers
    const res = await apiRequest("/api/v1/vendedores/?limit=100");
    const sellers = res.data || [];
    state.vendedores = sellers;
    
    // Fetch dashboard metrics
    let metricsMap = {};
    try {
        const dashboardRes = await apiRequest("/companies/kuroda/dashboard");
        if (dashboardRes && dashboardRes.sellers) {
            dashboardRes.sellers.forEach(s => {
                metricsMap[s.id] = s.metrics;
            });
        }
    } catch (e) {
        console.error("Error loading dashboard metrics for sellers:", e);
    }
    
    // Enrich sellers
    sellers.forEach(v => {
        v.metrics = metricsMap[v.id] || { sales: 0, target: 0, conversion_rate: 0, roi: 0 };
    });
    
    // Sort sellers
    const sortVal = DOM.selectSortSellers?.value || "nombre";
    if (sortVal === "nombre") {
        sellers.sort((a, b) => (a.nombre_completo || a.email).localeCompare(b.nombre_completo || b.email));
    } else if (sortVal === "eficiencia") {
        // Sort by ROI (Consistency Score) descending
        sellers.sort((a, b) => (b.metrics.roi || 0) - (a.metrics.roi || 0));
    } else if (sortVal === "efectividad") {
        // Sort by sales amount descending
        sellers.sort((a, b) => (b.metrics.sales || 0) - (a.metrics.sales || 0));
    } else if (sortVal === "conversion") {
        // Sort by conversion rate descending
        sellers.sort((a, b) => (b.metrics.conversion_rate || 0) - (a.metrics.conversion_rate || 0));
    }
    
    DOM.tableVendedores.innerHTML = "";
    if (sellers.length === 0) {
        DOM.tableVendedores.innerHTML = `<tr><td colspan="7" style="text-align: center;">No hay usuarios registrados.</td></tr>`;
        return;
    }
    
    sellers.forEach(v => {
        const tr = document.createElement("tr");
        
        // Format efficiency
        let efficiencyHtml = '<span class="text-muted">-</span>';
        if (v.rol === "vendedor" && v.metrics?.roi !== undefined) {
            efficiencyHtml = `<strong style="color: #f59e0b;">${v.metrics.roi} pts</strong>`;
        }
        
        // Format sales (effectiveness)
        let effectivenessHtml = '<span class="text-muted">-</span>';
        if (v.rol === "vendedor" && v.metrics?.sales !== undefined) {
            effectivenessHtml = `<strong style="color: #10b981;">$${v.metrics.sales.toLocaleString()}</strong>`;
        }
        
        // Format conversion rate
        let conversionHtml = '<span class="text-muted">-</span>';
        if (v.rol === "vendedor" && v.metrics?.conversion_rate !== undefined) {
            conversionHtml = `<span class="badge" style="background: rgba(56, 189, 248, 0.1); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.2);">${v.metrics.conversion_rate}%</span>`;
        }
        
        tr.innerHTML = `
            <td>
                <div style="display: flex; flex-direction: column; gap: 2px;">
                    <strong style="color: hsl(var(--text-primary)); font-size: 14px;">${escapeHTML(v.nombre_completo) || '<span class="text-muted">Sin Nombre</span>'}</strong>
                    <span style="font-size: 11px; color: hsl(var(--text-secondary));">${escapeHTML(v.email)}</span>
                    ${v.telefono_whatsapp ? `<span style="font-size: 11px; color: #38bdf8;"><i class="fa-brands fa-whatsapp" style="margin-right: 4px;"></i>${v.telefono_whatsapp}</span>` : ''}
                </div>
            </td>
            <td>
                <span class="status-pill status-rol" style="background: ${v.rol === 'admin' ? 'rgba(239, 68, 68, 0.15)' : v.rol === 'gerente' ? 'rgba(245, 158, 11, 0.15)' : 'rgba(93, 95, 239, 0.15)'}; color: ${v.rol === 'admin' ? '#ef4444' : v.rol === 'gerente' ? '#f59e0b' : '#5d5fef'}; border: 1px solid ${v.rol === 'admin' ? 'rgba(239, 68, 68, 0.3)' : v.rol === 'gerente' ? 'rgba(245, 158, 11, 0.3)' : 'rgba(93, 95, 239, 0.3)'};">
                    ${v.rol.toUpperCase()}
                </span>
            </td>
            <td>${v.codigo_vendedor || '<span class="text-muted">-</span>'}</td>
            <td>${efficiencyHtml}</td>
            <td>${effectivenessHtml}</td>
            <td>${conversionHtml}</td>
            <td>
                <div style="display: flex; gap: 8px;">
                    <button class="btn btn-secondary btn-sm edit-seller-btn" data-id="${v.id}" data-email="${escapeHTML(v.email)}" data-fullname="${escapeHTML(v.nombre_completo) || ''}" data-role="${v.rol}" data-phone="${v.telefono_whatsapp || ''}" data-code="${v.codigo_vendedor || ''}">
                        <i class="fa-solid fa-pen-to-square"></i> Editar
                    </button>
                    <button class="btn btn-danger btn-sm delete-seller-btn" data-id="${v.id}" data-email="${escapeHTML(v.email)}" ${v.id === state.user.id ? 'disabled' : ''} title="Eliminar" style="padding: 6px 10px;">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>
                </div>
            </td>
        `;
        DOM.tableVendedores.appendChild(tr);
    });
    
    // Attach event listeners to Edit buttons
    document.querySelectorAll(".edit-seller-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            console.log("Edit user button clicked:", btn);
            const targetBtn = e.currentTarget || btn;
            const id = targetBtn.getAttribute("data-id");
            const email = targetBtn.getAttribute("data-email");
            const fullname = targetBtn.getAttribute("data-fullname");
            const role = targetBtn.getAttribute("data-role");
            const phone = targetBtn.getAttribute("data-phone");
            const code = targetBtn.getAttribute("data-code");
            console.log("Edit attributes found:", { id, email, fullname, role, phone, code });
            openEditUserForm(id, email, fullname, role, phone, code);
        });
    });

    // Attach event listeners to Delete buttons
    document.querySelectorAll(".delete-seller-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            const id = btn.getAttribute("data-id");
            const email = btn.getAttribute("data-email");
            deleteUser(id, email);
        });
    });
}

async function loadPromocionesData(forceRefresh = false) {
    const searchTerm = DOM.filterPromoSearch ? DOM.filterPromoSearch.value.toLowerCase() : "";
    const statusFilter = DOM.filterPromoStatus ? DOM.filterPromoStatus.value : "activas";
    const sortFilter = DOM.filterPromoSort ? DOM.filterPromoSort.value : "default";
    const proveedorFilter = DOM.filterPromoProveedor ? DOM.filterPromoProveedor.value : "todos";
    let endpoint = "/api/v1/promociones/";
    
    try {
        if (forceRefresh || !state.promociones || state.promociones.length === 0) {
            const res = await apiRequest(endpoint);
            state.promociones = res.data || [];
        }
        let promociones = [...state.promociones];
        const today = new Date();
        today.setHours(0,0,0,0);
        
        // Filter Status
        if (statusFilter !== "todas") {
            promociones = promociones.filter(p => {
                if (!p.valido_hasta) return statusFilter === "activas";
                const vDate = new Date(p.valido_hasta);
                const isActive = vDate >= today;
                return statusFilter === "activas" ? isActive : !isActive;
            });
        }
        
        if (proveedorFilter !== "todos") {
            promociones = promociones.filter(p => (p.proveedor || "Sin Proveedor") === proveedorFilter);
        }
        
        // --- CALCULAR Y RENDERIZAR KPIs DE PROMOCIONES ---
        const activePromos = statusFilter === "activas" ? promociones : (state.promociones || []).filter(p => {
            if (!p.valido_hasta) return true;
            return new Date(p.valido_hasta) >= today;
        });

        const catMap = {};
        activePromos.forEach(p => {
            const cat = p.descrip_gpo_materiales || "Sin Categoría";
            if (!catMap[cat]) {
                catMap[cat] = { name: cat, count: 0, sumMargin: 0 };
            }
            catMap[cat].count++;
            catMap[cat].sumMargin += (p.margen_promocion || 0);
        });

        const categories = Object.values(catMap).map(c => {
            c.avgMargin = c.count > 0 ? (c.sumMargin / c.count) : 0;
            return c;
        });

        // Top 4 por cantidad de productos
        const topCategories = [...categories].sort((a, b) => b.count - a.count).slice(0, 4);
        // Top 4 por mayor margen promedio
        const topCommissions = [...categories].sort((a, b) => b.avgMargin - a.avgMargin).slice(0, 4);

        const provMap = {};
        activePromos.forEach(p => {
            const prov = p.proveedor || "Sin Proveedor";
            if (!provMap[prov]) {
                provMap[prov] = { name: prov, count: 0, sumMargin: 0 };
            }
            provMap[prov].count++;
            provMap[prov].sumMargin += (p.margen_promocion || 0);
        });

        const providers = Object.values(provMap).map(p => {
            p.avgMargin = p.count > 0 ? (p.sumMargin / p.count) : 0;
            return p;
        });
        
        const topProviders = [...providers].sort((a, b) => b.count - a.count).slice(0, 4);

        if (DOM.filterPromoProveedor && DOM.filterPromoProveedor.options.length <= 1) {
            const currentValue = DOM.filterPromoProveedor.value;
            DOM.filterPromoProveedor.innerHTML = '<option value="todos">Todos</option>';
            providers.sort((a, b) => a.name.localeCompare(b.name)).forEach(p => {
                const opt = document.createElement('option');
                opt.value = p.name;
                opt.textContent = p.name;
                DOM.filterPromoProveedor.appendChild(opt);
            });
            DOM.filterPromoProveedor.value = currentValue;
        }

        if (DOM.promoKpiCategories && DOM.promoKpiCommissions) {
            if (topCategories.length > 0) {
                DOM.promoKpiCategories.innerHTML = topCategories.map((c, i) => `
                    <div class="glass-card kpi-card animate-fade-in" onclick="const searchInput = document.getElementById('filter-promo-search'); if(searchInput){ searchInput.value = '${escapeHTML(c.name)}'; searchInput.dispatchEvent(new Event('input')); }" style="animation-delay: ${i * 0.1}s; border-radius: 12px; border-left: 3px solid #38bdf8; cursor: pointer; transition: all 0.2s ease;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 15px rgba(56, 189, 248, 0.15)';" onmouseout="this.style.transform='none'; this.style.boxShadow='none';">
                        <div class="kpi-icon icon-blue" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8;">
                            <i class="fa-solid fa-boxes-stacked"></i>
                        </div>
                        <div class="kpi-data" style="width: calc(100% - 60px);">
                            <h3 style="font-size: 13px; text-transform: none; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 4px;" title="${c.name}">${c.name}</h3>
                            <p style="font-size: 22px; font-weight: 700;">${c.count} <span style="font-size: 11px; color: hsl(var(--text-secondary)); font-weight: normal;">prods</span></p>
                            <span style="font-size: 12px; color: #10b981; font-weight: 600;"><i class="fa-solid fa-arrow-trend-up"></i> ${c.avgMargin.toFixed(1)}% margen prom.</span>
                        </div>
                    </div>
                `).join('');
            } else {
                DOM.promoKpiCategories.innerHTML = `<div class="glass-card kpi-card" style="grid-column: 1 / -1;"><div class="kpi-data" style="text-align: center; width: 100%;"><p>No hay promociones activas</p></div></div>`;
            }

            if (topCommissions.length > 0) {
                DOM.promoKpiCommissions.innerHTML = topCommissions.map((c, i) => `
                    <div class="glass-card kpi-card animate-fade-in" onclick="const searchInput = document.getElementById('filter-promo-search'); if(searchInput){ searchInput.value = '${escapeHTML(c.name)}'; searchInput.dispatchEvent(new Event('input')); }" style="animation-delay: ${i * 0.1}s; border-radius: 12px; border-left: 3px solid #10b981; cursor: pointer; transition: all 0.2s ease;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 15px rgba(16, 185, 129, 0.15)';" onmouseout="this.style.transform='none'; this.style.boxShadow='none';">
                        <div class="kpi-icon icon-green" style="background: rgba(16, 185, 129, 0.15); color: #10b981;">
                            <i class="fa-solid fa-sack-dollar"></i>
                        </div>
                        <div class="kpi-data" style="width: calc(100% - 60px);">
                            <h3 style="font-size: 13px; text-transform: none; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 4px;" title="${c.name}">${c.name}</h3>
                            <p style="font-size: 22px; font-weight: 700; color: #10b981;">${c.avgMargin.toFixed(1)}% <span style="font-size: 11px; color: hsl(var(--text-secondary)); font-weight: normal;">margen</span></p>
                            <span style="font-size: 12px; color: hsl(var(--text-secondary)); font-weight: 500;"><i class="fa-solid fa-cubes"></i> ${c.count} productos disp.</span>
                        </div>
                    </div>
                `).join('');
            } else {
                DOM.promoKpiCommissions.innerHTML = `<div class="glass-card kpi-card" style="grid-column: 1 / -1;"><div class="kpi-data" style="text-align: center; width: 100%;"><p>No hay comisiones calculables</p></div></div>`;
            }
        }
        if (DOM.promoKpiProveedores) {
            if (topProviders.length > 0) {
                DOM.promoKpiProveedores.innerHTML = topProviders.map((p, i) => `
                    <div class="glass-card kpi-card animate-fade-in" onclick="const sel = document.getElementById('filter-promo-proveedor'); if(sel){ sel.value = '${escapeHTML(p.name)}'; sel.dispatchEvent(new Event('change')); }" style="animation-delay: ${i * 0.1}s; cursor: pointer; border-radius: 12px; border-left: 4px solid #a855f7;">
                        <h4 style="color: #c084fc;">${escapeHTML(p.name)}</h4>
                        <div class="kpi-data" style="margin-top: 10px;">
                            <span style="font-size: 1.1rem; font-weight: 600;">${p.avgMargin.toFixed(2)}% Margen</span>
                            <span class="trend" style="font-size: 0.85rem; margin-top: 4px; display: block; color: hsl(var(--text-secondary));"><i class="fa-solid fa-boxes-stacked"></i> ${p.count} productos</span>
                        </div>
                    </div>
                `).join('');
            } else {
                DOM.promoKpiProveedores.innerHTML = `<div class="glass-card kpi-card" style="grid-column: 1 / -1;"><div class="kpi-data" style="text-align: center; width: 100%;"><p>No hay proveedores disponibles</p></div></div>`;
            }
        }
        // ----------------------------------------------------

        // Filter Search Text
        if (searchTerm) {
            promociones = promociones.filter(p => 
                (p.codigo_material && p.codigo_material.toLowerCase().includes(searchTerm)) ||
                (p.descripcion_material && p.descripcion_material.toLowerCase().includes(searchTerm)) ||
                (p.descrip_gpo_materiales && p.descrip_gpo_materiales.toLowerCase().includes(searchTerm))
            );
        }
        
        // Sort
        if (sortFilter === "margen-desc") {
            promociones.sort((a, b) => (b.margen_promocion || 0) - (a.margen_promocion || 0));
        } else if (sortFilter === "margen-asc") {
            promociones.sort((a, b) => (a.margen_promocion || 0) - (b.margen_promocion || 0));
        } else if (sortFilter === "precio-desc") {
            promociones.sort((a, b) => (b.precio_promocion || 0) - (a.precio_promocion || 0));
        } else if (sortFilter === "precio-asc") {
            promociones.sort((a, b) => (a.precio_promocion || 0) - (b.precio_promocion || 0));
        } else if (sortFilter === "inv-asc") {
            promociones.sort((a, b) => (a.inventario_disponible || 0) - (b.inventario_disponible || 0));
        } else if (sortFilter === "inv-desc") {
            promociones.sort((a, b) => (b.inventario_disponible || 0) - (a.inventario_disponible || 0));
        }
        
        DOM.tablePromociones.innerHTML = "";
        if (promociones.length === 0) {
            DOM.tablePromociones.innerHTML = `<tr><td colspan="6" style="text-align: center;">No se encontraron promociones cargadas.</td></tr>`;
            return;
        }
        
        promociones.forEach(p => {
            const tr = document.createElement("tr");
            let isActive = true;
            if (p.valido_hasta) {
                const vDate = new Date(p.valido_hasta);
                isActive = vDate >= today;
            }
            if (!isActive) {
                tr.style.opacity = "0.5";
            }
            
            tr.innerHTML = `
                <td>${p.centro || '-'}</td>
                <td><strong>${p.codigo_material || '-'}</strong></td>
                <td>${p.descripcion_material || '-'}</td>
                <td>${p.proveedor || '-'}</td>
                <td><strong>$${(p.precio_promocion || 0).toLocaleString('es-MX', { minimumFractionDigits: 2 })}</strong> ${p.moneda || ''}</td>
                <td>${p.margen_promocion ? (p.margen_promocion).toFixed(2) : '-'}</td>
                <td>${p.inventario_disponible !== null && p.inventario_disponible !== undefined ? p.inventario_disponible : '-'}</td>
                <td>${p.valido_hasta ? p.valido_hasta.split('T')[0] : '-'}</td>
            `;
            DOM.tablePromociones.appendChild(tr);
        });
    } catch (e) {
        showToast("Error cargando promociones: " + e.message, "error");
    }
}

// Upload Promociones Handler
if (DOM.uploadPromocionesForm) {
    DOM.uploadPromocionesForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const fileInput = DOM.filePromociones;
        if (!fileInput.files.length) return;
        
        const formData = new FormData();
        formData.append("file", fileInput.files[0]);
        
        try {
            showToast("Subiendo archivo, por favor espere...", "info");
            
            const token = localStorage.getItem("crm_token");
            const response = await fetch("/api/v1/promociones/upload", {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`
                },
                body: formData
            });
            
            const data = await response.json();
            if (response.ok) {
                showToast(data.message, "success");
                DOM.uploadPromocionesForm.reset();
                loadPromocionesData();
            } else {
                throw new Error(data.message || "Error al subir el archivo");
            }
        } catch (e) {
            showToast(e.message, "error");
        }
    });
}

async function loadCotizacionesData(forceRefresh = true) {
    // Make sure vendedores are loaded so we can resolve emails and populate the dropdown filter
    if (state.user.rol !== "vendedor" && state.vendedores.length === 0) {
        const sellersRes = await apiRequest("/api/v1/vendedores/?limit=100");
        state.vendedores = sellersRes.data || [];
    }
    
    // Dynamically populate the sellers select and toggle visibility based on role
    if (DOM.filterQuoteSeller) {
        if (state.user.rol === "vendedor") {
            DOM.filterQuoteSeller.innerHTML = "";
            const opt = document.createElement("option");
            opt.value = state.user.id;
            opt.textContent = state.user.email;
            DOM.filterQuoteSeller.appendChild(opt);
            DOM.filterQuoteSeller.value = state.user.id;
            DOM.filterQuoteSeller.disabled = true;
            
            const parent = DOM.filterQuoteSeller.closest(".input-group-inline");
            if (parent) {
                parent.style.display = "none";
            }
        } else {
            const parent = DOM.filterQuoteSeller.closest(".input-group-inline");
            if (parent) {
                parent.style.display = "";
            }
            DOM.filterQuoteSeller.disabled = false;
            
            // Rebuild dropdown list to avoid duplications or missing entries
            const currentSelected = DOM.filterQuoteSeller.value;
            DOM.filterQuoteSeller.innerHTML = '<option value="">Todos los vendedores</option>';
            state.vendedores.forEach(v => {
                const opt = document.createElement("option");
                opt.value = v.id;
                
                let displayName = v.email;
                if (v.codigo_vendedor && v.nombre_completo) {
                    displayName = `${v.codigo_vendedor} ${v.nombre_completo}`;
                } else if (v.codigo_vendedor) {
                    displayName = v.codigo_vendedor;
                } else if (v.nombre_completo) {
                    displayName = v.nombre_completo;
                }
                
                opt.textContent = displayName;
                DOM.filterQuoteSeller.appendChild(opt);
            });
            if (currentSelected) {
                DOM.filterQuoteSeller.value = currentSelected;
            }
        }
    }

    // Responsive Layout and visibility adjustments based on role
    const quotesFunnelCard = document.getElementById("quotes-funnel-card");
    const quotesKpiGridContainer = document.getElementById("quotes-kpi-grid-container");
    const quotesKpiGrid = document.getElementById("quotes-kpi-grid");

    if (state.user.rol === "vendedor") {
        if (quotesFunnelCard) quotesFunnelCard.style.display = "none";
        if (quotesKpiGridContainer) quotesKpiGridContainer.style.flex = "100%";
        if (quotesKpiGrid) {
            quotesKpiGrid.style.gridTemplateColumns = "repeat(auto-fit, minmax(220px, 1fr))";
        }
    } else {
        if (quotesFunnelCard) quotesFunnelCard.style.display = "flex";
        if (quotesKpiGridContainer) quotesKpiGridContainer.style.flex = "2";
        if (quotesKpiGrid) {
            quotesKpiGrid.style.gridTemplateColumns = "repeat(2, 1fr)";
        }
        
        // Fetch company dashboard metadata
        try {
            const coorRes = await apiRequest("/companies/kuroda/dashboard");
            state.companyDashboardData = coorRes || null;
        } catch (cErr) {
            console.error("Error loading company dashboard metadata for quotes:", cErr);
        }
    }
    if (state.promociones.length === 0) {
        try {
            const promoRes = await apiRequest("/api/v1/promociones/");
            state.promociones = promoRes.data || [];
        } catch (e) {
            console.error("Error loading promociones for kanban:", e);
        }
    }

    if (forceRefresh || state.cotizaciones.length === 0) {
        let endpoint = "/api/v1/cotizaciones/?limit=20000";
        const res = await apiRequest(endpoint);
        state.cotizaciones = res.data || [];
    }
    
    // Reset current page when loading fresh section
    state.quotesCurrentPage = 1;
    
    renderQuotesDashboard();
}

function renderQuotesDashboard() {
    const sellerVal = state.user.rol === "vendedor" ? state.user.id : (DOM.filterQuoteSeller ? DOM.filterQuoteSeller.value : "");
    const startDate = DOM.filterQuoteStartDate ? DOM.filterQuoteStartDate.value : "";
    const endDate = DOM.filterQuoteEndDate ? DOM.filterQuoteEndDate.value : "";
    const daysVal = DOM.filterQuoteDays ? DOM.filterQuoteDays.value : "all";
    
    const refDate = new Date(); // Reference date for mock data
    
    // Apply filters
    const filtered = state.cotizaciones.filter(q => {
        // 1. Seller Filter
        if (sellerVal && q.vendedor_id !== sellerVal) return false;
        
        // 2. Date Range Filter (alphabetical comparison)
        if (q.fecha_registro) {
            if (startDate && q.fecha_registro < startDate) return false;
            if (endDate && q.fecha_registro > endDate) return false;
        } else {
            if (startDate || endDate) return false;
        }
        
        // 3. Expiry / Status Calculations
        const hasInvoice = !!q.numero_factura;
        const isLost = q.venta_perdida === "Si" || q.venta_perdida === "si";
        let ageDays = 999;
        if (q.fecha_registro) {
            const qDate = new Date(`${q.fecha_registro}T12:00:00Z`);
            ageDays = Math.floor((refDate - qDate) / (1000 * 60 * 60 * 24));
        }
        
        const isExpired = !hasInvoice && (isLost || ageDays > 30);
        const isPending = !hasInvoice && !isLost && ageDays <= 30;
        const remainingDays = 30 - ageDays;
        
        // Status dropdown filter
        if (daysVal === "concretadas") {
            if (!hasInvoice) return false;
        } else if (daysVal === "vencidas") {
            if (!isExpired) return false;
        } else if (daysVal === "pendientes") {
            if (!isPending) return false;
        } else if (["7", "15", "30", "60", "90"].includes(daysVal)) {
            const limit = parseInt(daysVal);
            if (!isPending || remainingDays < 0 || remainingDays > limit) return false;
        }
        
        return true;
    });
    
    // Save to state for table rendering
    state.filteredQuotesForTable = filtered;
    
    // Calculate KPIs on the filtered dataset
    let totalCount = 0;
    let totalSum = 0;
    
    let soldCount = 0;
    let soldSum = 0;
    
    let pendingCount = 0;
    let pendingSum = 0;
    
    let expiredCount = 0;
    let expiredSum = 0;
    
    filtered.forEach(q => {
        const total = Number(q.total) || 0;
        totalCount++;
        totalSum += total;
        
        const hasInvoice = !!q.numero_factura;
        const isLost = q.venta_perdida === "Si" || q.venta_perdida === "si";
        let ageDays = 999;
        if (q.fecha_registro) {
            const qDate = new Date(`${q.fecha_registro}T12:00:00Z`);
            ageDays = Math.floor((refDate - qDate) / (1000 * 60 * 60 * 24));
        }
        
        const isExpired = !hasInvoice && (isLost || ageDays > 30);
        const isPending = !hasInvoice && !isLost && ageDays <= 30;
        
        if (hasInvoice) {
            soldCount++;
            soldSum += total;
        } else if (isExpired) {
            expiredCount++;
            expiredSum += total;
        } else if (isPending) {
            pendingCount++;
            pendingSum += total;
        }
    });
    
    // Update DOM KPI elements
    if (DOM.kpiQuotesTotalCount) DOM.kpiQuotesTotalCount.textContent = totalCount;
    if (DOM.kpiQuotesTotalAmount) DOM.kpiQuotesTotalAmount.textContent = `$${totalSum.toLocaleString('es-MX', { minimumFractionDigits: 2 })}`;
    
    if (DOM.kpiQuotesSoldCount) DOM.kpiQuotesSoldCount.textContent = soldCount;
    if (DOM.kpiQuotesSoldAmount) DOM.kpiQuotesSoldAmount.textContent = `$${soldSum.toLocaleString('es-MX', { minimumFractionDigits: 2 })}`;
    
    if (DOM.kpiQuotesPendingCount) DOM.kpiQuotesPendingCount.textContent = pendingCount;
    if (DOM.kpiQuotesPendingAmount) DOM.kpiQuotesPendingAmount.textContent = `$${pendingSum.toLocaleString('es-MX', { minimumFractionDigits: 2 })}`;
    
    if (DOM.kpiQuotesExpiredCount) DOM.kpiQuotesExpiredCount.textContent = expiredCount;
    if (DOM.kpiQuotesExpiredAmount) DOM.kpiQuotesExpiredAmount.textContent = `$${expiredSum.toLocaleString('es-MX', { minimumFractionDigits: 2 })}`;
    
    // Render visual charts
    renderDashboardCharts(filtered);
    
    // Render list details
    renderQuotesTableFiltered();

    // Update Quotes funnel card
    updateQuotesFunnelDisplay();
}

function updateQuotesFunnelDisplay() {
    if (state.user.rol === "vendedor") return;

    const toggle = document.getElementById("toggle-quotes-funnel-real");
    const showReal = toggle ? toggle.checked : false;
    const sellerVal = DOM.filterQuoteSeller ? DOM.filterQuoteSeller.value : "";

    const dashboard = state.companyDashboardData;
    if (!dashboard) return;

    let targetIncome = 0;
    let ticketAvg = 0;
    let conversionRate = 0;
    let calcSales = 0;
    let calcQuotes = 0;
    let calcMeetings = 0;
    let calcCalls = 0;

    let realMoneyWon = 0;
    let realTicketAvg = 0;
    let realConversionRate = 0;
    let realSales = 0;
    let realQuotes = 0;
    let realMeetings = 0;
    let realCalls = 0;

    // Filter quotes for current calendar month
    const now = new Date();
    const currentYear = now.getFullYear();
    const currentMonth = now.getMonth();

    const currentMonthQuotes = state.cotizaciones.filter(q => {
        if (!q.fecha_registro) return false;
        if (sellerVal && q.vendedor_id !== sellerVal) return false;
        const qDate = new Date(`${q.fecha_registro}T12:00:00Z`);
        return qDate.getFullYear() === currentYear && qDate.getMonth() === currentMonth;
    });

    const wonQuotes = currentMonthQuotes.filter(q => {
        const hasInvoice = !!q.numero_factura;
        const isLost = q.venta_perdida === "Si" || q.venta_perdida === "si";
        return hasInvoice && !isLost;
    });

    realMoneyWon = wonQuotes.reduce((sum, q) => sum + (Number(q.total) || 0), 0);
    realTicketAvg = wonQuotes.length > 0 ? (realMoneyWon / wonQuotes.length) : 0;
    realConversionRate = currentMonthQuotes.length > 0 ? (wonQuotes.length / currentMonthQuotes.length * 100) : 0;
    realSales = wonQuotes.length;
    realQuotes = currentMonthQuotes.length;

    if (!sellerVal) {
        // "Todos" (aggregated)
        let sellersWithTarget = 0;
        let sumTicket = 0;
        let sumConv = 0;

        dashboard.sellers.forEach(s => {
            const target = s.metrics.target || 0;
            const ticket = s.slight_edge.ticket_average || 0;
            const conv = s.slight_edge.planned_conversion_rate || 0;

            targetIncome += target;
            realMeetings += s.slight_edge.actual_meetings || 0;
            realCalls += s.slight_edge.actual_calls || 0;

            if (target > 0) {
                sellersWithTarget++;
                sumTicket += ticket;
                sumConv += conv;
            }
        });

        // Compute averages for ticket & conversion
        ticketAvg = sellersWithTarget > 0 ? (sumTicket / sellersWithTarget) : 0;
        conversionRate = sellersWithTarget > 0 ? (sumConv / sellersWithTarget) : 0;

        // Calculate funnel goals based on aggregate target and average ticket/conversion
        if (ticketAvg > 0) {
            calcSales = targetIncome / ticketAvg;
            if (conversionRate > 0) {
                calcMeetings = calcSales / (conversionRate / 100.0);
                calcQuotes = calcMeetings * 0.8;
                calcCalls = calcMeetings * 5.0;
            }
        }
    } else {
        // Specific seller
        const s = dashboard.sellers.find(sel => sel.id === sellerVal);
        if (s) {
            targetIncome = s.metrics.target || 0;
            ticketAvg = s.slight_edge.ticket_average || 0;
            conversionRate = s.slight_edge.planned_conversion_rate || 0;

            if (ticketAvg > 0) {
                calcSales = targetIncome / ticketAvg;
                if (conversionRate > 0) {
                    calcMeetings = calcSales / (conversionRate / 100.0);
                    calcQuotes = calcMeetings * 0.8;
                    calcCalls = calcMeetings * 5.0;
                }
            }

            realMeetings = s.slight_edge.actual_meetings || 0;
            realCalls = s.slight_edge.actual_calls || 0;
        }
    }

    // Now update DOM values
    const domTargetIncome = document.getElementById("quotes-funnel-target-income");
    const domTicketAvg = document.getElementById("quotes-funnel-ticket-avg");
    const domConvRate = document.getElementById("quotes-funnel-conv-rate");
    const domCalcSales = document.getElementById("quotes-funnel-calc-sales");
    const domCalcQuotes = document.getElementById("quotes-funnel-calc-quotes");
    const domCalcMeetings = document.getElementById("quotes-funnel-calc-meetings");
    const domCalcCalls = document.getElementById("quotes-funnel-calc-calls");

    const labelTargetIncome = document.getElementById("label-quotes-funnel-target-income");
    const labelTicketAvg = document.getElementById("label-quotes-funnel-ticket-avg");
    const labelConvRate = document.getElementById("label-quotes-funnel-conv-rate");
    const subtitleHeader = document.getElementById("subtitle-quotes-funnel-header");
    const labelSales = document.getElementById("label-quotes-funnel-sales");
    const labelQuotes = document.getElementById("label-quotes-funnel-quotes");
    const labelMeetings = document.getElementById("label-quotes-funnel-meetings");
    const labelCalls = document.getElementById("label-quotes-funnel-calls");

    if (showReal) {
        if (labelTargetIncome) labelTargetIncome.textContent = "Dinero Vendido:";
        if (labelTicketAvg) labelTicketAvg.textContent = "Ticket Promedio Real:";
        if (labelConvRate) labelConvRate.textContent = "Conversión Real:";
        if (subtitleHeader) subtitleHeader.textContent = "AVANCES DEL FUNNEL REALES";
        if (labelSales) labelSales.textContent = "Cierres";
        if (labelQuotes) labelQuotes.textContent = "Cotizaciones";
        if (labelMeetings) labelMeetings.textContent = "Citas";
        if (labelCalls) labelCalls.textContent = "Llamadas";

        if (domTargetIncome) domTargetIncome.textContent = `$${Math.round(realMoneyWon).toLocaleString()}`;
        if (domTicketAvg) domTicketAvg.textContent = `$${Math.round(realTicketAvg).toLocaleString()}`;
        if (domConvRate) domConvRate.textContent = `${realConversionRate.toFixed(1)}%`;
        if (domCalcSales) domCalcSales.textContent = realSales;
        if (domCalcQuotes) domCalcQuotes.textContent = realQuotes;
        if (domCalcMeetings) domCalcMeetings.textContent = realMeetings;
        if (domCalcCalls) domCalcCalls.textContent = realCalls;
    } else {
        if (labelTargetIncome) labelTargetIncome.textContent = "Meta Mensual:";
        if (labelTicketAvg) labelTicketAvg.textContent = "Ticket Promedio:";
        if (labelConvRate) labelConvRate.textContent = "Conversión Cotización-Cierre:";
        if (subtitleHeader) subtitleHeader.textContent = "METAS DEL FUNNEL CALCULADAS";
        if (labelSales) labelSales.textContent = "Cierres/Mes";
        if (labelQuotes) labelQuotes.textContent = "Cotizaciones/Mes";
        if (labelMeetings) labelMeetings.textContent = "Citas/Mes";
        if (labelCalls) labelCalls.textContent = "Llamadas/Mes";

        if (domTargetIncome) domTargetIncome.textContent = `$${Math.round(targetIncome).toLocaleString()}`;
        if (domTicketAvg) domTicketAvg.textContent = `$${Math.round(ticketAvg).toLocaleString()}`;
        if (domConvRate) domConvRate.textContent = `${conversionRate.toFixed(1)}%`;
        if (domCalcSales) domCalcSales.textContent = Math.round(calcSales);
        if (domCalcQuotes) domCalcQuotes.textContent = Math.round(calcQuotes);
        if (domCalcMeetings) domCalcMeetings.textContent = Math.round(calcMeetings);
        if (domCalcCalls) domCalcCalls.textContent = Math.round(calcCalls);
    }
}

function renderDashboardCharts(filtered) {
    const isLightMode = document.body.classList.contains("light-mode");
    const tickColor = isLightMode ? '#333333' : '#abb2bf';
    const gridColor = isLightMode ? 'rgba(0, 0, 0, 0.08)' : 'rgba(255, 255, 255, 0.05)';
    
    // Count status breakdown
    let soldCount = 0;
    let pendingCount = 0;
    let expiredCount = 0;
    
    const refDate = new Date();
    filtered.forEach(q => {
        const hasInvoice = !!q.numero_factura;
        const isLost = q.venta_perdida === "Si" || q.venta_perdida === "si";
        let ageDays = 999;
        if (q.fecha_registro) {
            const qDate = new Date(`${q.fecha_registro}T12:00:00Z`);
            ageDays = Math.floor((refDate - qDate) / (1000 * 60 * 60 * 24));
        }
        if (hasInvoice) soldCount++;
        else if (isLost || ageDays > 30) expiredCount++;
        else pendingCount++;
    });

    // 1. Chart Status (Doughnut)
    if (state.chartQuoteStatus) state.chartQuoteStatus.destroy();
    const canvasStatus = document.getElementById("chartQuoteStatus");
    if (canvasStatus) {
        const ctxStatus = canvasStatus.getContext("2d");
        state.chartQuoteStatus = new Chart(ctxStatus, {
            type: 'doughnut',
            data: {
                labels: ['Vendidas (Concretadas)', 'Pendientes', 'Vencidas / Perdidas'],
                datasets: [{
                    data: [soldCount, pendingCount, expiredCount],
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.4)',  // Green
                        'rgba(245, 158, 11, 0.4)',  // Orange
                        'rgba(239, 68, 68, 0.4)'    // Red
                    ],
                    borderColor: [
                        '#10b981',
                        '#f59e0b',
                        '#ef4444'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: tickColor, font: { family: 'Outfit, sans-serif', size: 11 } }
                    }
                },
                cutout: '70%'
            }
        });
    }

    // 2. Chart Seller (Bar)
    const groupedSeller = {};
    filtered.forEach(q => {
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
        groupedSeller[label] = (groupedSeller[label] || 0) + (Number(q.total) || 0);
    });
    const sortedSellers = Object.keys(groupedSeller).map(k => ({
        name: k,
        total: groupedSeller[k]
    })).sort((a, b) => b.total - a.total).slice(0, 10); // top 10

    if (state.chartQuoteSeller) state.chartQuoteSeller.destroy();
    const canvasSeller = document.getElementById("chartQuoteSeller");
    if (canvasSeller) {
        const ctxSeller = canvasSeller.getContext("2d");
        state.chartQuoteSeller = new Chart(ctxSeller, {
            type: 'bar',
            data: {
                labels: sortedSellers.map(s => s.name),
                datasets: [{
                    label: 'Monto Cotizado ($)',
                    data: sortedSellers.map(s => s.total),
                    backgroundColor: 'rgba(93, 95, 239, 0.4)', // Purple
                    borderColor: '#5d5fef',
                    borderWidth: 2,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: { ticks: { color: tickColor }, grid: { color: gridColor } },
                    y: { ticks: { color: tickColor }, grid: { color: gridColor } }
                }
            }
        });
    }

    // 3. Chart Trend (Line)
    const groupedTrend = {};
    filtered.forEach(q => {
        if (q.fecha_registro) {
            groupedTrend[q.fecha_registro] = (groupedTrend[q.fecha_registro] || 0) + (Number(q.total) || 0);
        }
    });
    const sortedDates = Object.keys(groupedTrend).sort();
    
    if (state.chartQuoteTrend) state.chartQuoteTrend.destroy();
    const canvasTrend = document.getElementById("chartQuoteTrend");
    if (canvasTrend) {
        const ctxTrend = canvasTrend.getContext("2d");
        const gradient = ctxTrend.createLinearGradient(0, 0, 0, 200);
        gradient.addColorStop(0, 'rgba(0, 242, 254, 0.3)');
        gradient.addColorStop(1, 'rgba(0, 242, 254, 0.0)');

        state.chartQuoteTrend = new Chart(ctxTrend, {
            type: 'line',
            data: {
                labels: sortedDates,
                datasets: [{
                    label: 'Monto Cotizado Diario ($)',
                    data: sortedDates.map(d => groupedTrend[d]),
                    backgroundColor: gradient,
                    borderColor: '#00f2fe',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3,
                    pointRadius: sortedDates.length > 30 ? 0 : 3,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: { 
                        ticks: { 
                            color: tickColor,
                            maxTicksLimit: 10
                        }, 
                        grid: { color: gridColor } 
                    },
                    y: { ticks: { color: tickColor }, grid: { color: gridColor } }
                }
            }
        });
    }

    // 4. Chart Channel (Doughnut)
    const groupedChannel = {};
    filtered.forEach(q => {
        let channel = q.canal || "Sin especificar";
        if (channel === "1.0") channel = "Canal 1 (Directo)";
        else if (channel === "2.0") channel = "Canal 2 (Telemarketing)";
        groupedChannel[channel] = (groupedChannel[channel] || 0) + 1;
    });

    if (state.chartQuoteChannel) state.chartQuoteChannel.destroy();
    const canvasChannel = document.getElementById("chartQuoteChannel");
    if (canvasChannel) {
        const ctxChannel = canvasChannel.getContext("2d");
        state.chartQuoteChannel = new Chart(ctxChannel, {
            type: 'doughnut',
            data: {
                labels: Object.keys(groupedChannel),
                datasets: [{
                    data: Object.values(groupedChannel),
                    backgroundColor: [
                        'rgba(93, 95, 239, 0.4)',   // Blue
                        'rgba(139, 92, 246, 0.4)',  // Purple
                        'rgba(0, 242, 254, 0.4)',   // Cyan
                        'rgba(16, 185, 129, 0.4)'   // Green
                    ],
                    borderColor: [
                        '#5d5fef',
                        '#8b5cf6',
                        '#00f2fe',
                        '#10b981'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: tickColor, font: { family: 'Outfit, sans-serif', size: 11 } }
                    }
                },
                cutout: '70%'
            }
        });
    }
}

function renderQuotesTableFiltered() {
    const searchVal = DOM.searchQuoteClient ? DOM.searchQuoteClient.value.toLowerCase() : "";
    let filteredQuotes = state.filteredQuotesForTable || state.cotizaciones;
    
    // Apply client search filter
    if (searchVal) {
        filteredQuotes = filteredQuotes.filter(q => q.cliente_nombre.toLowerCase().includes(searchVal));
    }
    
    // Sort by Total
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
    
    if (DOM.tableCotizaciones) {
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
    }
    
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
            let displayName = v.email;
            if (v.codigo_vendedor && v.nombre_completo) {
                displayName = `${v.codigo_vendedor} ${v.nombre_completo}`;
            } else if (v.codigo_vendedor) {
                displayName = v.codigo_vendedor;
            } else if (v.nombre_completo) {
                displayName = v.nombre_completo;
            }
            opt.textContent = displayName;
            DOM.kanbanFilterSeller.appendChild(opt);
        });
    }
    
    if (forceRefresh || state.cotizaciones.length === 0) {
        let endpoint = "/api/v1/cotizaciones/?limit=20000";
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
        const refDate = new Date();
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
        cotizado: [],
        promociones: [],
        vendido: [],
        vencido: []
    };
    
    const refDate = new Date();
    
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
        } else {
            // Check if quote has any promotional items
            let hasPromotion = false;
            if (q.items && Array.isArray(q.items) && state.promociones.length > 0) {
                for (const item of q.items) {
                    const prodName = (item.producto || "").toLowerCase();
                    const isPromo = state.promociones.some(p => 
                        prodName.includes((p.codigo_material || "").toLowerCase()) || 
                        prodName.includes((p.descripcion_material || "").toLowerCase())
                    );
                    if (isPromo) {
                        hasPromotion = true;
                        break;
                    }
                }
            }

            if (hasPromotion) {
                stages.promociones.push(q);
            } else {
                stages.cotizado.push(q);
            }
        }
    });
    
    // Sort columns if sort order is set
    const columns = ['cotizado', 'promociones', 'vendido', 'vencido'];
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
    
    // Render columns and update summaries
    columns.forEach(col => {
        const container = DOM[`kanban${col.charAt(0).toUpperCase() + col.slice(1)}`] || document.getElementById(`kanban-${col}`);
        const countSpan = DOM[`countKanban${col.charAt(0).toUpperCase() + col.slice(1)}`] || document.getElementById(`count-kanban-${col}`);
        
        const summaryCount = document.getElementById(`summary-count-${col}`);
        const summaryTotal = document.getElementById(`summary-total-${col}`);
        
        let colTotal = 0;
        
        if (container) {
            container.innerHTML = "";
        }
        if (countSpan) {
            countSpan.textContent = stages[col].length;
        }
        
        stages[col].forEach(q => {
            colTotal += Number(q.total);
            if (!container) return;
            
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
                    <h4 class="kanban-card-client">${escapeHTML(q.cliente_nombre)}</h4>
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
        
        // Update summary cards
        if (summaryCount) summaryCount.textContent = stages[col].length;
        if (summaryTotal) summaryTotal.textContent = `$${colTotal.toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    });
    
    setupKanbanDragAndDrop();
}

function setupKanbanDragAndDrop() {
    const columns = document.querySelectorAll(".kanban-column");
    
    columns.forEach(col => {
        if (col.dataset.dndSetup === "true") return;
        col.dataset.dndSetup = "true";

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

    const refDate = new Date();

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

/* --- Vendedores/Usuarios Handlers --- */
let editingUserId = null;

// Dynamically show/hide seller code input depending on selected role
if (DOM.sellerRole) {
    DOM.sellerRole.addEventListener("change", (e) => {
        if (e.target.value === "vendedor") {
            DOM.sellerCodeGroup.classList.remove("hidden");
        } else {
            DOM.sellerCodeGroup.classList.add("hidden");
            DOM.sellerCode.value = "";
        }
    });
}

DOM.btnAddSeller.addEventListener("click", () => {
    editingUserId = null;
    DOM.sellerForm.reset();
    DOM.sellerFormTitle.textContent = "Registrar Nuevo Usuario";
    DOM.btnSubmitSeller.textContent = "Registrar Usuario";
    DOM.sellerPassword.required = true;
    DOM.sellerPasswordLabel.innerHTML = 'Contraseña Temporal';
    DOM.sellerCodeGroup.classList.remove("hidden");
    DOM.sellerFormWrapper.classList.remove("hidden");
    DOM.sellerFormWrapper.scrollIntoView({ behavior: "smooth" });
});

DOM.btnCancelSeller.addEventListener("click", () => {
    DOM.sellerFormWrapper.classList.add("hidden");
    editingUserId = null;
});

DOM.btnCloseSellerForm.addEventListener("click", () => {
    DOM.sellerFormWrapper.classList.add("hidden");
    editingUserId = null;
});

function openEditUserForm(id, email, fullname, role, phone, code) {
    console.log("openEditUserForm called with parameters:", { id, email, fullname, role, phone, code });
    try {
        editingUserId = id;
        if (DOM.sellerFullname) DOM.sellerFullname.value = fullname || "";
        if (DOM.sellerRole) DOM.sellerRole.value = role || "vendedor";
        if (DOM.sellerEmail) DOM.sellerEmail.value = email || "";
        if (DOM.sellerPhone) DOM.sellerPhone.value = phone || "";
        if (DOM.sellerCode) DOM.sellerCode.value = code || "";
        if (DOM.sellerPassword) {
            DOM.sellerPassword.value = "";
            DOM.sellerPassword.required = false; // not required when editing
        }
        if (DOM.sellerPasswordLabel) {
            DOM.sellerPasswordLabel.innerHTML = 'Nueva Contraseña (dejar en blanco para mantener)';
        }

        // Trigger role visibility logic
        if (DOM.sellerCodeGroup) {
            if (role === "vendedor") {
                DOM.sellerCodeGroup.classList.remove("hidden");
            } else {
                DOM.sellerCodeGroup.classList.add("hidden");
            }
        }

        if (DOM.sellerFormTitle) DOM.sellerFormTitle.textContent = "Editar Usuario";
        if (DOM.btnSubmitSeller) DOM.btnSubmitSeller.textContent = "Guardar Cambios";
        
        if (DOM.sellerFormWrapper) {
            DOM.sellerFormWrapper.classList.remove("hidden");
            DOM.sellerFormWrapper.scrollIntoView({ behavior: "smooth" });
        }
        console.log("openEditUserForm UI updates complete");
    } catch (err) {
        console.error("Error in openEditUserForm:", err);
        showToast("Error al abrir el formulario de edición: " + err.message, "error");
    }
}

async function deleteUser(id, email) {
    if (!confirm(`¿Está seguro de que desea eliminar permanentemente la cuenta de "${email}"?\nSe revocarán todos los accesos al sistema.`)) {
        return;
    }
    try {
        await apiRequest(`/api/v1/vendedores/${id}`, {
            method: "DELETE"
        });
        showToast("Usuario eliminado correctamente.");
        loadVendedoresData();
    } catch (e) {
        showToast(e.message, "error");
    }
}

DOM.sellerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = DOM.sellerEmail.value;
    const fullname = DOM.sellerFullname.value;
    const role = DOM.sellerRole.value;
    const phone = DOM.sellerPhone.value || null;
    const code = role === "vendedor" ? (DOM.sellerCode.value || null) : null;
    const password = DOM.sellerPassword.value || null;
    
    const payload = {
        email,
        nombre_completo: fullname,
        rol: role,
        telefono_whatsapp: phone,
        codigo_vendedor: code
    };
    
    if (password) {
        payload.password = password;
    }

    try {
        if (editingUserId) {
            // Update User
            await apiRequest(`/api/v1/vendedores/${editingUserId}`, {
                method: "PUT",
                body: JSON.stringify(payload)
            });
            showToast("Usuario actualizado con éxito.");
        } else {
            // Create User (requires password)
            if (!password) {
                showToast("La contraseña es obligatoria para nuevos usuarios.", "error");
                return;
            }
            await apiRequest("/api/v1/vendedores/", {
                method: "POST",
                body: JSON.stringify(payload)
            });
            showToast("Usuario registrado con éxito.");
        }
        
        DOM.sellerForm.reset();
        DOM.sellerFormWrapper.classList.add("hidden");
        editingUserId = null;
        loadVendedoresData();
    } catch (err) {
        showToast(err.message, "error");
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
        let displayName = v.email;
            if (v.codigo_vendedor && v.nombre_completo) {
                displayName = `${v.codigo_vendedor} ${v.nombre_completo}`;
            } else if (v.codigo_vendedor) {
                displayName = v.codigo_vendedor;
            } else if (v.nombre_completo) {
                displayName = v.nombre_completo;
            }
            opt.textContent = displayName;
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
        loadPromocionesData();
    } catch (e) {
        showToast(e.message, "error");
    } finally {
        DOM.btnSubmitAiGoals.disabled = false;
        DOM.btnSubmitAiGoals.innerHTML = 'Analizar y Generar Meta con IA <i class="fa-solid fa-sparkles">';
    }
});

DOM.filterPromoProveedor?.addEventListener("change", () => loadPromocionesData(false));
DOM.filterPromoSearch?.addEventListener("input", () => loadPromocionesData(false));
DOM.thInvDisp?.addEventListener("click", () => {
    if (DOM.filterPromoSort) {
        if (DOM.filterPromoSort.value === "inv-asc") {
            DOM.filterPromoSort.value = "inv-desc";
        } else {
            DOM.filterPromoSort.value = "inv-asc";
        }
        loadPromocionesData(false);
    }
});
DOM.btnClearPromoFilters?.addEventListener("click", () => {
    if (DOM.filterPromoSearch) DOM.filterPromoSearch.value = '';
    if (DOM.filterPromoStatus) DOM.filterPromoStatus.value = 'activas';
    if (DOM.filterPromoSort) DOM.filterPromoSort.value = 'default';
    if (DOM.filterPromoProveedor) DOM.filterPromoProveedor.value = 'todos';
    loadPromocionesData(false);
});
DOM.filterPromoStatus?.addEventListener("change", () => loadPromocionesData(false));
DOM.filterPromoSort?.addEventListener("change", () => loadPromocionesData(false));

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
    renderQuotesDashboard();
});

DOM.filterQuoteDays.addEventListener("change", () => {
    state.quotesCurrentPage = 1;
    renderQuotesDashboard();
});

if (DOM.filterQuoteStartDate) {
    DOM.filterQuoteStartDate.addEventListener("change", () => {
        state.quotesCurrentPage = 1;
        renderQuotesDashboard();
    });
}

if (DOM.filterQuoteEndDate) {
    DOM.filterQuoteEndDate.addEventListener("change", () => {
        state.quotesCurrentPage = 1;
        renderQuotesDashboard();
    });
}

if (DOM.btnToggleQuotesDetails) {
    DOM.btnToggleQuotesDetails.addEventListener("click", () => {
        const content = DOM.quotesDetailsContent;
        const icon = DOM.quotesDetailsToggleIcon;
        if (content) {
            if (content.classList.contains("hidden")) {
                content.classList.remove("hidden");
                if (icon) icon.style.transform = "rotate(180deg)";
            } else {
                content.classList.add("hidden");
                if (icon) icon.style.transform = "rotate(0deg)";
            }
        }
    });
}

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

    // Setup Slight Edge Date listener
    if (DOM.slightEdgeDate) {
        DOM.slightEdgeDate.addEventListener("change", () => {
            loadSellerSlightEdgePlanAndLog();
        });
    }

    // Setup Slight Edge Funnel Real toggle listener
    if (DOM.toggleFunnelReal) {
        DOM.toggleFunnelReal.addEventListener("change", () => {
            updateFunnelDisplay();
        });
    }

    // Setup Quotes Funnel Real toggle listener
    const toggleQuotesFunnelReal = document.getElementById("toggle-quotes-funnel-real");
    if (toggleQuotesFunnelReal) {
        toggleQuotesFunnelReal.addEventListener("change", () => {
            updateQuotesFunnelDisplay();
        });
    }

    // Setup Vendedores Sort listener
    if (DOM.selectSortSellers) {
        DOM.selectSortSellers.addEventListener("change", () => {
            loadVendedoresData();
        });
    }

    // Setup Slight Edge Chat Form
    if (DOM.slightEdgeChatForm) {
        DOM.slightEdgeChatForm.addEventListener("submit", handleSlightEdgeChatSubmit);
    }

    // Setup Checklist Save Button
    if (DOM.btnSaveSlightEdgeLog) {
        DOM.btnSaveSlightEdgeLog.addEventListener("click", saveSlightEdgeLog);
    }

    // Setup Company Target Settings Form
    if (DOM.companySettingsForm) {
        DOM.companySettingsForm.addEventListener("submit", handleCompanySettingsSubmit);
    }

    // Close AI recommendation panel
    if (DOM.btnCloseSlightEdgeAi) {
        DOM.btnCloseSlightEdgeAi.addEventListener("click", () => {
            DOM.slightEdgeAiRecommendationCard.classList.add("hidden");
        });
    }

    // Close Burndown Modal
    const btnCloseBurndownModal = document.getElementById("btn-close-burndown-modal");
    if (btnCloseBurndownModal) {
        btnCloseBurndownModal.addEventListener("click", () => {
            document.getElementById("burndown-modal").classList.add("hidden");
        });
    }
    const btnCloseBurndown = document.getElementById("btn-close-burndown");
    if (btnCloseBurndown) {
        btnCloseBurndown.addEventListener("click", () => {
            document.getElementById("burndown-modal").classList.add("hidden");
        });
    }

    // Reset plan button listener
    const btnSlightEdgeResetPlan = document.getElementById("btn-slight-edge-reset-plan");
    if (btnSlightEdgeResetPlan) {
        btnSlightEdgeResetPlan.addEventListener("click", async () => {
            if (!confirm("¿Estás seguro de que deseas eliminar permanentemente tu plan de La Ventaja y todos tus registros de consistencia para empezar de cero con el Coach de IA?")) {
                return;
            }
            try {
                await apiRequest(`/api/slight-edge/plan/${state.user.id}`, {
                    method: "DELETE"
                });
                showToast("Plan restablecido correctamente. Iniciando sesión de coaching...");
                
                slightEdgeChatHistory = [];
                checklistQuantities = {};
                state.slightEdgePlan = null;
                
                await loadSellerSlightEdgePlanAndLog();
                await loadSlightEdgeSummaryWidget();
            } catch (err) {
                showToast("Error al restablecer plan: " + err.message, "error");
            }
        });
    }

    // Back to Dashboard button listener
    if (DOM.btnSlightEdgeBackToDashboard) {
        DOM.btnSlightEdgeBackToDashboard.addEventListener("click", () => {
            toggleSlightEdgeMode("dashboard");
        });
    }

    // Adjust with Coach button listener
    if (DOM.btnSlightEdgeAdjustCoach) {
        DOM.btnSlightEdgeAdjustCoach.addEventListener("click", () => {
            toggleSlightEdgeMode("coaching");
            if (DOM.btnSlightEdgeBackToDashboard) DOM.btnSlightEdgeBackToDashboard.classList.remove("hidden");
        });
    }

    // Adjust Weights button listener
    if (DOM.btnSlightEdgeAdjustWeights) {
        DOM.btnSlightEdgeAdjustWeights.addEventListener("click", () => {
            openWeightsModal();
        });
    }

    // Weights Form cancel and close listeners
    const btnCancelWeights = document.getElementById("btn-cancel-weights");
    const btnCloseWeightsModal = document.getElementById("btn-close-weights-modal");
    if (btnCancelWeights) {
        btnCancelWeights.addEventListener("click", () => {
            document.getElementById("adjust-weights-modal").classList.add("hidden");
        });
    }
    if (btnCloseWeightsModal) {
        btnCloseWeightsModal.addEventListener("click", () => {
            document.getElementById("adjust-weights-modal").classList.add("hidden");
        });
    }

    // Weights Form submit listener
    const adjustWeightsForm = document.getElementById("adjust-weights-form");
    if (adjustWeightsForm) {
        adjustWeightsForm.addEventListener("submit", handleWeightsSubmit);
    }

    // New Task button listener
    if (DOM.btnSlightEdgeNewTask) {
        DOM.btnSlightEdgeNewTask.addEventListener("click", () => {
            document.getElementById("new-task-modal").classList.remove("hidden");
        });
    }

    // New Task Form cancel and close listeners
    const btnCancelNewTask = document.getElementById("btn-cancel-new-task");
    const btnCloseNewTaskModal = document.getElementById("btn-close-new-task-modal");
    if (btnCancelNewTask) {
        btnCancelNewTask.addEventListener("click", () => {
            document.getElementById("new-task-modal").classList.add("hidden");
        });
    }
    if (btnCloseNewTaskModal) {
        btnCloseNewTaskModal.addEventListener("click", () => {
            document.getElementById("new-task-modal").classList.add("hidden");
        });
    }

    // New Task Form submit listener
    const newTaskForm = document.getElementById("new-task-form");
    if (newTaskForm) {
        newTaskForm.addEventListener("submit", handleNewTaskSubmit);
    }

    // Slight Edge Summary Card button listeners
    if (DOM.btnSlightEdgeSummaryCoach) {
        DOM.btnSlightEdgeSummaryCoach.addEventListener("click", () => {
            switchSection("slight-edge");
            toggleSlightEdgeMode("coaching");
            if (DOM.btnSlightEdgeBackToDashboard) DOM.btnSlightEdgeBackToDashboard.classList.remove("hidden");
        });
    }
    if (DOM.btnSlightEdgeSummaryGo) {
        DOM.btnSlightEdgeSummaryGo.addEventListener("click", () => {
            switchSection("slight-edge");
            toggleSlightEdgeMode("dashboard");
        });
    }
    
    // Setup button in summary card empty state
    const btnSlightEdgeSummarySetup = document.getElementById("btn-slight-edge-summary-setup");
    if (btnSlightEdgeSummarySetup) {
        btnSlightEdgeSummarySetup.addEventListener("click", () => {
            switchSection("slight-edge");
            toggleSlightEdgeMode("coaching");
            if (DOM.btnSlightEdgeBackToDashboard) DOM.btnSlightEdgeBackToDashboard.classList.remove("hidden");
        });
    }
});

/* ==========================================================================
   LA LIGERA VENTAJA (SLIGHT EDGE) SPA LOGIC
   ========================================================================== */

let slightEdgeChatHistory = [];
let checklistQuantities = {};

async function loadSlightEdgeData() {
    // Default date to today if not set
    if (DOM.slightEdgeDate && !DOM.slightEdgeDate.value) {
        const todayStr = new Date().toISOString().split("T")[0];
        DOM.slightEdgeDate.value = todayStr;
    }

    if (state.user.rol === "vendedor") {
        DOM.slightEdgeSellerView.classList.remove("hidden");
        DOM.slightEdgeCoordinatorView.classList.add("hidden");
        await loadSellerSlightEdgePlanAndLog();
    } else {
        DOM.slightEdgeSellerView.classList.add("hidden");
        DOM.slightEdgeCoordinatorView.classList.remove("hidden");
        await loadCoordinatorSlightEdgeDashboard();
    }
}

function toggleSlightEdgeMode(mode) {
    if (mode === "coaching") {
        if (DOM.slightEdgeChatContainer) DOM.slightEdgeChatContainer.classList.remove("hidden");
        if (DOM.slightEdgeDashboardContainer) DOM.slightEdgeDashboardContainer.classList.add("hidden");
    } else {
        if (DOM.slightEdgeChatContainer) DOM.slightEdgeChatContainer.classList.add("hidden");
        if (DOM.slightEdgeDashboardContainer) DOM.slightEdgeDashboardContainer.classList.remove("hidden");
    }
}

function updateFunnelDisplay() {
    const toggle = document.getElementById("toggle-funnel-real");
    const showReal = toggle ? toggle.checked : false;
    
    const plan = state.slightEdgePlan;
    if (!plan) return;

    if (showReal) {
        if (DOM.labelFunnelTargetIncome) DOM.labelFunnelTargetIncome.textContent = "Dinero Vendido:";
        if (DOM.labelFunnelTicketAvg) DOM.labelFunnelTicketAvg.textContent = "Ticket Promedio Real:";
        if (DOM.labelFunnelConvRate) DOM.labelFunnelConvRate.textContent = "Conversión Real:";
        if (DOM.subtitleFunnelHeader) DOM.subtitleFunnelHeader.textContent = "AVANCES DEL FUNNEL REALES";
        if (DOM.labelFunnelSales) DOM.labelFunnelSales.textContent = "Cierres";
        if (DOM.labelFunnelQuotes) DOM.labelFunnelQuotes.textContent = "Cotizaciones";
        if (DOM.labelFunnelMeetings) DOM.labelFunnelMeetings.textContent = "Citas";
        if (DOM.labelFunnelCalls) DOM.labelFunnelCalls.textContent = "Llamadas";

        const real = state.slightEdgeRealMetrics || {
            moneyWon: 0,
            ticketAvg: 0,
            conversionRate: 0,
            sales: 0,
            quotes: 0,
            meetings: 0,
            calls: 0
        };

        if (DOM.funnelTargetIncome) DOM.funnelTargetIncome.textContent = `$${Math.round(real.moneyWon).toLocaleString()}`;
        if (DOM.funnelTicketAvg) DOM.funnelTicketAvg.textContent = `$${Math.round(real.ticketAvg).toLocaleString()}`;
        if (DOM.funnelConvRate) DOM.funnelConvRate.textContent = `${real.conversionRate.toFixed(1)}%`;
        if (DOM.funnelCalcSales) DOM.funnelCalcSales.textContent = real.sales;
        if (DOM.funnelCalcQuotes) DOM.funnelCalcQuotes.textContent = real.quotes;
        if (DOM.funnelCalcMeetings) DOM.funnelCalcMeetings.textContent = real.meetings;
        if (DOM.funnelCalcCalls) DOM.funnelCalcCalls.textContent = real.calls;
    } else {
        if (DOM.labelFunnelTargetIncome) DOM.labelFunnelTargetIncome.textContent = "Meta Mensual:";
        if (DOM.labelFunnelTicketAvg) DOM.labelFunnelTicketAvg.textContent = "Ticket Promedio:";
        if (DOM.labelFunnelConvRate) DOM.labelFunnelConvRate.textContent = "Conversión Cotización-Cierre:";
        if (DOM.subtitleFunnelHeader) DOM.subtitleFunnelHeader.textContent = "METAS DEL FUNNEL CALCULADAS";
        if (DOM.labelFunnelSales) DOM.labelFunnelSales.textContent = "Cierres/Mes";
        if (DOM.labelFunnelQuotes) DOM.labelFunnelQuotes.textContent = "Cotizaciones/Mes";
        if (DOM.labelFunnelMeetings) DOM.labelFunnelMeetings.textContent = "Citas/Mes";
        if (DOM.labelFunnelCalls) DOM.labelFunnelCalls.textContent = "Llamadas/Mes";

        if (DOM.funnelTargetIncome) DOM.funnelTargetIncome.textContent = `$${plan.monthly_income_goal.toLocaleString()}`;
        if (DOM.funnelTicketAvg) DOM.funnelTicketAvg.textContent = `$${plan.ticket_average.toLocaleString()}`;
        if (DOM.funnelConvRate) DOM.funnelConvRate.textContent = `${plan.conversion_rate}%`;
        
        if (plan.funnel_metrics) {
            if (DOM.funnelCalcSales) DOM.funnelCalcSales.textContent = plan.funnel_metrics.ventas_mensuales;
            if (DOM.funnelCalcQuotes) DOM.funnelCalcQuotes.textContent = plan.funnel_metrics.cotizaciones_mensuales;
            if (DOM.funnelCalcMeetings) DOM.funnelCalcMeetings.textContent = plan.funnel_metrics.citas_mensuales;
            if (DOM.funnelCalcCalls) DOM.funnelCalcCalls.textContent = plan.funnel_metrics.llamadas_mensuales;
        }
    }
}

async function loadSellerSlightEdgePlanAndLog() {
    try {
        const planRes = await apiRequest(`/api/slight-edge/plan/${state.user.id}`);
        const plan = planRes.data;
        state.slightEdgePlan = plan;

        // Render checklist structure
        renderSlightEdgeChecklist(plan);

        // Fetch quotes to calculate real metrics
        let quotes = [];
        try {
            const quotesRes = await apiRequest(`/api/v1/cotizaciones/?limit=5000`);
            quotes = quotesRes.data || [];
        } catch (qErr) {
            console.error("Error fetching quotes for slight edge:", qErr);
        }

        // Fetch logs for the historical consistency chart
        const historyRes = await apiRequest(`/api/slight-edge/log/${state.user.id}`);
        const historyLogs = historyRes.data || [];

        // Now calculate real metrics for the current calendar month
        const now = new Date();
        const currentYear = now.getFullYear();
        const currentMonth = now.getMonth(); // 0-indexed

        // Filter quotes for the current calendar month
        const currentMonthQuotes = quotes.filter(q => {
            if (!q.fecha_registro) return false;
            const qDate = new Date(`${q.fecha_registro}T12:00:00Z`);
            return qDate.getFullYear() === currentYear && qDate.getMonth() === currentMonth;
        });

        const wonQuotes = currentMonthQuotes.filter(q => {
            const hasInvoice = !!q.numero_factura;
            const isLost = q.venta_perdida === "Si" || q.venta_perdida === "si";
            return hasInvoice && !isLost;
        });

        const realMoneyWon = wonQuotes.reduce((sum, q) => sum + (Number(q.total) || 0), 0);
        const realTicketAvg = wonQuotes.length > 0 ? (realMoneyWon / wonQuotes.length) : 0;
        const realConversionRate = currentMonthQuotes.length > 0 ? (wonQuotes.length / currentMonthQuotes.length * 100) : 0;

        // Sum checklist activities in the current calendar month
        let realCalls = 0;
        let realMeetings = 0;

        function jsCategorizeActivity(name) {
            const n = (name || "").toLowerCase().trim();
            if (n.includes("llam") || n.includes("call") || n.includes("prospect") || n.includes("contac")) {
                return "llamada";
            }
            if (n.includes("cit") || n.includes("reun") || n.includes("meet") || n.includes("visita")) {
                return "cita";
            }
            if (n.includes("cotiz") || n.includes("propuest") || n.includes("presupuest") || n.includes("quot") || n.includes("enviar")) {
                return "cotizacion";
            }
            if (n.includes("cierr") || n.includes("vent") || n.includes("cobro") || n.includes("clos") || n.includes("firm")) {
                return "venta";
            }
            return "otra";
        }

        historyLogs.forEach(log => {
            if (!log.date) return;
            const logDate = new Date(`${log.date}T12:00:00Z`);
            if (logDate.getFullYear() === currentYear && logDate.getMonth() === currentMonth) {
                if (log.completed_activities) {
                    for (const [act, count] of Object.entries(log.completed_activities)) {
                        const cat = jsCategorizeActivity(act);
                        if (cat === "llamada") {
                            realCalls += (Number(count) || 0);
                        } else if (cat === "cita") {
                            realMeetings += (Number(count) || 0);
                        }
                    }
                }
            }
        });

        state.slightEdgeRealMetrics = {
            moneyWon: realMoneyWon,
            ticketAvg: realTicketAvg,
            conversionRate: realConversionRate,
            sales: wonQuotes.length,
            quotes: currentMonthQuotes.length,
            meetings: realMeetings,
            calls: realCalls
        };

        // Render the funnel display
        updateFunnelDisplay();

        // Toggle to dashboard mode since plan exists
        toggleSlightEdgeMode("dashboard");

        // Fetch log for the selected date
        const targetDate = DOM.slightEdgeDate.value;
        const logRes = await apiRequest(`/api/slight-edge/log/${state.user.id}?date_str=${targetDate}`);
        const log = logRes.data;

        // Populate checklist quantities and update totals
        populateChecklistQuantities(plan, log);
        updateSlightEdgeProgressPoints(plan);

        // Render historical consistency chart
        renderSlightEdgeHistoryChart(historyLogs, plan);

        // Populate default active coaching message if chat history empty
        if (slightEdgeChatHistory.length === 0) {
            slightEdgeChatHistory = [
                { role: "assistant", content: `¡Hola ${state.user.nombre_completo || 'vendedor'}! Soy tu Sales Coach personal. Tu plan de La Ventaja está configurado y activo. Si deseas ajustar tus disciplinas o tus metas mensuales, haz clic en "Ajustar con Coach" y dime tus nuevos objetivos.` }
            ];
            renderSlightEdgeChat();
        }
    } catch (err) {
        if (err.message.includes("404") || err.message.includes("No se encontró")) {
            state.slightEdgePlan = null;
            toggleSlightEdgeMode("coaching");
            if (DOM.btnSlightEdgeBackToDashboard) DOM.btnSlightEdgeBackToDashboard.classList.add("hidden");

            if (slightEdgeChatHistory.length === 0) {
                slightEdgeChatHistory = [
                    { role: "assistant", content: `¡Hola! Soy tu IA Sales Coach de La Ligera Ventaja. Aún no tienes un plan de consistencia configurado.\n\nPara empezar, por favor indícame:\n1. ¿Cuál es tu **meta de ingresos mensuales** en pesos?\n2. ¿Cuál es tu **ticket de venta promedio**?\n3. ¿Cuál es tu **tasa de conversión** actual (porcentaje de cotizaciones/citas que logras cerrar)?\n\nCon esto calcularemos tu embudo inverso y estableceremos tus disciplinas.` }
                ];
                renderSlightEdgeChat();
            }
        } else {
            showToast("Error al cargar La Ventaja: " + err.message, "error");
        }
    }
}

function renderSlightEdgeChecklist(plan) {
    DOM.slightEdgeChecklistContainer.innerHTML = "";
    if (DOM.btnSaveSlightEdgeLog) DOM.btnSaveSlightEdgeLog.disabled = false;
    
    if (!plan || !plan.activities_config) return;

    plan.activities_config.forEach(act => {
        const key = act.activity;
        checklistQuantities[key] = 0;

        const row = document.createElement("div");
        row.className = "checklist-row";
        row.style = "display: flex; align-items: center; justify-content: space-between; background: rgba(255,255,255,0.02); padding: 12px 16px; border: 1px solid rgba(255,255,255,0.05); border-radius: 8px;";
        row.innerHTML = `
            <div style="flex: 1; margin-right: 12px;">
                <span style="font-size: 14px; font-weight: 500; display: block; color: #fff;">${escapeHTML(act.activity)}</span>
                <span style="font-size: 11px; color: hsl(var(--text-secondary));">+${act.points} ${act.points === 1 ? 'punto' : 'puntos'} por repetición</span>
            </div>
            <div style="display: flex; align-items: center; gap: 12px;">
                <button type="button" class="btn btn-secondary btn-icon btn-sm btn-qty-minus" data-activity="${key}" style="width: 28px; height: 28px; border-radius: 6px; padding: 0; background: rgba(255,255,255,0.05);"><i class="fa-solid fa-minus" style="font-size: 11px;"></i></button>
                <span class="qty-display" id="qty-display-${btoa(key).replace(/=/g, '')}" style="font-size: 16px; font-weight: bold; width: 20px; text-align: center; color: #fff;">0</span>
                <button type="button" class="btn btn-secondary btn-icon btn-sm btn-qty-plus" data-activity="${key}" style="width: 28px; height: 28px; border-radius: 6px; padding: 0; background: rgba(255,255,255,0.05);"><i class="fa-solid fa-plus" style="font-size: 11px;"></i></button>
            </div>
        `;
        DOM.slightEdgeChecklistContainer.appendChild(row);
    });

    // Attach click listeners
    DOM.slightEdgeChecklistContainer.querySelectorAll(".btn-qty-minus").forEach(btn => {
        btn.addEventListener("click", () => {
            const key = btn.getAttribute("data-activity");
            if (checklistQuantities[key] > 0) {
                checklistQuantities[key]--;
                updateQtyDisplay(key);
                updateSlightEdgeProgressPoints(plan);
            }
        });
    });

    DOM.slightEdgeChecklistContainer.querySelectorAll(".btn-qty-plus").forEach(btn => {
        btn.addEventListener("click", () => {
            const key = btn.getAttribute("data-activity");
            checklistQuantities[key]++;
            updateQtyDisplay(key);
            updateSlightEdgeProgressPoints(plan);
        });
    });
}

function updateQtyDisplay(activityKey) {
    const safeId = "qty-display-" + btoa(activityKey).replace(/=/g, '');
    const span = document.getElementById(safeId);
    if (span) {
        span.textContent = checklistQuantities[activityKey];
    }
}

function populateChecklistQuantities(plan, log) {
    if (!plan || !plan.activities_config) return;
    
    plan.activities_config.forEach(act => {
        const key = act.activity;
        const savedQty = log && log.completed_activities ? (log.completed_activities[key] || 0) : 0;
        checklistQuantities[key] = savedQty;
        updateQtyDisplay(key);
    });
}

function updateSlightEdgeProgressPoints(plan) {
    if (!plan || !plan.activities_config) return;
    
    let sum = 0;
    plan.activities_config.forEach(act => {
        const key = act.activity;
        const qty = checklistQuantities[key] || 0;
        sum += qty * act.points;
    });

    const goal = plan.daily_points_goal || 10;
    if (DOM.slightEdgePointsCounter) {
        DOM.slightEdgePointsCounter.textContent = sum;
    }
    const goalText = document.getElementById("slight-edge-points-goal-text");
    if (goalText) {
        goalText.textContent = `de ${goal} pts`;
    }
    
    const progressCircleBar = document.getElementById("progress-circle-bar");
    if (progressCircleBar) {
        if (sum >= goal) {
            progressCircleBar.style.borderColor = "#10b981";
            progressCircleBar.style.opacity = "0.9";
            progressCircleBar.style.boxShadow = "0 0 15px rgba(16,185,129,0.5)";
            if (DOM.slightEdgePointsCounter) DOM.slightEdgePointsCounter.style.color = "#10b981";
        } else {
            progressCircleBar.style.borderColor = "hsl(var(--primary))";
            progressCircleBar.style.opacity = "0.4";
            progressCircleBar.style.boxShadow = "none";
            if (DOM.slightEdgePointsCounter) DOM.slightEdgePointsCounter.style.color = "#fff";
        }
    }
}

async function saveSlightEdgeLog() {
    if (!state.slightEdgePlan) return;
    try {
        const targetDate = DOM.slightEdgeDate.value;
        const payload = {
            date_str: targetDate,
            completed_activities: checklistQuantities
        };

        await apiRequest(`/api/slight-edge/log/${state.user.id}`, {
            method: "POST",
            body: JSON.stringify(payload)
        });
        showToast("Consistencia del día guardada correctamente.");
        await loadSellerSlightEdgePlanAndLog();
    } catch (err) {
        showToast("Error al guardar consistencia: " + err.message, "error");
    }
}

let slightEdgeHistoryChartInstance = null;

function renderSlightEdgeHistoryChart(logs, plan) {
    const canvas = document.getElementById("slightEdgeHistoryChart");
    if (!canvas) return;
    
    const dates = [];
    const dateLabels = [];
    for (let i = 9; i >= 0; i--) {
        const d = new Date();
        d.setDate(d.getDate() - i);
        const dateStr = d.toISOString().split("T")[0];
        dates.push(dateStr);
        const parts = dateStr.split("-");
        dateLabels.push(`${parts[2]}/${parts[1]}`);
    }
    
    const pointsData = dates.map(dStr => {
        const log = logs.find(l => l.date === dStr);
        return log ? log.total_points : 0;
    });
    
    const goal = plan ? plan.daily_points_goal : 10;
    const goalData = dates.map(() => goal);
    
    if (slightEdgeHistoryChartInstance) {
        slightEdgeHistoryChartInstance.destroy();
    }
    
    const ctx = canvas.getContext("2d");
    const isDark = !document.body.classList.contains("light-theme");
    const textColor = isDark ? "rgba(255, 255, 255, 0.6)" : "rgba(0, 0, 0, 0.6)";
    const gridColor = isDark ? "rgba(255, 255, 255, 0.05)" : "rgba(0, 0, 0, 0.05)";
    
    slightEdgeHistoryChartInstance = new Chart(ctx, {
        type: "line",
        data: {
            labels: dateLabels,
            datasets: [
                {
                    label: "Puntos Logrados",
                    data: pointsData,
                    borderColor: "#a78bfa",
                    backgroundColor: "rgba(167, 139, 250, 0.1)",
                    borderWidth: 3,
                    fill: true,
                    tension: 0.35,
                    pointBackgroundColor: "#a78bfa",
                    pointRadius: 4
                },
                {
                    label: "Meta Diaria",
                    data: goalData,
                    borderColor: "rgba(239, 68, 68, 0.5)",
                    borderWidth: 1.5,
                    borderDash: [5, 5],
                    fill: false,
                    pointRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    labels: { color: textColor, font: { size: 10 } }
                }
            },
            scales: {
                x: {
                    grid: { color: gridColor },
                    ticks: { color: textColor, font: { size: 9 } }
                },
                y: {
                    min: 0,
                    max: Math.max(12, ...pointsData) + 2,
                    grid: { color: gridColor },
                    ticks: { color: textColor, font: { size: 9 } }
                }
            }
        }
    });
}

function openWeightsModal() {
    const container = document.getElementById("weights-list-container");
    if (!container || !state.slightEdgePlan) return;
    
    container.innerHTML = "";
    state.slightEdgePlan.activities_config.forEach((act, idx) => {
        const row = document.createElement("div");
        row.style = "display: flex; align-items: center; justify-content: space-between; gap: 12px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 8px;";
        row.innerHTML = `
            <div style="flex: 1; min-width: 0;">
                <span style="font-size: 13px; font-weight: 500; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #fff;">${escapeHTML(act.activity)}</span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <input type="number" class="weight-input" min="1" max="10" value="${act.points}" data-index="${idx}" style="width: 60px; padding: 6px; font-size: 13px; text-align: center; margin: 0; background: hsl(var(--bg-secondary)); border: 1px solid hsl(var(--border-color)); border-radius: 4px; color: #fff;">
                <button type="button" class="btn btn-danger btn-icon btn-sm btn-delete-activity" data-index="${idx}" style="width: 28px; height: 28px; padding: 0; display: flex; align-items: center; justify-content: center;"><i class="fa-solid fa-trash-can" style="font-size: 11px;"></i></button>
            </div>
        `;
        container.appendChild(row);
    });
    
    // Attach click listeners to delete button
    container.querySelectorAll(".btn-delete-activity").forEach(btn => {
        btn.addEventListener("click", () => {
            const idx = parseInt(btn.getAttribute("data-index"));
            if (confirm(`¿Estás seguro de que deseas eliminar la actividad "${state.slightEdgePlan.activities_config[idx].activity}" de tu plan?`)) {
                state.slightEdgePlan.activities_config.splice(idx, 1);
                openWeightsModal(); // refresh UI in modal
            }
        });
    });
    
    document.getElementById("adjust-weights-modal").classList.remove("hidden");
}

async function handleWeightsSubmit(e) {
    e.preventDefault();
    if (!state.slightEdgePlan) return;
    
    const inputs = document.querySelectorAll("#weights-list-container .weight-input");
    const updatedConfig = [];
    
    inputs.forEach(input => {
        const idx = parseInt(input.getAttribute("data-index"));
        const val = parseInt(input.value) || 1;
        const act = state.slightEdgePlan.activities_config[idx];
        if (act) {
            updatedConfig.push({
                activity: act.activity,
                points: val
            });
        }
    });
    
    try {
        const payload = {
            monthly_income_goal: state.slightEdgePlan.monthly_income_goal,
            ticket_average: state.slightEdgePlan.ticket_average,
            conversion_rate: state.slightEdgePlan.conversion_rate,
            activities_config: updatedConfig,
            daily_points_goal: state.slightEdgePlan.daily_points_goal
        };
        
        await apiRequest(`/api/slight-edge/plan/${state.user.id}`, {
            method: "POST",
            body: JSON.stringify(payload)
        });
        
        showToast("Pesos de disciplinas actualizados con éxito.");
        document.getElementById("adjust-weights-modal").classList.add("hidden");
        await loadSellerSlightEdgePlanAndLog();
    } catch (err) {
        showToast("Error al guardar pesos: " + err.message, "error");
    }
}

async function handleNewTaskSubmit(e) {
    e.preventDefault();
    if (!state.slightEdgePlan) return;
    
    const activityName = document.getElementById("new-task-activity").value.trim();
    const pointsVal = parseInt(document.getElementById("new-task-points").value) || 1;
    
    if (!activityName) return;
    
    const exists = state.slightEdgePlan.activities_config.some(
        act => act.activity.toLowerCase() === activityName.toLowerCase()
    );
    if (exists) {
        showToast("Esta actividad ya existe en tu plan.", "error");
        return;
    }
    
    const updatedConfig = [...state.slightEdgePlan.activities_config, { activity: activityName, points: pointsVal }];
    
    try {
        const payload = {
            monthly_income_goal: state.slightEdgePlan.monthly_income_goal,
            ticket_average: state.slightEdgePlan.ticket_average,
            conversion_rate: state.slightEdgePlan.conversion_rate,
            activities_config: updatedConfig,
            daily_points_goal: state.slightEdgePlan.daily_points_goal
        };
        
        await apiRequest(`/api/slight-edge/plan/${state.user.id}`, {
            method: "POST",
            body: JSON.stringify(payload)
        });
        
        showToast("Nueva actividad añadida con éxito.");
        document.getElementById("new-task-modal").classList.add("hidden");
        document.getElementById("new-task-form").reset();
        await loadSellerSlightEdgePlanAndLog();
    } catch (err) {
        showToast("Error al añadir actividad: " + err.message, "error");
    }
}

async function loadSlightEdgeSummaryWidget() {
    if (!DOM.slightEdgeSummaryCard) return;
    
    const metricsContainer = document.getElementById("slight-edge-summary-metrics-container");
    const emptyState = document.getElementById("slight-edge-summary-empty-state");
    
    DOM.slightEdgeSummaryCard.classList.remove("hidden");
    
    try {
        const planRes = await apiRequest(`/api/slight-edge/plan/${state.user.id}`);
        const plan = planRes.data;
        if (!plan) {
            if (metricsContainer) metricsContainer.classList.add("hidden");
            if (emptyState) emptyState.classList.remove("hidden");
            return;
        }
        
        if (metricsContainer) metricsContainer.classList.remove("hidden");
        if (emptyState) emptyState.classList.add("hidden");
        
        const logRes = await apiRequest(`/api/slight-edge/log/${state.user.id}`);
        const logs = logRes.data || [];
        
        // 1. Points Today
        const todayStr = new Date().toISOString().split("T")[0];
        const logToday = logs.find(l => l.date === todayStr);
        const pointsToday = logToday ? logToday.total_points : 0;
        const goalToday = plan.daily_points_goal || 10;
        if (DOM.summaryPointsToday) DOM.summaryPointsToday.textContent = `${pointsToday}/${goalToday}`;
        
        // 2. Points This Week
        const sevenDaysAgo = new Date();
        sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
        const logsThisWeek = logs.filter(l => new Date(l.date) >= sevenDaysAgo);
        const pointsWeek = logsThisWeek.reduce((acc, l) => acc + l.total_points, 0);
        if (DOM.summaryPointsWeek) DOM.summaryPointsWeek.textContent = `${pointsWeek}/${goalToday * 5}`;
        
        // 3. Completed Today List
        if (DOM.summaryCompletedTodayText) {
            if (logToday && logToday.completed_activities && Object.keys(logToday.completed_activities).length > 0) {
                const completedList = Object.entries(logToday.completed_activities)
                    .filter(([_, count]) => count > 0)
                    .map(([name, count]) => `${name} (${count})`)
                    .join(", ");
                DOM.summaryCompletedTodayText.textContent = completedList || "Ninguna actividad registrada hoy.";
            } else {
                DOM.summaryCompletedTodayText.textContent = "Ninguna actividad registrada hoy.";
            }
        }
        
        // 4. Sum up 30-day completed activities (fuzzy matching)
        let calls = 0;
        let meetings = 0;
        let quotes = 0;
        let sales = 0;
        let totalPoints30 = 0;
        let loggedDays30 = logs.length;
        
        function localCategorize(name) {
            const n = name.toLowerCase().trim();
            if (n.includes("llam") || n.includes("call") || n.includes("prospect") || n.includes("contac")) return "llamada";
            if (n.includes("cit") || n.includes("reun") || n.includes("meet") || n.includes("visita")) return "cita";
            if (n.includes("cotiz") || n.includes("propuest") || n.includes("presupuest") || n.includes("quot") || n.includes("enviar")) return "cotizacion";
            if (n.includes("cierr") || n.includes("vent") || n.includes("cobro") || n.includes("clos") || n.includes("firm")) return "venta";
            return "otra";
        }
        
        logs.forEach(log => {
            totalPoints30 += log.total_points;
            if (log.completed_activities) {
                Object.entries(log.completed_activities).forEach(([act, count]) => {
                    const cat = localCategorize(act);
                    if (cat === "llamada") calls += count;
                    else if (cat === "cita") meetings += count;
                    else if (cat === "cotizacion") quotes += count;
                    else if (cat === "venta") sales += count;
                });
            }
        });
        
        const f = plan.funnel_metrics || { llamadas_mensuales: 100, citas_mensuales: 20, cotizaciones_mensuales: 10, ventas_mensuales: 2 };
        if (DOM.summaryKpiCalls) DOM.summaryKpiCalls.textContent = `${calls} / ${f.llamadas_mensuales || 100} meta`;
        if (DOM.summaryKpiMeetings) DOM.summaryKpiMeetings.textContent = `${meetings} / ${f.citas_mensuales || 20} meta`;
        if (DOM.summaryKpiQuotes) DOM.summaryKpiQuotes.textContent = `${quotes} / ${f.cotizaciones_mensuales || 10} meta`;
        if (DOM.summaryKpiSales) DOM.summaryKpiSales.textContent = `${sales} / ${f.ventas_mensuales || 2} meta`;
        
        // 5. Real Conversion
        const conversionReal = meetings > 0 ? (sales / meetings * 100) : plan.conversion_rate;
        if (DOM.summaryConversionReal) DOM.summaryConversionReal.textContent = `${conversionReal.toFixed(1)}%`;
        if (DOM.summaryConversionPlan) DOM.summaryConversionPlan.textContent = `Plan: ${plan.conversion_rate}%`;
        
        // 6. Efficiency
        const avgDailyPoints = loggedDays30 > 0 ? (totalPoints30 / loggedDays30) : 0;
        const efficiency = goalToday > 0 ? (avgDailyPoints / goalToday * 100) : 0;
        if (DOM.summaryConversionEfficiency) DOM.summaryConversionEfficiency.textContent = `${efficiency.toFixed(1)}%`;
        
    } catch (err) {
        console.warn("Slight edge summary card error:", err);
        if (metricsContainer) metricsContainer.classList.add("hidden");
        if (emptyState) emptyState.classList.remove("hidden");
    }
}

function formatChatBubbleText(text) {
    if (!text) return "";
    let escaped = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
    
    // Convert markdown bold to HTML strong tags
    escaped = escaped.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    
    // Convert newlines to HTML line breaks
    escaped = escaped.replace(/\n/g, "<br>");
    
    return escaped;
}

function renderSlightEdgeChat() {
    DOM.slightEdgeChatMessages.innerHTML = "";
    slightEdgeChatHistory.forEach(msg => {
        const bubble = document.createElement("div");
        bubble.className = msg.role === "user" ? "chat-bubble user" : "chat-bubble assistant";
        bubble.style = `
            align-self: ${msg.role === "user" ? "flex-end" : "flex-start"};
            background: ${msg.role === "user" ? "hsl(var(--primary))" : "rgba(255,255,255,0.05)"};
            color: hsl(var(--text-primary));
            padding: 8px 12px;
            border-radius: 8px;
            max-width: 80%;
            font-size: 13px;
            line-height: 1.5;
            margin-bottom: 6px;
        `;
        bubble.innerHTML = formatChatBubbleText(msg.content);
        DOM.slightEdgeChatMessages.appendChild(bubble);
    });
    DOM.slightEdgeChatMessages.scrollTop = DOM.slightEdgeChatMessages.scrollHeight;
}

async function handleSlightEdgeChatSubmit(e) {
    e.preventDefault();
    const txt = DOM.slightEdgeChatInput.value;
    if (!txt) return;

    // Add user message
    slightEdgeChatHistory.push({ role: "user", content: txt });
    renderSlightEdgeChat();
    DOM.slightEdgeChatInput.value = "";

    // Show typing bubble
    const typingBubble = document.createElement("div");
    typingBubble.style = "align-self: flex-start; background: rgba(255,255,255,0.05); padding: 8px 12px; border-radius: 8px; font-size: 13px; color: #aaa; margin-bottom: 6px;";
    typingBubble.innerHTML = 'Coach está pensando... <i class="fa-solid fa-spinner animate-spin"></i>';
    DOM.slightEdgeChatMessages.appendChild(typingBubble);
    DOM.slightEdgeChatMessages.scrollTop = DOM.slightEdgeChatMessages.scrollHeight;

    try {
        const res = await apiRequest(`/api/slight-edge/coaching-chat/${state.user.id}`, {
            method: "POST",
            body: JSON.stringify({ messages: slightEdgeChatHistory })
        });

        // Remove typing bubble
        typingBubble.remove();

        // Add assistant response
        slightEdgeChatHistory.push({ role: "assistant", content: res.response });
        renderSlightEdgeChat();

        if (res.plan_saved) {
            showToast("¡Nuevo plan de consistencia guardado con éxito!");
            await loadSellerSlightEdgePlanAndLog();
        }
    } catch (err) {
        typingBubble.remove();
        showToast("Error de comunicación con el coach: " + err.message, "error");
    }
}

async function loadCoordinatorSlightEdgeDashboard() {
    try {
        const res = await apiRequest("/companies/kuroda/dashboard");
        
        // Populate inputs
        if (DOM.coordinatorGlobalTarget) DOM.coordinatorGlobalTarget.value = res.global_sales_target || "";
        if (DOM.coordinatorGlobalGoals) DOM.coordinatorGlobalGoals.value = res.global_goals || "";

        // Alignment logic
        const globalTarget = res.global_sales_target || 0.0;
        const totalTarget = res.aggregated.total_target || 0.0;

        if (DOM.coordinatorAlignmentAlert) {
            if (globalTarget <= 0) {
                DOM.coordinatorAlignmentAlert.style.display = "flex";
                DOM.coordinatorAlignmentAlert.style.borderLeft = "4px solid #aaa";
                DOM.alignmentIcon.innerHTML = '<i class="fa-solid fa-circle-info" style="color: #aaa;"></i>';
                DOM.alignmentStatusTitle.textContent = "Meta Global no Configurada";
                DOM.alignmentStatusDesc.textContent = "Define una meta de facturación mensual global de la empresa para auditar la cobertura y alineación del equipo.";
                DOM.alignmentDiffVal.textContent = "$0";
                DOM.alignmentDiffVal.style.color = "#aaa";
            } else if (totalTarget >= globalTarget) {
                const diff = totalTarget - globalTarget;
                DOM.coordinatorAlignmentAlert.style.display = "flex";
                DOM.coordinatorAlignmentAlert.style.borderLeft = "4px solid #10b981";
                DOM.alignmentIcon.innerHTML = '<i class="fa-solid fa-circle-check" style="color: #10b981;"></i>';
                DOM.alignmentStatusTitle.textContent = "Metas Alineadas con la Empresa";
                DOM.alignmentStatusDesc.textContent = "¡Excelente! La sumatoria de las metas de consistencia individuales de tus vendedores cubre o excede la meta global.";
                DOM.alignmentDiffVal.textContent = "+$" + diff.toLocaleString();
                DOM.alignmentDiffVal.style.color = "#10b981";
            } else {
                const diff = globalTarget - totalTarget;
                DOM.coordinatorAlignmentAlert.style.display = "flex";
                DOM.coordinatorAlignmentAlert.style.borderLeft = "4px solid #ef4444";
                DOM.alignmentIcon.innerHTML = '<i class="fa-solid fa-circle-exclamation" style="color: #ef4444;"></i>';
                DOM.alignmentStatusTitle.textContent = "Brecha en Metas del Equipo";
                DOM.alignmentStatusDesc.textContent = "La suma de las metas de ingresos de los vendedores NO cubre el objetivo de facturación global de la empresa.";
                DOM.alignmentDiffVal.textContent = "-$" + diff.toLocaleString();
                DOM.alignmentDiffVal.style.color = "#ef4444";
            }
        }

        // Render Performance Table
        DOM.tableSlightEdgePerformance.innerHTML = "";
        const sellers = res.sellers || [];

        if (sellers.length === 0) {
            DOM.tableSlightEdgePerformance.innerHTML = '<tr><td colspan="6" style="text-align: center;">No hay vendedores registrados.</td></tr>';
            return;
        }

        sellers.forEach(s => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>
                    <strong class="seller-burndown-trigger" data-id="${s.id}" data-name="${escapeHTML(s.name)}" style="cursor: pointer; color: #38bdf8;">
                        ${escapeHTML(s.name)} <i class="fa-solid fa-chart-line" style="font-size: 11px; margin-left: 4px; color: #a78bfa;"></i>
                    </strong>
                </td>
                <td>$${s.metrics.target.toLocaleString()}</td>
                <td>$${s.metrics.sales.toLocaleString()}</td>
                <td><span class="status-pill" style="background: rgba(16,185,129,0.1); color: #10b981; border: 1px solid rgba(16,185,129,0.2);">${s.metrics.conversion_rate}%</span></td>
                <td>${s.metrics.roi} pts / ${s.slight_edge.daily_points_goal}</td>
                <td>
                    <button class="btn btn-secondary btn-sm btn-audit-slight-edge-ai" data-id="${s.id}" data-name="${escapeHTML(s.name)}">
                        <i class="fa-solid fa-wand-magic-sparkles"></i> Auditar IA
                    </button>
                </td>
            `;
            DOM.tableSlightEdgePerformance.appendChild(tr);
        });

        // Attach audit click handlers
        DOM.tableSlightEdgePerformance.querySelectorAll(".btn-audit-slight-edge-ai").forEach(btn => {
            btn.addEventListener("click", async () => {
                const sellerId = btn.getAttribute("data-id");
                const name = btn.getAttribute("data-name");
                
                // Show loading
                DOM.slightEdgeAiRecommendationCard.classList.remove("hidden");
                DOM.slightEdgeAiContent.innerHTML = `Generando auditoría para **${name}** con el Sales Coach... <i class="fa-solid fa-spinner animate-spin"></i>`;
                DOM.slightEdgeAiRecommendationCard.scrollIntoView({ behavior: "smooth" });

                try {
                    const auditRes = await apiRequest(`/companies/kuroda/sellers/${sellerId}/ai-goals`, {
                        method: "POST"
                    });
                    DOM.slightEdgeAiContent.textContent = auditRes.ai_suggestion;
                } catch (err) {
                    DOM.slightEdgeAiContent.textContent = "Error al auditar: " + err.message;
                }
            });
        });

        // Attach burndown chart click handlers
        DOM.tableSlightEdgePerformance.querySelectorAll(".seller-burndown-trigger").forEach(el => {
            el.addEventListener("click", () => {
                const id = el.getAttribute("data-id");
                const name = el.getAttribute("data-name");
                openSellerBurndownModal(id, name);
            });
        });

    } catch (err) {
        showToast("Error al cargar panel de coordinación: " + err.message, "error");
    }
}

function categorizeActivityLocal(name) {
    const n = name.toLowerCase().trim();
    if (["llam", "call", "prospect", "contac"].some(x => n.includes(x))) {
        return "llamada";
    }
    if (["cit", "reun", "meet", "visita"].some(x => n.includes(x))) {
        return "cita";
    }
    if (["cotiz", "propuest", "presupuest", "quot", "enviar"].some(x => n.includes(x))) {
        return "cotizacion";
    }
    if (["cierr", "vent", "cobro", "clos", "firm"].some(x => n.includes(x))) {
        return "venta";
    }
    return "otra";
}

async function openSellerBurndownModal(sellerId, name) {
    const modal = document.getElementById("burndown-modal");
    if (!modal) return;

    document.getElementById("burndown-modal-title").textContent = `Gráfica de Burndown de Consistencia - ${name}`;
    
    document.getElementById("burndown-seller-sales").textContent = "...";
    document.getElementById("burndown-seller-target").textContent = "...";
    document.getElementById("burndown-seller-consistency").textContent = "...";
    document.getElementById("burndown-seller-conversion").textContent = "...";

    modal.classList.remove("hidden");

    try {
        const logsRes = await apiRequest(`/api/slight-edge/log/${sellerId}`);
        const logs = logsRes.data || [];

        let plan = null;
        try {
            plan = await apiRequest(`/api/slight-edge/plan/${sellerId}`);
        } catch (e) {
            console.warn("Seller has no plan set up:", e);
        }

        const quotesRes = await apiRequest(`/api/v1/cotizaciones/?vendedor_id=${sellerId}&limit=5000`);
        const quotes = quotesRes.data || [];

        const planObj = (plan && plan.data) ? plan.data : null;
        const salesGoal = planObj ? planObj.monthly_income_goal : 0;
        const conversionRatePlanned = planObj ? planObj.conversion_rate : 0;
        const dailyGoal = planObj ? planObj.daily_points_goal : 10;

        let totalSales = 0;
        let consistencyPointsSum = 0;
        let loggedDays = logs.length;
        
        let meetings = 0;
        let salesCount = 0;

        logs.forEach(l => {
            consistencyPointsSum += l.total_points;
            for (let act in l.completed_activities) {
                const count = l.completed_activities[act];
                const cat = categorizeActivityLocal(act);
                if (cat === "cita") meetings += count;
                else if (cat === "venta") salesCount += count;
            }
        });

        const avgPoints = loggedDays > 0 ? (consistencyPointsSum / loggedDays) : 0;
        const ticketAverage = planObj ? planObj.ticket_average : 0;
        totalSales = salesCount * ticketAverage;

        const actualConversion = meetings > 0 ? (salesCount / meetings * 100) : conversionRatePlanned;

        document.getElementById("burndown-seller-sales").textContent = `$${totalSales.toLocaleString()}`;
        document.getElementById("burndown-seller-target").textContent = `$${salesGoal.toLocaleString()}`;
        document.getElementById("burndown-seller-consistency").textContent = `${avgPoints.toFixed(1)} pts / ${dailyGoal}`;
        document.getElementById("burndown-seller-conversion").textContent = `${actualConversion.toFixed(1)}%`;

        const now = new Date();
        const year = now.getFullYear();
        const month = now.getMonth();
        const daysInMonth = new Date(year, month + 1, 0).getDate();

        const labels = [];
        const idealData = [];
        const realData = [];
        const quotesData = [];

        const totalTargetPoints = dailyGoal * daysInMonth;

        let accumulatedPoints = 0;
        let lastRealVal = totalTargetPoints;

        // Calculate max day to render based on current local day or latest log date to prevent timezone mismatch errors
        let maxDay = now.getDate();
        logs.forEach(l => {
            const parts = l.date.split("-");
            if (parts.length === 3 && Number(parts[0]) === year && Number(parts[1]) === (month + 1)) {
                const logDay = Number(parts[2]);
                if (logDay > maxDay) {
                    maxDay = logDay;
                }
            }
        });

        const barBackgrounds = [];
        const barBorders = [];

        for (let d = 1; d <= daysInMonth; d++) {
            labels.push(`${d}`);
            const idealVal = Math.max(0, totalTargetPoints - (d * dailyGoal));
            idealData.push(idealVal);
            
            const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
            const log = logs.find(l => l.date === dateStr);
            const dayPoints = log ? log.total_points : 0;

            if (d <= maxDay) {
                accumulatedPoints += dayPoints;
                lastRealVal = Math.max(0, totalTargetPoints - accumulatedPoints);
                realData.push(lastRealVal);
            }

            const dayQuotes = quotes.filter(q => q.fecha_registro === dateStr).length;
            quotesData.push(dayQuotes);

            // Determine color based on quote age (relative to today)
            // Verde: <= 7 días
            // Azul: <= 30 días
            // Amarillo: <= 60 días
            // Rojo: > 60 días
            const qDate = new Date(`${dateStr}T12:00:00Z`);
            const todayDate = new Date(`${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}T12:00:00Z`);
            const diffTime = todayDate - qDate;
            const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

            if (diffDays <= 7) {
                barBackgrounds.push('rgba(16, 185, 129, 0.45)'); // Verde
                barBorders.push('#10b981');
            } else if (diffDays <= 30) {
                barBackgrounds.push('rgba(56, 189, 248, 0.45)'); // Azul
                barBorders.push('#38bdf8');
            } else if (diffDays <= 60) {
                barBackgrounds.push('rgba(245, 158, 11, 0.45)'); // Amarillo
                barBorders.push('#f59e0b');
            } else {
                barBackgrounds.push('rgba(239, 68, 68, 0.45)'); // Rojo
                barBorders.push('#ef4444');
            }
        }

        const ctx = document.getElementById('burndownChartCanvas').getContext('2d');
        if (state.burndownChartInstance) {
            state.burndownChartInstance.destroy();
        }

        state.burndownChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Burndown Ideal (Puntos)',
                        type: 'line',
                        data: idealData,
                        borderColor: '#a78bfa',
                        borderDash: [5, 5],
                        borderWidth: 2,
                        fill: false,
                        tension: 0.1,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Burndown Real (Puntos Restantes)',
                        type: 'line',
                        data: realData,
                        borderColor: '#f59e0b',
                        borderWidth: 3,
                        fill: false,
                        tension: 0.1,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Cotizaciones (Barras)',
                        type: 'bar',
                        data: quotesData,
                        backgroundColor: barBackgrounds,
                        borderColor: barBorders,
                        borderWidth: 1.5,
                        yAxisID: 'yQuotes'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        type: 'linear',
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Puntos Restantes',
                            color: '#64748b'
                        },
                        ticks: {
                            color: '#ccc'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)'
                        },
                        min: 0,
                        max: totalTargetPoints
                    },
                    yQuotes: {
                        type: 'linear',
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Cotizaciones',
                            color: '#38bdf8'
                        },
                        ticks: {
                            color: '#38bdf8',
                            stepSize: 1,
                            beginAtZero: true
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Días del Mes',
                            color: '#64748b'
                        },
                        ticks: {
                            color: '#ccc'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        labels: {
                            color: '#64748b'
                        }
                    }
                }
            }
        });

    } catch (err) {
        showToast("Error al cargar burndown: " + err.message, "error");
    }
}

async function handleCompanySettingsSubmit(e) {
    e.preventDefault();
    try {
        const target = parseFloat(DOM.coordinatorGlobalTarget.value) || 0.0;
        const goals = DOM.coordinatorGlobalGoals.value;

        await apiRequest("/companies/kuroda/dashboard/target", {
            method: "POST",
            body: JSON.stringify({
                global_sales_target: target,
                global_goals: goals
            })
        });

        showToast("Metas de la empresa guardadas con éxito.");
        await loadCoordinatorSlightEdgeDashboard();
    } catch (err) {
        showToast("Error al guardar metas: " + err.message, "error");
    }
}

/* ==========================================================================
   ASIGNACIÓN Y SUBASTA DE CLIENTES
   ========================================================================== */

async function loadAsignacionData() {
    const managerView = document.getElementById("asignacion-manager-view");
    const sellerView = document.getElementById("asignacion-seller-view");
    
    if (!managerView || !sellerView) return;

    if (state.user.rol === "vendedor") {
        managerView.classList.add("hidden");
        sellerView.classList.remove("hidden");
        await loadSellerAsignacionView();
    } else {
        managerView.classList.remove("hidden");
        sellerView.classList.add("hidden");
        await loadManagerAsignacionView();
    }
}

async function loadManagerAsignacionView() {
    const listAvailable = document.getElementById("list-available-clients");
    const listSellers = document.getElementById("list-assign-sellers");
    const activeAuctions = document.getElementById("active-auctions-list");
    
    if (!listAvailable || !listSellers || !activeAuctions) return;

    try {
        // 1. Fetch available clients
        const clientsRes = await apiRequest("/api/v1/asignaciones/clientes");
        const clients = clientsRes || [];

        // 2. Fetch sellers
        const sellersRes = await apiRequest("/api/v1/vendedores/?limit=100");
        const sellers = sellersRes.data || [];

        // 3. Render Available Clients
        listAvailable.innerHTML = "";
        const availableClients = clients.filter(c => c.estado === "disponible");
        if (availableClients.length === 0) {
            listAvailable.innerHTML = `<p style="font-size: 13px; color: hsl(var(--text-secondary)); text-align: center; margin: 20px 0;">No hay clientes disponibles para asignación.</p>`;
        } else {
            availableClients.forEach(c => {
                const item = document.createElement("div");
                item.style = "display: flex; align-items: flex-start; gap: 10px; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); padding: 12px; border-radius: 6px;";
                item.innerHTML = `
                    <input type="checkbox" class="client-checkbox" value="${c.id}" style="margin-top: 3px;">
                    <div style="flex: 1;">
                        <strong style="font-size: 14px; color: #fff;">${escapeHTML(c.nombre)}</strong>
                        <span style="font-size: 12px; color: hsl(var(--text-secondary)); display: block; margin-top: 2px;">
                            ${c.email || ''} ${c.telefono ? ' | ' + c.telefono : ''}
                        </span>
                        ${c.comentarios ? `<p style="margin: 6px 0 0 0; font-size: 12px; color: #38bdf8;">${c.comentarios}</p>` : ''}
                    </div>
                `;
                listAvailable.appendChild(item);
            });
        }

        // 4. Render Sellers
        listSellers.innerHTML = "";
        const activeSellers = sellers.filter(s => s.rol === "vendedor");
        if (activeSellers.length === 0) {
            listSellers.innerHTML = `<p style="font-size: 13px; color: hsl(var(--text-secondary)); text-align: center; margin: 20px 0;">No hay vendedores registrados.</p>`;
        } else {
            activeSellers.forEach(s => {
                const item = document.createElement("div");
                item.style = "display: flex; align-items: center; gap: 10px; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); padding: 10px; border-radius: 6px;";
                item.innerHTML = `
                    <input type="checkbox" class="seller-checkbox" value="${s.id}">
                    <div>
                        <strong style="font-size: 13px; color: #fff;">${s.nombre_completo || s.email}</strong>
                        <span style="font-size: 11px; color: hsl(var(--text-secondary)); display: block;">${s.codigo_vendedor || 'Vendedor'}</span>
                    </div>
                `;
                listSellers.appendChild(item);
            });
        }

        // 5. Render Active Auctions
        activeAuctions.innerHTML = "";
        const auctionClients = clients.filter(c => c.estado === "en_subasta");
        if (auctionClients.length === 0) {
            activeAuctions.innerHTML = `<p style="font-size: 13px; color: hsl(var(--text-secondary)); text-align: center; margin: 20px 0;">No hay subastas activas en este momento.</p>`;
        } else {
            auctionClients.forEach(c => {
                const item = document.createElement("div");
                item.style = "background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); padding: 18px; border-radius: 8px; border-left: 4px solid #f59e0b; margin-bottom: 12px;";
                
                let bidsHtml = "";
                if (!c.pujas || c.pujas.length === 0) {
                    bidsHtml = `<p style="font-size: 12px; color: hsl(var(--text-secondary)); margin: 10px 0 0 0; font-style: italic;">Esperando postulaciones de los vendedores...</p>`;
                } else {
                    bidsHtml = `
                        <div style="margin-top: 14px; display: flex; flex-direction: column; gap: 10px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 14px;">
                            <h4 style="margin: 0 0 6px 0; font-size: 13px; color: #f59e0b;">Postulaciones Recibidas (${c.pujas.length}):</h4>
                            ${c.pujas.map(p => `
                                <div style="background: rgba(0,0,0,0.15); border: 1px solid rgba(255,255,255,0.03); padding: 12px; border-radius: 6px; display: flex; justify-content: space-between; align-items: flex-start; gap: 14px;">
                                    <div style="flex: 1;">
                                        <span style="font-size: 12px; color: #a78bfa; font-weight: bold;">
                                            ${p.vendedor ? (p.vendedor.nombre_completo || p.vendedor.email) : 'Vendedor'}
                                        </span>
                                        <p style="margin: 6px 0 0 0; font-size: 13px; color: hsl(var(--text-primary)); line-height: 1.4;">
                                            "${p.razon}"
                                        </p>
                                    </div>
                                    <button class="btn btn-primary btn-sm btn-approve-bid" data-client="${c.id}" data-bid="${p.id}" style="padding: 6px 12px; font-size: 11px;">
                                        <i class="fa-solid fa-check"></i> Asignar
                                    </button>
                                </div>
                            `).join('')}
                        </div>
                    `;
                }

                item.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div>
                            <strong style="font-size: 15px; color: #fff;">${escapeHTML(c.nombre)}</strong>
                            <span style="font-size: 12px; color: hsl(var(--text-secondary)); display: block; margin-top: 2px;">
                                ${c.email || ''} ${c.telefono ? ' | ' + c.telefono : ''}
                            </span>
                            ${c.comentarios ? `<p style="margin: 6px 0 0 0; font-size: 12px; color: hsl(var(--text-secondary));">${c.comentarios}</p>` : ''}
                        </div>
                        <span class="badge" style="background: rgba(245,158,11,0.15); color: #f59e0b; border: 1px solid rgba(245,158,11,0.3); font-size: 11px;">En Subasta</span>
                    </div>
                    ${bidsHtml}
                `;
                activeAuctions.appendChild(item);
            });

            // Attach event listeners to Approve buttons
            activeAuctions.querySelectorAll(".btn-approve-bid").forEach(btn => {
                btn.addEventListener("click", async () => {
                    const clientId = btn.getAttribute("data-client");
                    const bidId = btn.getAttribute("data-bid");
                    
                    if (!confirm("¿Estás seguro de asignar este cliente al vendedor seleccionado? Esto cerrará la subasta.")) return;

                    try {
                        await apiRequest("/api/v1/asignaciones/resolver", {
                            method: "POST",
                            body: JSON.stringify({
                                cliente_id: clientId,
                                puja_ganadora_id: bidId
                            })
                        });
                        showToast("Cliente asignado con éxito.");
                        await loadManagerAsignacionView();
                    } catch (err) {
                        showToast("Error al resolver subasta: " + err.message, "error");
                    }
                });
            });
        }

    } catch (err) {
        showToast("Error al cargar asignaciones: " + err.message, "error");
    }
}

async function loadSellerAsignacionView() {
    const listSellers = document.getElementById("seller-auctions-list");
    if (!listSellers) return;

    try {
        const clientsRes = await apiRequest("/api/v1/asignaciones/clientes");
        const clients = clientsRes || [];

        listSellers.innerHTML = "";
        
        // Show only active auctions where they can bid or show assigned ones
        const auctions = clients.filter(c => c.estado === "en_subasta");
        const assigned = clients.filter(c => c.estado === "asignado" && c.asignado_a === state.user.id);
        
        if (auctions.length === 0 && assigned.length === 0) {
            listSellers.innerHTML = `<p style="font-size: 13px; color: hsl(var(--text-secondary)); text-align: center; margin: 20px 0;">No tienes subastas disponibles ni clientes asignados.</p>`;
            return;
        }

        // Render Auctions
        if (auctions.length > 0) {
            const auctionTitle = document.createElement("h4");
            auctionTitle.style = "margin: 10px 0; font-size: 14px; color: #f59e0b;";
            auctionTitle.textContent = "Subastas Activas:";
            listSellers.appendChild(auctionTitle);

            auctions.forEach(c => {
                // Check if this seller has already bid
                const myBid = c.pujas ? c.pujas.find(p => p.vendedor_id === state.user.id) : null;
                
                const item = document.createElement("div");
                item.style = "background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); padding: 18px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; gap: 20px; margin-bottom: 12px;";
                
                let actionHtml = "";
                if (myBid) {
                    actionHtml = `
                        <div style="text-align: right;">
                            <span class="badge" style="background: rgba(16,185,129,0.15); color: #10b981; border: 1px solid rgba(16,185,129,0.3); font-size: 11px; display: inline-block; margin-bottom: 4px;">Propuesta Enviada</span>
                            <span style="font-size: 11px; color: hsl(var(--text-secondary)); display: block;">"${myBid.razon.substring(0, 30)}..."</span>
                        </div>
                    `;
                } else {
                    actionHtml = `
                        <button class="btn btn-glow btn-sm btn-pujar-cliente" data-id="${c.id}" data-nombre="${escapeHTML(c.nombre)}" style="background: linear-gradient(135deg, #f59e0b, #d97706); border: none; font-weight: bold; color: #fff;">
                            <i class="fa-solid fa-gavel"></i> Pujar
                        </button>
                    `;
                }

                item.innerHTML = `
                    <div style="flex: 1;">
                        <strong style="font-size: 15px; color: #fff;">${escapeHTML(c.nombre)}</strong>
                        ${c.comentarios ? `<p style="margin: 6px 0 0 0; font-size: 12px; color: hsl(var(--text-secondary));">${c.comentarios}</p>` : ''}
                    </div>
                    ${actionHtml}
                `;
                listSellers.appendChild(item);
            });
        }

        // Render Assigned Clientes
        if (assigned.length > 0) {
            const assignedTitle = document.createElement("h4");
            assignedTitle.style = "margin: 20px 0 10px 0; font-size: 14px; color: #10b981;";
            assignedTitle.textContent = "Mis Clientes Asignados:";
            listSellers.appendChild(assignedTitle);

            assigned.forEach(c => {
                const item = document.createElement("div");
                item.style = "background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); padding: 16px; border-radius: 8px; border-left: 4px solid #10b981; display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;";
                item.innerHTML = `
                    <div>
                        <strong style="font-size: 15px; color: #fff;">${escapeHTML(c.nombre)}</strong>
                        <span style="font-size: 12px; color: hsl(var(--text-secondary)); display: block; margin-top: 2px;">
                            ${c.email || ''} ${c.telefono ? ' | ' + c.telefono : ''}
                        </span>
                        ${c.comentarios ? `<p style="margin: 6px 0 0 0; font-size: 12px; color: hsl(var(--text-secondary));">${c.comentarios}</p>` : ''}
                    </div>
                    <span class="badge" style="background: rgba(16,185,129,0.1); color: #10b981; border: 1px solid rgba(16,185,129,0.2); font-size: 11px;">Asignado</span>
                `;
                listSellers.appendChild(item);
            });
        }

        // Attach event listeners to Bid buttons
        listSellers.querySelectorAll(".btn-pujar-cliente").forEach(btn => {
            btn.addEventListener("click", () => {
                const clientId = btn.getAttribute("data-id");
                const clientNombre = btn.getAttribute("data-nombre");
                
                const biddingModal = document.getElementById("bidding-modal");
                const biddingClientId = document.getElementById("bidding-client-id");
                const biddingClientDesc = document.getElementById("bidding-client-desc");
                
                if (biddingModal && biddingClientId && biddingClientDesc) {
                    biddingClientId.value = clientId;
                    biddingClientDesc.textContent = `Explica por qué crees que el cliente "${clientNombre}" debería ser asignado a ti.`;
                    document.getElementById("bidding-reason").value = "";
                    biddingModal.classList.remove("hidden");
                }
            });
        });

    } catch (err) {
        showToast("Error al cargar tus subastas: " + err.message, "error");
    }
}

async function handleExecuteAssignment() {
    const selectedClients = Array.from(document.querySelectorAll("#list-available-clients .client-checkbox:checked")).map(cb => cb.value);
    const selectedSellers = Array.from(document.querySelectorAll("#list-assign-sellers .seller-checkbox:checked")).map(cb => cb.value);

    if (selectedClients.length === 0) {
        showToast("Por favor, selecciona al menos un cliente disponible.", "error");
        return;
    }
    if (selectedSellers.length === 0) {
        showToast("Por favor, selecciona al menos un vendedor.", "error");
        return;
    }

    try {
        const res = await apiRequest("/api/v1/asignaciones/iniciar", {
            method: "POST",
            body: JSON.stringify({
                cliente_ids: selectedClients,
                vendedor_ids: selectedSellers
            })
        });
        showToast(res.message);
        await loadManagerAsignacionView();
    } catch (err) {
        showToast("Error al ejecutar asignación: " + err.message, "error");
    }
}

// Bidding Modal Submissions and Closures
document.addEventListener("DOMContentLoaded", () => {
    // Execute assignment button
    const btnExecute = document.getElementById("btn-execute-assignment");
    if (btnExecute) {
        btnExecute.addEventListener("click", handleExecuteAssignment);
    }

    // Select all clients button
    const btnSelectAll = document.getElementById("btn-select-all-clients");
    if (btnSelectAll) {
        btnSelectAll.addEventListener("click", () => {
            const checkboxes = document.querySelectorAll("#list-available-clients .client-checkbox");
            if (checkboxes.length === 0) return;
            
            // Check if all are checked
            const allChecked = Array.from(checkboxes).every(cb => cb.checked);
            checkboxes.forEach(cb => cb.checked = !allChecked);
            btnSelectAll.textContent = allChecked ? "Seleccionar Todos" : "Deseleccionar Todos";
        });
    }

    // Bidding Form Submission
    const biddingForm = document.getElementById("bidding-form");
    if (biddingForm) {
        biddingForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const clientId = document.getElementById("bidding-client-id").value;
            const reason = document.getElementById("bidding-reason").value;

            try {
                await apiRequest("/api/v1/asignaciones/pujas", {
                    method: "POST",
                    body: JSON.stringify({
                        cliente_id: clientId,
                        razon: reason
                    })
                });
                showToast("Propuesta enviada con éxito.");
                document.getElementById("bidding-modal").classList.add("hidden");
                await loadSellerAsignacionView();
            } catch (err) {
                showToast("Error al enviar propuesta: " + err.message, "error");
            }
        });
    }

    // Close Bidding Modal buttons
    const btnCloseBidding = document.getElementById("btn-close-bidding-modal");
    if (btnCloseBidding) {
        btnCloseBidding.addEventListener("click", () => {
            document.getElementById("bidding-modal").classList.add("hidden");
        });
    }
    const btnCancelBidding = document.getElementById("btn-cancel-bidding");
    if (btnCancelBidding) {
        btnCancelBidding.addEventListener("click", () => {
            document.getElementById("bidding-modal").classList.add("hidden");
        });
    }
});



// --- COTIZACIONES UPLOAD LOGIC ---
document.addEventListener("DOMContentLoaded", () => {
    const fileUploadCotizaciones = document.getElementById("file-upload-cotizaciones");
    if (fileUploadCotizaciones) {
        fileUploadCotizaciones.addEventListener("change", async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append("file", file);

            const btnUpload = document.getElementById("btn-upload-cotizaciones");
            const originalHtml = btnUpload.innerHTML;
            btnUpload.disabled = true;
            btnUpload.innerHTML = 'Cargando... <i class="fa-solid fa-spinner animate-spin"></i>';

            try {
                const response = await fetch("/api/v1/cotizaciones/upload", {
                    method: "POST",
                    headers: {
                        "Authorization": `Bearer ${localStorage.getItem("crm_token")}`
                    },
                    body: formData
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showToast(result.message || "Cotizaciones cargadas exitosamente.", "success");
                    await loadSummaryData(); // Reload table
                } else {
                    showToast(result.detail || "Error al cargar cotizaciones.", "error");
                }
            } catch (error) {
                console.error("Error uploading excel:", error);
                showToast("Ocurrió un error en la conexión con el servidor.", "error");
            } finally {
                btnUpload.disabled = false;
                btnUpload.innerHTML = originalHtml;
                e.target.value = ""; // Reset input
            }
        });
    }
});
