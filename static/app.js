
// --- KURODA OFFICIAL CLASSIFICATION MATRIX ---
const KURODA_FAMILIALES = [
    "PLOMERIA CROMADA",
    "ARTICULOS DE PLOMERIA",
    "CERAMICOS",
    "REVESTESIMIENTO DECORATIVOS",
    "SERVICIO",
    "HOGAR"
];

const KURODA_SUBFAMILIAS_MAP = {
    "PLOMERIA CROMADA": [
        "ACCESORIOS DE BAÑO", "ACCESORIOS DE BAÑ", "ACCESORIOS DE BANO", "PLOMERIA CROMADA"
    ],
    "ARTICULOS DE PLOMERIA": [
        "ABRAZADERAS", "ARTICULOS PLOMERIA", "ARTICULOS DE PLOMERIA", "BOMBAS",
        "COLADERAS", "CONEXIONES", "FILTROS", "MEDIDORES", "PEGAMENTOS",
        "REFACCIONES", "REFACCIONES P/BOMB", "REFACCIONES P/BOMBAS",
        "TOMAS DOMICILIARIA", "TOMAS DOMICILIARIAS", "TUBERIA",
        "VALVULA INDUSTRIAL", "VALVULAS"
    ],
    "CERAMICOS": [
        "ASIENTOS", "LAVABOS", "SANITARIOS"
    ],
    "REVESTESIMIENTO DECORATIVOS": [
        "ADHESIVOS CERAMICO", "ADHESIVOS CERAMICOS", "AZULEJOS", "BOQUILLAS",
        "ESQUINEROS/MOLDURA", "ESQUINEROS/MOLDURAS", "PISOS", "REVEST DECORADOS",
        "REVESTIMIENTO DECORATIVOS"
    ],
    "SERVICIO": [
        "AIRE ACON/MINI SPL", "ASPERSORES", "CALENTADORES", "CISTERNAS",
        "CORTADORAS", "EQ HIDRONEUMATICOS", "FERRETERIA", "FOSAS",
        "HERRAMIENTAS", "IRRIGACION", "JUEGOS ESPARCIMIEN", "MANGUERAS",
        "MANOMETROS", "MOTORES", "SERVICIOS", "TANQUES Y CILINDRO",
        "TANQUES Y CILINDROS", "TINACOS", "TINAS", "TRABAJOS DE TALLER"
    ],
    "HOGAR": [
        "ACCESORIOS", "ARTICULOS DE COCIN", "ARTICULOS DE COCINA", "CABLES Y ALAMBRES",
        "CTRO CARGA/INTERRU", "CTRO CARGA/INTERRUPT", "ESPEJOS", "FOCOS Y FILAMENTOS",
        "FREGADEROS", "GABINETES PARA BAÑ", "GABINETES PARA BAÑO", "ILUMINACION",
        "IMPERMEABILIZANTES", "LAM CANAL GALV ACR", "LAM CANAL GALV ACRI",
        "LAVADEROS", "LINEA BLANCA", "MATERIAL ELECTR/HE", "MATERIAL ELECTR/HERR",
        "PLACAS", "TAPA/CONTACT/APAGA", "TAPA/CONTACT/APAGAD"
    ]
};

// --- UNIFIED PAGINATION CONTROLS ---
function createPaginationControls(stateKey, totalItems, onPageChange, pageSize = 25) {
    const totalPages = Math.ceil(totalItems / pageSize) || 1;
    if (state[stateKey] === undefined) state[stateKey] = 1;
    if (state[stateKey] > totalPages && totalPages > 0) state[stateKey] = totalPages;
    if (state[stateKey] < 1) state[stateKey] = 1;
    
    const current = state[stateKey];
    const startIndex = (current - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    
    let html = '';
    if (totalItems > pageSize) {
        html = `
            <div style="display: flex; gap: 10px; align-items: center; justify-content: center; margin-top: 15px; width: 100%; padding: 10px 0;">
                <button class="btn btn-secondary btn-sm" id="btn-pag-first-${stateKey}" ${current === 1 ? 'disabled' : ''}><i class="fa-solid fa-angles-left"></i> Inicio</button>
                <button class="btn btn-secondary btn-sm" id="btn-pag-prev-${stateKey}" ${current === 1 ? 'disabled' : ''}><i class="fa-solid fa-chevron-left"></i> Anterior</button>
                <span style="font-size: 13px; font-weight: bold; padding: 0 10px;">Página ${current} de ${totalPages}</span>
                <button class="btn btn-secondary btn-sm" id="btn-pag-next-${stateKey}" ${current >= totalPages ? 'disabled' : ''}>Siguiente <i class="fa-solid fa-chevron-right"></i></button>
                <button class="btn btn-secondary btn-sm" id="btn-pag-last-${stateKey}" ${current >= totalPages ? 'disabled' : ''}>Final <i class="fa-solid fa-angles-right"></i></button>
            </div>
        `;
    }
    
    const bindEvents = () => {
        const btnFirst = document.getElementById(`btn-pag-first-${stateKey}`);
        const btnPrev = document.getElementById(`btn-pag-prev-${stateKey}`);
        const btnNext = document.getElementById(`btn-pag-next-${stateKey}`);
        const btnLast = document.getElementById(`btn-pag-last-${stateKey}`);
        
        if (btnFirst) btnFirst.addEventListener("click", () => { state[stateKey] = 1; onPageChange(); });
        if (btnPrev) btnPrev.addEventListener("click", () => { state[stateKey]--; onPageChange(); });
        if (btnNext) btnNext.addEventListener("click", () => { state[stateKey]++; onPageChange(); });
        if (btnLast) btnLast.addEventListener("click", () => { state[stateKey] = totalPages; onPageChange(); });
    };
    
    return {
        startIndex,
        endIndex,
        html,
        bindEvents
    };
}

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

function buildContactHtml(contact = {}) {
    const phone = contact.contacto_preferente || contact.celular || contact.telefono || "";
    const email = contact.email || "";
    const digits = String(phone).replace(/\D/g, "");
    if (!phone && !email) return '<span class="text-muted">Sin contacto</span>';
    const parts = [];
    if (email) parts.push(`<a href="mailto:${escapeHTML(email)}">${escapeHTML(email)}</a>`);
    if (phone) {
        parts.push(
            `<a href="tel:${escapeHTML(phone)}" title="Llamar"><i class="fa-solid fa-phone"></i> ${escapeHTML(phone)}</a>`
        );
        if (digits) {
            parts.push(
                `<a href="https://wa.me/${digits}" target="_blank" rel="noopener" title="Abrir WhatsApp"><i class="fa-brands fa-whatsapp"></i></a>`
            );
        }
    }
    return parts.join("<br>");
}

function normalizeSearchText(value) {
    return String(value ?? "")
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase()
        .trim();
}

function formatNumber(value) {
    const numericValue = Number(value || 0);
    return numericValue.toLocaleString("es-MX", { maximumFractionDigits: 2 });
}

const state = {
    token: localStorage.getItem("crm_token") || null,
    user: JSON.parse(localStorage.getItem("crm_user")) || null,
    currentSection: "summary",
    vendedores: [],
    metas: [],
    promociones: [],
    inventario_abcf: [],
    cotizaciones: [],
    lastDataUpdates: {},
    salesChart: null,
    goalsChart: null,
    sellerPerformanceChart: null,
    chartQuoteStatus: null,
    chartQuoteSeller: null,
    chartQuoteTrend: null,
    chartQuoteChannel: null,
    summaryChannelSales: [],
    quotesCurrentPage: 1,
    quotesPageSize: 50,
    quotePagination: { total: 0, limit: 50, offset: 0 },
    quoteSummary: null,
    kanbanCurrentPage: 1,
    kanbanPageSize: 50,
    kanbanPagination: { total: 0, limit: 50, offset: 0 },
    kanbanStageData: { pendientes: [], concretadas: [], vencidas: [] },
    kanbanStagePagination: {},
    quotesSortOrder: "desc", // date sort: 'asc' or 'desc'
    activeHeatmapFilter: null,
    sellerGoalPeriod: "day",
    sellerGoalProgress: null,
    commercialGoals: [],
    commercialGoalsDashboard: null,
    editingCommercialGoalId: null,
    kanbanSortOrders: {
        cotizado: null,
        promociones: null,
        vendido: null,
        vencido: null
    },
    pendingReminders: [],
    clientes: {
        page: 1,
        limit: 25,
        search: "",
        tipo_persona: "",
        colonia: "",
        poblacion: "",
        total: 0,
        pages: 1,
        total_fisicas: 0,
        total_morales: 0,
        filtersLoaded: false
    }
};

// Mapa rol -> secciones permitidas en el menú lateral y la navegación móvil.
// null/undefined = sin restricción (rol ve todas las secciones).
// Se usa tanto en initSession() (visibilidad) como en switchSection() (guard).
const ALLOWED_SECTIONS_BY_ROLE = {
    soporte: ["summary", "promociones", "inventario-abcf", "sobrepedidos", "por-entregar"],
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
    sellerHomeDashboard: document.getElementById("seller-home-dashboard"),
    sellerDashboardSearch: document.getElementById("seller-dashboard-search"),
    sellerDashboardToday: document.getElementById("seller-dashboard-today"),
    sellerQuickSearch: document.getElementById("seller-quick-search"),
    sellerDashboardProfile: document.getElementById("seller-dashboard-profile"),
    sellerDashboardInitials: document.getElementById("seller-dashboard-initials"),
    sellerMonthlyProgressRing: document.getElementById("seller-monthly-progress-ring"),
    sellerMonthlyProgressPercent: document.getElementById("seller-monthly-progress-percent"),
    sellerMonthlyGoalLabel: document.getElementById("seller-monthly-goal-label"),
    sellerMonthlyCurrent: document.getElementById("seller-monthly-current"),
    sellerMonthlyRemaining: document.getElementById("seller-monthly-remaining"),
    sellerMonthlyDaysLeft: document.getElementById("seller-monthly-days-left"),
    sellerPeriodButtons: document.querySelectorAll("[data-seller-period]"),
    sellerPendingCount: document.getElementById("seller-pending-count"),
    sellerPendingList: document.getElementById("seller-pending-list"),
    sellerFollowupAlert: document.getElementById("seller-followup-alert"),
    sellerFollowupList: document.getElementById("seller-followup-list"),
    sellerPromoList: document.getElementById("seller-promo-list"),
    sellerPerformanceChart: document.getElementById("seller-performance-chart"),
    sellerPerformancePeriod: document.getElementById("seller-performance-period"),
    sellerPerformanceAmount: document.getElementById("seller-performance-amount"),
    sellerPerformanceGoal: document.getElementById("seller-performance-goal"),
    sellerMiniProgress: document.getElementById("seller-mini-progress"),
    sellerMiniProgressPercent: document.getElementById("seller-mini-progress-percent"),
    sellerRecentActivity: document.getElementById("seller-recent-activity"),
    sellerChannelBars: document.getElementById("seller-channel-bars"),
    sellerTopClientsTable: document.getElementById("seller-top-clients-table"),
    sellerTopMaterialsTable: document.getElementById("seller-top-materials-table"),
    summaryAdminKpis: document.getElementById("summary-admin-kpis"),
    summaryAdminCharts: document.getElementById("summary-admin-charts"),
    summaryAdminHeatmap: document.getElementById("summary-admin-heatmap"),
    summaryAdminOperational: document.getElementById("summary-admin-operational"),
    summaryChannelSales: document.getElementById("summary-channel-sales"),
    summaryChannelFilter: document.getElementById("summary-channel-filter"),
    summaryChannelKpis: document.getElementById("summary-channel-kpis"),
    summaryChannelTable: document.querySelector("#summary-channel-table tbody"),
    adminTodayQuotes: document.getElementById("admin-today-quotes"),
    adminTodayAccessLog: document.getElementById("admin-today-access-log"),
    adminAccessMonth: document.getElementById("admin-access-month"),
    adminAccessSeller: document.getElementById("admin-access-seller"),
    kanbanDataUpdated: document.getElementById("kanban-data-updated"),
    
    sidebarMenu: document.getElementById("sidebar-menu"),
    menuVendedores: document.getElementById("menu-vendedores"),
    menuMetas: document.getElementById("menu-metas"),
    menuAsignacion: document.getElementById("menu-asignacion"),
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
    sellerParent: document.getElementById("seller-parent"),
    sellerParentGroup: document.getElementById("seller-parent-group"),
    sellerMonthlyGoalGroup: document.getElementById("seller-monthly-goal-group"),
    sellerMonthlyGoal: document.getElementById("seller-monthly-goal"),
    sellerEmail: document.getElementById("seller-email"),
    sellerPhone: document.getElementById("seller-phone"),
    sellerPassword: document.getElementById("seller-password"),
    sellerFormTitle: document.getElementById("seller-form-title"),
    sellerPasswordLabel: document.getElementById("seller-password-label"),
    btnSubmitSeller: document.getElementById("btn-submit-seller"),

    // Metas comerciales de gerencia
    metasMonth: document.getElementById("metas-month"),
    metasSellerFilter: document.getElementById("metas-seller-filter"),
    metasPeriod: document.getElementById("metas-period"),
    metasReferenceDate: document.getElementById("metas-reference-date"),
    btnLoadMetas: document.getElementById("btn-load-metas"),
    metasForm: document.getElementById("metas-form"),
    metasFormTitle: document.getElementById("metas-form-title"),
    metasType: document.getElementById("metas-type"),
    metasVendedorGroup: document.getElementById("metas-vendedor-group"),
    metasVendedor: document.getElementById("metas-vendedor"),
    metasSucursalGroup: document.getElementById("metas-sucursal-group"),
    metasSucursal: document.getElementById("metas-sucursal"),
    metasSucursalesList: document.getElementById("metas-sucursales-list"),
    metasTarget: document.getElementById("metas-target"),
    metasDescription: document.getElementById("metas-description"),
    btnSubmitMetas: document.getElementById("btn-submit-metas"),
    btnCancelMetasEdit: document.getElementById("btn-cancel-metas-edit"),
    metasGeneralTarget: document.getElementById("metas-general-target"),
    metasGeneralTargetLabel: document.getElementById("metas-general-target-label"),
    metasGeneralSales: document.getElementById("metas-general-sales"),
    metasGeneralProgress: document.getElementById("metas-general-progress"),
    tableMetasComerciales: document.getElementById("table-metas-comerciales"),
    metasSellersDashboard: document.getElementById("metas-sellers-dashboard"),
    metasSellersTitle: document.getElementById("metas-sellers-title"),
    metasBranchesCard: document.getElementById("metas-branches-card"),
    metasBranchesDashboard: document.getElementById("metas-branches-dashboard"),
    
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
    filterPromoFamilia: document.getElementById("filter-promo-familia"),
    filterPromoSubfamilia: document.getElementById("filter-promo-subfamilia"),
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
    uploadPromocionesWrapper: document.getElementById("upload-promociones-wrapper"),
    lastUploadPromociones: document.getElementById("last-upload-promociones"),
    
    
    // Inventario ABC+F Section
    tableInventarioAbcf: document.querySelector("#table-inventario-abcf tbody"),
    uploadInventarioAbcfForm: document.getElementById("upload-inventario-abcf-form"),
    uploadInventarioAbcfWrapper: document.getElementById("upload-inventario-abcf-wrapper"),
    filterInvSucursal: document.getElementById("filter-inv-sucursal"),
    filterInvAbcf: document.getElementById("filter-inv-abcf"),
    filterInvProveedor: document.getElementById("filter-inv-proveedor"),
    filterInvFamilia: document.getElementById("filter-inv-familia"),
    filterInvSubfamilia: document.getElementById("filter-inv-subfamilia"),
    filterInvSearch: document.getElementById("filter-inv-search"),
    btnClearInvFilters: document.getElementById("btn-clear-inv-filters"),
    pagInventarioAbcf: document.getElementById("pag-inventario-abcf"),
    fileInventarioAbcf: document.getElementById("file-inventario-abcf"),
    lastUploadInventarioAbcf: document.getElementById("last-upload-inventario-abcf"),
    invKpiCategorias: document.getElementById("inv-kpi-categorias"),
    invKpiProveedores: document.getElementById("inv-kpi-proveedores"),

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
    filterQuoteToday: document.getElementById("filter-quote-today"),
    filterQuoteMonth: document.getElementById("filter-quote-month"),
    filterQuoteAll: document.getElementById("filter-quote-all"),
    filterQuotePeriodStatus: document.getElementById("filter-quote-period-status"),
    activeHeatmapFilter: document.getElementById("active-heatmap-filter"),
    activeHeatmapFilterText: document.getElementById("active-heatmap-filter-text"),
    btnClearHeatmapFilter: document.getElementById("btn-clear-heatmap-filter"),
    btnLoadCommercialAnalytics: document.getElementById("btn-load-commercial-analytics"),
    kpiQuotesTotalCount: document.getElementById("kpi-quotes-total-count"),
    kpiQuotesTotalAmount: document.getElementById("kpi-quotes-total-amount"),
    kpiQuotesSoldCount: document.getElementById("kpi-quotes-sold-count"),
    kpiQuotesSoldAmount: document.getElementById("kpi-quotes-sold-amount"),
    kpiQuotesPendingCount: document.getElementById("kpi-quotes-pending-count"),
    kpiQuotesPendingAmount: document.getElementById("kpi-quotes-pending-amount"),
    kpiQuotesExpiredCount: document.getElementById("kpi-quotes-expired-count"),
    kpiQuotesExpiredAmount: document.getElementById("kpi-quotes-expired-amount"),
    quoteFilterCards: document.querySelectorAll(".quote-filter-card"),
    btnToggleQuotesDetails: document.getElementById("btn-toggle-quotes-details"),
    quotesDetailsToggleIcon: document.getElementById("quotes-details-toggle-icon"),
    quotesDetailsContent: document.getElementById("quotes-details-content"),
    tableCotizaciones: document.querySelector("#table-cotizaciones tbody"),
    uploadCotizacionesWrapper: document.getElementById("upload-cotizaciones-wrapper"),
    lastUploadCotizaciones: document.getElementById("last-upload-cotizaciones"),
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
    pagKanban: document.getElementById("pag-kanban"),
    
    // Proposal Modal
    proposalModal: document.getElementById("proposal-modal"),
    modalProposalTitle: document.getElementById("modal-proposal-title"),
    modalProposalBody: document.getElementById("modal-proposal-body"),
    btnCopyProposal: document.getElementById("btn-copy-proposal"),
    btnCloseProposalModal: document.getElementById("btn-close-proposal-modal"),
    btnCloseProposal: document.getElementById("btn-close-proposal"),
    lostReasonModal: document.getElementById("lost-reason-modal"),
    lostReasonTitle: document.getElementById("lost-reason-title"),
    lostReasonForm: document.getElementById("lost-reason-form"),
    lostReasonQuoteId: document.getElementById("lost-reason-quote-id"),
    lostReasonPrice: document.getElementById("lost-reason-price"),
    lostReasonStock: document.getElementById("lost-reason-stock"),
    lostReasonOptions: document.getElementById("lost-reason-options"),
    lostReasonJustificationLabel: document.getElementById("lost-reason-justification-label"),
    lostReasonJustification: document.getElementById("lost-reason-justification"),
    quoteCommentsModal: document.getElementById("quote-comments-modal"),
    quoteCommentsTitle: document.getElementById("quote-comments-title"),
    quoteCommentsQuoteId: document.getElementById("quote-comments-quote-id"),
    quoteCommentsHistory: document.getElementById("quote-comments-history"),
    quoteCommentsForm: document.getElementById("quote-comments-form"),
    quoteCommentsFormLabel: document.getElementById("quote-comments-form-label"),
    quoteCommentsEditId: document.getElementById("quote-comments-edit-id"),
    quoteCommentsText: document.getElementById("quote-comments-text"),
    btnCancelQuoteCommentEdit: document.getElementById("btn-cancel-quote-comment-edit"),
    btnSaveQuoteComment: document.getElementById("btn-save-quote-comment"),
    btnCloseQuoteComments: document.getElementById("btn-close-quote-comments"),
    btnCancelQuoteComments: document.getElementById("btn-cancel-quote-comments"),
    btnCloseLostReasonModal: document.getElementById("btn-close-lost-reason-modal"),
    btnCancelLostReason: document.getElementById("btn-cancel-lost-reason"),
    
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
    coordinatorPerformanceStart: document.getElementById("coordinator-performance-start"),
    coordinatorPerformanceEnd: document.getElementById("coordinator-performance-end"),
    coordinatorPerformancePeriodStatus: document.getElementById("coordinator-performance-period-status"),
    btnCoordinatorPerformanceFilter: document.getElementById("btn-coordinator-performance-filter"),
    btnCoordinatorPerformanceMonth: document.getElementById("btn-coordinator-performance-month"),
    tableSlightEdgePerformance: document.querySelector("#table-slight-edge-performance tbody"),
    slightEdgeAiRecommendationCard: document.getElementById("slight-edge-ai-recommendation-card"),
    btnCloseSlightEdgeAi: document.getElementById("btn-close-slight-edge-ai"),
    slightEdgeAiContent: document.getElementById("slight-edge-ai-content"),

    // Sobrepedidos Section
    tableSobrepedidos: document.querySelector("#table-sobrepedidos tbody"),
    uploadSobrepedidosForm: document.getElementById("upload-sobrepedidos-form"),
    uploadSobrepedidosWrapper: document.getElementById("upload-sobrepedidos-wrapper"),
    filterSobrepedidosProveedor: document.getElementById("filter-sobrepedidos-proveedor"),
    filterSobrepedidosVendedorWrapper: document.getElementById("filter-sobrepedidos-vendedor-wrapper"),
    filterSobrepedidosVendedor: document.getElementById("filter-sobrepedidos-vendedor"),
    filterSobrepedidosGrupo: document.getElementById("filter-sobrepedidos-grupo"),
    filterSobrepedidosEstado: document.getElementById("filter-sobrepedidos-estado"),
    filterSobrepedidosSearch: document.getElementById("filter-sobrepedidos-search"),
    mobileSobrepedidosSearch: document.getElementById("mobile-sobrepedidos-search"),
    mobileSobrepedidosCards: document.getElementById("mobile-sobrepedidos-cards"),
    btnClearSobrepedidosFilters: document.getElementById("btn-clear-sobrepedidos-filters"),
    pagSobrepedidos: document.getElementById("pag-sobrepedidos"),
    fileSobrepedidos: document.getElementById("file-sobrepedidos"),
    lastUploadSobrepedidos: document.getElementById("last-upload-sobrepedidos"),

    // Por Entregar Section
    tablePorEntregar: document.querySelector("#table-por-entregar tbody"),
    filterPorEntregarVendedorWrapper: document.getElementById("filter-por-entregar-vendedor-wrapper"),
    filterPorEntregarVendedor: document.getElementById("filter-por-entregar-vendedor"),
    filterPorEntregarEstado: document.getElementById("filter-por-entregar-estado"),
    filterPorEntregarSearch: document.getElementById("filter-por-entregar-search"),
    btnClearPorEntregarFilters: document.getElementById("btn-clear-por-entregar-filters"),
    pagPorEntregar: document.getElementById("pag-por-entregar"),

    // HU-1, HU-2, HU-3 UI elements
    clientHistoryModal: document.getElementById("client-history-modal"),
    btnCloseClientHistory: document.getElementById("btn-close-client-history"),
    btnCancelClientHistory: document.getElementById("btn-cancel-client-history"),
    clientHistorySubtitle: document.getElementById("client-history-subtitle"),
    clientHistoryTotalQuotes: document.getElementById("client-history-total-quotes"),
    clientHistoryInvoicedCount: document.getElementById("client-history-invoiced-count"),
    clientHistoryTotalQuoted: document.getElementById("client-history-total-quoted"),
    clientHistoryTotalInvoiced: document.getElementById("client-history-total-invoiced"),
    clientHistoryConversionRate: document.getElementById("client-history-conversion-rate"),
    clientHistoryTable: document.querySelector("#client-history-table tbody"),
    searchClientHistoryInput: document.getElementById("search-client-history-input"),
    btnSearchClientHistory: document.getElementById("btn-search-client-history"),

    promoClientsModal: document.getElementById("promo-clients-modal"),
    btnClosePromoClients: document.getElementById("btn-close-promo-clients"),
    btnCancelPromoClients: document.getElementById("btn-cancel-promo-clients"),
    promoClientsInfo: document.getElementById("promo-clients-info"),
    promoClientsTable: document.querySelector("#promo-clients-table tbody"),

    addReminderModal: document.getElementById("add-reminder-modal"),
    btnCloseAddReminder: document.getElementById("btn-close-add-reminder"),
    btnCancelAddReminder: document.getElementById("btn-cancel-add-reminder"),
    addReminderForm: document.getElementById("add-reminder-form"),
    reminderQuoteId: document.getElementById("reminder-quote-id"),
    reminderDateInput: document.getElementById("reminder-date-input"),
    reminderNoteInput: document.getElementById("reminder-note-input"),
    dailyRemindersCard: document.getElementById("daily-reminders-card"),
    dailyRemindersList: document.getElementById("daily-reminders-list"),
    dailyRemindersBadgeCount: document.getElementById("daily-reminders-badge-count"),
    remindersNavBtn: document.getElementById("reminders-nav-btn"),
    remindersNavBadge: document.getElementById("reminders-nav-badge")
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
        const previousUserId = state.user?.id || null;
        try {
            // Fetch fresh user profile
            const profileRes = await apiRequest("/api/auth/me");
            if (profileRes.status === "success" && profileRes.data) {
                state.user = profileRes.data;
                localStorage.setItem("crm_user", JSON.stringify(state.user));
                if (previousUserId && previousUserId !== state.user.id) {
                    state.currentSection = "summary";
                    state.vendedores = [];
                    state.metas = [];
                    state.promociones = [];
                    state.cotizaciones = [];
                    state.activeHeatmapFilter = null;
                }
                // Aplicar orden personalizado del menú lateral para este usuario
            }
        } catch (e) {
            console.error("Fallo al validar sesión:", e);
            logout();
            return;
        }

        // Hide login, show dashboard
        DOM.authContainer?.classList.add("hidden");
        DOM.dashboardContainer?.classList.remove("hidden");
        
        // Set user badge
        const displayName = state.user.nombre_completo || state.user.email.split("@")[0].toUpperCase();
        if (DOM.userDisplayName) DOM.userDisplayName.textContent = displayName;
        if (DOM.userRoleBadge) DOM.userRoleBadge.textContent = state.user.rol.toUpperCase();
        
        // Show avatar image if exists
        if (state.user.avatar) {
            if (DOM.userAvatarImg) {
                DOM.userAvatarImg.src = state.user.avatar;
                DOM.userAvatarImg.classList.remove("hidden");
            }
            if (DOM.userAvatarPlaceholder) DOM.userAvatarPlaceholder.classList.add("hidden");
        } else {
            if (DOM.userAvatarImg) {
                DOM.userAvatarImg.src = "";
                DOM.userAvatarImg.classList.add("hidden");
            }
            if (DOM.userAvatarPlaceholder) DOM.userAvatarPlaceholder.classList.remove("hidden");
        }
        // Restore saved menu order for current user
        restoreSavedMenuOrder();
        
        // Manage visible menu entries based on role.
        // Roles con un set restringido de secciones visibles (lista blanca).
        // null/undefined = sin restricción (todos los items visibles).
        const allowedSections = ALLOWED_SECTIONS_BY_ROLE[state.user.rol];
        if (allowedSections) {
            // Rol con acceso restringido (lista blanca por data-section)
            DOM.menuItems.forEach(item => {
                const sec = item.getAttribute("data-section");
                item.classList.toggle("hidden", !allowedSections.includes(sec));
            });
            document.querySelectorAll(".mobile-nav-item").forEach(item => {
                const sec = item.getAttribute("data-mobile-section");
                item.classList.toggle("hidden", !allowedSections.includes(sec));
            });
            // Ocultar widgets administrativos que no aplican a soporte
            DOM.btnGenerateGoalsModal?.classList.add("hidden");
            if (DOM.menuApi) DOM.menuApi.classList.add("hidden");
        } else {
            // Patrón existente: vendedor oculta Vendedores y API; admin/gerente ven todo
            DOM.menuItems.forEach(item => item.classList.remove("hidden"));
            document.querySelectorAll(".mobile-nav-item").forEach(item => item.classList.remove("hidden"));
            if (state.user.rol === "vendedor") {
                DOM.menuVendedores?.classList.add("hidden");
                DOM.menuMetas?.classList.add("hidden");
                if (DOM.menuAsignacion) DOM.menuAsignacion.classList.add("hidden");
                DOM.btnGenerateGoalsModal?.classList.add("hidden");
                if (DOM.menuApi) DOM.menuApi.classList.add("hidden");
            } else {
                DOM.menuVendedores?.classList.remove("hidden");
                if (DOM.menuAsignacion) DOM.menuAsignacion.classList.remove("hidden");
                DOM.btnGenerateGoalsModal?.classList.remove("hidden");
                if (DOM.menuApi) DOM.menuApi.classList.remove("hidden");
            }
        }
        updateUploadControlsVisibility();
        renderLastUploadLabels();
        await loadLastUploadLabels();

        // Show/hide conexion menu based on role
        
        // Always load the main dashboard and wait for its data before
        // considering the session ready. This prevents stale data from the
        // previously viewed user/section from remaining visible.
        state.currentSection = "summary";
        await switchSection("summary");
        await loadPendingReminders();
    } else {
        DOM.authContainer?.classList.remove("hidden");
        DOM.dashboardContainer?.classList.add("hidden");
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
    if (state.token) {
        fetch("/api/auth/logout", {
            method: "POST",
            headers: { "Authorization": `Bearer ${state.token}` },
            keepalive: true
        }).catch(() => {});
    }
    state.token = null;
    state.user = null;
    state.currentSection = "summary";
    state.vendedores = [];
    state.metas = [];
    state.promociones = [];
    state.cotizaciones = [];
    state.activeHeatmapFilter = null;
    localStorage.removeItem("crm_token");
    localStorage.removeItem("crm_user");
    initSession();
    showToast("Sesión cerrada correctamente", "info");
}

/* ==========================================================================
   ROUTING & VIEW SWITCHER
   ========================================================================== */

async function switchSection(sectionId) {
    // Guard defensivo: si el rol tiene un set restringido de secciones y la
    // solicitada no está permitida, redirigir a 'summary' (definido aquí para
    // que también aplique si ALLOWED_SECTIONS_BY_ROLE cambia en el futuro).
    const _allowedForRole = ALLOWED_SECTIONS_BY_ROLE && ALLOWED_SECTIONS_BY_ROLE[state.user && state.user.rol];
    if (_allowedForRole && !_allowedForRole.includes(sectionId)) {
        sectionId = "summary";
    }

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
    await loadSectionData(sectionId);
}

async function loadSectionData(sectionId) {
    try {
        if (sectionId === "summary") {
            await loadSummaryData();
        } else if (sectionId === "vendedores") {
            await loadVendedoresData();
        } else if (sectionId === "metas") {
            await loadCommercialGoalsData();
        } else if (sectionId === "promociones") {
            await loadPromocionesData();
        } else if (sectionId === "inventario-abcf") {
            await loadInventarioAbcfData();
        } else if (sectionId === "sobrepedidos") {
            await loadSobrepedidosData();
        } else if (sectionId === "por-entregar") {
            await loadPorEntregarData();
        } else if (sectionId === "clientes") {
            await loadClientesData();
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
    // In summary, we load sellers, metas, and quotes to compute metrics and draw charts.
    // Soporte no tiene permiso sobre /vendedores/ (403): se omite la carga y los
    // KPIs que dependen de ella quedan vacíos, que es el comportamiento esperado
    // para un rol de solo visualización operativa.
    let sellers = [];
    if (state.user.rol !== "vendedor" && state.user.rol !== "soporte") {
        const sellersRes = await apiRequest("/api/v1/vendedores/?limit=100");
        sellers = sellersRes.data || [];
    }
    
    const metasRes = await apiRequest("/api/v1/metas/?limit=100");
    const metas = metasRes.data || [];
    
    // El resumen no necesita materializar el histórico completo en el navegador.
    // La API calcula los KPI de forma determinista y entrega solo una muestra
    // reciente para las visualizaciones de contexto.
    const quotesRes = await apiRequest("/api/v1/cotizaciones/?limit=100&vista=resumen");
    const quotes = quotesRes.data || [];
    const quoteSummary = quotesRes.summary || null;
    
    state.vendedores = sellers;
    state.metas = metas;
    state.cotizaciones = quotes;

    await loadPendingReminders();

    if (state.user.rol === "vendedor") {
        if (DOM.sellerHomeDashboard) DOM.sellerHomeDashboard.classList.remove("hidden");
        if (DOM.summaryAdminKpis) DOM.summaryAdminKpis.classList.add("hidden");
        if (DOM.summaryAdminCharts) DOM.summaryAdminCharts.classList.add("hidden");
        if (DOM.summaryAdminHeatmap) DOM.summaryAdminHeatmap.classList.add("hidden");
        if (DOM.summaryAdminOperational) DOM.summaryAdminOperational.classList.add("hidden");
        if (DOM.summaryChannelSales) DOM.summaryChannelSales.classList.add("hidden");
        if (DOM.slightEdgeSummaryCard) DOM.slightEdgeSummaryCard.classList.add("hidden");

        let promociones = state.promociones || [];
        try {
            const promosRes = await apiRequest("/api/v1/promociones/");
            promociones = promosRes.data || [];
            state.promociones = promociones;
        } catch (err) {
            console.warn("No se pudieron cargar promociones para el panel vendedor:", err);
        }

        await refreshSellerGoalProgress();
        await renderSellerHomeDashboard({ metas, quotes, promociones, goalProgress: state.sellerGoalProgress });
        return;
    }

    if (DOM.sellerHomeDashboard) DOM.sellerHomeDashboard.classList.add("hidden");
    if (DOM.summaryAdminKpis) DOM.summaryAdminKpis.classList.remove("hidden");
    if (DOM.summaryAdminCharts) DOM.summaryAdminCharts.classList.remove("hidden");
    if (DOM.summaryAdminHeatmap) DOM.summaryAdminHeatmap.classList.remove("hidden");
    if (DOM.summaryAdminOperational) DOM.summaryAdminOperational.classList.remove("hidden");
    if (DOM.summaryChannelSales) DOM.summaryChannelSales.classList.toggle("hidden", state.user.rol === "soporte");
    
    // Calculate totals
    const totalCotizado = quoteSummary?.total?.amount ?? quotes.reduce((acc, q) => acc + q.total, 0);
    const completedMetas = metas.filter(m => m.estado === "completada").length;
    
    // Update KPI UI
    DOM.kpiTotalSales.textContent = `$${totalCotizado.toLocaleString('es-MX', { minimumFractionDigits: 2 })}`;
    DOM.kpiActiveGoals.textContent = `${completedMetas} / ${metas.length}`;
    DOM.kpiTotalQuotes.textContent = quoteSummary?.total?.count ?? quotesRes.pagination?.total ?? quotes.length;
    DOM.kpiTotalSellers.textContent = state.user.rol === "vendedor" ? 1 : sellers.length;
    
    // Render visual modules independently so one widget cannot freeze the dashboard refresh.
    try {
        renderSalesChart(quotes);
    } catch (chartErr) {
        console.error("Error renderizando grafica de ventas:", chartErr);
    }
    try {
        renderGoalsChart(metas, quotes, sellers);
    } catch (chartErr) {
        console.error("Error renderizando grafica de metas:", chartErr);
    }
    try {
        renderQuotesHeatmap(quotes);
    } catch (heatmapErr) {
        console.error("Error renderizando mapa de calor:", heatmapErr);
    }

    await Promise.all([
        loadAdminAccessLog(),
        loadSummaryChannelSales(),
    ]);
    
    // Load Slight Edge summary tracking card
    await loadSlightEdgeSummaryWidget();
    await loadPendingReminders();
}

function formatChannelMoney(value) {
    return `$${Number(value || 0).toLocaleString("es-MX", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function renderSummaryChannelSales(rows = []) {
    if (!DOM.summaryChannelKpis || !DOM.summaryChannelTable || !DOM.summaryChannelFilter) return;

    const selectedCode = DOM.summaryChannelFilter.value;
    const visibleRows = selectedCode
        ? rows.filter(row => String(row.codigo_canal || "") === selectedCode || String(row.canal || "") === selectedCode || String(row.etiqueta || "") === selectedCode)
        : rows;
    const totals = visibleRows.reduce((acc, row) => ({
        importe_facturado: acc.importe_facturado + Number(row.importe_facturado || 0),
        importe_cotizado: acc.importe_cotizado + Number(row.importe_cotizado || 0),
        operaciones_facturadas: acc.operaciones_facturadas + Number(row.operaciones_facturadas || 0),
        cotizaciones: acc.cotizaciones + Number(row.cotizaciones || 0),
    }), { importe_facturado: 0, importe_cotizado: 0, operaciones_facturadas: 0, cotizaciones: 0 });
    const conversion = totals.cotizaciones ? totals.operaciones_facturadas / totals.cotizaciones * 100 : 0;

    DOM.summaryChannelKpis.innerHTML = [
        ["Venta facturada", formatChannelMoney(totals.importe_facturado), "#10b981", "fa-hand-holding-dollar"],
        ["Importe cotizado", formatChannelMoney(totals.importe_cotizado), "#38bdf8", "fa-file-invoice-dollar"],
        ["Operaciones facturadas", totals.operaciones_facturadas.toLocaleString("es-MX"), "#a78bfa", "fa-file-circle-check"],
        ["Conversión", `${conversion.toFixed(1)}%`, "#f59e0b", "fa-arrow-trend-up"],
    ].map(([label, value, color, icon]) => `
        <div class="glass-card kpi-card" style="border-top:3px solid ${color};">
            <div class="kpi-icon" style="color:${color};"><i class="fa-solid ${icon}"></i></div>
            <div class="kpi-data"><h3>${label}</h3><p>${value}</p></div>
        </div>`).join("");

    DOM.summaryChannelTable.innerHTML = visibleRows.length
        ? visibleRows.map(row => `<tr>
            <td><code>${escapeHTML(row.codigo_canal || "Sin clave")}</code></td>
            <td><strong>${escapeHTML(row.etiqueta || row.canal || "Sin clasificar")}</strong></td>
            <td><strong>${formatChannelMoney(row.importe_facturado)}</strong></td>
            <td>${Number(row.operaciones_facturadas || 0).toLocaleString("es-MX")}</td>
            <td>${Number(row.conversion || 0).toFixed(1)}%</td>
            <td>${Number(row.participacion || 0).toFixed(1)}%</td>
        </tr>`).join("")
        : '<tr><td colspan="6" style="text-align:center;">No hay ventas para el canal seleccionado.</td></tr>';
}

async function loadSummaryChannelSales() {
    if (!DOM.summaryChannelSales) return;
    if (!["admin", "gerente"].includes(state.user?.rol)) {
        DOM.summaryChannelSales.classList.add("hidden");
        return;
    }
    try {
        const response = await apiRequest("/api/v1/analitica/resumen-principal/canales");
        const rows = response.data || [];
        const previouslySelected = DOM.summaryChannelFilter.value;
        state.summaryChannelSales = rows;
        DOM.summaryChannelFilter.innerHTML = [
            '<option value="">Todos los canales</option>',
            ...rows.map(row => {
                const val = row.codigo_canal || row.canal || "";
                const label = row.etiqueta || row.canal || row.codigo_canal || "Sin clave";
                return `<option value="${escapeHTML(val)}">${escapeHTML(label)}</option>`;
            }),
        ].join("");
        DOM.summaryChannelFilter.disabled = rows.length === 0;
        if (rows.some(row => String(row.codigo_canal || row.canal || "") === previouslySelected)) {
            DOM.summaryChannelFilter.value = previouslySelected;
        }
        renderSummaryChannelSales(rows);
    } catch (error) {
        console.error("No se pudo cargar el resumen de ventas por canal:", error);
        DOM.summaryChannelKpis.innerHTML = "";
        DOM.summaryChannelTable.innerHTML = '<tr><td colspan="6" style="text-align:center;">No se pudo cargar el resumen por canal.</td></tr>';
    }
}

function getCurrentMonthValue() {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

function metasMonthAsDate() {
    const value = DOM.metasMonth?.value || getCurrentMonthValue();
    return `${value}-01`;
}

function currentDateValue() {
    const now = new Date();
    return `${getCurrentMonthValue()}-${String(now.getDate()).padStart(2, "0")}`;
}

function renderCommercialGoalScopeFields() {
    const type = DOM.metasType?.value || "general";
    DOM.metasVendedorGroup?.classList.toggle("hidden", type !== "vendedor");
    DOM.metasSucursalGroup?.classList.toggle("hidden", type !== "sucursal");
}

function resetCommercialGoalForm() {
    state.editingCommercialGoalId = null;
    DOM.metasForm?.reset();
    if (DOM.metasType) DOM.metasType.value = "general";
    if (DOM.metasFormTitle) DOM.metasFormTitle.textContent = "Agregar meta mensual";
    if (DOM.btnSubmitMetas) DOM.btnSubmitMetas.innerHTML = '<i class="fa-solid fa-plus"></i> Guardar meta';
    DOM.btnCancelMetasEdit?.classList.add("hidden");
    if (DOM.metasType) DOM.metasType.disabled = false;
    if (DOM.metasVendedor) DOM.metasVendedor.disabled = false;
    if (DOM.metasSucursal) DOM.metasSucursal.disabled = false;
    renderCommercialGoalScopeFields();
}

function renderCommercialGoalsDashboard(data) {
    const selectedSellerId = DOM.metasSellerFilter?.value || "";
    const selectedSeller = (data?.vendedores || []).find(row => row.vendedor_id === selectedSellerId);
    const overview = selectedSeller || data?.general || {};
    if (DOM.metasGeneralTarget) DOM.metasGeneralTarget.textContent = formatSellerMoney(overview.meta);
    if (DOM.metasGeneralSales) DOM.metasGeneralSales.textContent = formatSellerMoney(overview.venta_facturada);
    if (DOM.metasGeneralProgress) DOM.metasGeneralProgress.textContent = `${Number(overview.cumplimiento || 0).toFixed(1)}%`;
    if (DOM.metasGeneralTargetLabel) DOM.metasGeneralTargetLabel.textContent = selectedSeller ? "Meta del vendedor" : "Meta general";
    if (DOM.metasSellersTitle) DOM.metasSellersTitle.textContent = selectedSeller ? "Avance del vendedor" : "Avance por vendedor";
    DOM.metasBranchesCard?.classList.toggle("hidden", Boolean(selectedSeller));

    const progressCell = row => `${Number(row.cumplimiento || 0).toFixed(1)}%`;
    if (DOM.metasSellersDashboard) {
        const rows = selectedSeller ? [selectedSeller] : data?.vendedores || [];
        DOM.metasSellersDashboard.innerHTML = rows.length ? rows.map(row => `
            <tr><td>${escapeHTML(row.vendedor)}</td><td>${formatSellerMoney(row.meta)}</td><td>${formatSellerMoney(row.venta_facturada)}</td><td>${progressCell(row)}</td></tr>
        `).join("") : '<tr><td colspan="4" class="text-muted">No hay vendedores para el periodo.</td></tr>';
    }
    if (DOM.metasBranchesDashboard) {
        const rows = data?.sucursales || [];
        DOM.metasBranchesDashboard.innerHTML = rows.length ? rows.map(row => `
            <tr><td>${escapeHTML(row.sucursal)}</td><td>${formatSellerMoney(row.meta)}</td><td>${formatSellerMoney(row.venta_facturada)}</td><td>${progressCell(row)}</td></tr>
        `).join("") : '<tr><td colspan="4" class="text-muted">No hay sucursales en las cotizaciones ni metas configuradas.</td></tr>';
    }
    if (DOM.metasSucursalesList) {
        DOM.metasSucursalesList.innerHTML = (data?.sucursales || []).map(row =>
            `<option value="${escapeHTML(row.sucursal)}"></option>`
        ).join("");
    }
}

function renderCommercialGoalsTable() {
    if (!DOM.tableMetasComerciales) return;
    const sellerNames = new Map((state.commercialGoalsDashboard?.vendedores || []).map(row => [row.vendedor_id, row.vendedor]));
    const selectedSellerId = DOM.metasSellerFilter?.value || "";
    const visibleGoals = selectedSellerId
        ? state.commercialGoals.filter(goal => goal.tipo === "vendedor" && goal.vendedor_id === selectedSellerId)
        : state.commercialGoals;
    if (!visibleGoals.length) {
        DOM.tableMetasComerciales.innerHTML = `<tr><td colspan="5" class="text-muted">${selectedSellerId ? "No hay meta configurada para este vendedor en este mes." : "No hay metas configuradas para este mes."}</td></tr>`;
        return;
    }
    DOM.tableMetasComerciales.innerHTML = visibleGoals.map(goal => {
        const scope = goal.tipo === "general" ? "General" : goal.tipo === "vendedor" ? "Vendedor" : "Sucursal";
        const subject = goal.tipo === "general" ? "Empresa" : goal.tipo === "vendedor" ? (sellerNames.get(goal.vendedor_id) || "Vendedor") : goal.sucursal;
        return `<tr>
            <td>${scope}</td><td>${escapeHTML(subject)}</td><td>${formatSellerMoney(goal.monto_objetivo)}</td><td>${escapeHTML(goal.descripcion || "—")}</td>
            <td><button class="btn btn-secondary btn-sm edit-commercial-goal" data-id="${goal.id}"><i class="fa-solid fa-pen"></i></button> <button class="btn btn-danger btn-sm delete-commercial-goal" data-id="${goal.id}"><i class="fa-solid fa-trash"></i></button></td>
        </tr>`;
    }).join("");
    DOM.tableMetasComerciales.querySelectorAll(".edit-commercial-goal").forEach(button => {
        button.addEventListener("click", () => startCommercialGoalEdit(button.dataset.id));
    });
    DOM.tableMetasComerciales.querySelectorAll(".delete-commercial-goal").forEach(button => {
        button.addEventListener("click", () => deleteCommercialGoal(button.dataset.id));
    });
}

function populateCommercialGoalSellers(rows) {
    if (!DOM.metasVendedor) return;
    const selected = DOM.metasVendedor.value;
    DOM.metasVendedor.innerHTML = '<option value="">Selecciona un vendedor</option>' + (rows || []).map(row =>
        `<option value="${row.vendedor_id}">${escapeHTML(row.vendedor)}</option>`
    ).join("");
    if (selected) DOM.metasVendedor.value = selected;
}

function populateCommercialGoalSellerFilter(rows) {
    if (!DOM.metasSellerFilter) return;
    const selected = DOM.metasSellerFilter.value;
    DOM.metasSellerFilter.innerHTML = '<option value="">Todos los vendedores</option>' + (rows || []).map(row =>
        `<option value="${row.vendedor_id}">${escapeHTML(row.vendedor)}</option>`
    ).join("");
    if ((rows || []).some(row => row.vendedor_id === selected)) {
        DOM.metasSellerFilter.value = selected;
    }
}

async function loadCommercialGoalsData() {
    if (!state.user || !["admin", "gerente"].includes(state.user.rol)) return;
    if (DOM.metasMonth && !DOM.metasMonth.value) DOM.metasMonth.value = getCurrentMonthValue();
    if (DOM.metasReferenceDate && !DOM.metasReferenceDate.value) DOM.metasReferenceDate.value = currentDateValue();
    const monthDate = metasMonthAsDate();
    const period = DOM.metasPeriod?.value || "mes";
    const referenceDate = DOM.metasReferenceDate?.value || monthDate;
    const [goalsRes, dashboardRes] = await Promise.all([
        apiRequest(`/api/v1/metas/comerciales?mes=${encodeURIComponent(monthDate)}`),
        apiRequest(`/api/v1/metas/comerciales/dashboard?periodo=${encodeURIComponent(period)}&fecha=${encodeURIComponent(referenceDate)}`),
    ]);
    state.commercialGoals = goalsRes.data || [];
    state.commercialGoalsDashboard = dashboardRes.data || null;
    populateCommercialGoalSellers(state.commercialGoalsDashboard?.vendedores || []);
    populateCommercialGoalSellerFilter(state.commercialGoalsDashboard?.vendedores || []);
    renderCommercialGoalsDashboard(state.commercialGoalsDashboard);
    renderCommercialGoalsTable();
    if (!state.editingCommercialGoalId) renderCommercialGoalScopeFields();
}

function startCommercialGoalEdit(goalId) {
    const goal = state.commercialGoals.find(item => item.id === goalId);
    if (!goal || !DOM.metasForm) return;
    state.editingCommercialGoalId = goalId;
    DOM.metasType.value = goal.tipo;
    DOM.metasVendedor.value = goal.vendedor_id || "";
    DOM.metasSucursal.value = goal.sucursal || "";
    DOM.metasTarget.value = goal.monto_objetivo;
    DOM.metasDescription.value = goal.descripcion || "";
    DOM.metasType.disabled = true;
    DOM.metasVendedor.disabled = true;
    DOM.metasSucursal.disabled = true;
    DOM.metasFormTitle.textContent = "Editar meta mensual";
    DOM.btnSubmitMetas.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> Actualizar meta';
    DOM.btnCancelMetasEdit.classList.remove("hidden");
    renderCommercialGoalScopeFields();
    DOM.metasForm.scrollIntoView({ behavior: "smooth", block: "center" });
}

async function deleteCommercialGoal(goalId) {
    if (!goalId || !window.confirm("¿Eliminar esta meta comercial? Esta acción no se puede deshacer.")) return;
    try {
        await apiRequest(`/api/v1/metas/comerciales/${goalId}`, { method: "DELETE" });
        showToast("Meta eliminada.");
        resetCommercialGoalForm();
        await loadCommercialGoalsData();
    } catch (error) {
        showToast(error.message, "error");
    }
}

async function refreshSellerGoalProgress() {
    if (state.user?.rol !== "vendedor") return;
    try {
        const periodParam = state.sellerGoalPeriod === "day" ? "dia" : state.sellerGoalPeriod === "week" ? "semana" : "mes";
        const res = await apiRequest(`/api/v1/metas/comerciales/mis-avances?periodo=${periodParam}`);
        state.sellerGoalProgress = res.data || null;
    } catch (error) {
        console.warn("No se pudo cargar el avance de meta comercial:", error);
        state.sellerGoalProgress = null;
    }
}

function formatSellerMoney(value) {
    return `$${Number(value || 0).toLocaleString('es-MX', { maximumFractionDigits: 0 })}`;
}

function quoteAgeDays(quote, refDate = new Date()) {
    if (!quote.fecha_registro) return 999;
    const quoteDate = new Date(`${quote.fecha_registro}T12:00:00`);
    const today = new Date(refDate);
    today.setHours(12, 0, 0, 0);
    return Math.max(0, Math.floor((today - quoteDate) / (1000 * 60 * 60 * 24)));
}

function getQuoteDate(quote) {
    if (!quote.fecha_registro) return null;
    const date = new Date(`${quote.fecha_registro}T12:00:00`);
    return Number.isNaN(date.getTime()) ? null : date;
}

function isSameCalendarDay(date, reference = new Date()) {
    return date
        && date.getFullYear() === reference.getFullYear()
        && date.getMonth() === reference.getMonth()
        && date.getDate() === reference.getDate();
}

function formatAccessTime(value) {
    if (!value) return "En sesión";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "Sin registro";
    return date.toLocaleTimeString("es-MX", { hour: "2-digit", minute: "2-digit" });
}

function formatAccessDate(value) {
    if (!value) return "Sin fecha";
    const date = parseLocalDate(value);
    if (!date) return "Sin fecha";
    return date.toLocaleDateString("es-MX", { day: "2-digit", month: "short" });
}

function getCurrentCalendarMonth() {
    const today = new Date();
    return `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}`;
}

function getQuoteSellerName(quote) {
    const storedName = String(quote?.vendedor_nombre || "").trim();
    if (storedName) return storedName;

    const seller = state.vendedores.find(item => String(item.id) === String(quote?.vendedor_id || ""));
    return seller?.nombre_completo || seller?.email || "No asignado";
}

function quoteMatchesSelectedSeller(quote, sellerId) {
    if (!sellerId) return true;
    if (String(quote?.vendedor_id || "") === String(sellerId)) return true;

    // Las cotizaciones importadas antes de vincular el UUID conservan el nombre
    // del vendedor del Excel. Se usa como respaldo para que sigan siendo filtrables.
    const seller = state.vendedores.find(item => String(item.id) === String(sellerId));
    const quoteSellerName = normalizeSearchText(quote?.vendedor_nombre).replace(/\s+/g, " ");
    const sellerName = normalizeSearchText(seller?.nombre_completo).replace(/\s+/g, " ");
    return Boolean(quoteSellerName && sellerName && (
        quoteSellerName === sellerName
        || quoteSellerName.includes(sellerName)
        || sellerName.includes(quoteSellerName)
    ));
}

function populateAdminAccessSellerFilter() {
    if (!DOM.adminAccessSeller) return;

    const selectedValue = DOM.adminAccessSeller.value;
    const sellers = state.vendedores
        .filter(seller => seller.rol === "vendedor")
        .sort((a, b) => String(a.nombre_completo || a.email).localeCompare(String(b.nombre_completo || b.email), "es"));

    DOM.adminAccessSeller.innerHTML = '<option value="">Todos los vendedores</option>';
    sellers.forEach(seller => {
        const option = document.createElement("option");
        option.value = seller.id;
        option.textContent = seller.nombre_completo || seller.email;
        DOM.adminAccessSeller.appendChild(option);
    });
    DOM.adminAccessSeller.value = sellers.some(seller => seller.id === selectedValue) ? selectedValue : "";
}

async function loadAdminAccessLog() {
    if (!DOM.adminTodayAccessLog || !state.user || !["admin", "gerente"].includes(state.user.rol)) return;

    if (DOM.adminAccessMonth && !DOM.adminAccessMonth.value) {
        DOM.adminAccessMonth.value = getCurrentCalendarMonth();
    }
    populateAdminAccessSellerFilter();

    const params = new URLSearchParams();
    if (DOM.adminAccessMonth?.value) params.set("month", DOM.adminAccessMonth.value);
    if (DOM.adminAccessSeller?.value) params.set("vendedor_id", DOM.adminAccessSeller.value);

    try {
        const accessLogRes = await apiRequest(`/api/auth/access-log?${params.toString()}`);
        renderAdminOperationalPanels(state.cotizaciones, accessLogRes.data || []);
    } catch (accessLogErr) {
        console.warn("No se pudo cargar la actividad de ingresos:", accessLogErr);
        renderAdminOperationalPanels(state.cotizaciones, []);
    }
}

function renderAdminOperationalPanels(quotes, accessLog) {
    const todayQuotes = quotes
        .filter(quote => isSameCalendarDay(parseLocalDate(quote.fecha_registro)))
        .sort((a, b) => String(b.numero_cotizacion || b.id || "").localeCompare(String(a.numero_cotizacion || a.id || "")))
        .slice(0, 6);

    if (DOM.adminTodayQuotes) {
        DOM.adminTodayQuotes.innerHTML = todayQuotes.length ? todayQuotes.map(quote => `
            <div class="admin-operational-row">
                <span class="admin-operational-icon quote"><i class="fa-regular fa-file-lines"></i></span>
                <div>
                    <strong>${escapeHTML(quote.cliente_nombre || "Cliente sin nombre")}</strong>
                    <span>${escapeHTML(quote.numero_cotizacion || "Sin folio")} · Vendedor: ${escapeHTML(getQuoteSellerName(quote))}</span>
                </div>
                <b>${formatSellerMoney(quote.total)}</b>
            </div>
        `).join("") : '<div class="admin-operational-empty">No hay cotizaciones registradas hoy.</div>';
    }

    if (DOM.adminTodayAccessLog) {
        DOM.adminTodayAccessLog.innerHTML = accessLog.length ? accessLog.map(record => `
            <div class="admin-operational-row">
                <span class="admin-operational-icon access"><i class="fa-solid fa-user-clock"></i></span>
                <div>
                    <strong>${escapeHTML(record.usuario || "Usuario")}</strong>
                    <span>${formatAccessDate(record.fecha_actividad || record.entrada)} · Entrada ${formatAccessTime(record.entrada)} · Salida ${formatAccessTime(record.salida)}</span>
                </div>
                <b class="admin-access-status ${record.salida ? "closed" : "open"}">${record.salida ? "Finalizó" : "Activo"}</b>
            </div>
        `).join("") : '<div class="admin-operational-empty">Aún no hay ingresos registrados hoy.</div>';
    }
}

function isQuoteAutoLostByAge(quote, refDate = new Date()) {
    if (quote.numero_factura) return false;
    const quoteDate = getQuoteDate(quote);
    if (!quoteDate) return false;
    const cutoff = new Date(refDate);
    cutoff.setHours(12, 0, 0, 0);
    cutoff.setMonth(cutoff.getMonth() - 3);
    return quoteDate <= cutoff;
}

function isQuoteLost(quote, refDate = new Date()) {
    if (isQuoteAutoLostByAge(quote, refDate)) return true;
    return String(quote.venta_perdida || "").toLowerCase() === "si";
}

function isQuoteExpired(quote, refDate = new Date()) {
    return !quote.numero_factura && (isQuoteLost(quote, refDate) || quoteAgeDays(quote, refDate) > 30);
}

function isPendingQuote(quote) {
    return !quote.numero_factura && !isQuoteExpired(quote);
}

function parseLostReason(quote) {
    if (!quote?.comentarios) return null;
    try {
        const data = JSON.parse(quote.comentarios);
        return data?.lost_reason || null;
    } catch {
        return null;
    }
}

function buildLostReasonComments(reason) {
    return JSON.stringify({
        lost_reason: {
            reasons: reason.reasons,
            justification: reason.justification,
            updated_at: new Date().toISOString()
        }
    });
}

function getLostReasons(reason) {
    if (!reason) return [];
    if (Array.isArray(reason.reasons)) return reason.reasons;
    return reason.reason ? [reason.reason] : [];
}

function hasLostReason(quote) {
    const reason = parseLostReason(quote);
    return getLostReasons(reason).length > 0 && !!reason?.justification;
}

const uploadMeta = {
    "inventario-abcf": {
        key: "crm_last_upload_inventario_abcf",
        label: () => DOM.lastUploadInventarioAbcf,
        wrapper: () => DOM.uploadInventarioAbcfWrapper
    },
    sobrepedidos: {
        key: "crm_last_upload_sobrepedidos",
        label: () => DOM.lastUploadSobrepedidos,
        wrapper: () => DOM.uploadSobrepedidosWrapper
    },
    promociones: {
        key: "crm_last_upload_promociones",
        label: () => DOM.lastUploadPromociones,
        wrapper: () => DOM.uploadPromocionesWrapper
    },
    cotizaciones: {
        key: "crm_last_upload_cotizaciones",
        label: () => DOM.lastUploadCotizaciones,
        wrapper: () => DOM.uploadCotizacionesWrapper
    }
};

function formatUploadTimestamp(value) {
    if (!value) return "Última actualización: sin registro";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "Última actualización: sin registro";
    return `Última actualización: ${date.toLocaleString("es-MX", {
        dateStyle: "short",
        timeStyle: "short"
    })}`;
}

function renderLastUploadLabels() {
    Object.entries(uploadMeta).forEach(([type, meta]) => {
        const label = meta.label();
        const sharedTimestamp = state.lastDataUpdates?.[type]?.actualizado_en;
        if (label) label.textContent = formatUploadTimestamp(sharedTimestamp || localStorage.getItem(meta.key));
    });

    if (DOM.kanbanDataUpdated) {
        const timestamp = state.lastDataUpdates?.cotizaciones?.actualizado_en || localStorage.getItem(uploadMeta.cotizaciones.key);
        DOM.kanbanDataUpdated.textContent = timestamp
            ? `Datos de cotizaciones actualizados: ${new Date(timestamp).toLocaleString("es-MX", { dateStyle: "short", timeStyle: "short" })}`
            : "Datos de cotizaciones: sin registro de actualización";
    }
}

async function loadLastUploadLabels() {
    if (!state.token) return;
    try {
        const result = await apiRequest("/api/v1/actualizaciones-datos/");
        state.lastDataUpdates = result.data || {};
    } catch (error) {
        console.warn("No se pudieron cargar las fechas de actualización:", error);
    }
    renderLastUploadLabels();
}

function markLastUpload(type) {
    const meta = uploadMeta[type];
    if (!meta) return;
    localStorage.setItem(meta.key, new Date().toISOString());
    renderLastUploadLabels();
}

function updateUploadControlsVisibility() {
    const canUpload = state.user && ["admin", "gerente"].includes(state.user.rol);
    Object.values(uploadMeta).forEach(meta => {
        const wrapper = meta.wrapper();
        if (wrapper) wrapper.classList.toggle("hidden", !canUpload);
    });
    const canFilterBySeller = state.user && ["admin", "gerente"].includes(state.user.rol);
    // Vendedores-padre (con hijos) también pueden filtrar por vendedor
    const vendedorTieneHijos = state.user && state.user.rol === "vendedor"
        && Array.isArray(state.user.vendedores_hijos) && state.user.vendedores_hijos.length > 0;
    const showVendedorFilter = canFilterBySeller || vendedorTieneHijos;

    if (DOM.filterSobrepedidosVendedorWrapper) {
        DOM.filterSobrepedidosVendedorWrapper.classList.toggle("hidden", !showVendedorFilter);
    }
    if (!showVendedorFilter && DOM.filterSobrepedidosVendedor) {
        DOM.filterSobrepedidosVendedor.value = "todos";
    }
    if (DOM.filterPorEntregarVendedorWrapper) {
        DOM.filterPorEntregarVendedorWrapper.classList.toggle("hidden", !showVendedorFilter);
    }
    if (!showVendedorFilter && DOM.filterPorEntregarVendedor) {
        DOM.filterPorEntregarVendedor.value = "todos";
    }
}

function buildProductImageSearchUrl(product) {
    const parts = [
        product.codigo_material,
        product.descripcion_material,
        product.proveedor
    ].filter(Boolean);
    const query = parts.join(" ");
    return `https://www.google.com/search?tbm=isch&q=${encodeURIComponent(query)}`;
}

function getInventoryProductKey(item) {
    const candidates = [item?.codigo_material, item?.almacen];
    const key = candidates.find(value => {
        const normalized = String(value ?? "").trim();
        return normalized && normalized !== "0" && normalized !== "0.0";
    });
    return key ? String(key).trim() : "";
}

function getInventoryDCode(item) {
    const value = item?.abc_f || item?.abc;
    return value === null || value === undefined ? "" : String(value).trim();
}

function isLegacyMisalignedInventory(item) {
    return getInventoryProductKey(item) === String(item?.almacen || "").trim()
        && ["0", "0.0", ""].includes(String(item?.codigo_material ?? "").trim())
        && ["0", "0.0", ""].includes(String(item?.descripcion_material ?? "").trim());
}

function getInventoryProviderName(item) {
    return isLegacyMisalignedInventory(item)
        ? (item.numero_proveedor || "")
        : (item.nombre_proveedor || "");
}

function getInventoryDescription(item) {
    return isLegacyMisalignedInventory(item)
        ? (item.nombre_proveedor || "")
        : (item.descripcion_material || "");
}

function getInventoryWarehouse(item) {
    return isLegacyMisalignedInventory(item) ? "" : (item.almacen || "");
}

function getDaysLeftInMonth() {
    const today = new Date();
    const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0).getDate();
    return Math.max(0, lastDay - today.getDate());
}

function parseLocalDate(dateValue) {
    if (!dateValue) return null;
    if (dateValue instanceof Date) return new Date(dateValue);

    const value = String(dateValue).trim();
    const dateOnly = value.split("T")[0].split(" ")[0];
    const isoMatch = dateOnly.match(/^(\d{4})[-\/](\d{2})[-\/](\d{2})$/);
    const localMatch = dateOnly.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);

    if (isoMatch) {
        return new Date(Number(isoMatch[1]), Number(isoMatch[2]) - 1, Number(isoMatch[3]), 12);
    }
    if (localMatch) {
        return new Date(Number(localMatch[3]), Number(localMatch[2]) - 1, Number(localMatch[1]), 12);
    }

    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function isQuoteDateInRange(quote, startDate, endDate) {
    const quoteDate = parseLocalDate(quote.fecha_registro);
    const start = parseLocalDate(startDate);
    const end = parseLocalDate(endDate);
    if (!quoteDate) return !start && !end;

    if (start && quoteDate < start) return false;
    if (end) {
        end.setHours(23, 59, 59, 999);
        if (quoteDate > end) return false;
    }
    return true;
}

function getSellerGoalPeriodConfig(period) {
    const today = new Date();
    const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
    const endOfMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0);

    if (period === "day") {
        return {
            label: "diaria",
            start: new Date(today.getFullYear(), today.getMonth(), today.getDate()),
            end: new Date(today.getFullYear(), today.getMonth(), today.getDate(), 23, 59, 59, 999),
            targetFactor: 1 / endOfMonth.getDate(),
            remainingLabel: "Hoy",
        };
    }

    if (period === "week") {
        const dayOfWeek = today.getDay() || 7;
        const start = new Date(today.getFullYear(), today.getMonth(), today.getDate() - dayOfWeek + 1);
        const end = new Date(today.getFullYear(), today.getMonth(), today.getDate() + (7 - dayOfWeek), 23, 59, 59, 999);
        return {
            label: "semanal",
            start,
            end,
            targetFactor: 7 / endOfMonth.getDate(),
            remainingLabel: `${Math.max(0, 7 - dayOfWeek)} dias restantes`,
        };
    }

    return {
        label: "mensual",
        start: startOfMonth,
        end: new Date(today.getFullYear(), today.getMonth() + 1, 0, 23, 59, 59, 999),
        targetFactor: 1,
        remainingLabel: `${getDaysLeftInMonth()} dias restantes`,
    };
}

