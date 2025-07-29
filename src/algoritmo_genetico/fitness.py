"""
Función de fitness para evaluar individuos del algoritmo genético.
Evalúa qué tan buena es una configuración de rancho según múltiples objetivos.
"""

import numpy as np
import math
from src.rancho.especies import obtener_info_especie, calcular_area_minima_corral, mapear_valor_del_vector
from src.utilidades.configuracion import configuracion_sistema

class EvaluadorFitness:
    """
    Evalúa el fitness de un individuo considerando todos los objetivos.
    """

    def __init__(self, configuracion):
        self.config = configuracion

    def calcular_fitness(self, individuo):
        """
        Calcula el fitness total de un individuo.

        Args:
            individuo: Instancia de la clase Individuo

        Returns:
            float: Valor de fitness (mayor es mejor)
        """
        # Decodificar el vector a datos físicos del rancho
        rancho_fisico = self._decodificar_individuo(individuo)

        # Verificar restricciones básicas
        if not self._es_factible(rancho_fisico):
            return 0.0  # Fitness muy bajo para soluciones no factibles

        # Calcular cada objetivo
        espacio_extra = self._calcular_espacio_extra(rancho_fisico)
        costo_construccion = self._calcular_costo_construccion(rancho_fisico)
        cantidad_materiales = self._calcular_cantidad_materiales(rancho_fisico)
        eficiencia_manejo = self._calcular_eficiencia_manejo(rancho_fisico)
        aprovechamiento_terreno = self._calcular_aprovechamiento_terreno(rancho_fisico)

        # Normalizar objetivos (convertir a valores 0-1)
        espacio_norm = self._normalizar_espacio(espacio_extra)
        costo_norm = self._normalizar_costo(costo_construccion)
        materiales_norm = self._normalizar_materiales(cantidad_materiales)
        manejo_norm = eficiencia_manejo  # Ya está normalizado
        terreno_norm = aprovechamiento_terreno  # Ya está normalizado

        # Aplicar pesos de objetivos
        pesos = self.config.rancho.pesos_objetivos
        fitness = (
            pesos['espacio_extra'] * espacio_norm +
            pesos['costo_construccion'] * (1.0 - costo_norm) +  # Invertir porque queremos minimizar
            pesos['cantidad_materiales'] * (1.0 - materiales_norm) +  # Invertir porque queremos minimizar
            pesos['eficiencia_manejo'] * manejo_norm +
            pesos['aprovechamiento_terreno'] * terreno_norm
        )

        return fitness

    def _decodificar_individuo(self, individuo):
        """
        Convierte el vector del individuo a datos físicos del rancho.

        Args:
            individuo: Instancia de Individuo

        Returns:
            dict: Datos físicos del rancho
        """
        corrales_data = individuo.obtener_datos_corrales()
        comederos_data = individuo.obtener_datos_comederos()
        bebederos_data = individuo.obtener_datos_bebederos()
        infraestructura_data = individuo.obtener_datos_infraestructura()

        rancho = {
            'corrales': {},
            'comederos': {},
            'bebederos': {},
            'infraestructura': {},
            'pasillos': {}
        }

        # Lista para verificar colisiones
        corrales_fisicos = []

        # Decodificar corrales con posicionamiento sin solapamientos
        especies_ordenadas = ['vacas', 'cerdos', 'cabras', 'gallinas']  # De mayor a menor área

        # Obtener peso de aprovechamiento del terreno para ajustar factores
        peso_terreno = self.config.rancho.pesos_objetivos.get('aprovechamiento_terreno', 0.1)

        for especie in especies_ordenadas:
            if self.config.rancho.cantidad_animales[especie] > 0:
                data = corrales_data[especie]

                # Mapear valores del vector a valores reales
                factor_agrand_base = mapear_valor_del_vector('factor_agrandamiento', data['factor_agrandamiento'])

                # Si el aprovechamiento del terreno tiene peso alto, aumentar el factor de agrandamiento
                if peso_terreno > 0.5:  # Más del 50% de peso
                    # Aumentar significativamente el factor de agrandamiento
                    factor_agrand = factor_agrand_base * (1.0 + peso_terreno)  # Hasta 6x con peso 1.0
                elif peso_terreno > 0.3:  # Más del 30% de peso
                    # Aumentar moderadamente el factor de agrandamiento
                    factor_agrand = factor_agrand_base * (1.0 + peso_terreno * 0.5)  # Hasta 5x con peso 1.0
                else:
                    factor_agrand = factor_agrand_base

                proporcion = mapear_valor_del_vector('proporcion', data['proporcion'])
                orientacion = mapear_valor_del_vector('orientacion', data['orientacion'])

                # Calcular área y dimensiones
                area_minima = calcular_area_minima_corral(especie, self.config.rancho.cantidad_animales[especie])
                area_real = area_minima * factor_agrand

                # Calcular ancho y alto del corral
                ancho = math.sqrt(area_real * proporcion)
                alto = area_real / ancho

                # Encontrar posición válida sin solapamientos
                pos_x, pos_y = self._encontrar_posicion_valida(
                    data['posicion_x'], data['posicion_y'],
                    ancho, alto, corrales_fisicos
                )

                corral_fisico = {
                    'posicion_x': pos_x,
                    'posicion_y': pos_y,
                    'ancho': ancho,
                    'alto': alto,
                    'area': area_real,
                    'area_minima': area_minima,
                    'orientacion': orientacion,
                    'factor_agrandamiento': factor_agrand
                }

                rancho['corrales'][especie] = corral_fisico
                corrales_fisicos.append({
                    'x': pos_x, 'y': pos_y, 'ancho': ancho, 'alto': alto, 'especie': especie
                })

        # Calcular sistema de pasillos basado en espacios libres
        infra = infraestructura_data
        ancho_pasillo_base = mapear_valor_del_vector('ancho_pasillos', infra['ancho_pasillos'])

        # Calcular ancho mínimo entre corrales
        ancho_pasillo_real = self._calcular_ancho_pasillos(corrales_fisicos, ancho_pasillo_base)

        rancho['infraestructura'] = {
            'ancho_pasillos': ancho_pasillo_real,
            'configuracion': infra['configuracion'],
            'acceso_principal': infra['acceso_principal'],
            'conectividad': infra['conectividad']
        }

        # Generar información de pasillos
        rancho['pasillos'] = self._generar_pasillos(corrales_fisicos, ancho_pasillo_real)

        return rancho

    def _encontrar_posicion_valida(self, pos_x_norm, pos_y_norm, ancho, alto, corrales_existentes):
        """
        Encuentra una posición válida para un corral sin solapamientos.
        """
        # Verificar peso de aprovechamiento del terreno
        peso_terreno = self.config.rancho.pesos_objetivos.get('aprovechamiento_terreno', 0.1)

        # Si el aprovechamiento del terreno tiene peso alto, ser menos conservador con las distancias
        if peso_terreno > 0.3:  # Más del 30% de peso
            margen_reducido = 1.0  # Reducir margen de separación
        else:
            margen_reducido = 1.5  # Margen normal

        # Posición inicial deseada
        pos_x_inicial = pos_x_norm * max(0, self.config.rancho.ancho_terreno - ancho)
        pos_y_inicial = pos_y_norm * max(0, self.config.rancho.largo_terreno - alto)

        # Verificar si la posición inicial es válida
        if self._posicion_es_valida(pos_x_inicial, pos_y_inicial, ancho, alto, corrales_existentes, margen_reducido):
            return pos_x_inicial, pos_y_inicial

        # Buscar posición alternativa en espiral
        max_intentos = 150 if peso_terreno > 0.3 else 100
        radio = 0.5

        for intento in range(max_intentos):
            angulo = (intento * 0.3) % (2 * math.pi)
            offset_x = radio * math.cos(angulo)
            offset_y = radio * math.sin(angulo)

            pos_x = pos_x_inicial + offset_x
            pos_y = pos_y_inicial + offset_y

            # Asegurar que esté dentro del terreno
            pos_x = max(0, min(pos_x, self.config.rancho.ancho_terreno - ancho))
            pos_y = max(0, min(pos_y, self.config.rancho.largo_terreno - alto))

            if self._posicion_es_valida(pos_x, pos_y, ancho, alto, corrales_existentes, margen_reducido):
                return pos_x, pos_y

            if intento % 15 == 14:  # Aumentar radio cada 15 intentos
                radio += 0.5

        # Si no se encuentra posición, usar la inicial (el fitness será penalizado)
        return pos_x_inicial, pos_y_inicial

    def _posicion_es_valida(self, x, y, ancho, alto, corrales_existentes, margen_minimo=1.5):
        """
        Verifica si una posición es válida (sin solapamientos).
        """
        for corral in corrales_existentes:
            if self._hay_solapamiento(x, y, ancho, alto,
                                    corral['x'], corral['y'],
                                    corral['ancho'], corral['alto'],
                                    margen_minimo):
                return False
        return True

    def _hay_solapamiento(self, x1, y1, w1, h1, x2, y2, w2, h2, margen):
        """
        Verifica si dos rectángulos se solapan considerando un margen.
        """
        return not (x1 + w1 + margen <= x2 or
                   x2 + w2 + margen <= x1 or
                   y1 + h1 + margen <= y2 or
                   y2 + h2 + margen <= y1)

    def _calcular_ancho_pasillos(self, corrales, ancho_base):
        """
        Calcula el ancho real de pasillos basado en el espacio disponible entre corrales.
        """
        if len(corrales) < 2:
            return ancho_base

        # Encontrar la distancia mínima entre corrales
        distancia_minima = float('inf')

        for i in range(len(corrales)):
            for j in range(i + 1, len(corrales)):
                c1, c2 = corrales[i], corrales[j]

                # Calcular distancia entre corrales
                distancia = self._distancia_entre_corrales(c1, c2)
                distancia_minima = min(distancia_minima, distancia)

        # El ancho de pasillos será el menor entre el deseado y el espacio disponible
        ancho_disponible = max(1.0, distancia_minima * 0.8)  # 80% del espacio disponible
        return min(ancho_base, ancho_disponible)

    def _distancia_entre_corrales(self, corral1, corral2):
        """
        Calcula la distancia mínima entre dos corrales.
        """
        # Calcular distancia entre bordes más cercanos
        dx = max(0, max(corral1['x'] - (corral2['x'] + corral2['ancho']),
                       corral2['x'] - (corral1['x'] + corral1['ancho'])))
        dy = max(0, max(corral1['y'] - (corral2['y'] + corral2['alto']),
                       corral2['y'] - (corral1['y'] + corral1['alto'])))

        return math.sqrt(dx*dx + dy*dy)

    def _generar_pasillos(self, corrales, ancho_pasillo):
        """
        Genera información de pasillos basada en espacios libres.
        """
        pasillos = {
            'perimetral': True,
            'ancho': ancho_pasillo,
            'conexiones': [],
            'areas_libres': []
        }

        # Calcular áreas libres (simplificado)
        ancho_terreno = self.config.rancho.ancho_terreno
        largo_terreno = self.config.rancho.largo_terreno

        # Área perimetral
        margen = 2.0
        pasillos['areas_libres'].append({
            'tipo': 'perimetral',
            'puntos': [
                (margen, margen),
                (ancho_terreno - margen, margen),
                (ancho_terreno - margen, largo_terreno - margen),
                (margen, largo_terreno - margen)
            ]
        })

        return pasillos

    def _es_factible(self, rancho_fisico):
        """
        Verifica si el rancho cumple las restricciones básicas.

        Args:
            rancho_fisico: Datos físicos del rancho

        Returns:
            bool: True si es factible
        """
        # Verificar que todos los corrales estén dentro del terreno
        for especie, corral in rancho_fisico['corrales'].items():
            x, y = corral['posicion_x'], corral['posicion_y']
            ancho, alto = corral['ancho'], corral['alto']

            # Verificar límites del terreno
            if (x < 0 or y < 0 or
                x + ancho > self.config.rancho.ancho_terreno or
                y + alto > self.config.rancho.largo_terreno):
                return False

        # Verificar que no haya solapamiento entre corrales
        especies = list(rancho_fisico['corrales'].keys())
        for i in range(len(especies)):
            for j in range(i + 1, len(especies)):
                if self._corrales_se_solapan(rancho_fisico['corrales'][especies[i]],
                                           rancho_fisico['corrales'][especies[j]]):
                    return False

        return True

    def _corrales_se_solapan(self, corral1, corral2):
        """
        Verifica si dos corrales se solapan.

        Args:
            corral1, corral2: Datos de los corrales

        Returns:
            bool: True si se solapan
        """
        # Coordenadas de las esquinas
        x1_min, y1_min = corral1['posicion_x'], corral1['posicion_y']
        x1_max, y1_max = x1_min + corral1['ancho'], y1_min + corral1['alto']

        x2_min, y2_min = corral2['posicion_x'], corral2['posicion_y']
        x2_max, y2_max = x2_min + corral2['ancho'], y2_min + corral2['alto']

        # Verificar solapamiento
        return not (x1_max <= x2_min or x2_max <= x1_min or
                   y1_max <= y2_min or y2_max <= y1_min)

    def _calcular_espacio_extra(self, rancho_fisico):
        """
        Calcula el espacio extra proporcionado por encima del mínimo.

        Args:
            rancho_fisico: Datos físicos del rancho

        Returns:
            float: Espacio extra total en m²
        """
        espacio_extra_total = 0

        for especie, corral in rancho_fisico['corrales'].items():
            area_extra = corral['area'] - corral['area_minima']
            espacio_extra_total += area_extra

        return espacio_extra_total

    def _calcular_costo_construccion(self, rancho_fisico):
        """
        Calcula el costo total de construcción.

        Args:
            rancho_fisico: Datos físicos del rancho

        Returns:
            float: Costo total en pesos
        """
        costo_total = 0

        for especie, corral in rancho_fisico['corrales'].items():
            # Calcular perímetro del corral
            perimetro = 2 * (corral['ancho'] + corral['alto'])

            # Obtener info del material
            material_info = self.config.obtener_info_material(especie)

            # Calcular costo de cerca
            costo_cerca = material_info['costo_por_metro'] * perimetro
            costo_total += costo_cerca

        # Agregar costo de pasillos (estimado)
        ancho_pasillos = rancho_fisico['infraestructura']['ancho_pasillos']
        longitud_pasillos_estimada = (self.config.rancho.ancho_terreno +
                                     self.config.rancho.largo_terreno) * 1.5
        costo_pasillos = 30 * ancho_pasillos * longitud_pasillos_estimada  # 30 pesos/m² para pasillos
        costo_total += costo_pasillos

        return costo_total

    def _calcular_cantidad_materiales(self, rancho_fisico):
        """
        Calcula la cantidad total de materiales necesarios.

        Args:
            rancho_fisico: Datos físicos del rancho

        Returns:
            float: Cantidad total de materiales (metros lineales)
        """
        metros_lineales_total = 0

        for especie, corral in rancho_fisico['corrales'].items():
            perimetro = 2 * (corral['ancho'] + corral['alto'])
            metros_lineales_total += perimetro

        return metros_lineales_total

    def _calcular_eficiencia_manejo(self, rancho_fisico):
        """
        Calcula la eficiencia de manejo del rancho.

        Args:
            rancho_fisico: Datos físicos del rancho

        Returns:
            float: Eficiencia normalizada entre 0 y 1
        """
        # Calcular distancias promedio entre corrales
        corrales = list(rancho_fisico['corrales'].values())
        if len(corrales) < 2:
            return 1.0

        distancias = []
        for i in range(len(corrales)):
            for j in range(i + 1, len(corrales)):
                x1, y1 = corrales[i]['posicion_x'], corrales[i]['posicion_y']
                x2, y2 = corrales[j]['posicion_x'], corrales[j]['posicion_y']
                distancia = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                distancias.append(distancia)

        distancia_promedio = sum(distancias) / len(distancias)

        # Normalizar (distancias más cortas = mejor manejo)
        distancia_maxima = math.sqrt(self.config.rancho.ancho_terreno**2 +
                                   self.config.rancho.largo_terreno**2)
        eficiencia = 1.0 - (distancia_promedio / distancia_maxima)

        # Considerar ancho de pasillos (más ancho = mejor manejo)
        factor_pasillos = min(rancho_fisico['infraestructura']['ancho_pasillos'] / 4.0, 1.0)

        return eficiencia * 0.7 + factor_pasillos * 0.3

    def _calcular_aprovechamiento_terreno(self, rancho_fisico):
        """
        Calcula qué tan bien se aprovecha el terreno.
        Mayor peso = corrales más grandes y mejor uso del espacio.

        Args:
            rancho_fisico: Datos físicos del rancho

        Returns:
            float: Aprovechamiento normalizado entre 0 y 1
        """
        area_total_terreno = self.config.rancho.ancho_terreno * self.config.rancho.largo_terreno
        area_total_corrales = sum(corral['area'] for corral in rancho_fisico['corrales'].values())

        # Calcular área mínima requerida
        area_minima_total = sum(corral['area_minima'] for corral in rancho_fisico['corrales'].values())

        # Obtener peso del aprovechamiento del terreno
        peso_terreno = self.config.rancho.pesos_objetivos.get('aprovechamiento_terreno', 0.1)

        # Si el peso es alto, ser más agresivo con el aprovechamiento
        if peso_terreno > 0.5:
            # Área de pasillos muy pequeña para maximizar corrales
            area_pasillos_estimada = area_total_terreno * 0.02  # Solo 2%
            meta_aprovechamiento = 0.95  # Meta del 95%
        elif peso_terreno > 0.3:
            # Área de pasillos pequeña
            area_pasillos_estimada = area_total_terreno * 0.03  # 3%
            meta_aprovechamiento = 0.85  # Meta del 85%
        else:
            # Área de pasillos normal
            area_pasillos_estimada = area_total_terreno * 0.05  # 5%
            meta_aprovechamiento = 0.70  # Meta del 70%

        # Área disponible para corrales
        area_disponible_corrales = area_total_terreno - area_pasillos_estimada

        if area_disponible_corrales <= area_minima_total:
            return 0.0

        # Calcular aprovechamiento real vs meta
        aprovechamiento_real = area_total_corrales / area_total_terreno
        aprovechamiento_relativo = aprovechamiento_real / meta_aprovechamiento

        # Factor de expansión: qué tanto se expandieron los corrales del mínimo
        if area_minima_total > 0:
            factor_expansion = area_total_corrales / area_minima_total
            # Con peso alto, premiar más la expansión
            if peso_terreno > 0.5:
                factor_expansion_norm = min((factor_expansion - 1.0) / 4.0, 1.0)  # 0 a 1 (hasta 5x)
            else:
                factor_expansion_norm = min((factor_expansion - 1.0) / 2.0, 1.0)  # 0 a 1 (hasta 3x)
        else:
            factor_expansion_norm = 0.0

        # Combinar factores dando más peso al aprovechamiento cuando es prioritario
        if peso_terreno > 0.5:
            aprovechamiento = (aprovechamiento_relativo * 0.8) + (factor_expansion_norm * 0.2)
        else:
            aprovechamiento = (aprovechamiento_relativo * 0.6) + (factor_expansion_norm * 0.4)

        return min(aprovechamiento, 1.0)

    def _normalizar_espacio(self, espacio_extra):
        """Normaliza el espacio extra a un valor entre 0 y 1."""
        # Estimar espacio extra máximo posible
        area_terreno = self.config.rancho.ancho_terreno * self.config.rancho.largo_terreno
        espacio_maximo = area_terreno * 0.5  # Máximo 50% del terreno como espacio extra

        return min(espacio_extra / espacio_maximo, 1.0)

    def _normalizar_costo(self, costo):
        """Normaliza el costo a un valor entre 0 y 1."""
        # Usar el presupuesto máximo como referencia
        return min(costo / self.config.rancho.presupuesto_maximo, 1.0)

    def _normalizar_materiales(self, metros_lineales):
        """Normaliza la cantidad de materiales a un valor entre 0 y 1."""
        # Estimar máximo de metros lineales posible
        perimetro_terreno = 2 * (self.config.rancho.ancho_terreno + self.config.rancho.largo_terreno)
        maximo_estimado = perimetro_terreno * 3  # Factor estimado

        return min(metros_lineales / maximo_estimado, 1.0)

def evaluar_individuo(individuo, configuracion=None):
    """
    Función de conveniencia para evaluar un individuo.

    Args:
        individuo: Instancia de Individuo
        configuracion: Configuración del sistema (opcional)

    Returns:
        float: Valor de fitness
    """
    if configuracion is None:
        configuracion = configuracion_sistema

    evaluador = EvaluadorFitness(configuracion)
    fitness = evaluador.calcular_fitness(individuo)
    individuo.fitness = fitness

    return fitness