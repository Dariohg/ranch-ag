"""
Definición de datos y requerimientos por especie animal.
Basado en las necesidades reales de los animales de rancho.
"""

class EspecieInfo:
    """
    Información básica de una especie animal.
    """

    def __init__(self, nombre, area_minima_por_animal, costo_cerca_por_metro,
                 distancia_minima_otras_especies, tipo_comedero, tipo_bebedero):
        self.nombre = nombre
        self.area_minima_por_animal = area_minima_por_animal  # m² por animal
        self.costo_cerca_por_metro = costo_cerca_por_metro    # pesos por metro
        self.distancia_minima_otras_especies = distancia_minima_otras_especies  # metros
        self.tipo_comedero = tipo_comedero
        self.tipo_bebedero = tipo_bebedero

# DATOS FIJOS - No modificables por el usuario
# Basados en estándares zootécnicos mexicanos
ESPECIES_DATA_FIJOS = {
    'gallinas': EspecieInfo(
        nombre='Gallinas',
        area_minima_por_animal=0.5,  # 0.5 m² por gallina - FIJO
        costo_cerca_por_metro=0,     # Se define en materiales configurables
        distancia_minima_otras_especies=3,  # 3 metros - FIJO
        tipo_comedero='tolva',
        tipo_bebedero='automatico'
    ),

    'cerdos': EspecieInfo(
        nombre='Cerdos',
        area_minima_por_animal=2.5,  # 2.5 m² por cerdo - FIJO
        costo_cerca_por_metro=0,     # Se define en materiales configurables
        distancia_minima_otras_especies=5,  # 5 metros - FIJO
        tipo_comedero='concreto',
        tipo_bebedero='chupón'
    ),

    'vacas': EspecieInfo(
        nombre='Vacas',
        area_minima_por_animal=15,   # 15 m² por vaca - FIJO
        costo_cerca_por_metro=0,     # Se define en materiales configurables
        distancia_minima_otras_especies=8,  # 8 metros - FIJO
        tipo_comedero='comedero_largo',
        tipo_bebedero='bebedero_grande'
    ),

    'cabras': EspecieInfo(
        nombre='Cabras',
        area_minima_por_animal=3,    # 3 m² por cabra - FIJO
        costo_cerca_por_metro=0,     # Se define en materiales configurables
        distancia_minima_otras_especies=2,  # 2 metros - FIJO
        tipo_comedero='comedero_elevado',
        tipo_bebedero='bebedero_medio'
    )
}

def obtener_info_especie(nombre_especie):
    """
    Obtiene la información FIJA de una especie específica.

    Args:
        nombre_especie: Nombre de la especie ('gallinas', 'cerdos', 'vacas', 'cabras')

    Returns:
        EspecieInfo: Información fija de la especie
    """
    if nombre_especie not in ESPECIES_DATA_FIJOS:
        raise ValueError(f"Especie {nombre_especie} no encontrada")

    return ESPECIES_DATA_FIJOS[nombre_especie]

def calcular_area_minima_corral(especie, cantidad_animales):
    """
    Calcula el área mínima requerida para un corral.

    Args:
        especie: Nombre de la especie
        cantidad_animales: Número de animales

    Returns:
        float: Área mínima en metros cuadrados
    """
    info = obtener_info_especie(especie)
    return info.area_minima_por_animal * cantidad_animales

def calcular_costo_cerca_corral(material_seleccionado, perimetro_metros):
    """
    Calcula el costo de cerca para un corral.
    El costo del material viene de la configuración del usuario.

    Args:
        material_seleccionado: Diccionario con info del material
        perimetro_metros: Perímetro del corral en metros

    Returns:
        float: Costo total de la cerca
    """
    return material_seleccionado['costo_por_metro'] * perimetro_metros

def obtener_especies_disponibles():
    """
    Obtiene la lista de especies disponibles.

    Returns:
        list: Lista de nombres de especies
    """
    return list(ESPECIES_DATA_FIJOS.keys())

def validar_compatibilidad_especies(especie1, especie2, distancia):
    """
    Valida si dos especies pueden estar a cierta distancia.

    Args:
        especie1: Primera especie
        especie2: Segunda especie
        distancia: Distancia entre corrales en metros

    Returns:
        bool: True si la distancia es adecuada
    """
    info1 = obtener_info_especie(especie1)
    info2 = obtener_info_especie(especie2)

    distancia_minima = max(info1.distancia_minima_otras_especies,
                          info2.distancia_minima_otras_especies)

    return distancia >= distancia_minima

# Configuración de rangos para mapeo de valores del vector
RANGOS_PARAMETROS = {
    'factor_agrandamiento': (1.0, 4.0),    # 1x a 4x el área mínima (aumentado de 2.0)
    'proporcion': (0.5, 2.0),              # Relación ancho/alto del corral
    'orientacion': (0, 360),               # Grados de orientación
    'densidad': (0.8, 1.2),               # Factor de densidad animal
    'acceso': (0, 1),                      # Tipo de acceso (normalizado)
    'ventilacion': (0, 1),                 # Nivel de ventilación (normalizado)
    'ancho_pasillos': (1.5, 4.0),         # Ancho de pasillos en metros
    'configuracion': (0, 1),              # Tipo de configuración (normalizado)
    'acceso_principal': (0, 1),           # Posición del acceso principal
    'conectividad': (0, 1)                # Nivel de conectividad
}

def mapear_valor_del_vector(parametro, valor_normalizado):
    """
    Mapea un valor normalizado [0,1] al rango real del parámetro.

    Args:
        parametro: Nombre del parámetro
        valor_normalizado: Valor entre 0 y 1

    Returns:
        float: Valor en el rango real del parámetro
    """
    if parametro not in RANGOS_PARAMETROS:
        return valor_normalizado

    min_val, max_val = RANGOS_PARAMETROS[parametro]
    return min_val + (max_val - min_val) * valor_normalizado