function getCurrentMonthlyGoal(metas) {
    const today = new Date();
    const monthlyMeta = metas
        .filter(meta => meta.descripcion === "Meta mensual comercial")
        .find(meta => {
            const start = parseLocalDate(meta.fecha_inicio);
            const end = parseLocalDate(meta.fecha_limite);
            return start && end && start <= today && end >= today;
        });

    // Conserva las metas activas creadas antes de esta mejora, sin fabricar un monto de respaldo.
    const activeMeta = monthlyMeta || metas
        .filter(meta => meta.estado !== "completada")
        .find(meta => {
            const start = parseLocalDate(meta.fecha_inicio);
            const end = parseLocalDate(meta.fecha_limite);
            return start && end && start <= today && end >= today;
        });
    return Number(activeMeta?.monto_objetivo || 0);
}

function getInvoiceAmount(quote) {
    const invoiceAmount = Number(quote.importe_facturado);
    return Number.isFinite(invoiceAmount) && invoiceAmount > 0 ? invoiceAmount : Number(quote.total || 0);
}

function getQuoteAgeDays(quote) {
    if (!quote.fecha_registro) return 999;
    const quoteDate = new Date(`${quote.fecha_registro}T12:00:00Z`);
    const refDate = new Date();
    const ageDays = Math.floor((refDate - quoteDate) / (1000 * 60 * 60 * 24));
    return Math.max(0, ageDays);
}

function getInitials(name) {
    return (name || "JP")
        .split(/\s+/)
        .filter(Boolean)
        .slice(0, 2)
        .map(part => part[0])
        .join("")
        .toUpperCase();
}

function filterSellerDashboardItems(items, search) {
    if (!search) return items;
    const needle = search.toLowerCase();
    return items.filter(item => JSON.stringify(item).toLowerCase().includes(needle));
}

function renderEmptySellerCard(container, message) {
    if (!container) return;
    container.innerHTML = `<div class="seller-empty-state">${escapeHTML(message)}</div>`;
}

function renderSellerPendingQuotes(quotes, search) {
    const pending = filterSellerDashboardItems(
        quotes.filter(isPendingQuote).sort((a, b) => quoteAgeDays(b) - quoteAgeDays(a)),
        search
    );

    if (DOM.sellerPendingCount) DOM.sellerPendingCount.textContent = pending.length;
    if (!DOM.sellerPendingList) return;
    DOM.sellerPendingList.innerHTML = "";

    if (pending.length === 0) {
        renderEmptySellerCard(DOM.sellerPendingList, "No hay cotizaciones pendientes con ese criterio.");
        return;
    }

    pending.slice(0, 2).forEach((quote, index) => {
        const age = quoteAgeDays(quote);
        const remaining = Math.max(0, 30 - age);
        const urgent = remaining <= 1 || age >= 30;
        const card = document.createElement("div");
        card.className = `seller-quote-card ${urgent ? "danger" : index === 1 ? "warning" : ""}`;
        card.innerHTML = `
            <span>${escapeHTML(quote.cliente_nombre || "Cliente")}</span>
            <strong>${urgent ? "VENCE HOY" : `En ${remaining} dias`}</strong>
            <small>${formatSellerMoney(quote.total)} cotizados</small>
            <button data-seller-jump="cotizaciones">${urgent ? "Aprobar y enviar" : "Revisar"} <i class="fa-regular fa-file-lines"></i></button>
        `;
        DOM.sellerPendingList.appendChild(card);
    });
}

