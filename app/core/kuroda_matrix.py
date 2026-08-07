"""
Matriz Oficial de Clasificación Kuroda:
Define las 6 Familias Macro (encabezados de columna) y sus Subfamilias (filas de columna) correspondientes.
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
        "ACCESORIOS DE BAÑO", "PLOMERIA CROMADA"
    ],
    "ARTICULOS DE PLOMERIA": [
        "ABRAZADERAS", "ARTICULOS PLOMERIA", "BOMBAS", "COLADERAS", "CONEXIONES",
        "FILTROS", "MEDIDORES", "PEGAMENTOS", "REFACCIONES", "REFACCIONES P/BOMB",
        "TOMAS DOMICILIARIA", "TUBERIA", "VALVULA INDUSTRIAL", "VALVULAS"
    ],
    "CERAMICOS": [
        "ASIENTOS", "LAVABOS", "SANITARIOS"
    ],
    "REVESTESIMIENTO DECORATIVOS": [
        "ADHESIVOS CERAMICO", "AZULEJOS", "BOQUILLAS", "ESQUINEROS/MOLDURA",
        "PISOS", "REVEST DECORADOS"
    ],
    "SERVICIO": [
        "AIRE ACON/MINI SPL", "ASPERSORES", "CALENTADORES", "CISTERNAS",
        "CORTADORAS", "EQ HIDRONEUMATICOS", "FERRETERIA", "FOSAS",
        "HERRAMIENTAS", "IRRIGACION", "JUEGOS ESPARCIMIEN", "MANGUERAS",
        "MANOMETROS", "MOTORES", "SERVICIOS", "TANQUES Y CILINDRO",
        "TINACOS", "TINAS", "TRABAJOS DE TALLER"
    ],
    "HOGAR": [
        "ACCESORIOS", "ARTICULOS DE COCIN", "CABLES Y ALAMBRES", "CTRO CARGA/INTERRU",
        "ESPEJOS", "FOCOS Y FILAMENTOS", "FREGADEROS", "GABINETES PARA BAÑ",
        "ILUMINACION", "IMPERMEABILIZANTES", "LAM CANAL GALV ACR", "LAVADEROS",
        "LINEA BLANCA", "MATERIAL ELECTR/HE", "PLACAS", "TAPA/CONTACT/APAGA"
    ]
}

# Key mappings including common singular/plural and description abbreviations
SUBFAMILIA_MATCHERS = {
    "PLOMERIA CROMADA": [
        ("ACCESORIOS DE BAÑO", ["ACCESORIOS DE BAÑO", "ACCESORIOS DE BAÑ", "ACCESORIOS DE BANO", "ACCESORIO BAÑO"]),
        ("PLOMERIA CROMADA", ["PLOMERIA CROMADA", "PLOM CROMADA", "GRIPHO", "MEZCLADORA", "MEZ"])
    ],
    "ARTICULOS DE PLOMERIA": [
        ("ABRAZADERAS", ["ABRAZADERAS", "ABRAZADERA"]),
        ("ARTICULOS PLOMERIA", ["ARTICULOS PLOMERIA", "ARTICULOS DE PLOMERIA", "PLOMERIA"]),
        ("BOMBAS", ["BOMBAS", "BOMBA"]),
        ("COLADERAS", ["COLADERAS", "COLADERA", "RESUMIDERO"]),
        ("CONEXIONES", ["CONEXIONES", "CONEXION", "CONECTOR", "CESPOL", "CONTRA", "CUELLO", "BRIDA", "ANILLO", "REJILLA"]),
        ("FILTROS", ["FILTROS", "FILTRO"]),
        ("MEDIDORES", ["MEDIDORES", "MEDIDOR"]),
        ("PEGAMENTOS", ["PEGAMENTOS", "PEGAMENTO", "PEGAVITRO"]),
        ("REFACCIONES", ["REFACCIONES", "REFACCION"]),
        ("REFACCIONES P/BOMB", ["REFACCIONES P/BOMB", "REFACCIONES P/BOMBAS", "REFACCION BOMBA"]),
        ("TOMAS DOMICILIARIA", ["TOMAS DOMICILIARIA", "TOMAS DOMICILIARIAS", "TOMA DOMICILIARIA"]),
        ("TUBERIA", ["TUBERIA", "TUBERIAS", "TUBO"]),
        ("VALVULA INDUSTRIAL", ["VALVULA INDUSTRIAL", "VALVULAS INDUSTRIALES"]),
        ("VALVULAS", ["VALVULAS", "VALVULA", "VALV"])
    ],
    "CERAMICOS": [
        ("ASIENTOS", ["ASIENTOS", "ASIENTO"]),
        ("LAVABOS", ["LAVABOS", "LAVABO"]),
        ("SANITARIOS", ["SANITARIOS", "SANITARIO", "INODORO", "TAZA", "WC"])
    ],
    "REVESTESIMIENTO DECORATIVOS": [
        ("ADHESIVOS CERAMICO", ["ADHESIVOS CERAMICO", "ADHESIVOS CERAMICOS", "ADHESIVO"]),
        ("AZULEJOS", ["AZULEJOS", "AZULEJO", "AZ"]),
        ("BOQUILLAS", ["BOQUILLAS", "BOQUILLA"]),
        ("ESQUINEROS/MOLDURA", ["ESQUINEROS/MOLDURA", "ESQUINEROS/MOLDURAS", "MOLDURA", "ESQUINERO"]),
        ("PISOS", ["PISOS", "PISO"]),
        ("REVEST DECORADOS", ["REVEST DECORADOS", "REVESTIMIENTO DECORATIVOS", "REVESTIMIENTO", "MALLA", "CENEZZA"])
    ],
    "SERVICIO": [
        ("AIRE ACON/MINI SPL", ["AIRE ACON/MINI SPL", "MINISPLIT", "CLIMA"]),
        ("ASPERSORES", ["ASPERSORES", "ASPERSOR"]),
        ("CALENTADORES", ["CALENTADORES", "CALENTADOR", "CALENT", "BOILER"]),
        ("CISTERNAS", ["CISTERNAS", "CISTERNA"]),
        ("CORTADORAS", ["CORTADORAS", "CORTADORA"]),
        ("EQ HIDRONEUMATICOS", ["EQ HIDRONEUMATICOS", "HIDRONEUMATICO", "HIDRO"]),
        ("FERRETERIA", ["FERRETERIA"]),
        ("FOSAS", ["FOSAS", "FOSA"]),
        ("HERRAMIENTAS", ["HERRAMIENTAS", "HERRAMIENTA"]),
        ("IRRIGACION", ["IRRIGACION"]),
        ("JUEGOS ESPARCIMIEN", ["JUEGOS ESPARCIMIEN", "ESPARCIMIENTO"]),
        ("MANGUERAS", ["MANGUERAS", "MANGUERA", "MT MANGUERA"]),
        ("MANOMETROS", ["MANOMETROS", "MANOMETRO"]),
        ("MOTORES", ["MOTORES", "MOTOR"]),
        ("SERVICIOS", ["SERVICIOS", "SERVICIO"]),
        ("TANQUES Y CILINDRO", ["TANQUES Y CILINDRO", "TANQUES Y CILINDROS", "TANQUE", "CILINDRO"]),
        ("TINACOS", ["TINACOS", "TINACO"]),
        ("TINAS", ["TINAS", "TINA"]),
        ("TRABAJOS DE TALLER", ["TRABAJOS DE TALLER", "TALLER"])
    ],
    "HOGAR": [
        ("ACCESORIOS", ["ACCESORIOS", "ACCESORIO"]),
        ("ARTICULOS DE COCIN", ["ARTICULOS DE COCIN", "ARTICULOS DE COCINA", "COCINA"]),
        ("CABLES Y ALAMBRES", ["CABLES Y ALAMBRES", "CABLE", "ALAMBRE"]),
        ("CTRO CARGA/INTERRU", ["CTRO CARGA/INTERRU", "CTRO CARGA/INTERRUPT", "CENTRO DE CARGA", "INTERRUPTOR"]),
        ("ESPEJOS", ["ESPEJOS", "ESPEJO"]),
        ("FOCOS Y FILAMENTOS", ["FOCOS Y FILAMENTOS", "FOCO", "FOCOS", "FILAMENTO"]),
        ("FREGADEROS", ["FREGADEROS", "FREGADERO"]),
        ("GABINETES PARA BAÑ", ["GABINETES PARA BAÑ", "GABINETES PARA BAÑO", "GABINETE"]),
        ("ILUMINACION", ["ILUMINACION", "LAMPARA", "FOCO"]),
        ("IMPERMEABILIZANTES", ["IMPERMEABILIZANTES", "IMPERMEABILIZANTE"]),
        ("LAM CANAL GALV ACR", ["LAM CANAL GALV ACR", "LAM CANAL GALV ACRI", "LAMINA", "LAMINAS"]),
        ("LAVADEROS", ["LAVADEROS", "LAVADERO"]),
        ("LINEA BLANCA", ["LINEA BLANCA"]),
        ("MATERIAL ELECTR/HE", ["MATERIAL ELECTR/HE", "MATERIAL ELECTR/HERR", "ELECTRICO"]),
        ("PLACAS", ["PLACAS", "PLACA"]),
        ("TAPA/CONTACT/APAGA", ["TAPA/CONTACT/APAGA", "CONTACTO", "APAGADORA", "APAGADOR", "TAPA"])
    ]
}

def get_kuroda_familia_y_subfamilia(descrip_gpo_materiales: str, descripcion_material: str = ""):
    """
    Dada la categoría original de materiales y la descripción del producto,
    devuelve una tupla (familia_macro, subfamilia_oficial).
    """
    gpo = str(descrip_gpo_materiales or "").strip().upper()
    desc = str(descripcion_material or "").strip().upper()
    full_text = f"{gpo} {desc}"

    # 1. First attempt: match against descrip_gpo_materiales
    for fam, sub_pairs in SUBFAMILIA_MATCHERS.items():
        for sub_official, keywords in sub_pairs:
            for kw in keywords:
                if kw == gpo or kw in gpo:
                    return fam, sub_official

    # 2. Second attempt: match keywords in product description full_text
    for fam, sub_pairs in SUBFAMILIA_MATCHERS.items():
        for sub_official, keywords in sub_pairs:
            for kw in keywords:
                if len(kw) >= 3 and (f" {kw} " in f" {full_text} " or full_text.startswith(kw)):
                    return fam, sub_official

    # Fallback to general grouping
    return "OTROS", gpo or "GENERAL"
