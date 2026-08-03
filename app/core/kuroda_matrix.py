"""
Matriz Oficial de Clasificación Kuroda:
Define las 6 Familias Macro y sus Subfamilias correspondientes.
"""

FAMILIA_MACRO_LIST = [
    "PLOMERIA CROMADA",
    "ARTICULOS DE PLOMERIA",
    "CERAMICOS",
    "REVESTESIMIENTO DECORATIVOS",
    "SERVICIO",
    "HOGAR"
]

FAMILIA_SUBFAMILIA_MAP = {
    "PLOMERIA CROMADA": [
        "ACCESORIOS DE BAÑO", "ACCESORIOS DE BAÑ", "ACCESORIOS DE BANO",
        "PLOMERIA CROMADA"
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
}

# Reverse lookup table: subfamilia (uppercase) -> familia macro
SUBFAMILIA_TO_FAMILIA = {}
for fam, sub_list in FAMILIA_SUBFAMILIA_MAP.items():
    for sub in sub_list:
        SUBFAMILIA_TO_FAMILIA[sub.upper()] = fam

def get_kuroda_familia_y_subfamilia(descrip_gpo_materiales: str):
    """
    Dada la categoría original de materiales (ej. PISOS, CALENTADORES, LAVABOS, SANITARIOS),
    devuelve una tupla (familia_macro, subfamilia_normalizada).
    """
    if not descrip_gpo_materiales:
        return "OTROS", "GENERAL"
    
    clean = str(descrip_gpo_materiales).strip().upper()
    fam = SUBFAMILIA_TO_FAMILIA.get(clean)
    
    if not fam:
        # Intento de coincidencia parcial
        for sub, f in SUBFAMILIA_TO_FAMILIA.items():
            if sub in clean or clean in sub:
                fam = f
                break
                
    return fam or "OTROS", clean