function renderSellerFollowups(quotes, plan, logToday, search) {
    const followups = filterSellerDashboardItems(
        quotes.filter(isPendingQuote).sort((a, b) => quoteAgeDays(b) - quoteAgeDays(a)),
        search
    );
    const count = followups.length;
    if (DOM.sellerFollowupAlert) DOM.sellerFollowupAlert.textContent = `RED ${Math.min(count, 9)}`;
    if (!DOM.sellerFollowupList) return;
    DOM.sellerFollowupList.innerHTML = "";

    if (followups.length === 0) {
        const activities = plan?.activities_config || [];
        if (activities.length === 0) {
            renderEmptySellerCard(DOM.sellerFollowupList, "Configura tu plan en La Ventaja para ver acciones diarias.");
            return;
        }
        const completed = logToday?.completed_activities || {};
        activities.slice(0, 2).forEach(activity => {
            const done = completed[activity.activity] || 0;
            const hasProgress = done > 0;
            const item = document.createElement("div");
            item.className = "seller-follow-card";
            item.innerHTML = `
                <div style="display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: 14px;">
                    <div>
                        <strong>${escapeHTML(activity.activity)}</strong>
                        <span>${hasProgress ? "Completadas hoy" : "Pendiente por registrar"}</span>
                    </div>
                    <div style="min-width: 78px; padding: 9px 11px; border-radius: 8px; text-align: center; background: ${hasProgress ? "rgba(34, 197, 94, 0.14)" : "rgba(148, 163, 184, 0.10)"}; border: 1px solid ${hasProgress ? "rgba(34, 197, 94, 0.35)" : "rgba(148, 163, 184, 0.20)"};">
                        <strong style="display: block; margin: 0; color: ${hasProgress ? "#4ade80" : "hsl(var(--text-secondary))"}; font-size: 34px; line-height: 0.9;">${done}</strong>
                        <small style="display: block; margin-top: 4px; color: ${hasProgress ? "#86efac" : "hsl(var(--text-secondary))"}; font-size: 10px; font-weight: 800; text-transform: uppercase;">hoy</small>
                    </div>
                </div>
                <button class="call" style="width: 100%; margin-top: 10px;" data-seller-jump="slight-edge"><i class="fa-solid fa-check"></i> Registrar</button>
            `;
            DOM.sellerFollowupList.appendChild(item);
        });
        return;
    }

    followups.slice(0, 2).forEach(quote => {
        const age = quoteAgeDays(quote);
        const phone = quote.datos_contacto?.contacto_preferente || quote.datos_contacto?.celular || quote.datos_contacto?.telefono || "";
        const item = document.createElement("div");
        item.className = "seller-follow-card";
        item.innerHTML = `
            <div>
                <strong>${escapeHTML(quote.cliente_nombre || "Cliente")}</strong>
                <span>Llamar para confirmar precio</span>
                <small>Ultimo contacto: hace ${age} dias</small>
            </div>
            <div class="seller-follow-actions">
                <a class="call" href="${phone ? `tel:${escapeHTML(phone)}` : "#"}"><i class="fa-solid fa-phone"></i> Llamar</a>
                <a class="whatsapp" href="${phone ? `https://wa.me/${escapeHTML(String(phone).replace(/\D/g, ""))}` : "#"}" target="_blank" rel="noopener"><i class="fa-brands fa-whatsapp"></i> WhatsApp</a>
            </div>
        `;
        DOM.sellerFollowupList.appendChild(item);
    });
}

function renderSellerPromos(promociones, search) {
    const today = new Date();
    const activePromos = filterSellerDashboardItems(
        promociones.filter(p => !p.valido_hasta || new Date(p.valido_hasta) >= today),
        search
    );

    if (!DOM.sellerPromoList) return;
    DOM.sellerPromoList.innerHTML = "";

    if (activePromos.length === 0) {
        renderEmptySellerCard(DOM.sellerPromoList, "No hay promociones activas con ese criterio.");
        return;
    }

    activePromos.slice(0, 2).forEach((promo, index) => {
        const validDate = promo.valido_hasta ? new Date(promo.valido_hasta).toLocaleDateString("es-MX", { day: "numeric", month: "short" }) : "vigencia abierta";
        const badge = promo.margen_promocion ? `${Math.round(Math.abs(promo.margen_promocion))}% OFF` : (index === 0 ? "Promo" : "2x1");
        const item = document.createElement("div");
        item.className = "seller-promo-card";
        item.innerHTML = `
            <div class="seller-promo-thumb"><i class="fa-solid ${index === 0 ? "fa-box-open" : "fa-faucet-drip"}"></i></div>
            <div>
                <strong>${escapeHTML(badge)}</strong>
                <span>${escapeHTML(promo.descripcion_material || promo.codigo_material || "Producto en promocion")}</span>
                <small>Vence ${escapeHTML(validDate)}</small>
            </div>
            <button data-seller-jump="cotizaciones">Añadir</button>
        `;
        DOM.sellerPromoList.appendChild(item);
    });
}

function renderSellerDashboardInsights(quotes, period, periodGoal, invoicedTotal, percent, logToday) {
    if (DOM.sellerPerformancePeriod) {
        DOM.sellerPerformancePeriod.textContent = state.sellerGoalPeriod === "week" ? "Semanal" : state.sellerGoalPeriod === "day" ? "Diario" : "Mensual";
    }
    if (DOM.sellerPerformanceAmount) DOM.sellerPerformanceAmount.textContent = formatSellerMoney(invoicedTotal);
    if (DOM.sellerPerformanceGoal) DOM.sellerPerformanceGoal.textContent = `de ${formatSellerMoney(periodGoal)}`;
    if (DOM.sellerMiniProgress) DOM.sellerMiniProgress.style.setProperty("--progress", percent);
    if (DOM.sellerMiniProgressPercent) DOM.sellerMiniProgressPercent.textContent = `${percent}%`;

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

    if (!DOM.sellerRecentActivity) return;
    const activities = [];
    Object.entries(logToday?.completed_activities || {}).forEach(([name, count]) => {
        if (Number(count) > 0) activities.push({ icon: "fa-check", tone: "green", title: `${count} ${escapeHTML(name)}`, detail: "Registrado hoy" });
    });
    const latestInvoice = quotes.filter(q => q.numero_factura).sort((a, b) => (parseLocalDate(b.fecha_factura || b.fecha_registro) || 0) - (parseLocalDate(a.fecha_factura || a.fecha_registro) || 0))[0];
    if (latestInvoice) activities.push({ icon: "fa-file-invoice-dollar", tone: "violet", title: "Cotización facturada", detail: `${escapeHTML(latestInvoice.cliente_nombre || "Cliente")} · ${formatSellerMoney(getInvoiceAmount(latestInvoice))}` });
    const nextFollowup = quotes.filter(isPendingQuote).sort((a, b) => quoteAgeDays(b) - quoteAgeDays(a))[0];
    if (nextFollowup) activities.push({ icon: "fa-phone", tone: "blue", title: "Seguimiento pendiente", detail: escapeHTML(nextFollowup.cliente_nombre || "Cliente") });

    if (activities.length === 0) {
        DOM.sellerRecentActivity.innerHTML = '<div class="seller-activity-empty">Aún no hay actividad registrada en este periodo.</div>';
        return;
    }
    DOM.sellerRecentActivity.innerHTML = activities.slice(0, 3).map(activity => `
        <div class="seller-activity-item">
            <span class="seller-activity-icon ${activity.tone}"><i class="fa-solid ${activity.icon}"></i></span>
            <div><strong>${activity.title}</strong><span>${activity.detail}</span></div>
            <i class="fa-solid fa-chevron-right"></i>
        </div>
    `).join("");
}

async function renderSellerHomeDashboard({ metas, quotes, promociones, goalProgress = null }) {
    const search = DOM.sellerDashboardSearch ? DOM.sellerDashboardSearch.value.trim() : "";
    const sellerName = state.user.nombre_completo || state.user.email || "Vendedor";
    const period = getSellerGoalPeriodConfig(state.sellerGoalPeriod);
    const monthlyGoal = getCurrentMonthlyGoal(metas);
    const fallbackPeriodGoal = monthlyGoal * period.targetFactor;
    const fallbackInvoicedTotal = quotes
        .filter(q => q.numero_factura)
        .filter(q => {
            // El periodo comercial se determina por la fecha de la cotización;
            // la factura solamente confirma que su importe sí cuenta como venta.
            const quoteDate = parseLocalDate(q.fecha_registro || q.fecha_factura);
            return quoteDate && quoteDate >= period.start && quoteDate <= period.end;
        })
        .reduce((sum, q) => sum + getInvoiceAmount(q), 0);
    // La API calcula el avance sobre el universo autorizado, no sobre la muestra
    // ligera de cotizaciones que usa el panel para tarjetas operativas.
    const periodGoal = Number(goalProgress?.meta ?? fallbackPeriodGoal);
    const invoicedTotal = Number(goalProgress?.venta_facturada ?? fallbackInvoicedTotal);
    const percent = periodGoal > 0 ? Math.min(100, Math.round((invoicedTotal / periodGoal) * 100)) : 0;
    const remaining = Math.max(0, periodGoal - invoicedTotal);

    if (DOM.sellerDashboardInitials) DOM.sellerDashboardInitials.textContent = getInitials(sellerName);
    if (DOM.sellerMonthlyProgressRing) DOM.sellerMonthlyProgressRing.style.setProperty("--progress", percent);
    if (DOM.sellerMonthlyProgressPercent) DOM.sellerMonthlyProgressPercent.textContent = `${percent}%`;
    if (DOM.sellerMonthlyGoalLabel) DOM.sellerMonthlyGoalLabel.textContent = `Meta ${period.label}: ${formatSellerMoney(periodGoal)}`;
    if (DOM.sellerMonthlyCurrent) DOM.sellerMonthlyCurrent.textContent = `${formatSellerMoney(invoicedTotal)} (${percent}%)`;
    if (DOM.sellerMonthlyRemaining) DOM.sellerMonthlyRemaining.textContent = `Faltan: ${formatSellerMoney(remaining)}`;
    if (DOM.sellerMonthlyDaysLeft) DOM.sellerMonthlyDaysLeft.textContent = period.remainingLabel;
    DOM.sellerPeriodButtons.forEach(button => {
        button.classList.toggle("active", button.dataset.sellerPeriod === state.sellerGoalPeriod);
    });

    let plan = null;
    let logToday = null;
    try {
        const planRes = await apiRequest(`/api/slight-edge/plan/${state.user.id}`);
        plan = planRes.data || null;
        const todayStr = new Date().toISOString().split("T")[0];
        const logRes = await apiRequest(`/api/slight-edge/log/${state.user.id}?date_str=${todayStr}`);
        logToday = logRes.data || null;
    } catch (err) {
        console.warn("No se pudo cargar La Ventaja para el panel vendedor:", err);
    }

    renderSellerPendingQuotes(quotes, search);
    renderSellerFollowups(quotes, plan, logToday, search);
    renderSellerPromos(promociones, search);
    renderSellerDashboardInsights(quotes, period, periodGoal, invoicedTotal, percent, logToday);
    await loadAndRenderSellerAnalytics();
}

function renderSellerChannelMetrics(canales) {
    if (!DOM.sellerChannelBars) return;
    if (!canales || canales.length === 0) {
        DOM.sellerChannelBars.innerHTML = '<div class="seller-empty-row">No hay ventas registradas por canal en este periodo.</div>';
        return;
    }
    DOM.sellerChannelBars.innerHTML = canales.map(c => `
        <div class="seller-channel-row">
            <span class="seller-channel-label">
                <span class="seller-channel-dot" style="background-color: ${c.color || '#6366f1'};"></span>
                ${escapeHTML(c.canal)}
            </span>
            <div class="seller-channel-bar-wrap">
                <div class="seller-channel-bar-fill" style="width: ${Math.min(100, Math.max(0, c.porcentaje))}%; background-color: ${c.color || '#6366f1'};"></div>
            </div>
            <div class="seller-channel-values">
                <span class="seller-channel-amount">${formatSellerMoney(c.monto)}</span>
                <span class="seller-channel-pct">${Number(c.porcentaje || 0).toFixed(1)}%</span>
            </div>
        </div>
    `).join("");
}

function renderSellerTopClientsMetrics(clientes) {
    if (!DOM.sellerTopClientsTable) return;
    if (!clientes || clientes.length === 0) {
        DOM.sellerTopClientsTable.innerHTML = '<tr><td colspan="4" class="seller-empty-row">No hay clientes con compras en este periodo.</td></tr>';
        return;
    }
    DOM.sellerTopClientsTable.innerHTML = clientes.map(c => `
        <tr>
            <td><strong>${escapeHTML(c.cliente)}</strong></td>
            <td style="text-align: right; font-weight: 600; color: #0f172a;">${formatSellerMoney(c.venta)}</td>
            <td style="text-align: center; color: #64748b; font-weight: 600;">${Number(c.porcentaje || 0).toFixed(1)}%</td>
            <td><span class="badge" style="background: #f1f5f9; color: #475569; font-weight: 500; padding: 4px 9px; border-radius: 6px; font-size: 12px;">${escapeHTML(c.material_principal || "General")}</span></td>
        </tr>
    `).join("");
}

function renderSellerTopMaterialsMetrics(materiales) {
    if (!DOM.sellerTopMaterialsTable) return;
    if (!materiales || materiales.length === 0) {
        DOM.sellerTopMaterialsTable.innerHTML = '<tr><td colspan="4" class="seller-empty-row">No hay materiales vendidos en este periodo.</td></tr>';
        return;
    }
    DOM.sellerTopMaterialsTable.innerHTML = materiales.map(m => `
        <tr>
            <td><strong>${escapeHTML(m.material)}</strong></td>
            <td><span style="color: #64748b; font-weight: 500;">${escapeHTML(m.grupo || "General")}</span></td>
            <td style="text-align: center; font-weight: 600; color: #334155;">${Number(m.unidades || 0).toLocaleString('es-MX')}</td>
            <td style="text-align: right; font-weight: 700; color: #0f172a;">${formatSellerMoney(m.monto)}</td>
        </tr>
    `).join("");
}

async function loadAndRenderSellerAnalytics() {
    if (state.user?.rol !== "vendedor") return;
    try {
        const periodParam = state.sellerGoalPeriod === "day" ? "dia" : state.sellerGoalPeriod === "week" ? "semana" : "mes";
        const res = await apiRequest(`/api/v1/analitica/vendedor/metricas?periodo=${periodParam}`);
        const data = res.data || {};
        renderSellerChannelMetrics(data.canales || []);
        renderSellerTopClientsMetrics(data.clientes || []);
        renderSellerTopMaterialsMetrics(data.materiales || []);
    } catch (err) {
        console.warn("No se pudieron cargar las analíticas del vendedor:", err);
    }
}

async function loadVendedoresData() {
    if (state.user.rol === "vendedor") return;
    
    // Fetch sellers and their current goals so the manager can edit the commercial quota.
    const monthDate = metasMonthAsDate();
    const [res, metasRes, commGoalsRes] = await Promise.all([
        apiRequest("/api/v1/vendedores/?limit=100"),
        apiRequest("/api/v1/metas/?limit=100"),
        apiRequest(`/api/v1/metas/comerciales?mes=${encodeURIComponent(monthDate)}`).catch(() => ({ data: [] })),
    ]);
    const sellers = res.data || [];
    state.vendedores = sellers;
    state.metas = metasRes.data || [];
    const commGoals = commGoalsRes.data || [];
    
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
        const commGoal = commGoals.find(g => g.tipo === "vendedor" && String(g.vendedor_id) === String(v.id));
        v.monthlyGoal = commGoal ? Number(commGoal.monto_objetivo) : getCurrentMonthlyGoal(state.metas.filter(meta => String(meta.vendedor_id) === String(v.id)));
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
                    <button class="btn btn-secondary btn-sm edit-seller-btn" data-id="${v.id}" data-email="${escapeHTML(v.email)}" data-fullname="${escapeHTML(v.nombre_completo) || ''}" data-role="${v.rol}" data-phone="${v.telefono_whatsapp || ''}" data-code="${v.codigo_vendedor || ''}" data-parent="${v.vendedor_padre_id || ''}" data-monthly-goal="${v.monthlyGoal || ''}">
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
            const parent = targetBtn.getAttribute("data-parent");
            const monthlyGoal = targetBtn.getAttribute("data-monthly-goal");
            console.log("Edit attributes found:", { id, email, fullname, role, phone, code, parent, monthlyGoal });
            openEditUserForm(id, email, fullname, role, phone, code, parent, monthlyGoal);
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


async function loadInventarioAbcfData(forceRefresh = false) {
    const searchTerm = DOM.filterInvSearch ? DOM.filterInvSearch.value.toLowerCase() : "";
    const sucursalFilter = DOM.filterInvSucursal ? DOM.filterInvSucursal.value : "todos";
    const abcfFilter = DOM.filterInvAbcf ? DOM.filterInvAbcf.value : "todos";
    const proveedorFilter = DOM.filterInvProveedor ? DOM.filterInvProveedor.value : "todos";
    
    try {
        if (forceRefresh || !state.inventario_abcf || state.inventario_abcf.length === 0) {
            const res = await apiRequest("/api/v1/inventario-abcf/");
            state.inventario_abcf = res.data || [];
        }
        
        let inventario = [...state.inventario_abcf];

        // --- KPI CARDS: Top 3 Categories & Top 3 Providers (based on full dataset, before filters) ---
        // Only rebuild KPI cards once (when no filter is active or on force refresh)
        if (DOM.invKpiCategorias && DOM.invKpiProveedores) {
            const allItems = state.inventario_abcf;

            // Build category map
            const catMap = {};
            allItems.forEach(i => {
                const cat = i.descrip_gpo_materiales || "Sin Categoría";
                if (!catMap[cat]) catMap[cat] = { count: 0, stock: 0 };
                catMap[cat].count++;
                catMap[cat].stock += (i.cantidad_propia || 0);
            });
            const topCats = Object.entries(catMap)
                .sort((a, b) => b[1].stock - a[1].stock)
                .slice(0, 3);

            // Build provider map
            const provMap = {};
            allItems.forEach(i => {
                const prov = getInventoryProviderName(i) || "Sin Proveedor";
                if (!provMap[prov]) provMap[prov] = { count: 0, stock: 0 };
                provMap[prov].count++;
                provMap[prov].stock += (i.cantidad_propia || 0);
            });
            const topProvs = Object.entries(provMap)
                .sort((a, b) => b[1].stock - a[1].stock)
                .slice(0, 3);

            const catColors = ['#3b82f6', '#10b981', '#8b5cf6'];
            const catBgs = ['rgba(59,130,246,0.15)', 'rgba(16,185,129,0.15)', 'rgba(139,92,246,0.15)'];
            const provColors = ['#ef4444', '#ef4444', '#ef4444'];
            const provBgs = ['rgba(239,68,68,0.15)', 'rgba(239,68,68,0.15)', 'rgba(239,68,68,0.15)'];

            DOM.invKpiCategorias.innerHTML = topCats.map(([name, data], i) => `
                <div class="kpi-card kpi-card-white animate-fade-in" style="animation-delay: ${i * 0.1}s; border-radius: 12px; border: none; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border-left: 5px solid ${catColors[i]}; background: white; cursor: pointer; transition: all 0.2s ease;"
                    onmouseover="this.style.transform='translateY(-3px)'; this.style.boxShadow='0 6px 20px rgba(0,0,0,0.1)';"
                    onmouseout="this.style.transform='none'; this.style.boxShadow='0 4px 12px rgba(0,0,0,0.05)';"
                    onclick="(function(){
                        const sel = document.getElementById('filter-inv-search');
                        if(sel){ sel.value = '${escapeHTML(name).replace(/'/g, "\\'").replace(/"/g, '&quot;')}'; sel.dispatchEvent(new Event('input')); }
                    })()" title="Filtrar por ${escapeHTML(name)}">
                    <div class="kpi-icon" style="background: ${catBgs[i]}; color: ${catColors[i]}; font-size: 1.2rem; border-radius: 12px;">
                        <i class="fa-solid fa-layer-group"></i>
                    </div>
                    <div class="kpi-data" style="width: calc(100% - 60px);">
                        <h3 style="font-size: 13px; font-weight: 700; color: #333; text-transform: none; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 4px;" title="${escapeHTML(name)}">${escapeHTML(name)}</h3>
                        <p style="font-size: 20px; font-weight: 800; color: ${catColors[i]}; margin-bottom: 2px;">${data.stock.toLocaleString('es-MX')} <span style="font-size: 12px; color: #6b7280; font-weight: 600;">piezas</span></p>
                        <span style="font-size: 11px; color: #6b7280; font-weight: 600;"><i class="fa-solid fa-box"></i> ${data.count} productos</span>
                    </div>
                </div>`).join('');

            DOM.invKpiProveedores.innerHTML = topProvs.map(([name, data], i) => `
                <div class="kpi-card kpi-card-white animate-fade-in" style="animation-delay: ${(i + 3) * 0.1}s; border-radius: 12px; border: none; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border-left: 5px solid ${provColors[i]}; background: white; cursor: pointer; transition: all 0.2s ease;"
                    onmouseover="this.style.transform='translateY(-3px)'; this.style.boxShadow='0 6px 20px rgba(0,0,0,0.1)';"
                    onmouseout="this.style.transform='none'; this.style.boxShadow='0 4px 12px rgba(0,0,0,0.05)';"
                    onclick="(function(){
                        const sel = document.getElementById('filter-inv-proveedor');
                        if(sel){ sel.value = '${escapeHTML(name).replace(/'/g, "\\'").replace(/"/g, '&quot;')}'; sel.dispatchEvent(new Event('change')); }
                    })()" title="Filtrar por ${escapeHTML(name)}">
                    <div class="kpi-icon" style="background: ${provBgs[i]}; color: ${provColors[i]}; font-size: 1.2rem; border-radius: 12px;">
                        <i class="fa-solid fa-truck"></i>
                    </div>
                    <div class="kpi-data" style="width: calc(100% - 60px);">
                        <h3 style="font-size: 13px; font-weight: 700; color: #333; text-transform: none; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 4px;" title="${escapeHTML(name)}">${escapeHTML(name)}</h3>
                        <p style="font-size: 20px; font-weight: 800; color: ${provColors[i]}; margin-bottom: 2px;">${data.stock.toLocaleString('es-MX')} <span style="font-size: 12px; color: #6b7280; font-weight: 600;">piezas</span></p>
                        <span style="font-size: 11px; color: #6b7280; font-weight: 600;"><i class="fa-solid fa-box"></i> ${data.count} productos</span>
                    </div>
                </div>`).join('');
        }
        // ----------------------------------------------------------

        // Populate Selects if empty
        if (DOM.filterInvSucursal && DOM.filterInvSucursal.options.length <= 1) {
            const currentSuc = DOM.filterInvSucursal.value;
            DOM.filterInvSucursal.innerHTML = '<option value="todos">Todos</option>';
            const sucursales = [...new Set(inventario.map(i => i.nombre_centro).filter(Boolean))].sort();
            sucursales.forEach(s => {
                const opt = document.createElement("option");
                opt.value = s;
                opt.textContent = s;
                DOM.filterInvSucursal.appendChild(opt);
            });
            DOM.filterInvSucursal.value = currentSuc;
        }

        if (DOM.filterInvAbcf && DOM.filterInvAbcf.options.length <= 1) {
            const currentAbcf = DOM.filterInvAbcf.value;
            DOM.filterInvAbcf.innerHTML = '<option value="todos">Todos</option>';
            const abcfs = [...new Set(inventario.map(getInventoryDCode).filter(Boolean))].sort();
            abcfs.forEach(a => {
                const opt = document.createElement("option");
                opt.value = a;
                opt.textContent = a;
                DOM.filterInvAbcf.appendChild(opt);
            });
            DOM.filterInvAbcf.value = currentAbcf;
        }

        if (DOM.filterInvProveedor && DOM.filterInvProveedor.options.length <= 1) {
            const currentProv = DOM.filterInvProveedor.value;
            DOM.filterInvProveedor.innerHTML = '<option value="todos">Todos</option>';
            const proveedores = [...new Set(inventario.map(getInventoryProviderName).filter(Boolean))].sort();
            proveedores.forEach(p => {
                const opt = document.createElement("option");
                opt.value = p;
                opt.textContent = p;
                DOM.filterInvProveedor.appendChild(opt);
            });
            DOM.filterInvProveedor.value = currentProv;
        }

        if (DOM.filterInvFamilia) {
            const currentFam = DOM.filterInvFamilia.value || "todos";
            DOM.filterInvFamilia.innerHTML = '<option value="todos">Todas</option>';
            KURODA_FAMILIALES.forEach(f => {
                const opt = document.createElement("option");
                opt.value = f;
                opt.textContent = f;
                DOM.filterInvFamilia.appendChild(opt);
            });
            DOM.filterInvFamilia.value = currentFam;
        }

        if (DOM.filterInvSubfamilia) {
            const currentSub = DOM.filterInvSubfamilia.value;
            const selectedFam = DOM.filterInvFamilia ? DOM.filterInvFamilia.value : "todos";
            DOM.filterInvSubfamilia.innerHTML = '<option value="todas">Todas</option>';
            let subList = [];
            if (selectedFam !== "todos" && KURODA_SUBFAMILIAS_MAP[selectedFam]) {
                subList = KURODA_SUBFAMILIAS_MAP[selectedFam];
            } else {
                let allSubs = [];
                Object.values(KURODA_SUBFAMILIAS_MAP).forEach(l => allSubs = allSubs.concat(l));
                subList = [...new Set(allSubs)].sort();
            }
            subList.forEach(sf => {
                const opt = document.createElement("option");
                opt.value = sf;
                opt.textContent = sf;
                DOM.filterInvSubfamilia.appendChild(opt);
            });
            DOM.filterInvSubfamilia.value = subList.includes(currentSub) ? currentSub : "todas";
        }

        // Apply filters
        const familiaFilter = DOM.filterInvFamilia ? DOM.filterInvFamilia.value : "todos";
        const subfamiliaFilter = DOM.filterInvSubfamilia ? DOM.filterInvSubfamilia.value : "todas";

        if (sucursalFilter !== "todos") {
            inventario = inventario.filter(i => i.nombre_centro === sucursalFilter);
        }
        if (abcfFilter !== "todos") {
            inventario = inventario.filter(i => getInventoryDCode(i) === abcfFilter);
        }
        if (proveedorFilter !== "todos") {
            inventario = inventario.filter(i => getInventoryProviderName(i) === proveedorFilter);
        }
        if (familiaFilter !== "todos") {
            inventario = inventario.filter(i => i.familia === familiaFilter);
        }
        if (subfamiliaFilter !== "todas") {
            inventario = inventario.filter(i => (i.subfamilia || i.descrip_gpo_materiales) === subfamiliaFilter);
        }
        if (searchTerm) {
            inventario = inventario.filter(i => {
                const searchableFields = [
                    getInventoryProductKey(i),
                    getInventoryDescription(i),
                    getInventoryProviderName(i),
                    i.numero_proveedor,
                    i.codigo_anterior_material,
                    i.grupo_materiales,
                    i.descrip_gpo_materiales
                ];
                
                return searchableFields.some(value =>
                    value && String(value).toLowerCase().includes(searchTerm)
                );
            });
        }
        const canViewCosts = state.user && (state.user.rol === "gerente" || state.user.rol === "admin");
        
        DOM.tableInventarioAbcf.innerHTML = "";
        if (inventario.length === 0) {
            DOM.tableInventarioAbcf.innerHTML = `<tr><td colspan="12" style="text-align: center;">No se encontraron registros de inventario.</td></tr>`;
            return;
        }
        
        const thPrecio = document.getElementById("th-inv-precio");
        const thImporte = document.getElementById("th-inv-importe");
        if (thPrecio) thPrecio.style.display = "";
        if (thImporte) thImporte.style.display = "";
        
        // --- SORTING LOGIC ---
        if (state.invSortField === undefined) state.invSortField = null;
        if (state.invSortDir === undefined) state.invSortDir = 'desc';
        if (state.invCurrentPage === undefined) state.invCurrentPage = 1;

        if (state.invSortField === 'cant_propia') {
            inventario.sort((a, b) => {
                const va = a.cantidad_propia || 0;
                const vb = b.cantidad_propia || 0;
                return state.invSortDir === 'asc' ? va - vb : vb - va;
            });
        } else if (state.invSortField === 'inv_consig') {
            inventario.sort((a, b) => {
                const va = a.existencia_consignacion || 0;
                const vb = b.existencia_consignacion || 0;
                return state.invSortDir === 'asc' ? va - vb : vb - va;
            });
        }

        // --- PAGINATION LOGIC ---
        const totalItems = inventario.length;
        const pag = createPaginationControls('invCurrentPage', totalItems, loadInventarioAbcfData, 25);
        const pageItems = inventario.slice(pag.startIndex, pag.endIndex);
        
        pageItems.forEach(i => {
            const tr = document.createElement("tr");
            const imageSearchUrl = buildProductImageSearchUrl({
                codigo_material: getInventoryProductKey(i),
                descripcion_material: getInventoryDescription(i),
                proveedor: getInventoryProviderName(i)
            });
            const cantPropia = Number(i.cantidad_propia || 0);
            const costoUnit = Number(i.costo_promedio_unitario || 0) || (cantPropia > 0 && Number(i.importe_inventario_propio || 0) > 0 ? Number(i.importe_inventario_propio) / cantPropia : 0);
            const importeInv = Number(i.importe_inventario_propio || 0) || (costoUnit > 0 && cantPropia > 0 ? costoUnit * cantPropia : 0);

            const precioFmt = `$${costoUnit.toLocaleString("es-MX", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
            const importeFmt = `$${importeInv.toLocaleString("es-MX", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

            tr.innerHTML = `
                <td>
                    <a href="${imageSearchUrl}" target="_blank" rel="noopener" title="Buscar imagen del producto" class="btn btn-secondary btn-sm" style="min-width: 34px; padding: 7px 9px; display: inline-flex; align-items: center; justify-content: center;">
                        <i class="fa-regular fa-image"></i>
                    </a>
                </td>
                <td><span class="badge badge-secondary">${escapeHTML(i.nombre_centro || "-")}</span></td>
                <td>${escapeHTML(getInventoryWarehouse(i) || "-")}</td>
                <td style="max-width: 150px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${escapeHTML(getInventoryProviderName(i))}">${escapeHTML(getInventoryProviderName(i) || "-")}</td>
                <td style="color: #ef4444; font-weight: 800;">${escapeHTML(getInventoryDCode(i) || "-")}</td>
                <td><code>${escapeHTML(getInventoryProductKey(i) || "-")}</code></td>
                <td style="max-width: 250px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${escapeHTML(getInventoryDescription(i))}">${escapeHTML(getInventoryDescription(i) || "-")}</td>
                <td>${i.cantidad_propia !== null ? Number(i.cantidad_propia).toLocaleString("es-MX") : "-"}</td>
                <td>${i.existencia_consignacion !== null ? Number(i.existencia_consignacion).toLocaleString("es-MX") : "-"}</td>
                <td style="font-weight: 600; color: #1e293b;">${precioFmt}</td>
                <td><strong style="color: #10b981;">${importeFmt}</strong></td>
                <td>${escapeHTML(i.ubicacion || "-")}</td>
            `;
            DOM.tableInventarioAbcf.appendChild(tr);
        });

        // Basic pagination info
        if(DOM.pagInventarioAbcf) {
            DOM.pagInventarioAbcf.innerHTML = `<span style="display:block;margin-bottom:10px;">Mostrando ${pag.startIndex + 1} - ${Math.min(pag.endIndex, totalItems)} de ${totalItems} registros</span>` + pag.html;
            DOM.pagInventarioAbcf.style.display = 'block';
            pag.bindEvents();
        }
        
        // UPDATE HEADERS UI
        const thCant = document.getElementById("th-inv-cant");
        const thConsig = document.getElementById("th-inv-consig");
        if (thCant) {
            const icon = thCant.querySelector('i');
            icon.className = 'fa-solid ' + (state.invSortField === 'cant_propia' ? (state.invSortDir === 'asc' ? 'fa-sort-up' : 'fa-sort-down') : 'fa-sort');
            icon.style.color = state.invSortField === 'cant_propia' ? '#10b981' : '#6b7280';
        }
        if (thConsig) {
            const icon = thConsig.querySelector('i');
            icon.className = 'fa-solid ' + (state.invSortField === 'inv_consig' ? (state.invSortDir === 'asc' ? 'fa-sort-up' : 'fa-sort-down') : 'fa-sort');
            icon.style.color = state.invSortField === 'inv_consig' ? '#10b981' : '#6b7280';
        }
        
    } catch (e) {
        console.error("Error loading inventario:", e);
        const inventoryColumns = state.user?.rol === "vendedor" ? 10 : 11;
        DOM.tableInventarioAbcf.innerHTML = `<tr><td colspan="${inventoryColumns}" style="text-align: center; color: #ef4444;">Error al cargar datos</td></tr>`;
    }
}

async function loadSobrepedidosData(forceRefresh = false) {
    const searchTerm = DOM.filterSobrepedidosSearch ? DOM.filterSobrepedidosSearch.value.toLowerCase() : "";
    const proveedorFilter = DOM.filterSobrepedidosProveedor ? DOM.filterSobrepedidosProveedor.value : "todos";
    const vendedorFilter = DOM.filterSobrepedidosVendedor ? DOM.filterSobrepedidosVendedor.value : "todos";
    const grupoFilter = DOM.filterSobrepedidosGrupo ? DOM.filterSobrepedidosGrupo.value : "todos";
    const estadoFilter = DOM.filterSobrepedidosEstado ? DOM.filterSobrepedidosEstado.value : "todos";
    
    try {
        if (forceRefresh || !state.sobrepedidos || state.sobrepedidos.length === 0) {
            const res = await apiRequest("/api/v1/sobrepedidos/");
            state.sobrepedidos = res.data || [];
        }
        
        let records = [...state.sobrepedidos];
        
        populateSobrepedidosSelect(DOM.filterSobrepedidosProveedor, records.map(r => r.proveedor));
        populateSobrepedidosSelect(DOM.filterSobrepedidosVendedor, records.map(r => r.vendedor_codigo || r.vendedor_nombre));
        populateSobrepedidosSelect(DOM.filterSobrepedidosGrupo, records.map(r => r.grupo));
        
        // Apply filters
        if (proveedorFilter !== "todos") {
            records = records.filter(r => r.proveedor === proveedorFilter);
        }
        if (vendedorFilter !== "todos") {
            records = records.filter(r => (r.vendedor_codigo || r.vendedor_nombre) === vendedorFilter);
        }
        if (grupoFilter !== "todos") {
            records = records.filter(r => r.grupo === grupoFilter);
        }
        if (estadoFilter !== "todos") {
            records = records.filter(r => {
                if (estadoFilter === "verde") return r.estado_crm.includes("Verde");
                if (estadoFilter === "amarillo") return r.estado_crm.includes("Amarillo");
                if (estadoFilter === "rojo") return r.estado_crm.includes("Rojo");
                return true;
            });
        }
        if (searchTerm) {
            records = records.filter(r => {
                const searchableFields = [
                    r.factura || String(r.id_pedido_erp),
                    r.fecha_venta,
                    r.numero_cliente,
                    r.cliente_nombre,
                    r.vendedor_codigo,
                    r.producto_sku,
                    r.producto_desc,
                    r.grupo,
                    r.proveedor,
                    r.vendedor_nombre,
                    r.estatus_compras,
                    r.disponibilidad_vl06o,
                    r.motivo_estado
                ];
                return searchableFields.some(value =>
                    value && String(value).toLowerCase().includes(searchTerm)
                );
            });
        }
        
        DOM.tableSobrepedidos.innerHTML = "";
        if (records.length === 0) {
            DOM.tableSobrepedidos.innerHTML = `<tr><td colspan="16" style="text-align: center;">No se encontraron registros de sobrepedidos.</td></tr>`;
            if (DOM.pagSobrepedidos) DOM.pagSobrepedidos.innerHTML = "";
            return;
        }
        
        // --- SORTING LOGIC ---
        if (state.spSortField === undefined) state.spSortField = null;
        if (state.spSortDir === undefined) state.spSortDir = 'desc';
        if (state.spCurrentPage === undefined) state.spCurrentPage = 1;

        if (state.spSortField === 'pedido') {
            records.sort((a, b) => {
                return state.spSortDir === 'asc' ? Number(a.id_pedido_erp || 0) - Number(b.id_pedido_erp || 0) : Number(b.id_pedido_erp || 0) - Number(a.id_pedido_erp || 0);
            });
        } else if (state.spSortField === 'sku') {
            records.sort((a, b) => {
                const va = String(a.producto_sku || "");
                const vb = String(b.producto_sku || "");
                return state.spSortDir === 'asc' ? va.localeCompare(vb) : vb.localeCompare(va);
            });
        } else if (state.spSortField === 'cant') {
            records.sort((a, b) => {
                return state.spSortDir === 'asc' ? a.cantidad_pendiente - b.cantidad_pendiente : b.cantidad_pendiente - a.cantidad_pendiente;
            });
        } else if (state.spSortField === 'fecha') {
            records.sort((a, b) => {
                const da = a.fecha_pedido ? new Date(a.fecha_pedido) : new Date(0);
                const db = b.fecha_pedido ? new Date(b.fecha_pedido) : new Date(0);
                return state.spSortDir === 'asc' ? da - db : db - da;
            });
        }

        // --- PAGINATION ---
        const totalItems = records.length;
        const pag = createPaginationControls('spCurrentPage', totalItems, loadSobrepedidosData, 25);
        const pageItems = records.slice(pag.startIndex, pag.endIndex);
        
        // Render rows
        const today = new Date();
        pageItems.forEach(item => {
            let rowClass = "";
            let isDelayed = false;
            let daysDelay = 0;
            
            if (item.fecha_venta || item.fecha_pedido) {
                const orderDate = new Date(item.fecha_venta || item.fecha_pedido);
                const diffTime = today - orderDate;
                daysDelay = Math.floor(diffTime / (1000 * 60 * 60 * 24));
                if (item.estado_crm.includes("Rojo") && daysDelay > 15) {
                    rowClass = "row-delayed-alert";
                    isDelayed = true;
                }
            }
            
            // Map CRM Status Pill
            let statusPill = "";
            if (item.estado_crm.includes("Verde")) {
                statusPill = `<span class="status-badge badge-success">Listo en Almacén</span>`;
            } else if (item.estado_crm.includes("Amarillo")) {
                statusPill = `<span class="status-badge badge-warning">En Proceso</span>`;
            } else {
                statusPill = `<span class="status-badge badge-error">Alerta (Rojo)</span>`;
            }
            
            const tr = document.createElement("tr");
            if (rowClass) tr.className = rowClass;
            
            const facturaText = item.factura || item.id_pedido_erp || "";
            const dateText = item.fecha_venta || item.fecha_pedido || "Sin fecha";
            const dateDisplay = isDelayed ? `<span class="cell-delayed-text" title="Retraso crítico: ${daysDelay} días">${dateText} (${daysDelay}d)</span>` : dateText;
            const vendedorText = item.vendedor_codigo || item.vendedor_nombre || "";
            const commentText = item.estatus_compras || "-";
            const commentDisplay = isDelayed ? `<span class="cell-delayed-text" title="${escapeHTML(commentText)}">${escapeHTML(commentText)}</span>` : escapeHTML(commentText);
            const motivoText = item.motivo_estado || item.motivo || "-";

            tr.innerHTML = [
                `<td style="white-space: nowrap;">${escapeHTML(facturaText)}</td>`,
                `<td style="white-space: nowrap;">${dateDisplay}</td>`,
                `<td class="col-truncate" title="${escapeHTML(item.cliente_nombre || '')}">${escapeHTML(item.cliente_nombre || '-')}</td>`,
                `<td style="white-space: nowrap;">${escapeHTML(vendedorText)}</td>`,
                `<td style="white-space: nowrap;"><code>${escapeHTML(item.producto_sku || '-')}</code></td>`,
                `<td class="col-truncate-lg" title="${escapeHTML(item.producto_desc || '')}">${escapeHTML(item.producto_desc || '-')}</td>`,
                `<td class="col-truncate-sm" title="${escapeHTML(item.grupo || '')}">${escapeHTML(item.grupo || '-')}</td>`,
                `<td style="text-align: right; font-weight: 600; white-space: nowrap;">${formatNumber(item.cantidad_pendiente || 0)}</td>`,
                `<td style="white-space: nowrap;">${escapeHTML(item.disponibilidad_vl06o || '-')}</td>`,
                `<td style="text-align: right; white-space: nowrap;">${formatNumber(item.cantidad_disponible || 0)}</td>`,
                `<td style="white-space: nowrap;">${escapeHTML(item.fecha_disponibilidad || "-")}</td>`,
                `<td style="text-align: right; white-space: nowrap;">${item.dias_disponible ?? "-"}</td>`,
                `<td class="col-truncate" title="${escapeHTML(item.proveedor || '')}">${escapeHTML(item.proveedor || '-')}</td>`,
                `<td class="col-truncate" title="${escapeHTML(commentText)}">${commentDisplay}</td>`,
                `<td class="col-truncate" title="${escapeHTML(motivoText)}">${escapeHTML(motivoText)}</td>`,
                `<td style="white-space: nowrap;">${statusPill}</td>`
            ].join("");
            DOM.tableSobrepedidos.appendChild(tr);
        });

        // Render Pagination UI
        if (DOM.pagSobrepedidos) {
            DOM.pagSobrepedidos.innerHTML = `<span style="display:block;margin-bottom:10px;">Mostrando ${pag.startIndex + 1} - ${Math.min(pag.endIndex, totalItems)} de ${totalItems} registros</span>` + pag.html;
            DOM.pagSobrepedidos.style.display = 'block';
            pag.bindEvents();
        }
        
        // Update header sorting icons
        const thPedido = document.getElementById("th-sobrepedidos-pedido");
        const thSku = document.getElementById("th-sobrepedidos-sku");
        const thCant = document.getElementById("th-sobrepedidos-cant");
        const thFecha = document.getElementById("th-sobrepedidos-fecha");
        
        [
            { th: thPedido, field: 'pedido' },
            { th: thSku, field: 'sku' },
            { th: thCant, field: 'cant' },
            { th: thFecha, field: 'fecha' }
        ].forEach(item => {
            if (item.th) {
                const icon = item.th.querySelector('i');
                if (icon) {
                    icon.className = 'fa-solid ' + (state.spSortField === item.field ? (state.spSortDir === 'asc' ? 'fa-sort-up' : 'fa-sort-down') : 'fa-sort');
                    icon.style.color = state.spSortField === item.field ? '#10b981' : '#6b7280';
                }
            }
        });
        
    } catch (e) {
        console.error("Error loading sobrepedidos:", e);
        DOM.tableSobrepedidos.innerHTML = `<tr><td colspan="16" style="text-align: center; color: #ef4444;">Error al cargar datos</td></tr>`;
    }
}

function populateSobrepedidosSelect(select, values) {
    if (!select || select.options.length > 1) return;
    const currentValue = select.value;
    select.innerHTML = '<option value="todos">Todos</option>';
    [...new Set(values.filter(Boolean))].sort().forEach(value => {
        const opt = document.createElement("option");
        opt.value = value;
        opt.textContent = value;
        select.appendChild(opt);
    });
    select.value = currentValue;
}

async function loadSobrepedidosData(forceRefresh = false) {
    const searchTerm = DOM.filterSobrepedidosSearch ? DOM.filterSobrepedidosSearch.value.toLowerCase() : "";
    const proveedorFilter = DOM.filterSobrepedidosProveedor ? DOM.filterSobrepedidosProveedor.value : "todos";
    const vendedorFilter = DOM.filterSobrepedidosVendedor ? DOM.filterSobrepedidosVendedor.value : "todos";
    const grupoFilter = DOM.filterSobrepedidosGrupo ? DOM.filterSobrepedidosGrupo.value : "todos";
    const estadoFilter = DOM.filterSobrepedidosEstado ? DOM.filterSobrepedidosEstado.value : "todos";

    try {
        if (forceRefresh || !state.sobrepedidos || state.sobrepedidos.length === 0) {
            const res = await apiRequest("/api/v1/sobrepedidos/");
            state.sobrepedidos = res.data || [];
        }

        let records = [...state.sobrepedidos];
        renderMobileSobrepedidosSummary(records);
        populateSobrepedidosSelect(DOM.filterSobrepedidosProveedor, records.map(r => r.proveedor));
        populateSobrepedidosSelect(DOM.filterSobrepedidosVendedor, records.map(r => r.vendedor_codigo || r.vendedor_nombre));
        populateSobrepedidosSelect(DOM.filterSobrepedidosGrupo, records.map(r => r.grupo));

        if (proveedorFilter !== "todos") records = records.filter(r => r.proveedor === proveedorFilter);
        if (vendedorFilter !== "todos") records = records.filter(r => (r.vendedor_codigo || r.vendedor_nombre) === vendedorFilter);
        if (grupoFilter !== "todos") records = records.filter(r => r.grupo === grupoFilter);
        if (estadoFilter !== "todos") {
            records = records.filter(r => {
                if (estadoFilter === "verde") return r.estado_crm.includes("Verde");
                if (estadoFilter === "amarillo") return r.estado_crm.includes("Amarillo");
                if (estadoFilter === "rojo") return r.estado_crm.includes("Rojo");
                return true;
            });
        }
        if (searchTerm) {
            records = records.filter(r => {
                const searchableFields = [
                    r.factura || String(r.id_pedido_erp || ""),
                    r.fecha_venta,
                    r.numero_cliente,
                    r.cliente_nombre,
                    r.vendedor_codigo,
                    r.vendedor_nombre,
                    r.producto_sku,
                    r.producto_desc,
                    r.grupo,
                    r.proveedor,
                    r.estatus_compras,
                    r.disponibilidad_vl06o,
                    r.motivo_estado
                ];
                return searchableFields.some(value => value && String(value).toLowerCase().includes(searchTerm));
            });
        }

        DOM.tableSobrepedidos.innerHTML = "";
        if (records.length === 0) {
            DOM.tableSobrepedidos.innerHTML = `<tr><td colspan="16" style="text-align: center;">No se encontraron registros de sobrepedidos.</td></tr>`;
            if (DOM.pagSobrepedidos) DOM.pagSobrepedidos.innerHTML = "";
            return;
        }

        if (state.spSortField === undefined) state.spSortField = null;
        if (state.spSortDir === undefined) state.spSortDir = "desc";
        if (state.spCurrentPage === undefined) state.spCurrentPage = 1;

        if (state.spSortField === "pedido") {
            records.sort((a, b) => state.spSortDir === "asc" ? Number(a.id_pedido_erp || 0) - Number(b.id_pedido_erp || 0) : Number(b.id_pedido_erp || 0) - Number(a.id_pedido_erp || 0));
        } else if (state.spSortField === "sku") {
            records.sort((a, b) => {
                const va = String(a.producto_sku || "");
                const vb = String(b.producto_sku || "");
                return state.spSortDir === "asc" ? va.localeCompare(vb) : vb.localeCompare(va);
            });
        } else if (state.spSortField === "cant") {
            records.sort((a, b) => state.spSortDir === "asc" ? Number(a.cantidad_pendiente || 0) - Number(b.cantidad_pendiente || 0) : Number(b.cantidad_pendiente || 0) - Number(a.cantidad_pendiente || 0));
        } else if (state.spSortField === "fecha") {
            records.sort((a, b) => {
                const da = a.fecha_venta ? new Date(a.fecha_venta) : new Date(0);
                const db = b.fecha_venta ? new Date(b.fecha_venta) : new Date(0);
                return state.spSortDir === "asc" ? da - db : db - da;
            });
        }

        const totalItems = records.length;
        const itemsPerPage = 50;
        const totalPages = Math.ceil(totalItems / itemsPerPage);
        if (state.spCurrentPage > totalPages && totalPages > 0) state.spCurrentPage = totalPages;
        if (state.spCurrentPage < 1) state.spCurrentPage = 1;

        const startIdx = (state.spCurrentPage - 1) * itemsPerPage;
        const pageItems = records.slice(startIdx, startIdx + itemsPerPage);
        const today = new Date();

        pageItems.forEach(item => {
            let rowClass = "";
            let isDelayed = false;
            let daysDelay = 0;
            const orderDateText = item.fecha_venta || item.fecha_pedido;
            if (orderDateText) {
                const orderDate = new Date(orderDateText);
                daysDelay = Math.floor((today - orderDate) / (1000 * 60 * 60 * 24));
                if (item.estado_crm.includes("Rojo") && daysDelay > 15) {
                    rowClass = "row-delayed-alert";
                    isDelayed = true;
                }
            }

            let statusPill = "";
            if (item.estado_crm.includes("Verde")) {
                statusPill = `<span class="status-badge badge-success">Listo / Disponible</span>`;
            } else if (item.estado_crm.includes("Amarillo")) {
                statusPill = `<span class="status-badge badge-warning">En Proceso</span>`;
            } else {
                statusPill = `<span class="status-badge badge-error">Requiere Accion</span>`;
            }

            const facturaText = item.factura || item.id_pedido_erp || "";
            const vendedorText = item.vendedor_codigo || item.vendedor_nombre || "";
            const safeDateText = escapeHTML(orderDateText || "Sin fecha");
            const dateDisplay = isDelayed ? `<span class="cell-delayed-text" title="Retraso critico: ${daysDelay} dias">${safeDateText} (${daysDelay}d)</span>` : safeDateText;
            const safeComment = escapeHTML(item.estatus_compras);
            const commentDisplay = isDelayed ? `<span class="cell-delayed-text">${safeComment}</span>` : safeComment;

            const tr = document.createElement("tr");
            if (rowClass) tr.className = rowClass;
            tr.innerHTML = [
                `<td>${escapeHTML(facturaText)}</td>`,
                `<td>${dateDisplay}</td>`,
                `<td>${escapeHTML(item.cliente_nombre)}</td>`,
                `<td>${escapeHTML(vendedorText)}</td>`,
                `<td><code>${escapeHTML(item.producto_sku)}</code></td>`,
                `<td>${escapeHTML(item.producto_desc)}</td>`,
                `<td>${escapeHTML(item.grupo)}</td>`,
                `<td style="text-align: right; font-weight: 600;">${formatNumber(item.cantidad_pendiente || 0)}</td>`,
                `<td>${escapeHTML(item.disponibilidad_vl06o)}</td>`,
                `<td style="text-align: right;">${formatNumber(item.cantidad_disponible || 0)}</td>`,
                `<td>${escapeHTML(item.fecha_disponibilidad || "-")}</td>`,
                `<td style="text-align: right;">${item.dias_disponible ?? "-"}</td>`,
                `<td>${escapeHTML(item.proveedor)}</td>`,
                `<td>${commentDisplay}</td>`,
                `<td>${escapeHTML(item.motivo_estado)}</td>`,
                `<td>${statusPill}</td>`
            ].join("");
            DOM.tableSobrepedidos.appendChild(tr);
        });

        if (DOM.pagSobrepedidos) {
            DOM.pagSobrepedidos.innerHTML = "";
            if (totalPages > 1) {
                const btnPrev = document.createElement("button");
                btnPrev.className = "btn btn-secondary btn-sm";
                btnPrev.disabled = state.spCurrentPage === 1;
                btnPrev.innerHTML = '<i class="fa-solid fa-chevron-left"></i>';
                btnPrev.addEventListener("click", () => {
                    state.spCurrentPage--;
                    loadSobrepedidosData();
                });

                const spanInfo = document.createElement("span");
                spanInfo.textContent = ` Pagina ${state.spCurrentPage} de ${totalPages} (Total: ${totalItems}) `;
                spanInfo.style.margin = "0 10px";
                spanInfo.style.fontSize = "13px";

                const btnNext = document.createElement("button");
                btnNext.className = "btn btn-secondary btn-sm";
                btnNext.disabled = state.spCurrentPage === totalPages;
                btnNext.innerHTML = '<i class="fa-solid fa-chevron-right"></i>';
                btnNext.addEventListener("click", () => {
                    state.spCurrentPage++;
                    loadSobrepedidosData();
                });

                DOM.pagSobrepedidos.appendChild(btnPrev);
                DOM.pagSobrepedidos.appendChild(spanInfo);
                DOM.pagSobrepedidos.appendChild(btnNext);
            } else {
                DOM.pagSobrepedidos.innerHTML = `<span style="font-size: 13px; color: hsl(var(--text-muted));">Mostrando todos los ${totalItems} registros</span>`;
            }
        }

        [
            { th: document.getElementById("th-sobrepedidos-pedido"), field: "pedido" },
            { th: document.getElementById("th-sobrepedidos-sku"), field: "sku" },
            { th: document.getElementById("th-sobrepedidos-cant"), field: "cant" },
            { th: document.getElementById("th-sobrepedidos-fecha"), field: "fecha" }
        ].forEach(item => {
            if (item.th) {
                const icon = item.th.querySelector("i");
                if (icon) {
                    icon.className = "fa-solid " + (state.spSortField === item.field ? (state.spSortDir === "asc" ? "fa-sort-up" : "fa-sort-down") : "fa-sort");
                    icon.style.color = state.spSortField === item.field ? "#10b981" : "#6b7280";
                }
            }
        });
    } catch (e) {
        console.error("Error loading sobrepedidos:", e);
        DOM.tableSobrepedidos.innerHTML = `<tr><td colspan="16" style="text-align: center; color: #ef4444;">Error al cargar datos</td></tr>`;
    }
}

function getSobrepedidoColor(record) {
    const estado = record?.estado_crm || "";
    if (estado.includes("Verde")) return "verde";
    if (estado.includes("Amarillo")) return "amarillo";
    return "rojo";
}

function getSobrepedidoMoney(record) {
    return Number(record?.importe || record?.monto || record?.total || record?.valor || 0);
}

function renderMobileSobrepedidosSummary(records) {
    if (!DOM.mobileSobrepedidosCards) return;
    const search = DOM.mobileSobrepedidosSearch ? DOM.mobileSobrepedidosSearch.value.trim().toLowerCase() : "";
    const buckets = {
        verde: { orders: new Set(), products: 0, money: 0, matches: 0 },
        amarillo: { orders: new Set(), products: 0, money: 0, matches: 0 },
        rojo: { orders: new Set(), products: 0, money: 0, matches: 0 }
    };

    records.forEach(record => {
        const color = getSobrepedidoColor(record);
        const bucket = buckets[color];
        bucket.orders.add(record.factura || record.id_pedido_erp || record.id);
        bucket.products += Number(record.cantidad_pendiente || 0);
        bucket.money += getSobrepedidoMoney(record);

        if (search) {
            const numCliente = String(record.numero_cliente || "").toLowerCase();
            const codigo = String(record.producto_sku || "").toLowerCase();
            if (numCliente.includes(search) || codigo.includes(search)) {
                bucket.matches += 1;
            }
        }
    });

    Object.entries(buckets).forEach(([color, data]) => {
        setText(`mobile-sp-${color}-ordenes`, data.orders.size);
        setText(`mobile-sp-${color}-products`, formatNumber(data.products));
        setText(`mobile-sp-${color}-money`, formatCurrency(data.money));

        const card = DOM.mobileSobrepedidosCards.querySelector(`[data-sp-color="${color}"]`);
        if (card) card.classList.toggle("mobile-sp-highlight", Boolean(search && data.matches > 0));
    });
}

function setText(id, value) {
    const element = document.getElementById(id);
    if (element) element.textContent = value;
}

function formatCurrency(value) {
    const numericValue = Number(value || 0);
    return numericValue.toLocaleString("es-MX", { style: "currency", currency: "MXN", maximumFractionDigits: 0 });
}

async function loadPorEntregarData(forceRefresh = false) {
    const searchTerm = DOM.filterPorEntregarSearch ? DOM.filterPorEntregarSearch.value.toLowerCase() : "";
    const vendedorFilter = DOM.filterPorEntregarVendedor ? DOM.filterPorEntregarVendedor.value : "todos";
    const estadoFilter = DOM.filterPorEntregarEstado ? DOM.filterPorEntregarEstado.value : "todos";

    try {
        if (forceRefresh || !state.porEntregar || state.porEntregar.length === 0) {
            const res = await apiRequest("/api/v1/por-entregar/");
            state.porEntregar = res.data || [];
        }

        let records = [...state.porEntregar];
        populateSobrepedidosSelect(DOM.filterPorEntregarVendedor, records.map(r => r.vendedor_codigo || r.vendedor_nombre));

        if (vendedorFilter !== "todos") {
            records = records.filter(r => (r.vendedor_codigo || r.vendedor_nombre) === vendedorFilter);
        }
        if (estadoFilter !== "todos") {
            records = records.filter(r => {
                if (estadoFilter === "verde") return r.estado_crm.includes("Verde");
                if (estadoFilter === "amarillo") return r.estado_crm.includes("Amarillo");
                if (estadoFilter === "rojo") return r.estado_crm.includes("Rojo");
                return true;
            });
        }
        if (searchTerm) {
            records = records.filter(r => {
                const searchableFields = [
                    r.factura,
                    r.numero_cliente,
                    r.cliente_nombre,
                    r.vendedor_codigo,
                    r.producto_sku,
                    r.producto_desc,
                    r.motivo_estado
                ];
                return searchableFields.some(value => value && String(value).toLowerCase().includes(searchTerm));
            });
        }

        DOM.tablePorEntregar.innerHTML = "";
        if (records.length === 0) {
            DOM.tablePorEntregar.innerHTML = `<tr><td colspan="11" style="text-align: center;">No se encontraron registros por entregar.</td></tr>`;
            if (DOM.pagPorEntregar) DOM.pagPorEntregar.innerHTML = "";
            return;
        }

        if (state.peCurrentPage === undefined) state.peCurrentPage = 1;
        if (state.peDiasSort === undefined) state.peDiasSort = 'desc';

        // Sort by dias_disponible based on current state
        records.sort((a, b) => {
            const va = Number(a.dias_disponible || 0);
            const vb = Number(b.dias_disponible || 0);
            return state.peDiasSort === 'asc' ? va - vb : vb - va;
        });

        const totalItems = records.length;
        const pag = createPaginationControls('peCurrentPage', totalItems, loadPorEntregarData, 25);
        const pageItems = records.slice(pag.startIndex, pag.endIndex);

        pageItems.forEach(item => {
            let statusPill = "";
            if (item.estado_crm.includes("Verde")) {
                statusPill = `<span class="status-badge badge-success">Verde</span>`;
            } else if (item.estado_crm.includes("Amarillo")) {
                statusPill = `<span class="status-badge badge-warning">Amarillo</span>`;
            } else {
                statusPill = `<span class="status-badge badge-error">Rojo</span>`;
            }

            const tr = document.createElement("tr");
            tr.innerHTML = [
                `<td style="white-space: nowrap;">${escapeHTML(item.factura || 'Sin Información')}</td>`,
                `<td style="white-space: nowrap;"><code>${escapeHTML(item.producto_sku || '-')}</code></td>`,
                `<td class="col-truncate-lg" title="${escapeHTML(item.producto_desc || '')}">${escapeHTML(item.producto_desc || '-')}</td>`,
                `<td style="text-align: right; font-weight: 600; white-space: nowrap;">${formatNumber(item.cantidad_entregar || 0)}</td>`,
                `<td style="white-space: nowrap;">${escapeHTML(item.vendedor_codigo || item.vendedor_nombre || "")}</td>`,
                `<td style="white-space: nowrap;">${escapeHTML(item.numero_cliente || '-')}</td>`,
                `<td class="col-truncate" title="${escapeHTML(item.cliente_nombre || '')}">${escapeHTML(item.cliente_nombre || '-')}</td>`,
                `<td style="white-space: nowrap;">${escapeHTML(item.fecha_disponibilidad || "-")}</td>`,
                `<td style="text-align: right; font-weight: 600; white-space: nowrap;">${item.dias_disponible ?? "-"}</td>`,
                `<td class="col-truncate-lg" title="${escapeHTML(item.motivo_estado || '')}">${escapeHTML(item.motivo_estado || '-')}</td>`,
                `<td style="white-space: nowrap;">${statusPill}</td>`
            ].join("");
            DOM.tablePorEntregar.appendChild(tr);
        });

        // Update sort icon on Días disponible header
        const iconDias = document.getElementById('icon-pe-dias');
        if (iconDias) {
            iconDias.className = 'fa-solid ' + (state.peDiasSort === 'asc' ? 'fa-sort-up' : 'fa-sort-down');
            iconDias.style.color = '#10b981';
        }

        if (DOM.pagPorEntregar) {
            DOM.pagPorEntregar.innerHTML = `<span style="display:block;margin-bottom:10px;">Mostrando ${pag.startIndex + 1} - ${Math.min(pag.endIndex, totalItems)} de ${totalItems} registros</span>` + pag.html;
            DOM.pagPorEntregar.style.display = 'block';
            pag.bindEvents();
        }
    } catch (e) {
        console.error("Error loading por entregar:", e);
        DOM.tablePorEntregar.innerHTML = `<tr><td colspan="11" style="text-align: center; color: #ef4444;">Error al cargar datos</td></tr>`;
    }
}

async function loadPromocionesData(forceRefresh = false) {
    const searchTerm = DOM.filterPromoSearch ? DOM.filterPromoSearch.value.toLowerCase() : "";
    const statusFilter = DOM.filterPromoStatus ? DOM.filterPromoStatus.value : "activas";
    const sortFilter = DOM.filterPromoSort ? DOM.filterPromoSort.value : "default";
    const proveedorFilter = DOM.filterPromoProveedor ? DOM.filterPromoProveedor.value : "todos";
    const familiaFilter = DOM.filterPromoFamilia ? DOM.filterPromoFamilia.value : "todos";
    const subfamiliaFilter = DOM.filterPromoSubfamilia ? DOM.filterPromoSubfamilia.value : "todas";
    let endpoint = "/api/v1/promociones/";
    

    console.log("loadPromocionesData called! searchTerm:", searchTerm, "proveedorFilter:", proveedorFilter, "statusFilter:", statusFilter);
    try {
        if (forceRefresh || !state.promociones || state.promociones.length === 0) {
            const res = await apiRequest(endpoint);
            state.promociones = res.data || [];
        }
        let promociones = [...state.promociones];
        const today = new Date();
        today.setHours(0,0,0,0);
        
        // Populate Familia select
        if (DOM.filterPromoFamilia) {
            const currentFam = DOM.filterPromoFamilia.value || "todos";
            DOM.filterPromoFamilia.innerHTML = '<option value="todos">Todas</option>';
            KURODA_FAMILIALES.forEach(f => {
                const opt = document.createElement("option");
                opt.value = f;
                opt.textContent = f;
                DOM.filterPromoFamilia.appendChild(opt);
            });
            DOM.filterPromoFamilia.value = currentFam;
        }

        // Populate Subfamilia select (cascading based on Familia)
        if (DOM.filterPromoSubfamilia) {
            const currentSub = DOM.filterPromoSubfamilia.value;
            const selectedFam = DOM.filterPromoFamilia ? DOM.filterPromoFamilia.value : "todos";
            DOM.filterPromoSubfamilia.innerHTML = '<option value="todas">Todas</option>';
            let subList = [];
            if (selectedFam !== "todos" && KURODA_SUBFAMILIAS_MAP[selectedFam]) {
                subList = KURODA_SUBFAMILIAS_MAP[selectedFam];
            } else {
                let allSubs = [];
                Object.values(KURODA_SUBFAMILIAS_MAP).forEach(l => allSubs = allSubs.concat(l));
                subList = [...new Set(allSubs)].sort();
            }

            subList.forEach(sf => {
                const opt = document.createElement("option");
                opt.value = sf;
                opt.textContent = sf;
                DOM.filterPromoSubfamilia.appendChild(opt);
            });
            DOM.filterPromoSubfamilia.value = subList.includes(currentSub) ? currentSub : "todas";
        }

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

        if (familiaFilter !== "todos") {
            promociones = promociones.filter(p => p.familia === familiaFilter);
        }

        if (subfamiliaFilter !== "todas") {
            promociones = promociones.filter(p => (p.subfamilia || p.descrip_gpo_materiales) === subfamiliaFilter);
        }

        // Filter Search Text
        if (searchTerm) {
            promociones = promociones.filter(p => 
                (p.codigo_material && String(p.codigo_material).toLowerCase().includes(searchTerm)) ||
                (p.descripcion_material && String(p.descripcion_material).toLowerCase().includes(searchTerm)) ||
                (p.descrip_gpo_materiales && String(p.descrip_gpo_materiales).toLowerCase().includes(searchTerm))
            );
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

        const promoKpisWrapper = document.querySelector('.promociones-kpis-wrapper');
        const btnPromoBack = document.getElementById('btn-promo-back');
        const hasFilters = searchTerm || familiaFilter !== "todos" || subfamiliaFilter !== "todas" || proveedorFilter !== "todos";
        
        if (promoKpisWrapper) {
            promoKpisWrapper.style.display = hasFilters ? 'none' : 'block';
        }
        if (btnPromoBack) {
            btnPromoBack.style.display = hasFilters ? 'inline-flex' : 'none';
        }
        // ----------------------------------------------------
        
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
            DOM.tablePromociones.innerHTML = `<tr><td colspan="11" style="text-align: center;">No se encontraron promociones cargadas.</td></tr>`;
            if (DOM.pagPromociones) DOM.pagPromociones.innerHTML = "";
            return;
        }
        
        const totalItems = promociones.length;
        const pag = createPaginationControls('promoCurrentPage', totalItems, loadPromocionesData, 25);
        const pageItems = promociones.slice(pag.startIndex, pag.endIndex);
        
        pageItems.forEach(p => {
            const tr = document.createElement("tr");
            const imageSearchUrl = buildProductImageSearchUrl(p);
            let isActive = true;
            if (p.valido_hasta) {
                const vDate = new Date(p.valido_hasta);
                isActive = vDate >= today;
            }
            if (!isActive) {
                tr.style.opacity = "0.5";
            }
            
            tr.innerHTML = `
                <td>
                    <a href="${imageSearchUrl}" target="_blank" rel="noopener" title="Buscar imagen del producto" class="btn btn-secondary btn-sm" style="min-width: 34px; padding: 7px 9px; display: inline-flex; align-items: center; justify-content: center;">
                        <i class="fa-regular fa-image"></i>
                    </a>
                </td>
                <td>${p.centro || '-'}</td>
                <td><strong>${p.codigo_material || '-'}</strong></td>
                <td>${p.descripcion_material || '-'}</td>
                <td><strong>${p.indicador_abc || '-'}</strong></td>
                <td>${p.proveedor || '-'}</td>
                <td><strong>$${(p.precio_promocion || 0).toLocaleString('es-MX', { minimumFractionDigits: 2 })}</strong> ${p.moneda || ''}</td>
                <td>${p.margen_promocion ? (p.margen_promocion).toFixed(2) : '-'}</td>
                <td>${p.inventario_disponible !== null && p.inventario_disponible !== undefined ? p.inventario_disponible : '-'}</td>
                <td>${p.valido_hasta ? p.valido_hasta.split('T')[0] : '-'}</td>
                <td>
                    <button type="button" class="btn btn-primary btn-sm btn-promo-clients" onclick="openPromoClientsModal(${p.id})">
                        <i class="fa-solid fa-users"></i> Ver Clientes
                    </button>
                </td>
            `;
            DOM.tablePromociones.appendChild(tr);
        });
        
        if (DOM.pagPromociones) {
            DOM.pagPromociones.innerHTML = `<span style="display:block;margin-bottom:10px;">Mostrando ${pag.startIndex + 1} - ${Math.min(pag.endIndex, totalItems)} de ${totalItems} registros</span>` + pag.html;
            DOM.pagPromociones.style.display = 'block';
            pag.bindEvents();
        }
    } catch (e) {
        showToast("Error cargando promociones: " + e.message, "error");
    }
}

// Upload Promociones Handler
if (DOM.uploadPromocionesForm) {
    DOM.uploadPromocionesForm?.addEventListener("submit", async (e) => {
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
                markLastUpload("promociones");
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
        const hijos = (state.user && state.user.vendedores_hijos) || [];
        if (state.user.rol === "vendedor" && hijos.length === 0) {
            // Vendedor sin hijos: dropdown fijo a sí mismo (comportamiento histórico)
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
        } else if (state.user.rol === "vendedor" && hijos.length > 0) {
            // Vendedor-padre: puede filtrar entre propios, hijos, o todos
            const parent = DOM.filterQuoteSeller.closest(".input-group-inline");
            if (parent) parent.style.display = "";
            DOM.filterQuoteSeller.disabled = false;
            DOM.filterQuoteSeller.innerHTML = "";
            const optAll = document.createElement("option");
            optAll.value = "";
            optAll.textContent = "Todos (míos + hijos)";
            DOM.filterQuoteSeller.appendChild(optAll);
            const optMine = document.createElement("option");
            optMine.value = state.user.id;
            optMine.textContent = "Solo los míos";
            DOM.filterQuoteSeller.appendChild(optMine);
            hijos.forEach(h => {
                const opt = document.createElement("option");
                opt.value = h.id;
                opt.textContent = `${h.codigo_vendedor || ""} ${h.nombre_completo || h.email}`.trim();
                DOM.filterQuoteSeller.appendChild(opt);
            });
            DOM.filterQuoteSeller.value = "";
        } else {
            const parent = DOM.filterQuoteSeller.closest(".input-group-inline");
            if (parent) {
                parent.style.display = "";
            }
            DOM.filterQuoteSeller.disabled = false;

            // Rebuild dropdown list to avoid duplications or missing entries
            const currentSelected = DOM.filterQuoteSeller.value;
            DOM.filterQuoteSeller.innerHTML = '<option value="">Todos los vendedores</option>';
            const unlinkedOption = document.createElement("option");
            unlinkedOption.value = "__unlinked__";
            unlinkedOption.textContent = "Asesor sin vincular";
            DOM.filterQuoteSeller.appendChild(unlinkedOption);
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

    const params = new URLSearchParams({
        limit: String(state.quotesPageSize),
        offset: String((state.quotesCurrentPage - 1) * state.quotesPageSize),
        vista: "resumen",
        orden: state.quotesSortOrder,
    });
    const startDate = DOM.filterQuoteStartDate?.value;
    const endDate = DOM.filterQuoteEndDate?.value;
    const seller = state.user?.rol === "vendedor" ? "" : DOM.filterQuoteSeller?.value;
    const status = DOM.filterQuoteDays?.value;
    const search = DOM.searchQuoteClient?.value?.trim();
    if (startDate) params.set("fecha_inicio", startDate);
    if (endDate) params.set("fecha_fin", endDate);
    if (search) params.set("busqueda", search);
    if (state.activeHeatmapFilter) {
        params.set("total_min", String(state.activeHeatmapFilter.minVal));
        params.set("total_max", String(state.activeHeatmapFilter.maxVal));
        params.set("edad_min_dias", String(state.activeHeatmapFilter.minDays));
        params.set("edad_max_dias", String(state.activeHeatmapFilter.maxDays));
    }
    if (["total", "concretadas", "pendientes", "vencidas"].includes(status)) {
        params.set("estado", status);
    }
    if (seller === "__unlinked__") params.set("sin_vincular", "true");
    if (seller && seller !== "__unlinked__") params.set("vendedor_id", seller);

    const endpoint = `/api/v1/cotizaciones/?${params.toString()}`;
    const res = await apiRequest(endpoint);
    state.cotizaciones = res.data || [];
    state.quotePagination = res.pagination || { total: state.cotizaciones.length, limit: state.quotesPageSize, offset: 0 };
    state.quoteSummary = res.summary || null;

    renderQuotesDashboard();
}

function currentCommercialAnalyticsParams() {
    const params = new URLSearchParams();
    const startDate = DOM.filterQuoteStartDate?.value;
    const endDate = DOM.filterQuoteEndDate?.value;
    const seller = state.user?.rol === "vendedor" ? "" : DOM.filterQuoteSeller?.value;
    if (startDate) params.set("fecha_inicio", startDate);
    if (endDate) params.set("fecha_fin", endDate);
    if (seller === "__unlinked__") params.set("sin_vincular", "true");
    if (seller && seller !== "__unlinked__") params.set("vendedor_id", seller);
    return params;
}

function renderChannelAnalytics(payload) {
    const data = payload.data || [];
    const canvas = document.getElementById("chartQuoteChannel");
    if (state.chartQuoteChannel) state.chartQuoteChannel.destroy();
    if (canvas) {
        state.chartQuoteChannel = new Chart(canvas.getContext("2d"), {
            type: "doughnut",
            data: {
                labels: data.map(row => row.canal),
                datasets: [{
                    data: data.map(row => row.importe_facturado),
                    backgroundColor: ["#38bdf8", "#a78bfa", "#22c55e", "#f59e0b", "#ec4899", "#64748b"]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: "bottom" },
                    tooltip: {
                        callbacks: {
                            label: context => `${context.label}: $${Number(context.raw || 0).toLocaleString("es-MX")}`
                        }
                    }
                }
            }
        });
    }
    const summary = document.getElementById("channel-analytics-summary");
    if (summary) {
        summary.innerHTML = data.length
            ? data.map(row => `<span style="display:inline-block;margin:2px 8px 2px 0;"><strong>${escapeHTML(row.canal)}</strong>: $${Number(row.importe_facturado).toLocaleString("es-MX")} · ${row.conversion}% conv.</span>`).join("")
            : "Sin ventas facturadas para el periodo.";
    }
}

function renderMaterialAnalytics(payload) {
    const tbody = document.querySelector("#table-material-analytics tbody");
    const status = document.getElementById("material-analytics-status");
    const data = payload.data || [];
    if (!tbody) return;
    if (!data.length) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;">Sin detalle de materiales cargado para el periodo.</td></tr>';
        if (status) status.textContent = "Carga el archivo de detalle SKU para habilitar este desglose.";
        return;
    }
    const hierarchy = new Map();
    data.forEach(row => {
        const seller = row.vendedor || "Asesor sin vincular";
        if (!hierarchy.has(seller)) hierarchy.set(seller, new Map());
        const families = hierarchy.get(seller);
        if (!families.has(row.familia)) families.set(row.familia, new Map());
        const groups = families.get(row.familia);
        if (!groups.has(row.grupo_materiales)) groups.set(row.grupo_materiales, []);
        groups.get(row.grupo_materiales).push(row);
    });
    const totals = rows => rows.reduce((result, row) => ({
        quantity: result.quantity + Number(row.cantidad_facturada || 0),
        amount: result.amount + Number(row.importe_facturado || 0)
    }), { quantity: 0, amount: 0 });
    const formatAmount = amount => `$${amount.toLocaleString("es-MX", { minimumFractionDigits: 2 })}`;
    const rendered = [];
    let groupIndex = 0;
    hierarchy.forEach((families, seller) => {
        const sellerRows = [...families.values()].flatMap(groups => [...groups.values()].flat());
        const sellerTotals = totals(sellerRows);
        rendered.push(`
            <tr style="background:rgba(56,189,248,.10);font-weight:800;">
                <td colspan="5"><i class="fa-solid fa-user-tie"></i> ${escapeHTML(seller)}</td>
                <td>${sellerTotals.quantity.toLocaleString("es-MX")}</td>
                <td>${formatAmount(sellerTotals.amount)}</td>
            </tr>
        `);
        families.forEach((groups, family) => {
            const familyRows = [...groups.values()].flat();
            const familyTotals = totals(familyRows);
            rendered.push(`
                <tr style="background:rgba(167,139,250,.08);font-weight:700;">
                    <td></td><td colspan="4"><i class="fa-solid fa-layer-group"></i> ${escapeHTML(family)}</td>
                    <td>${familyTotals.quantity.toLocaleString("es-MX")}</td>
                    <td>${formatAmount(familyTotals.amount)}</td>
                </tr>
            `);
            groups.forEach((rows, group) => {
                const groupTotals = totals(rows);
                const groupKey = `material-group-${groupIndex++}`;
                rendered.push(`
                    <tr style="background:rgba(255,255,255,.025);font-weight:700;">
                        <td></td><td></td>
                        <td colspan="3">
                            <button type="button" class="btn-icon material-group-toggle" data-group="${groupKey}" aria-expanded="false" title="Mostrar SKU">
                                <i class="fa-solid fa-chevron-right"></i>
                            </button>
                            ${escapeHTML(group)}
                        </td>
                        <td>${groupTotals.quantity.toLocaleString("es-MX")}</td>
                        <td>${formatAmount(groupTotals.amount)}</td>
                    </tr>
                `);
                rows.forEach(row => rendered.push(`
                    <tr class="hidden" data-material-group="${groupKey}">
                        <td></td><td></td><td></td>
                        <td><code>${escapeHTML(row.codigo_material)}</code></td>
                        <td>${escapeHTML(row.descripcion || "-")}</td>
                        <td>${Number(row.cantidad_facturada).toLocaleString("es-MX")}</td>
                        <td><strong>${formatAmount(Number(row.importe_facturado))}</strong></td>
                    </tr>
                `));
            });
        });
    });
    tbody.innerHTML = rendered.join("");
    if (status) status.textContent = `Importe facturado reconciliado en partidas: $${Number(payload.totals?.importe_facturado || 0).toLocaleString("es-MX", { minimumFractionDigits: 2 })}`;
}

document.addEventListener("click", event => {
    const button = event.target.closest(".material-group-toggle");
    if (!button) return;
    const rows = document.querySelectorAll(`[data-material-group="${button.dataset.group}"]`);
    const expanded = button.getAttribute("aria-expanded") === "true";
    rows.forEach(row => row.classList.toggle("hidden", expanded));
    button.setAttribute("aria-expanded", String(!expanded));
    const icon = button.querySelector("i");
    if (icon) icon.className = expanded ? "fa-solid fa-chevron-right" : "fa-solid fa-chevron-down";
});

async function loadChannelConfiguration() {
    const panel = document.getElementById("channel-config-panel");
    if (!panel) return;
    const canConfigure = ["admin", "gerente"].includes(state.user?.rol);
    panel.classList.toggle("hidden", !canConfigure);
    if (!canConfigure) return;
    try {
        const response = await apiRequest("/api/v1/analitica/canales");
        const list = document.getElementById("channel-config-list");
        if (list) {
            list.innerHTML = (response.data || []).map(item =>
                `<span style="display:inline-block;margin:2px 8px 2px 0;"><code>${escapeHTML(item.codigo_origen)}</code> → ${escapeHTML(item.nombre_normalizado)}</span>`
            ).join("") || "Sin códigos configurados.";
        }
    } catch (error) {
        console.warn("No se pudo cargar el catálogo de canales:", error);
    }
}

async function loadCommercialAnalytics() {
    if (!state.token || !state.user) return;
    const params = currentCommercialAnalyticsParams().toString();
    try {
        const [channels, materials] = await Promise.all([
            apiRequest(`/api/v1/analitica/ventas-por-canal?${params}`),
            apiRequest(`/api/v1/analitica/ventas-por-material?${params}`)
        ]);
        renderChannelAnalytics(channels);
        renderMaterialAnalytics(materials);
        await loadChannelConfiguration();
    } catch (error) {
        console.error("Error cargando analítica comercial:", error);
    }
}

DOM.btnLoadCommercialAnalytics?.addEventListener("click", () => loadCommercialAnalytics());
DOM.summaryChannelFilter?.addEventListener("change", () => renderSummaryChannelSales(state.summaryChannelSales));

function updateActiveHeatmapFilterBadge() {
    if (!DOM.activeHeatmapFilter || !DOM.activeHeatmapFilterText) return;

    if (!state.activeHeatmapFilter) {
        DOM.activeHeatmapFilter.classList.add("hidden");
        return;
    }

    DOM.activeHeatmapFilterText.textContent = `Mapa de calor: ${state.activeHeatmapFilter.amountLabel} · ${state.activeHeatmapFilter.ageLabel}`;
    DOM.activeHeatmapFilter.classList.remove("hidden");
}

async function applyHeatmapQuoteFilter(filter) {
    state.activeHeatmapFilter = filter;
    state.quotesCurrentPage = 1;

    if (DOM.searchQuoteClient) DOM.searchQuoteClient.value = "";
    if (DOM.filterQuoteDays) DOM.filterQuoteDays.value = "all";
    if (DOM.filterQuoteStartDate) DOM.filterQuoteStartDate.value = "";
    if (DOM.filterQuoteEndDate) DOM.filterQuoteEndDate.value = "";

    await switchSection("cotizaciones");
    showToast(`Filtro aplicado: ${filter.amountLabel} · ${filter.ageLabel}`, "info");
}

function clearHeatmapQuoteFilter() {
    state.activeHeatmapFilter = null;
    state.quotesCurrentPage = 1;
    updateActiveHeatmapFilterBadge();
    loadCotizacionesData(true);
}

function renderQuotesDashboard() {
    const daysVal = DOM.filterQuoteDays ? DOM.filterQuoteDays.value : "all";
    updateActiveHeatmapFilterBadge();
    // Los KPI provienen de la misma consulta filtrada, agregados por PostgreSQL;
    // no se extrapolan a partir de la página visible.
    const summary = state.quoteSummary || {};
    const totalCount = Number(summary.total?.count || 0);
    const totalSum = Number(summary.total?.amount || 0);
    const soldCount = Number(summary.concretadas?.count || 0);
    const soldSum = Number(summary.concretadas?.amount || 0);
    const pendingCount = Number(summary.pendientes?.count || 0);
    const pendingSum = Number(summary.pendientes?.amount || 0);
    const expiredCount = Number(summary.vencidas?.count || 0);
    const expiredSum = Number(summary.vencidas?.amount || 0);

    state.filteredQuotesForTable = state.cotizaciones;
    
    // Update DOM KPI elements
    if (DOM.kpiQuotesTotalCount) DOM.kpiQuotesTotalCount.textContent = totalCount;
    if (DOM.kpiQuotesTotalAmount) DOM.kpiQuotesTotalAmount.textContent = `$${totalSum.toLocaleString('es-MX', { minimumFractionDigits: 2 })}`;
    
    if (DOM.kpiQuotesSoldCount) DOM.kpiQuotesSoldCount.textContent = soldCount;
    if (DOM.kpiQuotesSoldAmount) DOM.kpiQuotesSoldAmount.textContent = `$${soldSum.toLocaleString('es-MX', { minimumFractionDigits: 2 })}`;
    
    if (DOM.kpiQuotesPendingCount) DOM.kpiQuotesPendingCount.textContent = pendingCount;
    if (DOM.kpiQuotesPendingAmount) DOM.kpiQuotesPendingAmount.textContent = `$${pendingSum.toLocaleString('es-MX', { minimumFractionDigits: 2 })}`;
    
    if (DOM.kpiQuotesExpiredCount) DOM.kpiQuotesExpiredCount.textContent = expiredCount;
    if (DOM.kpiQuotesExpiredAmount) DOM.kpiQuotesExpiredAmount.textContent = `$${expiredSum.toLocaleString('es-MX', { minimumFractionDigits: 2 })}`;
    updateQuoteFilterCards(daysVal);
    
    // Render list details
    renderQuotesTableFiltered();

    // Render visual charts independently; the table above must refresh even if a chart fails.
    try {
        renderDashboardCharts(state.cotizaciones);
    } catch (chartErr) {
        console.error("Error renderizando graficas de cotizaciones:", chartErr);
    }

    // El embudo necesita un universo completo; se conserva solo cuando todos
    // los resultados caben en la página para no presentar datos parciales.
    if (state.quotePagination.total <= state.cotizaciones.length) {
        try {
            updateQuotesFunnelDisplay();
        } catch (funnelErr) {
            console.error("Error actualizando embudo de cotizaciones:", funnelErr);
        }
    }
}

function getQuoteStatusInfo(q, refDate = new Date()) {
    const hasInvoice = !!q.numero_factura;
    const isLost = isQuoteLost(q, refDate);
    const ageDays = quoteAgeDays(q, refDate);
    const isExpired = isQuoteExpired(q, refDate);
    const isPending = !hasInvoice && !isExpired;
    const remainingDays = 30 - ageDays;
    
    return { hasInvoice, isLost, isExpired, isPending, remainingDays };
}

function quoteMatchesStatusFilter(q, filterValue, refDate = new Date()) {
    if (!filterValue || filterValue === "all") return true;
    
    const statusInfo = getQuoteStatusInfo(q, refDate);
    
    if (filterValue === "total") return !statusInfo.isExpired;
    if (filterValue === "concretadas") return statusInfo.hasInvoice;
    if (filterValue === "vencidas") return statusInfo.isExpired;
    if (filterValue === "pendientes") return statusInfo.isPending;
    
    if (["7", "15", "30", "60", "90"].includes(filterValue)) {
        const limit = parseInt(filterValue);
        return statusInfo.isPending && statusInfo.remainingDays >= 0 && statusInfo.remainingDays <= limit;
    }
    
    return true;
}

function updateQuoteFilterCards(activeFilter = "all") {
    DOM.quoteFilterCards?.forEach(card => {
        const cardFilter = card.getAttribute("data-quote-filter") || "all";
        const isActive = cardFilter === activeFilter;
        card.classList.toggle("active", isActive);
        card.setAttribute("aria-pressed", isActive ? "true" : "false");
    });
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
        const isLost = isQuoteLost(q, now);
        return hasInvoice && !isLost;
    });

    realMoneyWon = wonQuotes.reduce((sum, q) => sum + (Number(q.importe_facturado) || 0), 0);
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
        const isLost = isQuoteLost(q, refDate);
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
        let sellerEmail = q.vendedor_nombre || "Asesor sin vincular";
        if (q.vendedor_id === state.user.id) {
            sellerEmail = state.user.email;
        } else {
            const seller = state.vendedores.find(v => v.id === q.vendedor_id);
            if (seller && seller.email) {
                sellerEmail = seller.email;
            }
        }
        const label = String(sellerEmail).includes("@") ? String(sellerEmail).split("@")[0] : String(sellerEmail);
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
    const pageQuotes = state.filteredQuotesForTable || state.cotizaciones;
    const totalItems = state.quotePagination?.total ?? pageQuotes.length;
    const pag = createPaginationControls(
        'quotesCurrentPage',
        totalItems,
        () => loadCotizacionesData(true),
        state.quotesPageSize,
    );
    
    if (DOM.tableCotizaciones) {
        DOM.tableCotizaciones.innerHTML = "";
        if (pageQuotes.length === 0) {
            DOM.tableCotizaciones.innerHTML = `<tr><td colspan="10" style="text-align: center;">No hay cotizaciones registradas con los filtros seleccionados.</td></tr>`;
            if (DOM.pagCotizaciones) { DOM.pagCotizaciones.innerHTML = pag.html; pag.bindEvents(); }
            return;
        }
        
        pageQuotes.forEach(c => {
            const sellerEmail = c.vendedor_id === state.user.id
                ? state.user.email
                : (state.vendedores.find(v => v.id === c.vendedor_id)?.email || c.vendedor_nombre || "Asesor sin vincular");
            const contactInfo = buildContactHtml(c.datos_contacto || {});
            const invoiceNumber = c.numero_factura || "";
            
            const dateStr = c.fecha_registro || '-';
            const quoteNum = c.numero_cotizacion || '-';
            const canal = c.canal || '-';
            const lost = isQuoteLost(c);
            const noteSaved = lost ? hasLostReason(c) : Boolean(c.comentarios);
            const noteColor = noteSaved ? "#22c55e" : "#ffffff";
            const noteTitle = lost
                ? (noteSaved ? "Editar motivo de perdida" : "Registrar motivo de perdida")
                : (noteSaved ? "Editar comentario" : "Agregar comentario");
            const lossPill = lost ?
                `<span class="status-pill status-pendiente">Si</span>` :
                `<span class="status-pill status-completada">No</span>`;
                
            const clientDisplay = `<strong>${escapeHTML(c.cliente_nombre)}</strong>${c.numero_cliente ? `<br><a href="#" class="btn-client-history text-muted" style="font-size: 11px; text-decoration: underline;" data-cliente="${escapeHTML(c.numero_cliente)}"><i class="fa-solid fa-clock-rotate-left"></i> ${escapeHTML(c.numero_cliente)}</a>` : ''}`;

            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><code>${quoteNum}</code></td>
                <td>${dateStr}</td>
                <td>${clientDisplay}</td>
                <td>${contactInfo}</td>
                <td>${canal}</td>
                <td><strong>$${c.total.toLocaleString('es-MX', { minimumFractionDigits: 2 })}</strong></td>
                <td>${sellerEmail}</td>
                <td>${lossPill}</td>
                <td>${invoiceNumber ? `<code title="Factura">${escapeHTML(invoiceNumber)}</code>` : `<span class="text-muted">-</span>`}</td>
                <td>
                    <div style="display:flex; gap:6px;">
                        <button class="btn btn-secondary btn-sm lost-reason-btn" data-id="${c.id}" title="${noteTitle}" style="min-width: 38px; padding: 8px 10px; color: ${noteColor};">
                            <i class="fa-regular fa-note-sticky"></i>
                        </button>
                        <button class="btn btn-secondary btn-sm reminder-btn" data-id="${c.id}" title="Agendar recordatorio" style="min-width:38px; padding:8px 10px;">
                            <i class="fa-regular fa-bell"></i>
                        </button>
                        <button class="btn btn-secondary btn-sm client-history-btn" data-cliente="${escapeHTML(c.numero_cliente || '')}" title="Historial del Cliente" style="min-width:38px; padding:8px 10px;" ${!c.numero_cliente ? 'disabled' : ''}>
                            <i class="fa-solid fa-clock-rotate-left"></i>
                        </button>
                    </div>
                </td>
            `;
            DOM.tableCotizaciones.appendChild(tr);
        });
        
        document.querySelectorAll(".lost-reason-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                const id = btn.getAttribute("data-id");
                const quote = state.cotizaciones.find(q => q.id === id);
                if (quote) openLostReasonModal(quote);
            });
        });

        document.querySelectorAll(".reminder-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                const id = btn.getAttribute("data-id");
                if (id) openAddReminderModal(id);
            });
        });

        document.querySelectorAll(".client-history-btn, .btn-client-history").forEach(btn => {
            btn.addEventListener("click", (e) => {
                e.preventDefault();
                const cliente = btn.getAttribute("data-cliente");
                if (cliente) openClientHistoryModal(cliente);
            });
        });
    }
    
    if (DOM.pagCotizaciones) { DOM.pagCotizaciones.innerHTML = pag.html; pag.bindEvents(); }
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

function closeLostReasonModal() {
    DOM.lostReasonModal?.classList.add("hidden");
}

function openLostReasonModal(quote) {
    if (!DOM.lostReasonModal || !DOM.lostReasonForm) return;
    const lost = isQuoteLost(quote);
    const reason = parseLostReason(quote);
    const reasons = getLostReasons(reason);
    if (DOM.lostReasonQuoteId) DOM.lostReasonQuoteId.value = quote.id;
    if (DOM.lostReasonTitle) DOM.lostReasonTitle.textContent = `${lost ? "Motivo de Venta Perdida" : "Observaciones"} - ${quote.cliente_nombre || "Cliente"}`;
    if (DOM.lostReasonOptions) DOM.lostReasonOptions.classList.toggle("hidden", !lost);
    if (DOM.lostReasonPrice) DOM.lostReasonPrice.checked = reasons.includes("precio");
    if (DOM.lostReasonStock) DOM.lostReasonStock.checked = reasons.includes("existencia");
    if (DOM.lostReasonJustificationLabel) DOM.lostReasonJustificationLabel.textContent = lost ? "Justificación" : "Comentarios";
    if (DOM.lostReasonJustification) {
        DOM.lostReasonJustification.placeholder = lost
            ? "Describe brevemente qué pasó con esta cotización..."
            : "Agrega un comentario sobre esta cotización...";
        DOM.lostReasonJustification.value = lost ? (reason?.justification || "") : (quote.comentarios || "");
    }
    DOM.lostReasonModal.classList.remove("hidden");
}

async function saveLostReason(event) {
    event.preventDefault();
    const quoteId = DOM.lostReasonQuoteId?.value;
    const quote = state.cotizaciones.find(q => q.id === quoteId);
    if (!quote) {
        showToast("No se encontró la cotización.", "error");
        return;
    }

    const lost = isQuoteLost(quote);
    const reasons = [
        DOM.lostReasonPrice?.checked ? "precio" : null,
        DOM.lostReasonStock?.checked ? "existencia" : null
    ].filter(Boolean);
    const justification = DOM.lostReasonJustification?.value.trim() || "";

    if (lost && reasons.length === 0) {
        showToast("Selecciona Precio, Existencia o ambas opciones.", "error");
        return;
    }
    if (!justification) {
        showToast(lost ? "Agrega una justificación breve." : "Agrega un comentario.", "error");
        return;
    }

    try {
        const res = await apiRequest(`/api/v1/cotizaciones/${quoteId}`, {
            method: "PUT",
            body: JSON.stringify({
                comentarios: lost
                    ? buildLostReasonComments({ reasons, justification })
                    : justification
            })
        });

        if (res.data) {
            const idx = state.cotizaciones.findIndex(q => q.id === quoteId);
            if (idx !== -1) state.cotizaciones[idx] = res.data;
        }

        closeLostReasonModal();
        renderQuotesDashboard();
        showToast(lost ? "Motivo de venta perdida guardado." : "Comentario guardado.");
    } catch (e) {
        showToast(e.message, "error");
    }
}

function closeQuoteCommentsModal() {
    DOM.quoteCommentsModal?.classList.add("hidden");
    resetQuoteCommentEditor();
}

function resetQuoteCommentEditor() {
    if (DOM.quoteCommentsEditId) DOM.quoteCommentsEditId.value = "";
    if (DOM.quoteCommentsText) DOM.quoteCommentsText.value = "";
    if (DOM.quoteCommentsFormLabel) DOM.quoteCommentsFormLabel.textContent = "Nuevo comentario";
    if (DOM.btnSaveQuoteComment) DOM.btnSaveQuoteComment.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Agregar';
    DOM.btnCancelQuoteCommentEdit?.classList.add("hidden");
}

function renderQuoteComments(comments) {
    if (!DOM.quoteCommentsHistory) return;
    if (!comments.length) {
        DOM.quoteCommentsHistory.innerHTML = '<p class="text-muted">Sin comentarios de seguimiento.</p>';
        return;
    }
    DOM.quoteCommentsHistory.innerHTML = comments.map(comment => {
        const timestamp = comment.creado_en
            ? new Date(comment.creado_en).toLocaleString("es-MX", { dateStyle: "short", timeStyle: "short" })
            : "";
        const canEdit = ["admin", "gerente"].includes(state.user?.rol)
            || String(comment.autor_id || "") === String(state.user?.id || "");
        return `
            <article style="padding:12px; border:1px solid rgba(255,255,255,.10); border-radius:8px; background:rgba(255,255,255,.035);">
                <div style="display:flex; justify-content:space-between; gap:12px; margin-bottom:6px;">
                    <strong style="font-size:12px; color:#38bdf8;">${escapeHTML(comment.autor_nombre || "Usuario")}</strong>
                    <div style="display:flex; align-items:center; gap:8px;">
                        <small class="text-muted">${escapeHTML(timestamp)}${comment.editado_en ? " · editado" : ""}</small>
                        ${canEdit ? `
                            <button type="button" class="btn-icon quote-comment-edit-btn"
                                data-id="${comment.id}" data-text="${escapeHTML(comment.comentario)}"
                                title="Editar comentario" aria-label="Editar comentario">
                                <i class="fa-solid fa-pen"></i>
                            </button>
                        ` : ""}
                    </div>
                </div>
                <p style="margin:0; white-space:pre-wrap;">${escapeHTML(comment.comentario)}</p>
            </article>
        `;
    }).join("");
    DOM.quoteCommentsHistory.scrollTop = DOM.quoteCommentsHistory.scrollHeight;
}

async function openQuoteCommentsModal(quote) {
    if (!quote || !DOM.quoteCommentsModal) return;
    DOM.quoteCommentsQuoteId.value = quote.id;
    DOM.quoteCommentsTitle.textContent = `Seguimiento - ${quote.cliente_nombre || "Cliente"}`;
    DOM.quoteCommentsHistory.innerHTML = '<p class="text-muted">Cargando comentarios...</p>';
    resetQuoteCommentEditor();
    DOM.quoteCommentsModal.classList.remove("hidden");
    try {
        const result = await apiRequest(`/api/v1/cotizaciones/${quote.id}/comentarios`);
        renderQuoteComments(result.data || []);
    } catch (error) {
        DOM.quoteCommentsHistory.innerHTML = `<p style="color:#ef4444;">${escapeHTML(error.message)}</p>`;
    }
}

async function saveQuoteComment(event) {
    event.preventDefault();
    const quoteId = DOM.quoteCommentsQuoteId?.value;
    const text = DOM.quoteCommentsText?.value.trim();
    const commentId = DOM.quoteCommentsEditId?.value;
    if (!quoteId || !text) {
        showToast("Escribe un comentario.", "error");
        return;
    }
    try {
        await apiRequest(
            commentId
                ? `/api/v1/cotizaciones/${quoteId}/comentarios/${commentId}`
                : `/api/v1/cotizaciones/${quoteId}/comentarios`,
            {
            method: commentId ? "PUT" : "POST",
            body: JSON.stringify({ comentario: text })
            }
        );
        const quote = state.cotizaciones.find(item => item.id === quoteId);
        if (quote && !commentId) {
            quote.comentarios_seguimiento_count = (quote.comentarios_seguimiento_count || 0) + 1;
        }
        resetQuoteCommentEditor();
        const result = await apiRequest(`/api/v1/cotizaciones/${quoteId}/comentarios`);
        renderQuoteComments(result.data || []);
        renderQuotesTableFiltered();
        if (state.currentSection === "seguimiento") renderKanbanColumns();
        showToast(commentId ? "Comentario actualizado." : "Comentario de seguimiento agregado.");
    } catch (error) {
        showToast(error.message, "error");
    }
}

function normalizeClientLookupText(value) {
    return String(value || "")
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .trim()
        .toLowerCase();
}

async function findCatalogClientForQuote(quote) {
    const search = String(quote.numero_cliente || quote.cliente_nombre || "").trim();
    if (!search) return null;
    try {
        const result = await apiRequest(`/api/v1/clientes/?search=${encodeURIComponent(search)}&limit=10`);
        const clients = result.data || [];
        const exactNumber = clients.find(client =>
            quote.numero_cliente && String(client.numero_cliente || "").trim() === String(quote.numero_cliente).trim()
        );
        if (exactNumber) return exactNumber;
        const quoteName = normalizeClientLookupText(quote.cliente_nombre);
        return clients.find(client => normalizeClientLookupText(client.nombre) === quoteName) || null;
    } catch (error) {
        console.warn("No se pudo consultar el contacto del catálogo:", error);
        return null;
    }
}

function renderProposalClientContact(quote, catalogClient) {
    const quoteContact = quote.datos_contacto || {};
    const celular = quoteContact.celular || catalogClient?.celular || "";
    const nombreContacto = quoteContact.nombre_contacto || catalogClient?.nombre_contacto || "";
    const digits = String(celular).replace(/\D/g, "");
    const hasCellular = Boolean(celular);
    const clientId = catalogClient?.id || "";

    return `
        <section class="proposal-client-contact" style="margin-bottom:14px; padding:12px; border:1px solid rgba(59,130,246,.2); border-radius:10px; background:rgba(59,130,246,.04);">
            <div style="display:flex; align-items:center; justify-content:space-between; gap:8px; margin-bottom:10px;">
                <strong><i class="fa-solid fa-address-card" style="color:#38bdf8;"></i> Contacto comercial</strong>
                ${hasCellular && digits ? `<a href="https://wa.me/${digits}" target="_blank" rel="noopener" class="btn btn-secondary btn-sm" title="Abrir WhatsApp" aria-label="Abrir WhatsApp"><i class="fa-brands fa-whatsapp" style="color:#25d366;"></i> WhatsApp</a>` : ""}
            </div>
            ${catalogClient
                ? `<div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:10px; align-items:end;">
                    <label style="display:grid; gap:4px; font-size:12px; font-weight:700;">Nombre de contacto
                        <input id="proposal-contact-name" class="form-control" value="${escapeHTML(nombreContacto)}" placeholder="Ej. Romana Pérez Iribe" autocomplete="name">
                    </label>
                    <label style="display:grid; gap:4px; font-size:12px; font-weight:700;">Celular
                        <input id="proposal-contact-cell" class="form-control" value="${escapeHTML(celular)}" placeholder="Ej. 6671500942" inputmode="tel" autocomplete="tel">
                    </label>
                    <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
                        <button type="button" class="btn btn-primary btn-sm proposal-save-client-contact" data-client-id="${escapeHTML(clientId)}"><i class="fa-solid fa-floppy-disk"></i> Guardar</button>
                        <button type="button" class="btn btn-secondary btn-sm proposal-open-client-contact" title="Abrir ficha completa del cliente" aria-label="Abrir ficha completa del cliente" data-client-id="${escapeHTML(clientId)}" data-client-search="${escapeHTML(quote.numero_cliente || quote.cliente_nombre || "")}"><i class="fa-solid fa-arrow-up-right-from-square"></i></button>
                    </div>
                </div>`
                : `<div style="display:flex; align-items:center; justify-content:space-between; gap:10px; flex-wrap:wrap;">
                    <span style="font-size:13px; color:hsl(var(--text-secondary));">Vincula este cliente para guardar su contacto y celular.</span>
                    <button type="button" class="btn btn-secondary btn-sm proposal-update-client-contact proposal-open-client-contact" data-client-search="${escapeHTML(quote.numero_cliente || quote.cliente_nombre || "")}"><i class="fa-solid fa-user-plus"></i> Buscar en Clientes</button>
                </div>`}
        </section>
    `;
}

function renderProposalModalContent(quote, catalogClient) {
    const proposal = quote.texto_propuesta || "Esta cotización no contiene propuesta detallada.";
    DOM.modalProposalBody.innerHTML = `${renderProposalClientContact(quote, catalogClient)}<div style="white-space:pre-wrap;">${escapeHTML(proposal)}</div>`;
    DOM.modalProposalBody.querySelector(".proposal-open-client-contact")?.addEventListener("click", () => {
        openClientContactMaintenance(catalogClient?.id, quote.numero_cliente || quote.cliente_nombre);
    });
    DOM.modalProposalBody.querySelector(".proposal-save-client-contact")?.addEventListener("click", event => {
        saveProposalClientContact(quote, catalogClient, event.currentTarget);
    });
}

async function saveProposalClientContact(quote, catalogClient, button) {
    if (!catalogClient?.id) return;
    const contactName = DOM.modalProposalBody.querySelector("#proposal-contact-name")?.value.trim() || "";
    const celular = DOM.modalProposalBody.querySelector("#proposal-contact-cell")?.value.trim() || "";
    button.disabled = true;
    try {
        const savedClient = await apiRequest(`/api/v1/clientes/${catalogClient.id}`, {
            method: "PUT",
            body: JSON.stringify({ nombre_contacto: contactName, celular }),
        });
        const updatedQuote = {
            ...quote,
            datos_contacto: { ...(quote.datos_contacto || {}), nombre_contacto: contactName, celular },
        };
        const index = state.cotizaciones.findIndex(item => item.id === updatedQuote.id);
        if (index >= 0) state.cotizaciones[index] = updatedQuote;
        showToast("Contacto actualizado en Clientes.", "success");
        renderProposalModalContent(updatedQuote, savedClient);
    } catch (error) {
        showToast(error.message, "error");
        button.disabled = false;
    }
}

async function openClientContactMaintenance(clientId, clientSearch) {
    closeModal();
    state.clientes.search = String(clientSearch || "").trim();
    await switchSection("clientes");
    const input = document.getElementById("clientes-search-input");
    if (input) input.value = state.clientes.search;
    if (clientId) {
        await openModalCliente(clientId);
        document.getElementById("cliente-cel-input")?.focus();
    } else {
        showToast("Busca el cliente en la tabla o regístralo para capturar su celular.", "info");
        input?.focus();
    }
}

async function showProposalModal(quote) {
    DOM.modalProposalTitle.textContent = `Propuesta Comercial - ${quote.cliente_nombre}`;
    DOM.proposalModal.classList.remove("hidden");
    DOM.modalProposalBody.textContent = "Cargando propuesta…";
    try {
        if (!Object.prototype.hasOwnProperty.call(quote, "texto_propuesta")) {
            const result = await apiRequest(`/api/v1/cotizaciones/${quote.id}`);
            quote = { ...quote, ...(result.data || {}) };
            const index = state.cotizaciones.findIndex(item => item.id === quote.id);
            if (index >= 0) state.cotizaciones[index] = quote;
        }
        const catalogClient = await findCatalogClientForQuote(quote);
        renderProposalModalContent(quote, catalogClient);
    } catch (error) {
        DOM.modalProposalBody.textContent = "No fue posible cargar la propuesta.";
        showToast(error.message, "error");
    }
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
    
    const baseParams = new URLSearchParams({
        limit: String(state.kanbanPageSize),
        offset: String((state.kanbanCurrentPage - 1) * state.kanbanPageSize),
        vista: "resumen",
    });
    const seller = DOM.kanbanFilterSeller?.value;
    const search = DOM.kanbanSearchClient?.value?.trim();
    const days = Number(DOM.kanbanFilterDays?.value || 0);
    if (seller) baseParams.set("vendedor_id", seller);
    if (search) baseParams.set("busqueda", search);
    if (Number.isFinite(days) && days > 0) {
        const start = new Date();
        start.setDate(start.getDate() - days);
        baseParams.set("fecha_inicio", start.toISOString().slice(0, 10));
    }

    // Cada estado recibe su propia página ligera. Así, las vencidas no quedan
    // ocultas detrás de las cotizaciones más recientes del listado cronológico.
    const kanbanStages = ["pendientes", "concretadas", "vencidas"];
    const stageResults = await Promise.all(
        kanbanStages.map(async stage => {
            const params = new URLSearchParams(baseParams);
            params.set("estado", stage);
            const response = await apiRequest(`/api/v1/cotizaciones/?${params.toString()}`);
            return [stage, response];
        })
    );
    state.kanbanStageData = Object.fromEntries(
        stageResults.map(([stage, response]) => [stage, response.data || []])
    );
    state.kanbanStagePagination = Object.fromEntries(
        stageResults.map(([stage, response]) => [
            stage,
            response.pagination || { total: 0, limit: state.kanbanPageSize, offset: 0 },
        ])
    );
    state.kanbanPagination = {
        total: Math.max(
            ...Object.values(state.kanbanStagePagination).map(page => Number(page.total || 0)),
            0,
        ),
        limit: state.kanbanPageSize,
        offset: (state.kanbanCurrentPage - 1) * state.kanbanPageSize,
    };
    state.cotizaciones = Object.values(state.kanbanStageData)
        .flat()
        .filter((quote, index, quotes) => quotes.findIndex(item => item.id === quote.id) === index);
    
    renderKanbanColumns();
}

function renderKanbanColumns() {
    // Búsqueda, vendedor, periodo y estado se ejecutaron en PostgreSQL. Las
    // tres páginas permanecen acotadas y se muestran en sus columnas correctas.
    const filteredQuotes = state.kanbanStageData.pendientes || [];
    
    // Categorize quotes
    const stages = {
        cotizado: [],
        promociones: [],
    inventario_abcf: [],
        vendido: [],
        vencido: []
    };
    
    const refDate = new Date();
    
    filteredQuotes.forEach(q => {
        const hasInvoice = !!q.numero_factura;
        const isLost = isQuoteLost(q, refDate);
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
            // La prioridad promocional proviene exclusivamente del cruce exacto
            // de SKU y vigencia calculado por el backend.
            if (q.tiene_promocion === true) {
                stages.promociones.push(q);
            } else {
                stages.cotizado.push(q);
            }
        }
    });
    stages.vendido = [...(state.kanbanStageData.concretadas || [])];
    stages.vencido = [...(state.kanbanStageData.vencidas || [])];
    
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
        } else if (col === "promociones") {
            const priorityWeight = { alta: 3, media: 2, normal: 1 };
            stages[col].sort((a, b) => {
                const priorityDiff = (priorityWeight[b.nivel_prioridad] || 0) - (priorityWeight[a.nivel_prioridad] || 0);
                if (priorityDiff) return priorityDiff;
                const aExpiry = a.promociones_coincidentes?.[0]?.dias_restantes ?? 9999;
                const bExpiry = b.promociones_coincidentes?.[0]?.dias_restantes ?? 9999;
                return aExpiry - bExpiry;
            });
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
            
            const sellerEmail = q.vendedor_id === state.user.id
                ? state.user.email
                : (state.vendedores.find(v => v.id === q.vendedor_id)?.email || q.vendedor_nombre || "Asesor sin vincular");
            const dateStr = q.fecha_registro || '-';
            const quoteNum = q.numero_cotizacion || '-';
            const totalStr = q.total.toLocaleString('es-MX', { minimumFractionDigits: 2 });
            
            let statusBadge = "";
            if (col === "vendido") {
                statusBadge = `<span class="kanban-card-badge status-badge badge-success" style="padding: 2px 8px; font-size: 10px;" title="Factura: ${q.numero_factura || ''}">Vendido</span>`;
            } else if (col === "vencido") {
                statusBadge = `<span class="kanban-card-badge status-badge badge-error" style="padding: 2px 8px; font-size: 10px;">${isQuoteLost(q) ? 'Perdida' : 'Expirada'}</span>`;
            } else if (col === "promociones") {
                const promoClass = q.nivel_prioridad === "alta" ? "#ef4444" : (q.nivel_prioridad === "media" ? "#f59e0b" : "#22c55e");
                const expiry = q.promociones_coincidentes?.[0]?.valido_hasta || "";
                statusBadge = `<span class="kanban-card-badge" style="background:${promoClass}22;color:${promoClass};border:1px solid ${promoClass}66;" title="Promoción vigente hasta ${escapeHTML(expiry)}"><i class="fa-solid fa-tags"></i> Promoción</span>`;
            }
            const promotionDetail = col === "promociones" && q.promociones_coincidentes?.length
                ? `<div style="margin-top:8px;font-size:11px;color:#fbbf24;">${q.promociones_coincidentes.map(p => `${escapeHTML(p.codigo_material)} · vence ${escapeHTML(p.valido_hasta)}`).join("<br>")}</div>`
                : "";
            
            const hasPendingReminder = (state.pendingReminders || []).some(r => String(r.cotizacion_id) === String(q.id));
            const reminderIndicator = hasPendingReminder
                ? `<span class="kanban-card-reminder-indicator" title="Tiene recordatorio pendiente agendado"><i class="fa-regular fa-calendar-check"></i></span>`
                : "";

            card.innerHTML = `
                <div class="kanban-card-header">
                    <h4 class="kanban-card-client" style="display:flex; align-items:center; gap:6px;">
                        <span>${escapeHTML(q.cliente_nombre)}</span> ${reminderIndicator}
                    </h4>
                    <span class="kanban-card-num">${quoteNum !== '-' ? '#' + quoteNum : 'Sin #'}</span>
                </div>
                <div class="kanban-card-body">
                    <div class="kanban-card-date"><i class="fa-regular fa-calendar"></i> ${dateStr}</div>
                    <div class="kanban-card-seller" title="${sellerEmail}"><i class="fa-regular fa-user"></i> ${sellerEmail}</div>
                </div>
                <div class="kanban-card-footer">
                    <span class="kanban-card-total">$${totalStr}</span>
                    ${statusBadge}
                    <div class="kanban-card-actions" style="display:flex; gap:4px;">
                        <button class="btn btn-secondary btn-sm quote-comments-btn" data-id="${q.id}" title="Comentarios de seguimiento" style="min-width:34px;padding:6px 8px;">
                            <i class="fa-regular fa-comments"></i>${q.comentarios_seguimiento_count ? ` <small>${q.comentarios_seguimiento_count}</small>` : ""}
                        </button>
                        <button class="btn btn-secondary btn-sm kanban-reminder-btn" data-id="${q.id}" title="Agendar recordatorio" style="min-width:34px;padding:6px 8px;">
                            <i class="fa-regular fa-bell"></i>
                        </button>
                        <button class="btn btn-secondary btn-sm kanban-history-btn" data-cliente="${escapeHTML(q.numero_cliente || '')}" title="Historial del cliente" style="min-width:34px;padding:6px 8px;" ${!q.numero_cliente ? 'disabled' : ''}>
                            <i class="fa-solid fa-clock-rotate-left"></i>
                        </button>
                    </div>
                </div>
                ${promotionDetail}
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
            
            // Action button listeners
            const remBtn = card.querySelector(".kanban-reminder-btn");
            if (remBtn) {
                remBtn.addEventListener("click", (e) => {
                    e.stopPropagation();
                    openAddReminderModal(q.id);
                });
            }

            const histBtn = card.querySelector(".kanban-history-btn");
            if (histBtn) {
                histBtn.addEventListener("click", (e) => {
                    e.stopPropagation();
                    if (q.numero_cliente) openClientHistoryModal(q.numero_cliente);
                });
            }

            // Open proposal modal on click (if they don't click action buttons or drag)
            card.addEventListener("click", (e) => {
                if (e.target.closest(".kanban-card-actions") || e.target.closest(".quote-comments-btn") || e.target.closest(".kanban-reminder-btn") || e.target.closest(".kanban-history-btn") || card.classList.contains("dragging")) return;
                showProposalModal(q);
            });
            
            container.appendChild(card);
        });
        
        // Update summary cards
        if (summaryCount) summaryCount.textContent = stages[col].length;
        if (summaryTotal) summaryTotal.textContent = `$${colTotal.toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    });
    
    setupKanbanDragAndDrop();
    if (DOM.pagKanban) {
        const pag = createPaginationControls(
            "kanbanCurrentPage",
            state.kanbanPagination?.total ?? filteredQuotes.length,
            () => loadKanbanData(true),
            state.kanbanPageSize,
        );
        DOM.pagKanban.innerHTML = pag.html;
        pag.bindEvents();
    }
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
        const label = String(sellerEmail).includes("@") ? String(sellerEmail).split("@")[0] : String(sellerEmail);
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
        if (String(sid) === String(state.user.id)) return state.user.email.split("@")[0];
        return String(sellers.find(s => String(s.id) === String(sid))?.email || sid).split("@")[0];
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
    quotes.forEach(q => {
        const ageDays = getQuoteAgeDays(q);

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
            cell.setAttribute("role", "button");
            cell.setAttribute("tabindex", cellData.count > 0 ? "0" : "-1");
            cell.setAttribute("aria-label", `Filtrar cotizaciones: ${yCat.label}, ${xCat.label}, ${cellData.count} cotizaciones`);
            if (cellData.count === 0) {
                cell.classList.add("is-empty");
                cell.style.cursor = "default";
            }

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
            if (cellData.count > 0) {
                const filter = {
                    minDays: xCat.minDays,
                    maxDays: xCat.maxDays,
                    minVal: yCat.minVal,
                    maxVal: yCat.maxVal,
                    ageLabel: xCat.label,
                    amountLabel: yCat.label
                };
                cell.addEventListener("click", () => applyHeatmapQuoteFilter(filter));
                cell.addEventListener("keydown", (event) => {
                    if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        applyHeatmapQuoteFilter(filter);
                    }
                });
            }
            gridEl.appendChild(cell);
        });
    }
}

/* ==========================================================================
   EVENT LISTENERS & FORM SUBMISSIONS
   ========================================================================== */

// Handle Auth Form Submission
DOM.loginForm?.addEventListener("submit", async (e) => {
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
        await initSession();
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
DOM.logoutBtn?.addEventListener("click", logout);

/* --- Vendedores/Usuarios Handlers --- */
let editingUserId = null;

// Llena el <select> de vendedor padre con los vendedores que pueden ser padre.
// Excluye al usuario que se está editando (no puede ser su propio padre).
async function populateSellerParentOptions(excludeId = null, selectedParentId = null) {
    if (!DOM.sellerParent) return;
    try {
        const url = excludeId
            ? `/api/v1/vendedores/posibles-padres?excluir=${excludeId}`
            : `/api/v1/vendedores/posibles-padres`;
        const res = await apiRequest(url);
        const options = ['<option value="">Sin padre (solo sus propios datos)</option>'];
        const padres = (res && res.data) || [];
        // Si el usuario editado ya tiene padre, ese padre aparece igualmente (aunque ya tenga este hijo)
        for (const p of padres) {
            const label = `${p.codigo_vendedor || ""} ${p.nombre_completo || p.email}`.trim();
            const sel = (selectedParentId && p.id === selectedParentId) ? " selected" : "";
            options.push(`<option value="${p.id}"${sel}>${escapeHTML(label)}</option>`);
        }
        // Si hay un padre seleccionado pero no apareció en la lista (porque ya tiene este hijo como
        // su propio padre), lo añadimos manualmente para mostrarlo.
        if (selectedParentId && !padres.some(p => p.id === selectedParentId)) {
            const hijo = state.vendedores.find(v => v.id === selectedParentId);
            if (hijo) {
                const label = `${hijo.codigo_vendedor || ""} ${hijo.nombre_completo || hijo.email}`.trim();
                options.push(`<option value="${selectedParentId}" selected>${escapeHTML(label)}</option>`);
            }
        }
        DOM.sellerParent.innerHTML = options.join("");
    } catch (e) {
        console.error("Error cargando posibles padres:", e);
    }
}

// Dynamically show/hide seller code input depending on selected role
function syncSellerGoalFieldVisibility() {
    const shouldShow = editingUserId && DOM.sellerRole?.value === "vendedor";
    DOM.sellerMonthlyGoalGroup?.classList.toggle("hidden", !shouldShow);
}

if (DOM.sellerRole) {
    DOM.sellerRole?.addEventListener("change", (e) => {
        if (e.target.value === "vendedor") {
            DOM.sellerCodeGroup?.classList.remove("hidden");
            DOM.sellerParentGroup?.classList.remove("hidden");
        } else {
            DOM.sellerCodeGroup?.classList.add("hidden");
            DOM.sellerParentGroup?.classList.add("hidden");
            if (DOM.sellerCode) DOM.sellerCode.value = "";
            if (DOM.sellerParent) DOM.sellerParent.value = "";
        }
        syncSellerGoalFieldVisibility();
    });
}

DOM.btnAddSeller?.addEventListener("click", () => {
    editingUserId = null;
    DOM.sellerForm.reset();
    DOM.sellerFormTitle.textContent = "Registrar Nuevo Usuario";
    DOM.btnSubmitSeller.textContent = "Registrar Usuario";
    DOM.sellerPassword.required = true;
    DOM.sellerPasswordLabel.innerHTML = 'Contraseña Temporal';
    DOM.sellerCodeGroup.classList.remove("hidden");
    DOM.sellerParentGroup?.classList.remove("hidden");
    if (DOM.sellerMonthlyGoal) DOM.sellerMonthlyGoal.value = "";
    syncSellerGoalFieldVisibility();
    populateSellerParentOptions(null, null);
    DOM.sellerFormWrapper.classList.remove("hidden");
    DOM.sellerFormWrapper.scrollIntoView({ behavior: "smooth" });
});

DOM.btnCancelSeller?.addEventListener("click", () => {
    DOM.sellerFormWrapper.classList.add("hidden");
    editingUserId = null;
});

DOM.btnCloseSellerForm?.addEventListener("click", () => {
    DOM.sellerFormWrapper.classList.add("hidden");
    editingUserId = null;
});

function openEditUserForm(id, email, fullname, role, phone, code, parent, monthlyGoal) {
    console.log("openEditUserForm called with parameters:", { id, email, fullname, role, phone, code, parent, monthlyGoal });
    try {
        editingUserId = id;
        if (DOM.sellerFullname) DOM.sellerFullname.value = fullname || "";
        if (DOM.sellerRole) DOM.sellerRole.value = role || "vendedor";
        if (DOM.sellerEmail) DOM.sellerEmail.value = email || "";
        if (DOM.sellerPhone) DOM.sellerPhone.value = phone || "";
        if (DOM.sellerCode) DOM.sellerCode.value = code || "";
        if (DOM.sellerMonthlyGoal) DOM.sellerMonthlyGoal.value = monthlyGoal || "";
        if (DOM.sellerPassword) {
            DOM.sellerPassword.value = "";
            DOM.sellerPassword.required = false; // not required when editing
        }
        if (DOM.sellerPasswordLabel) {
            DOM.sellerPasswordLabel.innerHTML = 'Nueva Contraseña (dejar en blanco para mantener)';
        }

        // Trigger role visibility logic
        if (role === "vendedor") {
            DOM.sellerCodeGroup?.classList.remove("hidden");
            DOM.sellerParentGroup?.classList.remove("hidden");
            // Poblar select de padre y preseleccionar el actual
            populateSellerParentOptions(id, parent || null);
        } else {
            DOM.sellerCodeGroup?.classList.add("hidden");
            DOM.sellerParentGroup?.classList.add("hidden");
        }

        if (DOM.sellerFormTitle) DOM.sellerFormTitle.textContent = "Editar Usuario";
        if (DOM.btnSubmitSeller) DOM.btnSubmitSeller.textContent = "Guardar Cambios";
        syncSellerGoalFieldVisibility();

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

DOM.sellerForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = DOM.sellerEmail.value;
    const fullname = DOM.sellerFullname.value;
    const role = DOM.sellerRole.value;
    const phone = DOM.sellerPhone.value || null;
    const code = role === "vendedor" ? (DOM.sellerCode.value || null) : null;
    const password = DOM.sellerPassword.value || null;
    const parentId = role === "vendedor" ? (DOM.sellerParent?.value || "") : "";
    const monthlyGoal = DOM.sellerMonthlyGoal?.value;

    const payload = {
        email,
        nombre_completo: fullname,
        rol: role,
        telefono_whatsapp: phone,
        codigo_vendedor: code,
        vendedor_padre_id: parentId
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
            if (role === "vendedor" && monthlyGoal) {
                await apiRequest(`/api/v1/metas/mensual/${editingUserId}`, {
                    method: "PUT",
                    body: JSON.stringify({ monto_objetivo: Number(monthlyGoal) })
                });
            }
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
DOM.btnGenerateGoalsModal?.addEventListener("click", () => {
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

DOM.btnCancelAiGoals?.addEventListener("click", () => {
    DOM.aiGoalsWrapper.classList.add("hidden");
});

DOM.btnCloseAiGoals?.addEventListener("click", () => {
    DOM.aiGoalsWrapper.classList.add("hidden");
});

DOM.aiGoalsForm?.addEventListener("submit", async (e) => {
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
DOM.filterPromoFamilia?.addEventListener("change", () => {
    if (DOM.filterPromoSubfamilia) DOM.filterPromoSubfamilia.options.length = 1;
    loadPromocionesData(false);
});
DOM.filterPromoSubfamilia?.addEventListener("change", () => loadPromocionesData(false));
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
    if (DOM.filterPromoFamilia) DOM.filterPromoFamilia.value = 'todos';
    if (DOM.filterPromoSubfamilia) DOM.filterPromoSubfamilia.value = 'todas';
    loadPromocionesData(false);
});

document.getElementById('btn-promo-back')?.addEventListener("click", () => {
    if (DOM.btnClearPromoFilters) {
        DOM.btnClearPromoFilters.click();
    }
});
DOM.filterPromoStatus?.addEventListener("change", () => loadPromocionesData(false));
DOM.filterPromoSort?.addEventListener("change", () => loadPromocionesData(false));

/* --- Cotizaciones Handlers --- */
DOM.btnGenerateQuoteModal?.addEventListener("click", () => {
    DOM.aiQuoteWrapper.classList.remove("hidden");
});

DOM.btnCancelAiQuote?.addEventListener("click", () => {
    DOM.aiQuoteWrapper.classList.add("hidden");
});

DOM.btnCloseAiQuote?.addEventListener("click", () => {
    DOM.aiQuoteWrapper.classList.add("hidden");
});

DOM.btnAddItemRow?.addEventListener("click", () => {
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

DOM.aiQuoteForm?.addEventListener("submit", async (e) => {
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

DOM.searchQuoteClient?.addEventListener("input", () => {
    state.quotesCurrentPage = 1;
    window.quoteSearchTimeout && clearTimeout(window.quoteSearchTimeout);
    window.quoteSearchTimeout = setTimeout(() => loadCotizacionesData(true), 300);
});

DOM.filterQuoteSeller?.addEventListener("change", () => {
    state.activeHeatmapFilter = null;
    state.quotesCurrentPage = 1;
    loadCotizacionesData(true);
});

DOM.filterQuoteDays?.addEventListener("change", () => {
    state.activeHeatmapFilter = null;
    state.quotesCurrentPage = 1;
    loadCotizacionesData(true);
});

DOM.quoteFilterCards?.forEach(card => {
    const applyCardFilter = () => {
        const filterValue = card.getAttribute("data-quote-filter") || "all";
        state.activeHeatmapFilter = null;
        state.quotesCurrentPage = 1;
        updateActiveHeatmapFilterBadge();
        
        if (DOM.filterQuoteDays) {
            DOM.filterQuoteDays.value = filterValue;
        }
        
        if (DOM.quotesDetailsContent?.classList.contains("hidden")) {
            DOM.quotesDetailsContent.classList.remove("hidden");
            if (DOM.quotesDetailsToggleIcon) DOM.quotesDetailsToggleIcon.style.transform = "rotate(180deg)";
        }
        
        loadCotizacionesData(true);
    };
    
    card.addEventListener("click", applyCardFilter);
    card.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            applyCardFilter();
        }
    });
});

function getBusinessDateParts() {
    const parts = new Intl.DateTimeFormat("en-US", {
        timeZone: "America/Mazatlan",
        year: "numeric",
        month: "2-digit",
        day: "2-digit"
    }).formatToParts(new Date());
    const values = Object.fromEntries(parts.map(part => [part.type, part.value]));
    return { year: values.year, month: values.month, day: values.day };
}

function applyQuoteQuickPeriod(period) {
    const { year, month, day } = getBusinessDateParts();
    if (period === "today") {
        const today = `${year}-${month}-${day}`;
        DOM.filterQuoteStartDate.value = today;
        DOM.filterQuoteEndDate.value = today;
        if (DOM.filterQuotePeriodStatus) DOM.filterQuotePeriodStatus.textContent = `Hoy: ${today}`;
    } else if (period === "month") {
        DOM.filterQuoteStartDate.value = `${year}-${month}-01`;
        DOM.filterQuoteEndDate.value = `${year}-${month}-${day}`;
        if (DOM.filterQuotePeriodStatus) DOM.filterQuotePeriodStatus.textContent = `Mes actual: ${year}-${month}`;
    } else {
        DOM.filterQuoteStartDate.value = "";
        DOM.filterQuoteEndDate.value = "";
        if (DOM.filterQuotePeriodStatus) DOM.filterQuotePeriodStatus.textContent = "Todas las fechas";
    }
    state.activeHeatmapFilter = null;
    state.quotesCurrentPage = 1;
    loadCotizacionesData(true);
}

DOM.filterQuoteToday?.addEventListener("click", () => applyQuoteQuickPeriod("today"));
DOM.filterQuoteMonth?.addEventListener("click", () => applyQuoteQuickPeriod("month"));
DOM.filterQuoteAll?.addEventListener("click", () => applyQuoteQuickPeriod("all"));

if (DOM.filterQuoteStartDate) {
    DOM.filterQuoteStartDate?.addEventListener("change", () => {
        state.activeHeatmapFilter = null;
        state.quotesCurrentPage = 1;
        if (DOM.filterQuotePeriodStatus) DOM.filterQuotePeriodStatus.textContent = "Periodo personalizado";
        loadCotizacionesData();
    });
}

if (DOM.filterQuoteEndDate) {
    DOM.filterQuoteEndDate?.addEventListener("change", () => {
        state.activeHeatmapFilter = null;
        state.quotesCurrentPage = 1;
        if (DOM.filterQuotePeriodStatus) DOM.filterQuotePeriodStatus.textContent = "Periodo personalizado";
        loadCotizacionesData();
    });
}

DOM.btnClearHeatmapFilter?.addEventListener("click", () => {
    clearHeatmapQuoteFilter();
});

if (DOM.btnToggleQuotesDetails) {
    DOM.btnToggleQuotesDetails?.addEventListener("click", () => {
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
    DOM.kanbanSearchClient?.addEventListener("input", () => {
        state.kanbanCurrentPage = 1;
        window.kanbanSearchTimeout && clearTimeout(window.kanbanSearchTimeout);
        window.kanbanSearchTimeout = setTimeout(() => loadKanbanData(true), 300);
    });
}
if (DOM.kanbanFilterSeller) {
    DOM.kanbanFilterSeller?.addEventListener("change", () => {
        state.kanbanCurrentPage = 1;
        loadKanbanData(true);
    });
}
if (DOM.kanbanFilterDays) {
    DOM.kanbanFilterDays?.addEventListener("change", () => {
        state.kanbanCurrentPage = 1;
        loadKanbanData(true);
    });
}

// Quotes Table Sorting listeners
if (DOM.sortQuotesAsc) {
    DOM.sortQuotesAsc?.addEventListener("click", () => {
        state.quotesSortOrder = "asc";
        DOM.sortQuotesAsc.classList.add("active");
        if (DOM.sortQuotesDesc) DOM.sortQuotesDesc.classList.remove("active");
        state.quotesCurrentPage = 1;
        loadCotizacionesData(true);
    });
}

if (DOM.sortQuotesDesc) {
    DOM.sortQuotesDesc?.addEventListener("click", () => {
        state.quotesSortOrder = "desc";
        DOM.sortQuotesDesc.classList.add("active");
        if (DOM.sortQuotesAsc) DOM.sortQuotesAsc.classList.remove("active");
        state.quotesCurrentPage = 1;
        loadCotizacionesData(true);
    });
}

DOM.lostReasonForm?.addEventListener("submit", saveLostReason);
DOM.btnCloseLostReasonModal?.addEventListener("click", closeLostReasonModal);
DOM.btnCancelLostReason?.addEventListener("click", closeLostReasonModal);
DOM.lostReasonPrice?.addEventListener("change", () => {
    if (DOM.lostReasonPrice.checked && DOM.lostReasonStock) DOM.lostReasonStock.checked = false;
});
DOM.lostReasonStock?.addEventListener("change", () => {
    if (DOM.lostReasonStock.checked && DOM.lostReasonPrice) DOM.lostReasonPrice.checked = false;
});
DOM.quoteCommentsForm?.addEventListener("submit", saveQuoteComment);
DOM.btnCloseQuoteComments?.addEventListener("click", closeQuoteCommentsModal);
DOM.btnCancelQuoteComments?.addEventListener("click", closeQuoteCommentsModal);
DOM.btnCancelQuoteCommentEdit?.addEventListener("click", resetQuoteCommentEditor);
DOM.quoteCommentsModal?.addEventListener("click", event => {
    if (event.target === DOM.quoteCommentsModal) closeQuoteCommentsModal();
});
document.addEventListener("click", event => {
    const editButton = event.target.closest(".quote-comment-edit-btn");
    if (editButton) {
        event.preventDefault();
        if (DOM.quoteCommentsEditId) DOM.quoteCommentsEditId.value = editButton.dataset.id || "";
        if (DOM.quoteCommentsText) {
            DOM.quoteCommentsText.value = editButton.dataset.text || "";
            DOM.quoteCommentsText.focus();
        }
        if (DOM.quoteCommentsFormLabel) DOM.quoteCommentsFormLabel.textContent = "Editar comentario";
        if (DOM.btnSaveQuoteComment) DOM.btnSaveQuoteComment.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> Guardar cambios';
        DOM.btnCancelQuoteCommentEdit?.classList.remove("hidden");
        return;
    }
    const button = event.target.closest(".quote-comments-btn");
    if (!button) return;
    event.preventDefault();
    event.stopPropagation();
    const quote = state.cotizaciones.find(item => item.id === button.dataset.id);
    if (quote) openQuoteCommentsModal(quote);
});

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

/* ==========================================================================
   HU-1, HU-2, HU-3 FEATURE MODULES
   ========================================================================== */

// --- HU-2: CLIENT HISTORY MODAL ---
async function openClientHistoryModal(numeroCliente) {
    if (!numeroCliente) {
        showToast("Por favor ingresa un número de cliente.", "info");
        return;
    }
    const cleanNum = String(numeroCliente).trim();
    if (!cleanNum || !DOM.clientHistoryModal) return;

    if (DOM.clientHistorySubtitle) DOM.clientHistorySubtitle.textContent = `Consultando historial para el cliente: ${cleanNum}...`;
    if (DOM.clientHistoryTotalQuotes) DOM.clientHistoryTotalQuotes.textContent = "0";
    if (DOM.clientHistoryInvoicedCount) DOM.clientHistoryInvoicedCount.textContent = "0";
    if (DOM.clientHistoryTotalQuoted) DOM.clientHistoryTotalQuoted.textContent = "$0.00";
    if (DOM.clientHistoryTotalInvoiced) DOM.clientHistoryTotalInvoiced.textContent = "$0.00";
    if (DOM.clientHistoryConversionRate) DOM.clientHistoryConversionRate.textContent = "0%";
    if (DOM.clientHistoryTable) {
        DOM.clientHistoryTable.innerHTML = '<tr><td colspan="7" style="text-align: center;">Cargando historial...</td></tr>';
    }

    DOM.clientHistoryModal.classList.remove("hidden");

    try {
        const res = await apiRequest(`/api/v1/cotizaciones/historial-cliente?numero_cliente=${encodeURIComponent(cleanNum)}`);
        const data = res.data || {};
        const resumen = data.resumen || {};
        const ops = data.operaciones || [];

        const clientName = data.cliente_nombre ? `${data.cliente_nombre} (${cleanNum})` : `Cliente No. ${cleanNum}`;
        if (DOM.clientHistorySubtitle) DOM.clientHistorySubtitle.textContent = clientName;

        if (DOM.clientHistoryTotalQuotes) DOM.clientHistoryTotalQuotes.textContent = resumen.total_cotizaciones || 0;
        if (DOM.clientHistoryInvoicedCount) DOM.clientHistoryInvoicedCount.textContent = resumen.total_facturadas || 0;
        if (DOM.clientHistoryTotalQuoted) DOM.clientHistoryTotalQuoted.textContent = `$${formatNumber(resumen.importe_cotizado || 0)}`;
        if (DOM.clientHistoryTotalInvoiced) DOM.clientHistoryTotalInvoiced.textContent = `$${formatNumber(resumen.importe_facturado || 0)}`;
        if (DOM.clientHistoryConversionRate) DOM.clientHistoryConversionRate.textContent = `${resumen.tasa_conversion || 0}%`;

        if (DOM.clientHistoryTable) {
            DOM.clientHistoryTable.innerHTML = "";
            if (ops.length === 0) {
                DOM.clientHistoryTable.innerHTML = '<tr><td colspan="7" style="text-align: center;">No se registraron operaciones para este cliente.</td></tr>';
                return;
            }

            ops.forEach(op => {
                let statusBadge = `<span class="badge badge-secondary">${escapeHTML(op.estado || 'Pendiente')}</span>`;
                if (op.estado === "Facturado") {
                    statusBadge = `<span class="badge badge-success" style="background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.4);">Facturado</span>`;
                } else if (op.estado === "Venta Perdida") {
                    statusBadge = `<span class="badge badge-danger" style="background: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.4);">Venta Perdida</span>`;
                } else if (op.estado === "Expirada") {
                    statusBadge = `<span class="badge badge-secondary" style="background: rgba(156, 163, 175, 0.2); color: #9ca3af;">Expirada</span>`;
                } else if (op.estado === "Pendiente") {
                    statusBadge = `<span class="badge badge-warning" style="background: rgba(245, 158, 11, 0.2); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.4);">Pendiente</span>`;
                }

                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td><code>${escapeHTML(op.numero_cotizacion || 'S/N')}</code></td>
                    <td>${op.fecha_registro ? escapeHTML(op.fecha_registro.split('T')[0]) : '-'}</td>
                    <td>${escapeHTML(op.canal || '-')}</td>
                    <td><strong>$${formatNumber(op.total_cotizado || 0)}</strong></td>
                    <td>$${formatNumber(op.importe_facturado || 0)}${op.numero_factura ? ` <small class="text-muted">(${escapeHTML(op.numero_factura)})</small>` : ''}</td>
                    <td>${statusBadge}</td>
                    <td>${escapeHTML(op.vendedor_nombre || '-')}</td>
                `;
                DOM.clientHistoryTable.appendChild(tr);
            });
        }
    } catch (err) {
        showToast("Error al cargar historial del cliente: " + err.message, "error");
        if (DOM.clientHistoryTable) {
            DOM.clientHistoryTable.innerHTML = `<tr><td colspan="7" style="text-align: center; color: #ef4444;">${escapeHTML(err.message)}</td></tr>`;
        }
    }
}

function closeClientHistoryModal() {
    if (DOM.clientHistoryModal) DOM.clientHistoryModal.classList.add("hidden");
}

if (DOM.btnCloseClientHistory) DOM.btnCloseClientHistory.addEventListener("click", closeClientHistoryModal);
if (DOM.btnCancelClientHistory) DOM.btnCancelClientHistory.addEventListener("click", closeClientHistoryModal);
if (DOM.clientHistoryModal) {
    DOM.clientHistoryModal.addEventListener("click", (e) => {
        if (e.target === DOM.clientHistoryModal) closeClientHistoryModal();
    });
}

if (DOM.btnSearchClientHistory) {
    DOM.btnSearchClientHistory.addEventListener("click", () => {
        const val = DOM.searchClientHistoryInput ? DOM.searchClientHistoryInput.value : "";
        openClientHistoryModal(val);
    });
}
if (DOM.searchClientHistoryInput) {
    DOM.searchClientHistoryInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            openClientHistoryModal(DOM.searchClientHistoryInput.value);
        }
    });
}


// --- HU-3: POTENTIAL CLIENTS FOR PROMOTION MODAL ---
async function openPromoClientsModal(promoId) {
    if (!promoId || !DOM.promoClientsModal) return;

    if (DOM.promoClientsInfo) DOM.promoClientsInfo.textContent = "Cargando clientes potenciales...";
    if (DOM.promoClientsTable) {
        DOM.promoClientsTable.innerHTML = '<tr><td colspan="5" style="text-align: center;">Cargando clientes potenciales...</td></tr>';
    }

    DOM.promoClientsModal.classList.remove("hidden");

    try {
        const res = await apiRequest(`/api/v1/promociones/${promoId}/clientes-potenciales`);
        const data = res.data || {};
        const promo = data.promocion || {};
        const clients = data.clientes || [];

        const promoDesc = promo.descripcion_material || promo.codigo_material || "Material en Promoción";
        const promoPrice = promo.precio_promocion ? `$${formatNumber(promo.precio_promocion)}` : "Precio especial";
        const promoValid = promo.valido_hasta ? promo.valido_hasta.split("T")[0] : "por tiempo limitado";

        if (DOM.promoClientsInfo) {
            DOM.promoClientsInfo.innerHTML = `<strong>${escapeHTML(promoDesc)}</strong> · Precio Promo: <span style="color:#10b981; font-weight:700;">${escapeHTML(promoPrice)}</span> · Válido hasta: ${escapeHTML(promoValid)} · <strong>${data.total_clientes || clients.length} clientes potenciales</strong>`;
        }

        if (DOM.promoClientsTable) {
            DOM.promoClientsTable.innerHTML = "";
            if (clients.length === 0) {
                DOM.promoClientsTable.innerHTML = '<tr><td colspan="5" style="text-align: center;">No se encontraron clientes anteriores para este producto.</td></tr>';
                return;
            }

            clients.forEach(c => {
                const acciones = c.acciones || {};
                const contact = c.contacto || {};
                const phone = acciones.telefono || contact.contacto_preferente || contact.telefono || "";

                let actionButtons = [];

                if (acciones.whatsapp_url) {
                    actionButtons.push(`
                        <a href="${escapeHTML(acciones.whatsapp_url)}" target="_blank" rel="noopener" class="btn btn-sm btn-action-wa" title="Contactar por WhatsApp">
                            <i class="fa-brands fa-whatsapp"></i> WhatsApp
                        </a>
                    `);
                }

                if (acciones.email_url) {
                    actionButtons.push(`
                        <a href="${escapeHTML(acciones.email_url)}" class="btn btn-sm btn-action-email" title="Enviar Email">
                            <i class="fa-regular fa-envelope"></i> Email
                        </a>
                    `);
                }

                if (phone) {
                    actionButtons.push(`
                        <a href="tel:${escapeHTML(phone)}" class="btn btn-secondary btn-sm" title="Llamar">
                            <i class="fa-solid fa-phone"></i> ${escapeHTML(phone)}
                        </a>
                    `);
                }

                if (actionButtons.length === 0) {
                    actionButtons.push('<span class="text-muted" style="font-size: 12px;">Sin contacto disponible</span>');
                }

                const clientDisplay = `<strong>${escapeHTML(c.cliente_nombre || 'Cliente')}</strong>${c.numero_cliente ? `<br><small class="text-muted">No. ${escapeHTML(c.numero_cliente)}</small>` : ''}`;

                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td>${clientDisplay}</td>
                    <td>${escapeHTML(c.vendedor_nombre || '-')}</td>
                    <td>${c.ultima_compra ? escapeHTML(c.ultima_compra.split('T')[0]) : '-'}</td>
                    <td style="text-align: right; font-weight: 600;">${formatNumber(c.cantidad_comprada || 0)}</td>
                    <td><div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center;">${actionButtons.join('')}</div></td>
                `;
                DOM.promoClientsTable.appendChild(tr);
            });
        }
    } catch (err) {
        showToast("Error al cargar clientes potenciales: " + err.message, "error");
        if (DOM.promoClientsTable) {
            DOM.promoClientsTable.innerHTML = `<tr><td colspan="5" style="text-align: center; color: #ef4444;">${escapeHTML(err.message)}</td></tr>`;
        }
    }
}

function closePromoClientsModal() {
    if (DOM.promoClientsModal) DOM.promoClientsModal.classList.add("hidden");
}

if (DOM.btnClosePromoClients) DOM.btnClosePromoClients.addEventListener("click", closePromoClientsModal);
if (DOM.btnCancelPromoClients) DOM.btnCancelPromoClients.addEventListener("click", closePromoClientsModal);
if (DOM.promoClientsModal) {
    DOM.promoClientsModal.addEventListener("click", (e) => {
        if (e.target === DOM.promoClientsModal) closePromoClientsModal();
    });
}


// --- HU-1: SCHEDULED FOLLOW-UP REMINDERS ---
function openAddReminderModal(quoteId) {
    if (!quoteId || !DOM.addReminderModal) return;
    if (DOM.reminderQuoteId) DOM.reminderQuoteId.value = quoteId;
    if (DOM.reminderDateInput) {
        const todayStr = new Date().toISOString().split("T")[0];
        DOM.reminderDateInput.value = todayStr;
    }
    if (DOM.reminderNoteInput) DOM.reminderNoteInput.value = "";
    DOM.addReminderModal.classList.remove("hidden");
}

function closeAddReminderModal() {
    if (DOM.addReminderModal) DOM.addReminderModal.classList.add("hidden");
    if (DOM.addReminderForm) DOM.addReminderForm.reset();
}

if (DOM.btnCloseAddReminder) DOM.btnCloseAddReminder.addEventListener("click", closeAddReminderModal);
if (DOM.btnCancelAddReminder) DOM.btnCancelAddReminder.addEventListener("click", closeAddReminderModal);
if (DOM.addReminderModal) {
    DOM.addReminderModal.addEventListener("click", (e) => {
        if (e.target === DOM.addReminderModal) closeAddReminderModal();
    });
}

if (DOM.addReminderForm) {
    DOM.addReminderForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const quoteId = DOM.reminderQuoteId ? DOM.reminderQuoteId.value : "";
        const dateVal = DOM.reminderDateInput ? DOM.reminderDateInput.value : "";
        const noteVal = DOM.reminderNoteInput ? DOM.reminderNoteInput.value : "";
        await saveReminder(quoteId, dateVal, noteVal);
    });
}

async function saveReminder(quoteId, dateVal, noteVal) {
    if (!quoteId || !dateVal) {
        showToast("Por favor selecciona una fecha programada.", "error");
        return;
    }
    try {
        const payload = {
            fecha_programada: dateVal,
            nota: noteVal ? noteVal.trim() : null
        };
        const res = await apiRequest(`/api/v1/cotizaciones/${quoteId}/recordatorio`, {
            method: "POST",
            body: JSON.stringify(payload)
        });
        if (res.status === "success") {
            showToast(res.message || "Recordatorio agendado exitosamente.", "success");
            closeAddReminderModal();
            await loadPendingReminders();
        }
    } catch (err) {
        showToast("Error al guardar recordatorio: " + err.message, "error");
    }
}

async function toggleReminderComplete(reminderId, completed) {
    try {
        const res = await apiRequest(`/api/v1/cotizaciones/recordatorios/${reminderId}`, {
            method: "PATCH",
            body: JSON.stringify({ completado: completed })
        });
        if (res.status === "success") {
            showToast(completed ? "Recordatorio marcado como completado." : "Recordatorio actualizado.", "success");
            await loadPendingReminders();
        }
    } catch (err) {
        showToast("Error al actualizar recordatorio: " + err.message, "error");
    }
}

async function loadPendingReminders() {
    if (!state.token || !state.user || state.user.rol === "soporte") return;
    try {
        const res = await apiRequest("/api/v1/cotizaciones/recordatorios/pendientes");
        state.pendingReminders = res.data || [];
        const pendingCount = state.pendingReminders.length;
        if (DOM.remindersNavBadge) {
            DOM.remindersNavBadge.textContent = pendingCount;
            if (pendingCount > 0) {
                DOM.remindersNavBadge.classList.remove("hidden");
            } else {
                DOM.remindersNavBadge.classList.add("hidden");
            }
        }

        if (DOM.dailyRemindersBadgeCount) {
            DOM.dailyRemindersBadgeCount.textContent = `${pendingCount} pendiente${pendingCount !== 1 ? 's' : ''}`;
        }

        if (DOM.dailyRemindersList) {
            if (state.pendingReminders.length === 0) {
                DOM.dailyRemindersList.innerHTML = `<p class="text-muted" style="margin: 0; padding: 12px 0;">No tienes seguimientos pendientes agendados.</p>`;
            } else {
                const todayStr = new Date().toISOString().split("T")[0];
                DOM.dailyRemindersList.innerHTML = state.pendingReminders.map(r => {
                    const rDate = r.fecha_programada ? r.fecha_programada.split("T")[0] : "";
                    const isPast = rDate && rDate < todayStr;
                    const isToday = rDate === todayStr;
                    let badgeClass = "badge-primary";
                    let badgeText = rDate;
                    if (isPast) {
                        badgeClass = "badge-danger";
                        badgeText = `${rDate} (Vencido)`;
                    } else if (isToday) {
                        badgeClass = "badge-warning";
                        badgeText = `${rDate} (Hoy)`;
                    }

                    return `
                        <div class="reminder-item-card glass-card" style="display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; gap: 16px; border-radius: 8px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08);">
                            <div style="display: flex; align-items: center; gap: 12px; flex: 1;">
                                <input type="checkbox" class="reminder-checkbox" data-id="${r.id}" style="width: 18px; height: 18px; cursor: pointer; accent-color: #10b981;">
                                <div style="display: flex; flex-direction: column; gap: 2px;">
                                    <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                                        <strong style="font-size: 14px; color: hsl(var(--text-primary));">${escapeHTML(r.cliente_nombre || "Cliente")}</strong>
                                        ${r.numero_cotizacion ? `<span style="font-size: 12px; color: #38bdf8; font-weight: 600;">Cotización #${escapeHTML(r.numero_cotizacion)}</span>` : ""}
                                        <span class="badge ${badgeClass}" style="font-size: 11px;">${escapeHTML(badgeText)}</span>
                                    </div>
                                    ${r.nota ? `<p style="font-size: 13px; color: hsl(var(--text-secondary)); margin: 2px 0 0 0;">${escapeHTML(r.nota)}</p>` : ""}
                                </div>
                            </div>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <button type="button" class="btn btn-secondary btn-sm" onclick="openQuoteCommentsModal({ id: '${r.cotizacion_id}', cliente_nombre: '${escapeHTML(r.cliente_nombre || '')}' })" title="Ver comentarios de seguimiento">
                                    <i class="fa-regular fa-comments"></i>
                                </button>
                                ${r.numero_cliente ? `<button type="button" class="btn btn-secondary btn-sm" onclick="openClientHistoryModal('${escapeHTML(r.numero_cliente)}')" title="Historial del Cliente"><i class="fa-solid fa-clock-rotate-left"></i></button>` : ''}
                            </div>
                        </div>
                    `;
                }).join("");

                DOM.dailyRemindersList.querySelectorAll(".reminder-checkbox").forEach(chk => {
                    chk.addEventListener("change", (e) => {
                        const id = e.target.getAttribute("data-id");
                        if (id) toggleReminderComplete(id, e.target.checked);
                    });
                });
            }
        }

        if (state.currentSection === "seguimiento") {
            renderKanbanColumns();
        }
    } catch (err) {
        console.error("Error loading pending reminders:", err);
    }
}

if (DOM.remindersNavBtn) {
    DOM.remindersNavBtn.addEventListener("click", () => {
        switchSection("summary");
        if (DOM.dailyRemindersCard) {
            DOM.dailyRemindersCard.scrollIntoView({ behavior: "smooth" });
        }
    });
}


DOM.btnCloseProposalModal?.addEventListener("click", closeModal);
DOM.btnCloseProposal?.addEventListener("click", closeModal);
DOM.proposalModal?.addEventListener("click", (e) => {
    if (e.target === DOM.proposalModal) closeModal();
});

DOM.btnCopyProposal?.addEventListener("click", () => {
    const text = DOM.modalProposalBody.textContent;
    navigator.clipboard.writeText(text).then(() => {
        showToast("Copiado al portapapeles");
    }).catch(e => {
        showToast("Fallo al copiar texto", "error");
    });
});

/* ==========================================================================
   SIDEBAR MENU REORDERING (DRAG & DROP)
   ========================================================================== */

const FIXED_SYSTEM_MENU_ORDER = [
    "summary",
    "seguimiento",
    "cotizaciones",
    "promociones",
    "inventario-abcf",
    "sobrepedidos",
    "por-entregar",
    "vendedores",
    "metas",
    "agentes",
    "slight-edge",
    "asignacion",
    "api"
];

function restoreSavedMenuOrder() {
    const menuContainer = document.getElementById("sidebar-menu");
    if (!menuContainer) return;

    // Purge ALL legacy custom menu order keys from localStorage
    try {
        for (let i = localStorage.length - 1; i >= 0; i--) {
            const key = localStorage.key(i);
            if (key && key.startsWith("crm_menu_order")) {
                localStorage.removeItem(key);
            }
        }
    } catch (e) {
        // Ignore storage errors
    }

    // Force strict DOM reordering according to FIXED_SYSTEM_MENU_ORDER
    const currentItemsMap = new Map();
    const items = Array.from(menuContainer.querySelectorAll(".menu-item"));
    items.forEach(item => {
        const sec = item.getAttribute("data-section");
        if (sec) currentItemsMap.set(sec, item);
    });

    FIXED_SYSTEM_MENU_ORDER.forEach(secId => {
        if (currentItemsMap.has(secId)) {
            menuContainer.appendChild(currentItemsMap.get(secId));
            currentItemsMap.delete(secId);
        }
    });

    // Append any remaining items if added in future
    currentItemsMap.forEach(item => {
        menuContainer.appendChild(item);
    });

    DOM.menuItems = document.querySelectorAll(".menu-item");
}

function saveCurrentMenuOrder() {
    // Menu order is fixed by specification; custom reordering is disabled.
}

function initSidebarMenuDragAndDrop() {
    const menuContainer = document.getElementById("sidebar-menu");
    if (!menuContainer) return;

    menuContainer.querySelectorAll(".menu-item").forEach(item => {
        item.draggable = false;
        item.removeAttribute("draggable");
    });
}

// Initialize Sidebar Menu on startup
initSidebarMenuDragAndDrop();

// Sidebar collapse persistence on load
if (localStorage.getItem("sidebar_collapsed") === "true" && DOM.sidebar) {
    DOM.sidebar.classList.add("collapsed");
}

if (DOM.btnToggleSidebar) {
    DOM.btnToggleSidebar?.addEventListener("click", () => {
        if (DOM.sidebar) {
            DOM.sidebar.classList.toggle("collapsed");
            const isCollapsed = DOM.sidebar.classList.contains("collapsed");
            localStorage.setItem("sidebar_collapsed", isCollapsed);
        }
    });
}

/* ==========================================================================
   FIXED SIDEBAR MENU
   ========================================================================== */

function initSidebarDrag() {
    document.querySelectorAll(".sidebar-menu .menu-item").forEach(item => {
        item.draggable = false;
        item.removeAttribute("draggable");
    });
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initSidebarDrag);
} else {
    initSidebarDrag();
}

// Theme Toggle Handler
if (DOM.themeToggleBtn) {
    DOM.themeToggleBtn?.addEventListener("click", () => {
        toggleTheme();
    });
}

// User Profile Modal Handlers
if (DOM.userAvatarBtn) {
    DOM.userAvatarBtn?.addEventListener("click", () => {
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

if (DOM.btnCloseProfileModal) DOM.btnCloseProfileModal?.addEventListener("click", closeProfileModal);
if (DOM.btnCancelProfile) DOM.btnCancelProfile?.addEventListener("click", closeProfileModal);
if (DOM.profileModal) {
    DOM.profileModal?.addEventListener("click", (e) => {
        if (e.target === DOM.profileModal) closeProfileModal();
    });
}

// Click trigger for circular avatar uploader
if (DOM.profileAvatarUploader && DOM.inputProfileAvatar) {
    DOM.profileAvatarUploader?.addEventListener("click", () => {
        DOM.inputProfileAvatar.click();
    });
}

// Convert uploaded photo to Base64
let profileAvatarBase64 = null;
if (DOM.inputProfileAvatar) {
    DOM.inputProfileAvatar?.addEventListener("change", (e) => {
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
    DOM.profileForm?.addEventListener("submit", async (e) => {
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
    if (savedTheme === "dark") {
        document.body.classList.remove("light-mode");
        if (DOM.themeToggleIcon) {
            DOM.themeToggleIcon.className = "fa-solid fa-moon";
        }
    } else {
        document.body.classList.add("light-mode");
        localStorage.setItem("theme_mode", "light");
        if (DOM.themeToggleIcon) {
            DOM.themeToggleIcon.className = "fa-solid fa-sun";
        }
    }
}

function toggleTheme() {
    const isLight = document.body.classList.toggle("light-mode");
    const newTheme = isLight ? "light" : "dark";
    localStorage.setItem("theme_mode", newTheme);
    if (DOM.themeToggleIcon) {
        DOM.themeToggleIcon.className = isLight ? "fa-solid fa-sun" : "fa-solid fa-moon";
    }
}

/* ==========================================================================
   INITIALIZATION
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    initSession();

    if (DOM.metasMonth && !DOM.metasMonth.value) DOM.metasMonth.value = getCurrentMonthValue();
    if (DOM.metasReferenceDate && !DOM.metasReferenceDate.value) DOM.metasReferenceDate.value = currentDateValue();
    DOM.metasType?.addEventListener("change", renderCommercialGoalScopeFields);
    DOM.metasSellerFilter?.addEventListener("change", () => {
        renderCommercialGoalsDashboard(state.commercialGoalsDashboard);
        renderCommercialGoalsTable();
    });
    DOM.btnLoadMetas?.addEventListener("click", async () => {
        resetCommercialGoalForm();
        try {
            await loadCommercialGoalsData();
        } catch (error) {
            showToast(error.message, "error");
        }
    });
    DOM.btnCancelMetasEdit?.addEventListener("click", resetCommercialGoalForm);
    DOM.metasForm?.addEventListener("submit", async event => {
        event.preventDefault();
        const type = DOM.metasType.value;
        const payload = {
            monto_objetivo: Number(DOM.metasTarget.value),
            descripcion: DOM.metasDescription.value.trim() || null,
        };
        if (!payload.monto_objetivo || payload.monto_objetivo <= 0) {
            showToast("Indica una meta mayor a cero.", "error");
            return;
        }
        try {
            if (state.editingCommercialGoalId) {
                await apiRequest(`/api/v1/metas/comerciales/${state.editingCommercialGoalId}`, {
                    method: "PUT",
                    body: JSON.stringify(payload),
                });
                showToast("Meta actualizada.");
            } else {
                const createPayload = {
                    ...payload,
                    tipo: type,
                    mes: metasMonthAsDate(),
                    vendedor_id: type === "vendedor" ? (DOM.metasVendedor.value || null) : null,
                    sucursal: type === "sucursal" ? (DOM.metasSucursal.value.trim() || null) : null,
                };
                await apiRequest("/api/v1/metas/comerciales", {
                    method: "POST",
                    body: JSON.stringify(createPayload),
                });
                showToast("Meta creada.");
            }
            resetCommercialGoalForm();
            await loadCommercialGoalsData();
        } catch (error) {
            showToast(error.message, "error");
        }
    });

    if (DOM.sellerDashboardSearch) {
        DOM.sellerDashboardSearch.addEventListener("input", () => {
            if (state.user?.rol === "vendedor" && state.currentSection === "summary") {
                renderSellerHomeDashboard({
                    metas: state.metas || [],
                    quotes: state.cotizaciones || [],
                    promociones: state.promociones || [],
                    goalProgress: state.sellerGoalProgress
                });
            }
        });
    }

    DOM.sellerDashboardToday?.addEventListener("click", async () => {
        state.sellerGoalPeriod = "day";
        await refreshSellerGoalProgress();
        await renderSellerHomeDashboard({
            metas: state.metas || [],
            quotes: state.cotizaciones || [],
            promociones: state.promociones || [],
            goalProgress: state.sellerGoalProgress
        });
    });

    DOM.sellerQuickSearch?.addEventListener("click", () => {
        DOM.sellerDashboardSearch?.focus();
    });

    DOM.sellerPeriodButtons.forEach(button => {
        button.addEventListener("click", async () => {
            if (state.user?.rol !== "vendedor") return;
            state.sellerGoalPeriod = button.dataset.sellerPeriod || "month";
            await refreshSellerGoalProgress();
            await renderSellerHomeDashboard({
                metas: state.metas || [],
                quotes: state.cotizaciones || [],
                promociones: state.promociones || [],
                goalProgress: state.sellerGoalProgress
            });
        });
    });

    if (DOM.sellerHomeDashboard) {
        DOM.sellerHomeDashboard.addEventListener("click", (event) => {
            const jumpButton = event.target.closest("[data-seller-jump]");
            if (!jumpButton) return;
            event.preventDefault();
            switchSection(jumpButton.getAttribute("data-seller-jump"));
        });
    }

    if (DOM.sellerDashboardProfile) {
        DOM.sellerDashboardProfile.addEventListener("click", () => {
            if (DOM.userAvatarBtn) DOM.userAvatarBtn.click();
        });
    }
    
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
        DOM.slightEdgeDate?.addEventListener("change", () => {
            loadSellerSlightEdgePlanAndLog();
        });
    }

    // Setup Slight Edge Funnel Real toggle listener
    if (DOM.toggleFunnelReal) {
        DOM.toggleFunnelReal?.addEventListener("change", () => {
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
        DOM.selectSortSellers?.addEventListener("change", () => {
            loadVendedoresData();
        });
    }

    // Setup Slight Edge Chat Form
    if (DOM.slightEdgeChatForm) {
        DOM.slightEdgeChatForm?.addEventListener("submit", handleSlightEdgeChatSubmit);
    }

    // Setup Checklist Save Button
    if (DOM.btnSaveSlightEdgeLog) {
        DOM.btnSaveSlightEdgeLog?.addEventListener("click", saveSlightEdgeLog);
    }

    // Setup Company Target Settings Form
    if (DOM.companySettingsForm) {
        DOM.companySettingsForm?.addEventListener("submit", handleCompanySettingsSubmit);
    }

    // Close AI recommendation panel
    if (DOM.btnCloseSlightEdgeAi) {
        DOM.btnCloseSlightEdgeAi?.addEventListener("click", () => {
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
        DOM.btnSlightEdgeBackToDashboard?.addEventListener("click", () => {
            toggleSlightEdgeMode("dashboard");
        });
    }

    // Adjust with Coach button listener
    if (DOM.btnSlightEdgeAdjustCoach) {
        DOM.btnSlightEdgeAdjustCoach?.addEventListener("click", () => {
            toggleSlightEdgeMode("coaching");
            if (DOM.btnSlightEdgeBackToDashboard) DOM.btnSlightEdgeBackToDashboard.classList.remove("hidden");
        });
    }

    // Adjust Weights button listener
    if (DOM.btnSlightEdgeAdjustWeights) {
        DOM.btnSlightEdgeAdjustWeights?.addEventListener("click", () => {
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
        DOM.btnSlightEdgeNewTask?.addEventListener("click", () => {
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
        DOM.btnSlightEdgeSummaryCoach?.addEventListener("click", () => {
            switchSection("slight-edge");
            toggleSlightEdgeMode("coaching");
            if (DOM.btnSlightEdgeBackToDashboard) DOM.btnSlightEdgeBackToDashboard.classList.remove("hidden");
        });
    }
    if (DOM.btnSlightEdgeSummaryGo) {
        DOM.btnSlightEdgeSummaryGo?.addEventListener("click", () => {
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

        // Fetch logs for the historical consistency chart
        const historyRes = await apiRequest(`/api/slight-edge/log/${state.user.id}`);
        const historyLogs = historyRes.data || [];

        // Now calculate real metrics for the current calendar month
        const now = new Date();
        const currentYear = now.getFullYear();
        const currentMonth = now.getMonth(); // 0-indexed
        const monthStart = `${currentYear}-${String(currentMonth + 1).padStart(2, "0")}-01`;
        const monthEnd = `${currentYear}-${String(currentMonth + 1).padStart(2, "0")}-${String(new Date(currentYear, currentMonth + 1, 0).getDate()).padStart(2, "0")}`;
        let quoteSummary = null;
        try {
            const quotesRes = await apiRequest(`/api/v1/cotizaciones/?limit=1&vista=resumen&fecha_inicio=${monthStart}&fecha_fin=${monthEnd}`);
            quoteSummary = quotesRes.summary || null;
        } catch (qErr) {
            console.error("Error fetching quote summary for slight edge:", qErr);
        }
        const monthlyQuotes = Number(quoteSummary?.total?.count || 0);
        const wonQuotes = Number(quoteSummary?.concretadas?.count || 0);
        const realMoneyWon = Number(quoteSummary?.concretadas?.invoiced_amount || 0);
        const realTicketAvg = wonQuotes > 0 ? (realMoneyWon / wonQuotes) : 0;
        const realConversionRate = monthlyQuotes > 0 ? (wonQuotes / monthlyQuotes * 100) : 0;

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
            sales: wonQuotes,
            quotes: monthlyQuotes,
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
        if (DOM.coordinatorPerformanceStart && !DOM.coordinatorPerformanceStart.value) {
            const { year, month, day } = getBusinessDateParts();
            DOM.coordinatorPerformanceStart.value = `${year}-${month}-01`;
            DOM.coordinatorPerformanceEnd.value = `${year}-${month}-${day}`;
        }
        const performanceParams = new URLSearchParams();
        if (DOM.coordinatorPerformanceStart?.value) {
            performanceParams.set("fecha_inicio", DOM.coordinatorPerformanceStart.value);
        }
        if (DOM.coordinatorPerformanceEnd?.value) {
            performanceParams.set("fecha_fin", DOM.coordinatorPerformanceEnd.value);
        }
        const [res, performance] = await Promise.all([
            apiRequest("/companies/kuroda/dashboard"),
            apiRequest(`/api/v1/analitica/rendimiento-asesores?${performanceParams.toString()}`)
        ]);
        if (DOM.coordinatorPerformancePeriodStatus) {
            DOM.coordinatorPerformancePeriodStatus.textContent =
                `${performance.filters?.fecha_inicio || "Inicio"} a ${performance.filters?.fecha_fin || "hoy"}`;
        }
        
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
        const sellers = performance.data || [];

        if (sellers.length === 0) {
            DOM.tableSlightEdgePerformance.innerHTML = '<tr><td colspan="10" style="text-align: center;">No hay vendedores registrados.</td></tr>';
            return;
        }

        sellers.forEach(s => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>
                    <strong class="seller-burndown-trigger" data-id="${s.vendedor_id}" data-name="${escapeHTML(s.vendedor)}" style="cursor: pointer; color: #38bdf8;">
                        ${escapeHTML(s.vendedor)} <i class="fa-solid fa-chart-line" style="font-size: 11px; margin-left: 4px; color: #a78bfa;"></i>
                    </strong>
                </td>
                <td>$${Number(s.meta).toLocaleString("es-MX")}</td>
                <td>$${Number(s.venta_facturada).toLocaleString("es-MX")}</td>
                <td><span class="status-pill">${Number(s.cumplimiento).toFixed(1)}%</span></td>
                <td>${s.cotizaciones}</td>
                <td><span class="status-pill" style="background: rgba(16,185,129,0.1); color: #10b981; border: 1px solid rgba(16,185,129,0.2);">${s.conversion}%</span></td>
                <td>$${Number(s.ticket_promedio).toLocaleString("es-MX")}</td>
                <td>${s.pendientes}</td>
                <td>${s.consistencia_promedio} pts</td>
                <td>
                    <button class="btn btn-secondary btn-sm btn-audit-slight-edge-ai" data-id="${s.vendedor_id}" data-name="${escapeHTML(s.vendedor)}">
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

        // El burndown usa una muestra reciente para sus barras diarias; los
        // indicadores comerciales del modal se calculan con el plan y bitácora.
        const quotesRes = await apiRequest(`/api/v1/cotizaciones/?vendedor_id=${sellerId}&limit=100&vista=resumen`);
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

DOM.btnCoordinatorPerformanceFilter?.addEventListener("click", () => {
    const start = DOM.coordinatorPerformanceStart?.value;
    const end = DOM.coordinatorPerformanceEnd?.value;
    if (start && end && end < start) {
        showToast("La fecha final no puede ser anterior a la inicial.", "error");
        return;
    }
    loadCoordinatorSlightEdgeDashboard();
});

DOM.btnCoordinatorPerformanceMonth?.addEventListener("click", () => {
    const { year, month, day } = getBusinessDateParts();
    if (DOM.coordinatorPerformanceStart) DOM.coordinatorPerformanceStart.value = `${year}-${month}-01`;
    if (DOM.coordinatorPerformanceEnd) DOM.coordinatorPerformanceEnd.value = `${year}-${month}-${day}`;
    loadCoordinatorSlightEdgeDashboard();
});

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
            listAvailable.innerHTML = `<p style="font-size: 13px; color: #64748b; text-align: center; margin: 20px 0;">No hay clientes disponibles para asignación.</p>`;
        } else {
            availableClients.forEach(c => {
                const item = document.createElement("div");
                item.style = "display: flex; align-items: flex-start; gap: 12px; background: #ffffff; border: 1px solid #e2e8f0; padding: 12px 14px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);";
                item.innerHTML = `
                    <input type="checkbox" class="client-checkbox" value="${c.id}" style="margin-top: 3px; cursor: pointer; width: 16px; height: 16px; accent-color: #ef4444;">
                    <div style="flex: 1; min-width: 0;">
                        <strong style="font-size: 14px; font-weight: 700; color: #0f172a; display: block; line-height: 1.3;">${escapeHTML(c.nombre)}</strong>
                        <span style="font-size: 12px; color: #64748b; display: block; margin-top: 3px;">
                            ${buildContactHtml({ email: c.email, telefono: c.telefono })}
                        </span>
                        ${c.comentarios ? `<p style="margin: 6px 0 0 0; font-size: 12px; color: #0369a1; background: #f0f9ff; padding: 4px 8px; border-radius: 4px; border: 1px solid #bae6fd;">${escapeHTML(c.comentarios)}</p>` : ''}
                    </div>
                `;
                listAvailable.appendChild(item);
            });
        }

        // 4. Render Sellers
        listSellers.innerHTML = "";
        const activeSellers = sellers.filter(s => s.rol === "vendedor");
        if (activeSellers.length === 0) {
            listSellers.innerHTML = `<p style="font-size: 13px; color: #64748b; text-align: center; margin: 20px 0;">No hay vendedores registrados.</p>`;
        } else {
            activeSellers.forEach(s => {
                const item = document.createElement("div");
                item.style = "display: flex; align-items: center; gap: 12px; background: #ffffff; border: 1px solid #e2e8f0; padding: 10px 14px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);";
                const codeBadge = s.codigo_vendedor 
                    ? `<span style="background: #ede9fe; color: #6d28d9; padding: 2px 7px; border-radius: 4px; font-size: 11px; font-weight: 700; border: 1px solid #ddd6fe; margin-right: 6px;">${escapeHTML(s.codigo_vendedor)}</span>`
                    : '';
                const nameText = escapeHTML(s.nombre_completo || s.email);
                item.innerHTML = `
                    <input type="checkbox" class="seller-checkbox" value="${s.id}" style="cursor: pointer; width: 16px; height: 16px; accent-color: #ef4444;">
                    <div style="flex: 1; min-width: 0;">
                        <strong style="font-size: 13.5px; font-weight: 600; color: #0f172a;">${codeBadge}${nameText}</strong>
                        ${s.email && s.nombre_completo ? `<span style="font-size: 11.5px; color: #64748b; display: block; margin-top: 1px;">${escapeHTML(s.email)}</span>` : ''}
                    </div>
                `;
                listSellers.appendChild(item);
            });
        }

        // 5. Render Active Auctions
        activeAuctions.innerHTML = "";
        const auctionClients = clients.filter(c => c.estado === "en_subasta");
        if (auctionClients.length === 0) {
            activeAuctions.innerHTML = `<p style="font-size: 13px; color: #64748b; text-align: center; margin: 20px 0;">No hay subastas activas en este momento.</p>`;
        } else {
            auctionClients.forEach(c => {
                const item = document.createElement("div");
                item.style = "background: #ffffff; border: 1px solid #e2e8f0; padding: 18px; border-radius: 10px; border-left: 4px solid #f59e0b; box-shadow: 0 2px 4px rgba(0,0,0,0.04); margin-bottom: 14px;";
                
                let bidsHtml = "";
                if (!c.pujas || c.pujas.length === 0) {
                    bidsHtml = `<p style="font-size: 12px; color: #94a3b8; margin: 10px 0 0 0; font-style: italic;">Esperando postulaciones de los vendedores...</p>`;
                } else {
                    bidsHtml = `
                        <div style="margin-top: 14px; display: flex; flex-direction: column; gap: 10px; border-top: 1px solid #e2e8f0; padding-top: 14px;">
                            <h4 style="margin: 0 0 6px 0; font-size: 13px; color: #d97706; font-weight: 700;">Postulaciones Recibidas (${c.pujas.length}):</h4>
                            ${c.pujas.map(p => `
                                <div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 12px; border-radius: 6px; display: flex; justify-content: space-between; align-items: flex-start; gap: 14px;">
                                    <div style="flex: 1; min-width: 0;">
                                        <span style="font-size: 12px; color: #6d28d9; font-weight: 700;">
                                            ${escapeHTML(p.vendedor ? (p.vendedor.nombre_completo || p.vendedor.email) : 'Vendedor')}
                                        </span>
                                        <p style="margin: 6px 0 0 0; font-size: 13px; color: #1e293b; line-height: 1.4;">
                                            "${escapeHTML(p.razon)}"
                                        </p>
                                    </div>
                                    <button class="btn btn-primary btn-sm btn-approve-bid" data-client="${c.id}" data-bid="${p.id}" style="padding: 6px 14px; font-size: 12px; font-weight: 600; white-space: nowrap;">
                                        <i class="fa-solid fa-check"></i> Asignar
                                    </button>
                                </div>
                            `).join('')}
                        </div>
                    `;
                }

                item.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 12px;">
                        <div style="flex: 1; min-width: 0;">
                            <strong style="font-size: 15px; font-weight: 700; color: #0f172a;">${escapeHTML(c.nombre)}</strong>
                            <span style="font-size: 12px; color: #64748b; display: block; margin-top: 3px;">
                                ${buildContactHtml({ email: c.email, telefono: c.telefono })}
                            </span>
                            ${c.comentarios ? `<p style="margin: 6px 0 0 0; font-size: 12px; color: #64748b;">${escapeHTML(c.comentarios)}</p>` : ''}
                        </div>
                        <span class="badge" style="background: #fef3c7; color: #b45309; border: 1px solid #fde68a; font-size: 11px; font-weight: 600; padding: 4px 8px; border-radius: 4px;">En Subasta</span>
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
            listSellers.innerHTML = `<p style="font-size: 13px; color: #64748b; text-align: center; margin: 20px 0;">No tienes subastas disponibles ni clientes asignados.</p>`;
            return;
        }

        // Render Auctions
        if (auctions.length > 0) {
            const auctionTitle = document.createElement("h4");
            auctionTitle.style = "margin: 10px 0; font-size: 14px; color: #d97706; font-weight: 700;";
            auctionTitle.textContent = "Subastas Activas:";
            listSellers.appendChild(auctionTitle);

            auctions.forEach(c => {
                // Check if this seller has already bid
                const myBid = c.pujas ? c.pujas.find(p => p.vendedor_id === state.user.id) : null;
                
                const item = document.createElement("div");
                item.style = "background: #ffffff; border: 1px solid #e2e8f0; padding: 18px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; gap: 20px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);";
                
                let actionHtml = "";
                if (myBid) {
                    actionHtml = `
                        <div style="text-align: right;">
                            <span class="badge" style="background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; font-size: 11px; font-weight: 600; display: inline-block; margin-bottom: 4px; padding: 3px 8px; border-radius: 4px;">Propuesta Enviada</span>
                            <span style="font-size: 11px; color: #64748b; display: block;">"${escapeHTML(myBid.razon.substring(0, 30))}..."</span>
                        </div>
                    `;
                } else {
                    actionHtml = `
                        <button class="btn btn-sm btn-pujar-cliente" data-id="${c.id}" data-nombre="${escapeHTML(c.nombre)}" style="background: linear-gradient(135deg, #f59e0b, #d97706); border: none; font-weight: bold; color: #fff; padding: 8px 16px;">
                            <i class="fa-solid fa-gavel"></i> Pujar
                        </button>
                    `;
                }

                item.innerHTML = `
                    <div style="flex: 1; min-width: 0;">
                        <strong style="font-size: 15px; font-weight: 700; color: #0f172a;">${escapeHTML(c.nombre)}</strong>
                        ${c.comentarios ? `<p style="margin: 6px 0 0 0; font-size: 12px; color: #64748b;">${escapeHTML(c.comentarios)}</p>` : ''}
                    </div>
                    ${actionHtml}
                `;
                listSellers.appendChild(item);
            });
        }

        // Render Assigned Clientes
        if (assigned.length > 0) {
            const assignedTitle = document.createElement("h4");
            assignedTitle.style = "margin: 20px 0 10px 0; font-size: 14px; color: #059669; font-weight: 700;";
            assignedTitle.textContent = "Mis Clientes Asignados:";
            listSellers.appendChild(assignedTitle);

            assigned.forEach(c => {
                const item = document.createElement("div");
                item.style = "background: #ffffff; border: 1px solid #e2e8f0; padding: 16px; border-radius: 8px; border-left: 4px solid #10b981; display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);";
                item.innerHTML = `
                    <div style="flex: 1; min-width: 0;">
                        <strong style="font-size: 15px; font-weight: 700; color: #0f172a;">${escapeHTML(c.nombre)}</strong>
                        <span style="font-size: 12px; color: #64748b; display: block; margin-top: 3px;">
                            ${buildContactHtml({ email: c.email, telefono: c.telefono })}
                        </span>
                        ${c.comentarios ? `<p style="margin: 6px 0 0 0; font-size: 12px; color: #64748b;">${escapeHTML(c.comentarios)}</p>` : ''}
                    </div>
                    <span class="badge" style="background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; font-size: 11px; font-weight: 600; padding: 4px 8px; border-radius: 4px;">Asignado</span>
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

// Catalog Clients Modal - global state & functions
let catalogPage = 1;
let catalogSearch = "";
let catalogSelected = new Set();

function openCatalogModal() {
    catalogPage = 1;
    catalogSearch = "";
    catalogSelected.clear();
    const input = document.getElementById("catalog-search-input");
    if (input) input.value = "";
    const modal = document.getElementById("catalog-clients-modal");
    if (modal) modal.classList.remove("hidden");
    loadCatalogClients();
}

async function loadCatalogClients() {
    const catalogList = document.getElementById("catalog-clients-list");
    if (!catalogList) return;
    try {
        const params = new URLSearchParams();
        params.set("page", catalogPage);
        params.set("limit", "30");
        if (catalogSearch) params.set("search", catalogSearch);

        const res = await apiRequest("/api/v1/asignaciones/clientes-catalogo?" + params.toString());
        const clientes = res.data || [];
        const total = res.total || 0;
        const pages = res.pages || 1;

        if (clientes.length === 0) {
            catalogList.innerHTML = `<p style="font-size: 13px; color: #64748b; text-align: center; margin: 24px 0;">No se encontraron clientes en el cat&aacute;logo.</p>`;
        } else {
            catalogList.innerHTML = clientes.map(c => `
                <div class="catalog-client-card" style="display: flex; align-items: flex-start; gap: 12px; background: #ffffff; border: 1px solid #e2e8f0; padding: 12px 14px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                    <input type="checkbox" class="catalog-client-checkbox" value="${c.id}" ${catalogSelected.has(c.id) ? 'checked' : ''} style="margin-top: 3px; cursor: pointer; width: 16px; height: 16px; accent-color: #ef4444;">
                    <div style="flex: 1; min-width: 0;">
                        <strong style="font-size: 13.5px; font-weight: 700; color: #0f172a; display: block; word-break: break-word; line-height: 1.3;">${escapeHTML(c.nombre)}</strong>
                        <div style="display: flex; flex-wrap: wrap; gap: 6px; align-items: center; margin-top: 4px;">
                            ${c.rfc ? `<span style="background: #f1f5f9; color: #334155; padding: 2px 7px; border-radius: 4px; font-size: 11px; font-weight: 600; border: 1px solid #e2e8f0; font-family: monospace;">RFC: ${escapeHTML(c.rfc)}</span>` : ''}
                            ${c.numero_cliente ? `<span style="background: #f1f5f9; color: #334155; padding: 2px 7px; border-radius: 4px; font-size: 11px; font-weight: 600; border: 1px solid #e2e8f0;"># ${escapeHTML(c.numero_cliente)}</span>` : ''}
                            ${c.poblacion || c.estado ? `<span style="font-size: 11px; color: #64748b;">${escapeHTML([c.poblacion, c.estado].filter(Boolean).join(', '))}</span>` : ''}
                        </div>
                    </div>
                </div>
            `).join("");

            catalogList.querySelectorAll(".catalog-client-checkbox").forEach(cb => {
                cb.addEventListener("change", () => {
                    const id = parseInt(cb.value);
                    if (cb.checked) catalogSelected.add(id);
                    else catalogSelected.delete(id);
                });
            });
        }

        const catalogPagination = document.getElementById("catalog-pagination");
        if (catalogPagination) {
            catalogPagination.innerHTML = `
                <button class="btn btn-sm btn-secondary" ${catalogPage <= 1 ? 'disabled' : ''} id="catalog-prev-btn" style="padding: 2px 10px; font-size: 11px;">&laquo; Anterior</button>
                <span style="color: hsl(var(--text-secondary));">P&aacute;g. ${catalogPage} de ${pages}</span>
                <button class="btn btn-sm btn-secondary" ${catalogPage >= pages ? 'disabled' : ''} id="catalog-next-btn" style="padding: 2px 10px; font-size: 11px;">Siguiente &raquo;</button>
            `;
            document.getElementById("catalog-prev-btn")?.addEventListener("click", () => {
                if (catalogPage > 1) { catalogPage--; loadCatalogClients(); }
            });
            document.getElementById("catalog-next-btn")?.addEventListener("click", () => {
                if (catalogPage < pages) { catalogPage++; loadCatalogClients(); }
            });
        }
    } catch (err) {
        catalogList.innerHTML = `<p style="font-size: 13px; color: #ef4444; text-align: center;">Error al cargar cat&aacute;logo: ${escapeHTML(err.message)}</p>`;
    }
}

// Expose openCatalogModal globally
window.openCatalogModal = openCatalogModal;
window.loadCatalogClients = loadCatalogClients;

// Register catalog modal listeners (script runs at bottom of body, DOM ready)
(function() {
    document.getElementById("btn-add-catalog-clients")?.addEventListener("click", openCatalogModal);
    document.getElementById("btn-close-catalog-modal")?.addEventListener("click", () => {
        document.getElementById("catalog-clients-modal")?.classList.add("hidden");
    });
    document.getElementById("btn-cancel-catalog")?.addEventListener("click", () => {
        document.getElementById("catalog-clients-modal")?.classList.add("hidden");
    });
    const searchInput = document.getElementById("catalog-search-input");
    if (searchInput) {
        let timeout;
        searchInput.addEventListener("input", () => {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                catalogSearch = searchInput.value.trim();
                catalogPage = 1;
                catalogSelected.clear();
                loadCatalogClients();
            }, 350);
        });
    }
    document.getElementById("btn-confirm-add-clients")?.addEventListener("click", async () => {
        if (catalogSelected.size === 0) {
            showToast("Selecciona al menos un cliente para agregar.", "error");
            return;
        }
        try {
            const ids = Array.from(catalogSelected);
            const res = await apiRequest("/api/v1/asignaciones/agregar-clientes", {
                method: "POST",
                body: JSON.stringify(ids)
            });
            showToast(res.message);
            document.getElementById("catalog-clients-modal")?.classList.add("hidden");
            loadManagerAsignacionView();
        } catch (err) {
            showToast("Error al agregar clientes: " + err.message, "error");
        }
    });
})();


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
                    markLastUpload("cotizaciones");
                    await loadLastUploadLabels();
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

document.addEventListener("DOMContentLoaded", () => {
    const detailInput = document.getElementById("file-upload-cotizacion-items");
    const detailButton = document.getElementById("btn-upload-cotizacion-items");
    detailInput?.addEventListener("change", async event => {
        const file = event.target.files?.[0];
        if (!file) return;
        const formData = new FormData();
        formData.append("file", file);
        const original = detailButton.innerHTML;
        detailButton.disabled = true;
        detailButton.innerHTML = 'Cargando detalle... <i class="fa-solid fa-spinner animate-spin"></i>';
        try {
            const response = await fetch("/api/v1/cotizaciones/detalle-materiales/upload", {
                method: "POST",
                headers: { "Authorization": `Bearer ${localStorage.getItem("crm_token")}` },
                body: formData
            });
            const result = await response.json();
            if (!response.ok) {
                const detail = typeof result.detail === "string"
                    ? result.detail
                    : (result.detail?.message || "El detalle no pudo procesarse.");
                throw new Error(detail);
            }
            showToast(`${result.aceptadas} partidas cargadas; ${result.rechazadas} rechazadas.`, "success");
            await loadCotizacionesData(true);
        } catch (error) {
            showToast(error.message, "error");
        } finally {
            detailButton.disabled = false;
            detailButton.innerHTML = original;
            event.target.value = "";
        }
    });

    document.getElementById("channel-config-form")?.addEventListener("submit", async event => {
        event.preventDefault();
        const code = document.getElementById("channel-config-code").value.trim();
        const name = document.getElementById("channel-config-name").value;
        if (!code) return;
        try {
            await apiRequest("/api/v1/analitica/canales", {
                method: "PUT",
                body: JSON.stringify([{ codigo_origen: code, nombre_normalizado: name, activo: true }])
            });
            document.getElementById("channel-config-code").value = "";
            showToast("Código de canal guardado.");
            await loadCommercialAnalytics();
        } catch (error) {
            showToast(error.message, "error");
        }
    });
});


// INVENTARIO ABC+F EVENTS
document.addEventListener('DOMContentLoaded', () => {
    if (DOM.uploadInventarioAbcfForm) {
        DOM.uploadInventarioAbcfForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const file = DOM.fileInventarioAbcf.files[0];
            if (!file) {
                showToast('Por favor selecciona un archivo', 'info');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', file);
            
            const btn = DOM.uploadInventarioAbcfForm.querySelector('button[type=\'submit\']');
            const ogHtml = btn.innerHTML;
            btn.innerHTML = '<i class=\'fa-solid fa-spinner fa-spin\'></i> Subiendo...';
            btn.disabled = true;
            
            try {
                const res = await fetch('/api/v1/inventario-abcf/upload', {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${state.token}` },
                    body: formData
                });
                const data = await res.json();
                
                if (res.ok) {
                    showToast(data.message || 'Inventario subido correctamente', 'success');
                    markLastUpload("inventario-abcf");
                    await loadLastUploadLabels();
                    DOM.fileInventarioAbcf.value = '';
                    const fileNameSpan = document.getElementById('file-inv-name');
                    if (fileNameSpan) fileNameSpan.textContent = 'Seleccionar Archivo';
                    await loadInventarioAbcfData(true);
                } else {
                    showToast(data.detail || 'Error al subir inventario', 'error');
                }
            } catch (err) {
                showToast('Error de conexión', 'error');
            } finally {
                btn.innerHTML = ogHtml;
                btn.disabled = false;
            }
        });
    }

    if (DOM.filterInvSucursal) DOM.filterInvSucursal.addEventListener('change', () => { state.invCurrentPage = 1; loadInventarioAbcfData(); });
    if (DOM.filterInvAbcf) DOM.filterInvAbcf.addEventListener('change', () => { state.invCurrentPage = 1; loadInventarioAbcfData(); });
    if (DOM.filterInvProveedor) DOM.filterInvProveedor.addEventListener('change', () => { state.invCurrentPage = 1; loadInventarioAbcfData(); });
    if (DOM.filterInvFamilia) DOM.filterInvFamilia.addEventListener('change', () => {
        if (DOM.filterInvSubfamilia) DOM.filterInvSubfamilia.options.length = 1;
        state.invCurrentPage = 1;
        loadInventarioAbcfData();
    });
    if (DOM.filterInvSubfamilia) DOM.filterInvSubfamilia.addEventListener('change', () => { state.invCurrentPage = 1; loadInventarioAbcfData(); });
    if (DOM.filterInvSearch) DOM.filterInvSearch.addEventListener('input', () => {
        clearTimeout(window.invSearchTimeout);
        window.invSearchTimeout = setTimeout(() => { state.invCurrentPage = 1; loadInventarioAbcfData(); }, 300);
    });
    if (DOM.btnClearInvFilters) {
        DOM.btnClearInvFilters.addEventListener('click', () => {
            if (DOM.filterInvSucursal) DOM.filterInvSucursal.value = 'todos';
            if (DOM.filterInvAbcf) DOM.filterInvAbcf.value = 'todos';
            if (DOM.filterInvProveedor) DOM.filterInvProveedor.value = 'todos';
            if (DOM.filterInvFamilia) DOM.filterInvFamilia.value = 'todos';
            if (DOM.filterInvSubfamilia) DOM.filterInvSubfamilia.value = 'todas';
            if (DOM.filterInvSearch) DOM.filterInvSearch.value = '';
            state.invCurrentPage = 1;
            loadInventarioAbcfData();
        });
    }

    const thCant = document.getElementById("th-inv-cant");
    if (thCant) thCant.addEventListener('click', () => {
        if (state.invSortField !== 'cant_propia') { state.invSortField = 'cant_propia'; state.invSortDir = 'desc'; }
        else { state.invSortDir = state.invSortDir === 'asc' ? 'desc' : 'asc'; }
        loadInventarioAbcfData();
    });

    const thConsig = document.getElementById("th-inv-consig");
    if (thConsig) thConsig.addEventListener('click', () => {
        if (state.invSortField !== 'inv_consig') { state.invSortField = 'inv_consig'; state.invSortDir = 'desc'; }
        else { state.invSortDir = state.invSortDir === 'asc' ? 'desc' : 'asc'; }
        loadInventarioAbcfData();
    });

    // SOBREPEDIDOS EVENTS
    if (DOM.uploadSobrepedidosForm) {
        DOM.uploadSobrepedidosForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const file = DOM.fileSobrepedidos.files[0];
            if (!file) {
                showToast('Por favor selecciona un archivo', 'info');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', file);
            
            const btn = DOM.uploadSobrepedidosForm.querySelector("button[type='submit']");
            const ogHtml = btn.innerHTML;
            btn.innerHTML = "<i class='fa-solid fa-spinner fa-spin'></i> Subiendo...";
            btn.disabled = true;
            
            try {
                const res = await fetch('/api/v1/sobrepedidos/upload', {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${state.token}` },
                    body: formData
                });
                const data = await res.json();
                
                if (res.ok) {
                    showToast(data.message || 'Reporte de sobrepedidos subido correctamente', 'success');
                    markLastUpload("sobrepedidos");
                    DOM.fileSobrepedidos.value = '';
                    const fileNameSpan = document.getElementById('file-sobrepedidos-name');
                    if (fileNameSpan) fileNameSpan.textContent = 'Seleccionar Archivo';
                    state.porEntregar = [];
                    await loadSobrepedidosData(true);
                    if (state.currentSection === "por-entregar") await loadPorEntregarData(true);
                } else {
                    showToast(data.detail || 'Error al subir reporte', 'error');
                }
            } catch (err) {
                showToast('Error de conexión', 'error');
            } finally {
                btn.innerHTML = ogHtml;
                btn.disabled = false;
            }
        });
    }

    if (DOM.filterSobrepedidosProveedor) DOM.filterSobrepedidosProveedor.addEventListener('change', () => { state.spCurrentPage = 1; loadSobrepedidosData(); });
    if (DOM.filterSobrepedidosVendedor) DOM.filterSobrepedidosVendedor.addEventListener('change', () => { state.spCurrentPage = 1; loadSobrepedidosData(); });
    if (DOM.filterSobrepedidosGrupo) DOM.filterSobrepedidosGrupo.addEventListener('change', () => { state.spCurrentPage = 1; loadSobrepedidosData(); });
    if (DOM.filterSobrepedidosEstado) DOM.filterSobrepedidosEstado.addEventListener('change', () => { state.spCurrentPage = 1; loadSobrepedidosData(); });
    if (DOM.filterSobrepedidosSearch) DOM.filterSobrepedidosSearch.addEventListener('input', () => {
        clearTimeout(window.spSearchTimeout);
        window.spSearchTimeout = setTimeout(() => { state.spCurrentPage = 1; loadSobrepedidosData(); }, 300);
    });
    if (DOM.mobileSobrepedidosSearch) DOM.mobileSobrepedidosSearch.addEventListener('input', () => {
        renderMobileSobrepedidosSummary(state.sobrepedidos || []);
    });
    if (DOM.filterPorEntregarVendedor) DOM.filterPorEntregarVendedor.addEventListener('change', () => { state.peCurrentPage = 1; loadPorEntregarData(); });
    if (DOM.filterPorEntregarEstado) DOM.filterPorEntregarEstado.addEventListener('change', () => { state.peCurrentPage = 1; loadPorEntregarData(); });
    // Sort by Días disponible
    const thPeDias = document.getElementById('th-pe-dias');
    if (thPeDias) {
        thPeDias.addEventListener('click', () => {
            state.peDiasSort = (state.peDiasSort === 'desc') ? 'asc' : 'desc';
            state.peCurrentPage = 1;
            loadPorEntregarData();
        });
    }
    if (DOM.filterPorEntregarSearch) DOM.filterPorEntregarSearch.addEventListener('input', () => {
        clearTimeout(window.peSearchTimeout);
        window.peSearchTimeout = setTimeout(() => { state.peCurrentPage = 1; loadPorEntregarData(); }, 300);
    });
    if (DOM.btnClearPorEntregarFilters) {
        DOM.btnClearPorEntregarFilters.addEventListener('click', () => {
            if (DOM.filterPorEntregarVendedor) DOM.filterPorEntregarVendedor.value = 'todos';
            if (DOM.filterPorEntregarEstado) DOM.filterPorEntregarEstado.value = 'todos';
            if (DOM.filterPorEntregarSearch) DOM.filterPorEntregarSearch.value = '';
            state.peCurrentPage = 1;
            loadPorEntregarData();
        });
    }
    if (DOM.btnClearSobrepedidosFilters) {
        DOM.btnClearSobrepedidosFilters.addEventListener('click', () => {
            if (DOM.filterSobrepedidosProveedor) DOM.filterSobrepedidosProveedor.value = 'todos';
            if (DOM.filterSobrepedidosVendedor) DOM.filterSobrepedidosVendedor.value = 'todos';
            if (DOM.filterSobrepedidosGrupo) DOM.filterSobrepedidosGrupo.value = 'todos';
            if (DOM.filterSobrepedidosEstado) DOM.filterSobrepedidosEstado.value = 'todos';
            if (DOM.filterSobrepedidosSearch) DOM.filterSobrepedidosSearch.value = '';
            state.spCurrentPage = 1;
            loadSobrepedidosData();
        });
    }

    DOM.adminAccessMonth?.addEventListener("change", () => loadAdminAccessLog());
    DOM.adminAccessSeller?.addEventListener("change", () => loadAdminAccessLog());

    // Sorting Headers
    const thSpPedido = document.getElementById("th-sobrepedidos-pedido");
    if (thSpPedido) thSpPedido.addEventListener('click', () => {
        if (state.spSortField !== 'pedido') { state.spSortField = 'pedido'; state.spSortDir = 'desc'; }
        else { state.spSortDir = state.spSortDir === 'asc' ? 'desc' : 'asc'; }
        loadSobrepedidosData();
    });
    const thSpSku = document.getElementById("th-sobrepedidos-sku");
    if (thSpSku) thSpSku.addEventListener('click', () => {
        if (state.spSortField !== 'sku') { state.spSortField = 'sku'; state.spSortDir = 'desc'; }
        else { state.spSortDir = state.spSortDir === 'asc' ? 'desc' : 'asc'; }
        loadSobrepedidosData();
    });
    const thSpCant = document.getElementById("th-sobrepedidos-cant");
    if (thSpCant) thSpCant.addEventListener('click', () => {
        if (state.spSortField !== 'cant') { state.spSortField = 'cant'; state.spSortDir = 'desc'; }
        else { state.spSortDir = state.spSortDir === 'asc' ? 'desc' : 'asc'; }
        loadSobrepedidosData();
    });
    const thSpFecha = document.getElementById("th-sobrepedidos-fecha");
    if (thSpFecha) thSpFecha.addEventListener('click', () => {
        if (state.spSortField !== 'fecha') { state.spSortField = 'fecha'; state.spSortDir = 'desc'; }
        else { state.spSortDir = state.spSortDir === 'asc' ? 'desc' : 'asc'; }
        loadSobrepedidosData();
    });
});

/* ==========================================================================
   HU-1, HU-2, HU-3 FUNCTIONS & EVENT LISTENERS
   ========================================================================== */

// --- HU-2: HISTORIAL DEL CLIENTE ---
async function openClientHistoryModal(numeroCliente) {
    if (!numeroCliente) return;
    if (!DOM.clientHistoryModal) return;

    DOM.clientHistorySubtitle.textContent = `Buscando historial para el Cliente No. ${escapeHTML(numeroCliente)}...`;
    DOM.clientHistoryTable.innerHTML = '<tr><td colspan="7" class="text-center">Cargando operaciones...</td></tr>';
    DOM.clientHistoryModal.classList.remove("hidden");

    try {
        const res = await apiRequest(`/api/v1/cotizaciones/historial-cliente?numero_cliente=${encodeURIComponent(numeroCliente)}`);
        const history = res.data;

        const nombre = history.cliente_nombre || `Cliente No. ${numeroCliente}`;
        DOM.clientHistorySubtitle.textContent = `${escapeHTML(nombre)} · No. SAP: ${escapeHTML(history.numero_cliente)}`;

        DOM.clientHistoryTotalQuotes.textContent = history.resumen.total_cotizaciones;
        DOM.clientHistoryInvoicedCount.textContent = history.resumen.total_facturadas;
        DOM.clientHistoryTotalQuoted.textContent = `$${history.resumen.importe_cotizado.toLocaleString('es-MX', { minimumFractionDigits: 2 })}`;
        DOM.clientHistoryTotalInvoiced.textContent = `$${history.resumen.importe_facturado.toLocaleString('es-MX', { minimumFractionDigits: 2 })}`;
        DOM.clientHistoryConversionRate.textContent = `${history.resumen.tasa_conversion}%`;

        if (!history.operaciones || history.operaciones.length === 0) {
            DOM.clientHistoryTable.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No se encontraron operaciones registradas para este cliente.</td></tr>';
            return;
        }

        DOM.clientHistoryTable.innerHTML = history.operaciones.map(op => {
            let badgeClass = "badge-secondary";
            if (op.estado === "Facturado") badgeClass = "badge-success";
            else if (op.estado === "Venta Perdida") badgeClass = "badge-danger";
            else if (op.estado === "Expirada") badgeClass = "badge-warning";
            else if (op.estado === "Pendiente") badgeClass = "badge-primary";

            return `
                <tr>
                    <td><strong>${escapeHTML(op.numero_cotizacion || 'Sin #')}</strong></td>
                    <td>${op.fecha_registro || '-'}</td>
                    <td>${escapeHTML(op.canal || '-')}</td>
                    <td>$${op.total_cotizado.toLocaleString('es-MX', { minimumFractionDigits: 2 })}</td>
                    <td>${op.importe_facturado > 0 ? '$' + op.importe_facturado.toLocaleString('es-MX', { minimumFractionDigits: 2 }) : '-'}</td>
                    <td><span class="badge ${badgeClass}">${op.estado}</span></td>
                    <td><small>${escapeHTML(op.vendedor_nombre || 'Asesor')}</small></td>
                </tr>
            `;
        }).join("");
    } catch (err) {
        showToast("Error al obtener historial del cliente: " + err.message, "error");
        DOM.clientHistorySubtitle.textContent = "Error al cargar datos.";
    }
}

// --- HU-3: CLIENTES POTENCIALES DE PROMOCIÓN ---
async function openPromoClientsModal(promoId) {
    if (!promoId) return;
    if (!DOM.promoClientsModal) return;

    DOM.promoClientsInfo.textContent = "Cargando clientes potenciales...";
    DOM.promoClientsTable.innerHTML = '<tr><td colspan="5" class="text-center">Cargando...</td></tr>';
    DOM.promoClientsModal.classList.remove("hidden");

    try {
        const res = await apiRequest(`/api/v1/promociones/${promoId}/clientes-potenciales`);
        const data = res.data;
        const promo = data.promocion;

        DOM.promoClientsInfo.innerHTML = `
            <strong>${escapeHTML(promo.descripcion_material || promo.codigo_material)}</strong>
            · Precio Promo: <span style="color:#10b981; font-weight:700;">$${(promo.precio_promocion || 0).toLocaleString('es-MX', {minimumFractionDigits: 2})}</span>
            · Total Clientes: <span class="badge badge-primary">${data.total_clientes}</span>
        `;

        if (!data.clientes || data.clientes.length === 0) {
            DOM.promoClientsTable.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No se encontraron clientes registrados que hayan comprado previamente este material.</td></tr>';
            return;
        }

        DOM.promoClientsTable.innerHTML = data.clientes.map(c => {
            const waBtn = c.acciones.whatsapp_url
                ? `<a href="${c.acciones.whatsapp_url}" target="_blank" rel="noopener" class="btn btn-sm btn-action-wa" title="Enviar WhatsApp"><i class="fa-brands fa-whatsapp"></i> WhatsApp</a>`
                : `<span class="text-muted" style="font-size:11px;">Sin celular</span>`;

            const emailBtn = c.acciones.email_url
                ? `<a href="${c.acciones.email_url}" class="btn btn-sm btn-action-email" title="Enviar Correo"><i class="fa-regular fa-envelope"></i> Correo</a>`
                : `<span class="text-muted" style="font-size:11px;">Sin correo</span>`;

            return `
                <tr>
                    <td>
                        <strong>${escapeHTML(c.cliente_nombre || 'Cliente sin nombre')}</strong>
                        ${c.numero_cliente ? `<br><small class="text-muted">No. ${escapeHTML(c.numero_cliente)}</small>` : ''}
                    </td>
                    <td><small>${escapeHTML(c.vendedor_nombre || 'Asesor')}</small></td>
                    <td>${c.ultima_compra || '-'}</td>
                    <td><strong>${c.cantidad_total}</strong> <small class="text-muted">($${c.importe_total.toLocaleString('es-MX', {minimumFractionDigits: 2})})</small></td>
                    <td>
                        <div style="display: flex; gap: 6px; align-items: center;">
                            ${waBtn}
                            ${emailBtn}
                        </div>
                    </td>
                </tr>
            `;
        }).join("");
    } catch (err) {
        showToast("Error al cargar clientes potenciales: " + err.message, "error");
    }
}

// --- HU-1: RECORDATORIOS DE SEGUIMIENTO ---
async function openAddReminderModal(quoteId) {
    if (!quoteId) return;
    if (!DOM.addReminderModal) return;

    DOM.reminderQuoteId.value = quoteId;
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    DOM.reminderDateInput.value = tomorrow.toISOString().split('T')[0];
    DOM.reminderNoteInput.value = "";
    DOM.addReminderModal.classList.remove("hidden");
}

async function saveReminder(e) {
    e.preventDefault();
    const quoteId = DOM.reminderQuoteId.value;
    const dateVal = DOM.reminderDateInput.value;
    const noteVal = DOM.reminderNoteInput.value;

    if (!quoteId || !dateVal) {
        showToast("Selecciona una fecha válida.", "error");
        return;
    }

    try {
        const res = await apiRequest(`/api/v1/cotizaciones/${quoteId}/recordatorio`, {
            method: "POST",
            body: JSON.stringify({
                fecha_programada: dateVal,
                nota: noteVal || null
            })
        });
        showToast(res.message, "success");
        DOM.addReminderModal.classList.add("hidden");
        await loadPendingReminders();
    } catch (err) {
        showToast("Error al guardar recordatorio: " + err.message, "error");
    }
}

async function loadPendingReminders() {
    try {
        const res = await apiRequest("/api/v1/cotizaciones/recordatorios/pendientes");
        state.pendingReminders = res.data || [];

        // Update nav badge
        const count = state.pendingReminders.length;
        if (DOM.remindersNavBadge) {
            DOM.remindersNavBadge.textContent = count;
            if (count > 0) DOM.remindersNavBadge.classList.remove("hidden");
            else DOM.remindersNavBadge.classList.add("hidden");
        }

        // Update Dashboard card
        if (DOM.dailyRemindersBadgeCount) {
            DOM.dailyRemindersBadgeCount.textContent = `${count} pendiente${count === 1 ? '' : 's'}`;
        }

        if (DOM.dailyRemindersList) {
            if (count === 0) {
                DOM.dailyRemindersList.innerHTML = '<p class="text-muted" style="margin: 0; padding: 8px 0;"><i class="fa-solid fa-circle-check" style="color: #10b981;"></i> No tienes seguimientos pendientes para hoy.</p>';
            } else {
                const todayStr = new Date().toISOString().split('T')[0];
                DOM.dailyRemindersList.innerHTML = state.pendingReminders.map(r => {
                    const isDueToday = r.fecha_programada <= todayStr;
                    const borderStyle = isDueToday ? 'border-left: 4px solid #f59e0b;' : 'border-left: 4px solid #38bdf8;';
                    const dueLabel = isDueToday ? '<span class="badge badge-warning">¡Hoy!</span>' : `<span class="badge badge-secondary">${r.fecha_programada}</span>`;

                    return `
                        <div class="glass-card reminder-item-card" style="padding: 12px 16px; display: flex; justify-content: space-between; align-items: center; ${borderStyle}">
                            <div>
                                <div style="display: flex; align-items: center; gap: 8px;">
                                    <strong>${escapeHTML(r.cliente_nombre)}</strong>
                                    ${r.numero_cotizacion ? `<small class="text-muted">#${escapeHTML(r.numero_cotizacion)}</small>` : ''}
                                    ${dueLabel}
                                </div>
                                ${r.nota ? `<p style="margin: 4px 0 0 0; font-size: 12px; color: hsl(var(--text-secondary));"><i class="fa-regular fa-note-sticky"></i> ${escapeHTML(r.nota)}</p>` : ''}
                            </div>
                            <button class="btn btn-sm btn-secondary btn-complete-reminder" data-id="${r.id}" title="Marcar como completado">
                                <i class="fa-solid fa-check"></i> Listo
                            </button>
                        </div>
                    `;
                }).join("");

                // Attach event listener for complete button
                DOM.dailyRemindersList.querySelectorAll(".btn-complete-reminder").forEach(btn => {
                    btn.addEventListener("click", async () => {
                        const remId = btn.getAttribute("data-id");
                        try {
                            await apiRequest(`/api/v1/cotizaciones/recordatorios/${remId}`, {
                                method: "PATCH",
                                body: JSON.stringify({ completado: true })
                            });
                            showToast("Seguimiento marcado como completado.", "success");
                            await loadPendingReminders();
                        } catch (err) {
                            showToast("Error al actualizar recordatorio: " + err.message, "error");
                        }
                    });
                });
            }
        }
    } catch (err) {
        console.error("Error loading pending reminders:", err);
    }
}

// Global Event Listeners for HU-1, HU-2, HU-3
document.addEventListener("DOMContentLoaded", () => {
    // Client History Modal Listeners
    DOM.btnCloseClientHistory?.addEventListener("click", () => DOM.clientHistoryModal.classList.add("hidden"));
    DOM.btnCancelClientHistory?.addEventListener("click", () => DOM.clientHistoryModal.classList.add("hidden"));

    if (DOM.btnSearchClientHistory && DOM.searchClientHistoryInput) {
        DOM.btnSearchClientHistory.addEventListener("click", () => {
            const val = DOM.searchClientHistoryInput.value.trim();
            if (val) openClientHistoryModal(val);
            else showToast("Ingresa un número de cliente.", "info");
        });
        DOM.searchClientHistoryInput.addEventListener("keypress", (e) => {
            if (e.key === "Enter") {
                const val = DOM.searchClientHistoryInput.value.trim();
                if (val) openClientHistoryModal(val);
            }
        });
    }

    // Promo Clients Modal Listeners
    DOM.btnClosePromoClients?.addEventListener("click", () => DOM.promoClientsModal.classList.add("hidden"));
    DOM.btnCancelPromoClients?.addEventListener("click", () => DOM.promoClientsModal.classList.add("hidden"));

    // Add Reminder Modal Listeners
    DOM.btnCloseAddReminder?.addEventListener("click", () => DOM.addReminderModal.classList.add("hidden"));
    DOM.btnCancelAddReminder?.addEventListener("click", () => DOM.addReminderModal.classList.add("hidden"));
    DOM.addReminderForm?.addEventListener("submit", saveReminder);
    DOM.remindersNavBtn?.addEventListener("click", () => switchSection("summary"));

    // Clientes Event Listeners
    setupClientesEventListeners();
});

/* ==========================================================================
   CLIENTES CATALOG SECTION
   ========================================================================== */

let searchClientesDebounceTimer = null;
let targetDeleteClienteId = null;

async function loadClientesData(page = 1) {
    state.clientes.page = page;
    const tbody = document.getElementById("tbody-clientes");
    if (tbody) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" style="text-align: center; padding: 30px; color: #9ca3af;">
                    <i class="fa-solid fa-spinner fa-spin" style="font-size: 24px; margin-bottom: 10px;"></i>
                    <p>Cargando catálogo de clientes...</p>
                </td>
            </tr>
        `;
    }

    try {
        const queryParams = new URLSearchParams({
            page: state.clientes.page,
            limit: state.clientes.limit,
            search: state.clientes.search || "",
            tipo_persona: state.clientes.tipo_persona || "",
            colonia: state.clientes.colonia || "",
            poblacion: state.clientes.poblacion || ""
        });

        const res = await apiRequest(`/api/v1/clientes/?${queryParams.toString()}`);
        state.clientes.total = res.total || 0;
        state.clientes.pages = res.pages || 1;
        state.clientes.total_fisicas = res.total_fisicas || 0;
        state.clientes.total_morales = res.total_morales || 0;

        // Update KPI values
        const kpiTotal = document.getElementById("kpi-clientes-total");
        const kpiFisicas = document.getElementById("kpi-clientes-fisicas");
        const kpiMorales = document.getElementById("kpi-clientes-morales");

        if (kpiTotal) kpiTotal.textContent = state.clientes.total.toLocaleString();
        if (kpiFisicas) kpiFisicas.textContent = state.clientes.total_fisicas.toLocaleString();
        if (kpiMorales) kpiMorales.textContent = state.clientes.total_morales.toLocaleString();

        renderClientesTable(res.data || []);
        renderClientesPagination();

        if (!state.clientes.filtersLoaded) {
            await loadClientesFilters();
        }

    } catch (err) {
        console.error("Error loading clientes:", err);
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" style="text-align: center; padding: 30px; color: #ef4444;">
                        <i class="fa-solid fa-circle-exclamation" style="font-size: 24px; margin-bottom: 10px;"></i>
                        <p>Error al cargar clientes: ${escapeHTML(err.message)}</p>
                    </td>
                </tr>
            `;
        }
    }
}

function renderClientesTable(clientes) {
    const tbody = document.getElementById("tbody-clientes");
    if (!tbody) return;

    if (!clientes || clientes.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" style="text-align: center; padding: 40px; color: #9ca3af;">
                    <i class="fa-solid fa-folder-open" style="font-size: 32px; margin-bottom: 10px; opacity: 0.5;"></i>
                    <p style="font-size: 1.05rem; margin: 0;">No se encontraron clientes con los filtros aplicados.</p>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = clientes.map(c => {
        const numCliente = c.numero_cliente ? `#${escapeHTML(c.numero_cliente)}` : "-";
        const rfc = c.rfc ? escapeHTML(c.rfc) : "-";

        return `
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.05); cursor: pointer;" class="table-row-hover" data-cliente-id="${c.id}">
                <td style="font-family: monospace; font-weight: bold; color: #3b82f6; white-space: nowrap;">${numCliente}</td>
                <td>
                    <strong style="color: hsl(var(--text-primary)); display: block;">${escapeHTML(c.nombre)}</strong>
                    ${c.sociedad ? `<small class="text-muted" style="font-size: 11px;">Sociedad: ${escapeHTML(c.sociedad)}</small>` : ''}
                </td>
                <td style="font-family: monospace; font-size: 12px; white-space: nowrap;">${rfc}</td>
                <td>${escapeHTML(c.poblacion || '-')}</td>
                <td>${escapeHTML(c.estado || '-')}</td>
                <td style="white-space: nowrap;">${c.celular ? `<a href="tel:${escapeHTML(c.celular)}" style="color: #10b981; text-decoration: none;" onclick="event.stopPropagation();"><i class="fa-solid fa-mobile-screen" style="font-size: 10px;"></i> ${escapeHTML(c.celular)}</a>` : '-'}</td>
                <td style="max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                    ${c.email ? `<a href="mailto:${escapeHTML(c.email)}" style="color: #a855f7; text-decoration: none;" title="${escapeHTML(c.email)}" onclick="event.stopPropagation();"><i class="fa-regular fa-envelope" style="font-size: 10px;"></i> ${escapeHTML(c.email)}</a>` : '-'}
                </td>
                <td style="text-align: center; white-space: nowrap;" onclick="event.stopPropagation();">
                    <div style="display: flex; gap: 6px; justify-content: center;">
                        <button class="btn btn-sm btn-secondary btn-edit-cliente" data-id="${c.id}" title="Editar cliente" style="padding: 4px 8px;">
                            <i class="fa-solid fa-pen" style="font-size: 12px;"></i>
                        </button>
                        <button class="btn btn-sm btn-danger btn-delete-cliente" data-id="${c.id}" data-nombre="${escapeHTML(c.nombre)}" data-rfc="${escapeHTML(c.rfc || '')}" title="Eliminar cliente" style="padding: 4px 8px;">
                            <i class="fa-solid fa-trash-can" style="font-size: 12px;"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join("");

    // Attach row click event to open edit modal with all fields
    tbody.querySelectorAll("tr[data-cliente-id]").forEach(tr => {
        tr.addEventListener("click", () => {
            const id = tr.getAttribute("data-cliente-id");
            openModalCliente(id);
        });
    });

    // Attach row action click events
    tbody.querySelectorAll(".btn-edit-cliente").forEach(btn => {
        btn.addEventListener("click", (e) => {
            e.stopPropagation();
            const id = btn.getAttribute("data-id");
            openModalCliente(id);
        });
    });

    tbody.querySelectorAll(".btn-delete-cliente").forEach(btn => {
        btn.addEventListener("click", (e) => {
            e.stopPropagation();
            const id = btn.getAttribute("data-id");
            const nombre = btn.getAttribute("data-nombre");
            const rfc = btn.getAttribute("data-rfc");
            confirmDeleteCliente(id, nombre, rfc);
        });
    });
}

function renderClientesPagination() {
    const pag = document.getElementById("clientes-pagination");
    if (!pag) return;

    const { page, pages, limit, total } = state.clientes;
    const start = total > 0 ? (page - 1) * limit + 1 : 0;
    const end = Math.min(page * limit, total);

    pag.innerHTML = `
        <div style="font-size: 0.85rem; color: hsl(var(--text-secondary)); display: flex; align-items: center; gap: 8px;">
            <span>Mostrando <strong>${start}</strong> - <strong>${end}</strong> de <strong>${total.toLocaleString()}</strong> clientes</span>
            <span style="font-size: 11px; padding: 2px 8px; border-radius: 12px; background: rgba(59, 130, 246, 0.15); color: #60a5fa; font-weight: 500;">(25 por página)</span>
        </div>
        <div style="display: flex; gap: 6px; align-items: center; flex-wrap: wrap;">
            <button class="btn btn-sm btn-secondary" id="btn-clientes-first" ${page <= 1 ? 'disabled' : ''} title="Primera página">
                <i class="fa-solid fa-angles-left"></i> Inicio
            </button>
            <button class="btn btn-sm btn-secondary" id="btn-clientes-prev" ${page <= 1 ? 'disabled' : ''} title="Página anterior">
                <i class="fa-solid fa-chevron-left"></i> Anterior
            </button>

            <span style="font-size: 0.85rem; padding: 0 10px; color: hsl(var(--text-secondary)); font-weight: 500;">
                Página <strong style="color: hsl(var(--text-primary));">${page}</strong> de <strong>${pages}</strong>
            </span>

            <button class="btn btn-sm btn-secondary" id="btn-clientes-next" ${page >= pages ? 'disabled' : ''} title="Página siguiente">
                Siguiente <i class="fa-solid fa-chevron-right"></i>
            </button>
            <button class="btn btn-sm btn-secondary" id="btn-clientes-last" ${page >= pages ? 'disabled' : ''} title="Última página">
                Fin <i class="fa-solid fa-angles-right"></i>
            </button>
        </div>
    `;

    document.getElementById("btn-clientes-first")?.addEventListener("click", () => {
        if (page > 1) loadClientesData(1);
    });

    document.getElementById("btn-clientes-prev")?.addEventListener("click", () => {
        if (page > 1) loadClientesData(page - 1);
    });

    document.getElementById("btn-clientes-next")?.addEventListener("click", () => {
        if (page < pages) loadClientesData(page + 1);
    });

    document.getElementById("btn-clientes-last")?.addEventListener("click", () => {
        if (page < pages) loadClientesData(pages);
    });
}

async function loadClientesFilters() {
    try {
        const res = await apiRequest("/api/v1/clientes/filters");
        const selColonia = document.getElementById("clientes-filter-colonia");
        const selPoblacion = document.getElementById("clientes-filter-poblacion");

        if (selColonia && res.colonias) {
            const curCol = state.clientes.colonia;
            selColonia.innerHTML = '<option value="">Todas las colonias</option>' +
                res.colonias.map(c => `<option value="${escapeHTML(c)}" ${c === curCol ? 'selected' : ''}>${escapeHTML(c)}</option>`).join("");
        }

        if (selPoblacion && res.poblaciones) {
            const curPob = state.clientes.poblacion;
            selPoblacion.innerHTML = '<option value="">Todas las poblaciones</option>' +
                res.poblaciones.map(p => `<option value="${escapeHTML(p)}" ${p === curPob ? 'selected' : ''}>${escapeHTML(p)}</option>`).join("");
        }

        state.clientes.filtersLoaded = true;
    } catch (err) {
        console.error("Error loading filter options:", err);
    }
}

async function openModalCliente(clienteId = null) {
    const modal = document.getElementById("modal-cliente");
    const form = document.getElementById("form-cliente");
    const title = document.getElementById("modal-cliente-title");
    if (!modal || !form) return;

    form.reset();
    document.getElementById("cliente-id-input").value = "";

    if (clienteId) {
        if (title) title.innerHTML = '<i class="fa-solid fa-user-pen" style="color: #3b82f6;"></i> <span>Editar Cliente</span>';
        try {
            const cliente = await apiRequest(`/api/v1/clientes/${clienteId}`);
            document.getElementById("cliente-id-input").value = cliente.id || "";
            document.getElementById("cliente-nombre-input").value = cliente.nombre || "";
            document.getElementById("cliente-contacto-input").value = cliente.nombre_contacto || "";
            document.getElementById("cliente-num-input").value = cliente.numero_cliente || "";
            document.getElementById("cliente-rfc-input").value = cliente.rfc || "";
            document.getElementById("cliente-persona-input").value = cliente.tipo_persona || "Persona física";
            document.getElementById("cliente-sociedad-input").value = cliente.sociedad || "MKS";
            document.getElementById("cliente-calle-input").value = cliente.calle || "";
            document.getElementById("cliente-numext-input").value = cliente.numero_exterior || "";
            document.getElementById("cliente-colonia-input").value = cliente.colonia || "";
            document.getElementById("cliente-cp-input").value = cliente.codigo_postal || "";
            document.getElementById("cliente-poblacion-input").value = cliente.poblacion || "";
            document.getElementById("cliente-estado-input").value = cliente.estado || "";
            document.getElementById("cliente-tel-input").value = cliente.telefono || "";
            document.getElementById("cliente-cel-input").value = cliente.celular || "";
            document.getElementById("cliente-fax-input").value = cliente.fax || "";
            document.getElementById("cliente-email-input").value = cliente.email || "";
        } catch (err) {
            showToast("Error al cargar datos del cliente: " + err.message, "error");
            return;
        }
    } else {
        if (title) title.innerHTML = '<i class="fa-solid fa-user-plus" style="color: #3b82f6;"></i> <span>Alta de Cliente</span>';
        document.getElementById("cliente-sociedad-input").value = "MKS";
    }

    modal.classList.remove("hidden");
}

async function saveClienteForm(e) {
    if (e) e.preventDefault();

    const id = document.getElementById("cliente-id-input")?.value;
    const nombre = document.getElementById("cliente-nombre-input")?.value.trim();

    if (!nombre) {
        showToast("El nombre del cliente es obligatorio.", "warning");
        return;
    }

    const payload = {
        sociedad: document.getElementById("cliente-sociedad-input")?.value.trim() || "MKS",
        numero_cliente: document.getElementById("cliente-num-input")?.value.trim() || "",
        nombre: nombre,
        nombre_contacto: document.getElementById("cliente-contacto-input")?.value.trim() || "",
        rfc: document.getElementById("cliente-rfc-input")?.value.trim() || "",
        tipo_persona: document.getElementById("cliente-persona-input")?.value || "Persona física",
        calle: document.getElementById("cliente-calle-input")?.value.trim() || "",
        numero_exterior: document.getElementById("cliente-numext-input")?.value.trim() || "",
        colonia: document.getElementById("cliente-colonia-input")?.value.trim() || "",
        codigo_postal: document.getElementById("cliente-cp-input")?.value.trim() || "",
        poblacion: document.getElementById("cliente-poblacion-input")?.value.trim() || "",
        estado: document.getElementById("cliente-estado-input")?.value.trim() || "",
        telefono: document.getElementById("cliente-tel-input")?.value.trim() || "",
        celular: document.getElementById("cliente-cel-input")?.value.trim() || "",
        fax: document.getElementById("cliente-fax-input")?.value.trim() || "",
        email: document.getElementById("cliente-email-input")?.value.trim() || "",
    };

    try {
        if (id) {
            await apiRequest(`/api/v1/clientes/${id}`, {
                method: "PUT",
                body: JSON.stringify(payload)
            });
            showToast(`Cliente '${nombre}' actualizado con éxito.`, "success");
        } else {
            await apiRequest("/api/v1/clientes/", {
                method: "POST",
                body: JSON.stringify(payload)
            });
            showToast(`Cliente '${nombre}' dado de alta exitosamente.`, "success");
        }

        document.getElementById("modal-cliente")?.classList.add("hidden");
        await loadClientesData(state.clientes.page);
        state.clientes.filtersLoaded = false;
    } catch (err) {
        showToast("Error al guardar cliente: " + err.message, "error");
    }
}

function confirmDeleteCliente(id, nombre, rfc) {
    targetDeleteClienteId = id;
    const modal = document.getElementById("modal-confirm-delete-cliente");
    const nameDisplay = document.getElementById("delete-cliente-nombre-display");
    const rfcDisplay = document.getElementById("delete-cliente-rfc-display");

    if (nameDisplay) nameDisplay.textContent = nombre || "Cliente sin nombre";
    if (rfcDisplay) rfcDisplay.textContent = rfc ? `RFC: ${rfc}` : "Sin RFC registrado";

    if (modal) modal.classList.remove("hidden");
}

async function executeDeleteCliente() {
    if (!targetDeleteClienteId) return;

    try {
        const res = await apiRequest(`/api/v1/clientes/${targetDeleteClienteId}`, {
            method: "DELETE"
        });
        showToast(res.message || "Cliente eliminado exitosamente.", "success");
        document.getElementById("modal-confirm-delete-cliente")?.classList.add("hidden");
        targetDeleteClienteId = null;
        await loadClientesData(state.clientes.page);
        state.clientes.filtersLoaded = false;
    } catch (err) {
        showToast("Error al eliminar cliente: " + err.message, "error");
    }
}

function setupClientesEventListeners() {
    // Search input dynamic live listener (debounced)
    const searchInput = document.getElementById("clientes-search-input");
    if (searchInput) {
        searchInput.addEventListener("input", (e) => {
            clearTimeout(searchClientesDebounceTimer);
            searchClientesDebounceTimer = setTimeout(() => {
                state.clientes.search = e.target.value.trim();
                loadClientesData(1);
            }, 300);
        });
    }

    // Filter selects
    document.getElementById("clientes-filter-persona")?.addEventListener("change", (e) => {
        state.clientes.tipo_persona = e.target.value;
        loadClientesData(1);
    });

    document.getElementById("clientes-filter-colonia")?.addEventListener("change", (e) => {
        state.clientes.colonia = e.target.value;
        loadClientesData(1);
    });

    document.getElementById("clientes-filter-poblacion")?.addEventListener("change", (e) => {
        state.clientes.poblacion = e.target.value;
        loadClientesData(1);
    });

    // Clear filters button
    document.getElementById("clientes-btn-clear-filters")?.addEventListener("click", () => {
        state.clientes.search = "";
        state.clientes.tipo_persona = "";
        state.clientes.colonia = "";
        state.clientes.poblacion = "";

        if (searchInput) searchInput.value = "";
        const selPersona = document.getElementById("clientes-filter-persona");
        const selColonia = document.getElementById("clientes-filter-colonia");
        const selPoblacion = document.getElementById("clientes-filter-poblacion");

        if (selPersona) selPersona.value = "";
        if (selColonia) selColonia.value = "";
        if (selPoblacion) selPoblacion.value = "";

        loadClientesData(1);
    });

    // New client modal button
    document.getElementById("btn-nuevo-cliente")?.addEventListener("click", () => {
        openModalCliente(null);
    });

    // Modal forms and close buttons
    document.getElementById("form-cliente")?.addEventListener("submit", saveClienteForm);
    document.getElementById("btn-close-modal-cliente")?.addEventListener("click", () => {
        document.getElementById("modal-cliente")?.classList.add("hidden");
    });
    document.getElementById("btn-cancel-modal-cliente")?.addEventListener("click", () => {
        document.getElementById("modal-cliente")?.classList.add("hidden");
    });

    // Delete confirm modal buttons
    document.getElementById("btn-confirm-delete-cliente")?.addEventListener("click", executeDeleteCliente);
    document.getElementById("btn-close-delete-cliente")?.addEventListener("click", () => {
        document.getElementById("modal-confirm-delete-cliente")?.classList.add("hidden");
    });
    document.getElementById("btn-cancel-delete-cliente")?.addEventListener("click", () => {
        document.getElementById("modal-confirm-delete-cliente")?.classList.add("hidden");
    });
}
