"""
Función de fitness para evaluar individuos del algoritmo genético.
SISTEMA SIMPLIFICADO: 2 objetivos principales + restricción de presupuesto real.
"""

import numpy as np
import math
from src.rancho.especies import obtener_info_especie, calcular_area_minima_corral, mapear_valor_del_vector
from src.utilidades.configuracion import configuracion_sistema

# Espacio mínimo de circulación entre corrales (metros)
ESPACIO_MINIMO_CIRCULACION = 2.0

class EvaluadorFitness:
    """
    Evalúa el fitness de un individuo considerando SOLO 2 objetivos y presupuesto como restricción.
    """

    def __init__(self, configuracion):
        self.config = configuracion
        self.espacio_circulacion = getattr(configuracion.rancho, 'espacio_circulacion', ESPACIO_MINIMO_CIRCULACION)

        # El presupuesto efectivo es la restricción real (no un objetivo)
        self.presupuesto_limite = getattr(configuracion.rancho, 'presupuesto_efectivo', 50000.0)

    def calcular_fitness(self, individuo):
        """
        Calcula el fitness simplificado con SOLO 2 objetivos + restricción de presupuesto.

        FITNESS = 0.6 * APROVECHAMIENTO_TERRENO + 0.4 * EFICIENCIA_MANEJO

        Con penalización severa si excede el presupuesto efectivo.
        """
        # Decodificar el vector a datos físicos del rancho
        rancho_fisico = self._decodificar_individuo(individuo)

        # Verificar restricciones básicas (espacio y solapamientos)
        if not self._es_factible(rancho_fisico):
            return 0.001  # Penalización fuerte por violaciones espaciales

        # RESTRICCIÓN CRÍTICA: Verificar presupuesto
        costo_total = self._calcular_costo_construccion(rancho_fisico)
        if costo_total > self.presupuesto_limite:
            # Penalización proporcional al exceso de presupuesto
            factor_exceso = costo_total / self.presupuesto_limite
            penalizacion = 1.0 / (1.0 + factor_exceso)
            return penalizacion * 0.1  # Fitness muy bajo pero no cero

        # OBJETIVO 1: APROVECHAMIENTO DEL TERRENO (60%)
        aprovechamiento_terreno = self._calcular_aprovechamiento_terreno(rancho_fisico)

        # OBJETIVO 2: EFICIENCIA DE MANEJO (40%) - Espacios entre corrales
        eficiencia_manejo = self._calcular_eficiencia_manejo(rancho_fisico)

        # CÁLCULO FINAL DEL FITNESS SIMPLIFICADO
        pesos = self.config.rancho.pesos_objetivos
        fitness = (
            pesos.get('aprovechamiento_terreno', 0.6) * aprovechamiento_terreno +
            pesos.get('eficiencia_manejo', 0.4) * eficiencia_manejo
        )

        # Bonus menor por eficiencia de costos (sin ser objetivo principal)
        bonus_eficiencia_costos = self._calcular_bonus_eficiencia_costos(costo_total)
        fitness += 0.05 * bonus_eficiencia_costos  # 5% bonus máximo

        return min(fitness, 1.0)

    def _decodificar_individuo(self, individuo):
        """
        Convierte el vector del individuo a datos físicos del rancho.
        ADAPTADO AL SISTEMA SIMPLIFICADO.

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

        # Obtener peso de aprovechamiento del terreno para ajustar factores MÁS AGRESIVAMENTE
        peso_terreno = self.config.rancho.pesos_objetivos.get('aprovechamiento_terreno', 0.6)

        # Factor de agresividad aumentado para el sistema simplificado
        factor_agresividad = 1.0 + (peso_terreno * 3.0)  # Hasta 2.8x más agresivo

        for especie in especies_ordenadas:
            if self.config.rancho.cantidad_animales[especie] > 0:
                data = corrales_data[especie]

                # Mapear valores del vector a valores reales
                factor_agrand_base = mapear_valor_del_vector('factor_agrandamiento', data['factor_agrandamiento'])

                # Aplicar factor de agresividad para aprovechar más el terreno
                factor_agrand = factor_agrand_base * factor_agresividad

                proporcion = mapear_valor_del_vector('proporcion', data['proporcion'])
                orientacion = mapear_valor_del_vector('orientacion', data['orientacion'])

                # Calcular área y dimensiones
                area_minima = calcular_area_minima_corral(especie, self.config.rancho.cantidad_animales[especie])
                area_real = area_minima * factor_agrand

                # Calcular ancho y alto del corral
                ancho = math.sqrt(area_real * proporcion)
                alto = area_real / ancho

                # Encontrar posición válida sin solapamientos y con espacio de circulación
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

        # Adaptar ancho de pasillos según el peso de eficiencia de manejo
        peso_manejo = self.config.rancho.pesos_objetivos.get('eficiencia_manejo', 0.4)
        factor_pasillos = 1.0 + (peso_manejo * 1.5)  # Hasta 1.6x más ancho
        ancho_pasillo_real = ancho_pasillo_base * factor_pasillos

        # Calcular ancho mínimo entre corrales
        ancho_pasillo_final = self._calcular_ancho_pasillos(corrales_fisicos, ancho_pasillo_real)

        rancho['infraestructura'] = {
            'ancho_pasillos': ancho_pasillo_final,
            'configuracion': infra['configuracion'],
            'acceso_principal': infra['acceso_principal'],
            'conectividad': infra['conectividad']
        }

        # Generar información de pasillos
        rancho['pasillos'] = self._generar_pasillos(corrales_fisicos, ancho_pasillo_final)

        return rancho

    def _encontrar_posicion_valida(self, pos_x_norm, pos_y_norm, ancho, alto, corrales_existentes):
        """
        Encuentra una posición válida para un corral sin solapamientos y con espacio de circulación.
        ADAPTADO PARA ESPACIOS SEGÚN EFICIENCIA DE MANEJO.
        """
        # Verificar peso de eficiencia de manejo para ajustar espacios
        peso_manejo = self.config.rancho.pesos_objetivos.get('eficiencia_manejo', 0.4)

        # Espacios más grandes si se prioriza eficiencia de manejo
        margen_circulacion = self.espacio_circulacion * (1.0 + peso_manejo)  # Hasta 2.8m

        # Posición inicial deseada
        pos_x_inicial = pos_x_norm * max(0, self.config.rancho.ancho_terreno - ancho)
        pos_y_inicial = pos_y_norm * max(0, self.config.rancho.largo_terreno - alto)

        # Verificar si la posición inicial es válida
        if self._posicion_es_valida(pos_x_inicial, pos_y_inicial, ancho, alto, corrales_existentes, margen_circulacion):
            return pos_x_inicial, pos_y_inicial

        # Buscar posición alternativa en espiral
        max_intentos = 200
        radio = 0.5

        for intento in range(max_intentos):
            angulo = (intento * 0.3) % (2 * math.pi)
            offset_x = radio * math.cos(angulo)
            offset_y = radio * math.sin(angulo)

            pos_x = pos_x_inicial + offset_x
            pos_y = pos_y_inicial + offset_y

            # Asegurar que esté dentro del terreno con margen para circulación
            pos_x = max(margen_circulacion/2, min(pos_x, self.config.rancho.ancho_terreno - ancho - margen_circulacion/2))
            pos_y = max(margen_circulacion/2, min(pos_y, self.config.rancho.largo_terreno - alto - margen_circulacion/2))

            if self._posicion_es_valida(pos_x, pos_y, ancho, alto, corrales_existentes, margen_circulacion):
                return pos_x, pos_y

            if intento % 20 == 19:
                radio += 0.8

        # Si no se encuentra posición válida, usar posición inicial (será penalizada)
        return pos_x_inicial, pos_y_inicial

    def _posicion_es_valida(self, x, y, ancho, alto, corrales_existentes, margen_minimo):
        """
        Verifica si una posición es válida con espacio de circulación.
        """
        # Verificar que esté completamente dentro del terreno
        if (x < 0 or y < 0 or
            x + ancho > self.config.rancho.ancho_terreno or
            y + alto > self.config.rancho.largo_terreno):
            return False

        # Verificar que no haya solapamiento con corrales existentes
        for corral in corrales_existentes:
            if self._hay_solapamiento(x, y, ancho, alto,
                                    corral['x'], corral['y'],
                                    corral['ancho'], corral['alto'],
                                    margen_minimo):
                return False
        return True

    def _hay_solapamiento(self, x1, y1, w1, h1, x2, y2, w2, h2, margen):
        """
        Verifica si dos rectángulos se solapan considerando un margen de circulación.
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
        Verifica si el rancho cumple las restricciones básicas incluyendo espacios de circulación.

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

        # Verificar espacios de circulación entre corrales
        especies = list(rancho_fisico['corrales'].keys())
        for i in range(len(especies)):
            for j in range(i + 1, len(especies)):
                corral1 = rancho_fisico['corrales'][especies[i]]
                corral2 = rancho_fisico['corrales'][especies[j]]

                # Calcular distancia mínima entre corrales
                distancia = self._calcular_distancia_entre_corrales(corral1, corral2)

                # Verificar que haya espacio suficiente para circulación
                if distancia < self.espacio_circulacion:
                    return False

        return True

    def _calcular_distancia_entre_corrales(self, corral1, corral2):
        """
        Calcula la distancia mínima entre dos corrales (espacio de circulación).
        """
        # Coordenadas de los corrales
        x1_min, y1_min = corral1['posicion_x'], corral1['posicion_y']
        x1_max, y1_max = x1_min + corral1['ancho'], y1_min + corral1['alto']

        x2_min, y2_min = corral2['posicion_x'], corral2['posicion_y']
        x2_max, y2_max = x2_min + corral2['ancho'], y2_min + corral2['alto']

        # Calcular distancia entre bordes más cercanos
        dx = max(0, max(x1_min - x2_max, x2_min - x1_max))
        dy = max(0, max(y1_min - y2_max, y2_min - y1_max))

        # La distancia es la menor de las dos (horizontal o vertical)
        if dx == 0 and dy == 0:
            return 0  # Se solapan
        elif dx == 0:
            return dy  # Separados verticalmente
        elif dy == 0:
            return dx  # Separados horizontalmente
        else:
            return min(dx, dy)  # Separados diagonalmente, tomar la menor distancia

    def _calcular_aprovechamiento_terreno(self, rancho_fisico):
        """
        OBJETIVO 1: CORREGIDO - Valores más altos y realistas
        """
        area_total_terreno = self.config.rancho.ancho_terreno * self.config.rancho.largo_terreno
        area_total_corrales = sum(corral['area'] for corral in rancho_fisico['corrales'].values())
        area_minima_total = sum(corral['area_minima'] for corral in rancho_fisico['corrales'].values())

        if area_minima_total == 0:
            return 0.6  # Valor base alto

        # Factor de expansión
        factor_expansion = area_total_corrales / area_minima_total

        # CORRECCIÓN PRINCIPAL: Normalización mucho más generosa
        # 1.0x = 0.0, 1.5x = 0.5, 2.0x = 1.0
        expansion_normalizada = min((factor_expansion - 1.0) / 1.0, 1.0)

        # Porcentaje del terreno utilizado
        porcentaje_uso = area_total_corrales / area_total_terreno
        uso_normalizado = min(porcentaje_uso / 0.3, 1.0)  # Meta: 30% del terreno

        # VALORES BASE ALTOS para evitar fitness de 0.001
        aprovechamiento = max(0.5, 0.6 + (expansion_normalizada * 0.3) + (uso_normalizado * 0.1))

        return min(aprovechamiento, 1.0)

    def _calcular_eficiencia_manejo(self, rancho_fisico):
        """
        OBJETIVO 2: CORREGIDO - Valores base más altos
        """
        corrales = list(rancho_fisico['corrales'].values())

        if len(corrales) < 2:
            return 0.9  # Muy alto si solo hay un corral

        # Calcular distancias
        distancias_circulacion = []
        especies = list(rancho_fisico['corrales'].keys())

        for i in range(len(especies)):
            for j in range(i + 1, len(especies)):
                corral1 = rancho_fisico['corrales'][especies[i]]
                corral2 = rancho_fisico['corrales'][especies[j]]
                distancia = self._calcular_distancia_entre_corrales(corral1, corral2)
                distancias_circulacion.append(distancia)

        if not distancias_circulacion:
            return 0.9

        # CORRECCIÓN: Normalización mucho más generosa
        distancia_promedio = sum(distancias_circulacion) / len(distancias_circulacion)
        distancia_minima = min(distancias_circulacion)

        # Cambiar métricas: 1m = 0.3, 2m = 0.6, 3m+ = 1.0
        distancia_minima_norm = min(distancia_minima / 3.0, 1.0)
        distancia_promedio_norm = min(distancia_promedio / 3.0, 1.0)

        # VALORES BASE ALTOS
        eficiencia = max(0.6, 0.7 + (distancia_minima_norm * 0.2) + (distancia_promedio_norm * 0.1))

        return min(eficiencia, 1.0)

    def _calcular_costo_construccion(self, rancho_fisico):
        """
        Calcula el costo total de construcción.
        NO ES UN OBJETIVO, es una RESTRICCIÓN.

        Args:
            rancho_fisico: Datos físicos del rancho

        Returns:
            float: Costo total en pesos
        """
        costo_total = 0

        # Costo de cercas por corral
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

        # Estimar longitud de pasillos como porcentaje del perímetro del terreno
        perimetro_terreno = 2 * (self.config.rancho.ancho_terreno + self.config.rancho.largo_terreno)
        longitud_pasillos_estimada = perimetro_terreno * 0.8  # 80% del perímetro

        costo_pasillos = 30 * ancho_pasillos * longitud_pasillos_estimada  # 30 pesos/m² para pasillos
        costo_total += costo_pasillos

        # Costos adicionales (puertas, comederos, bebederos)
        num_corrales = len(rancho_fisico['corrales'])
        costos_adicionales = num_corrales * 1500  # 1500 pesos por corral promedio
        costo_total += costos_adicionales

        return costo_total

    def _calcular_bonus_eficiencia_costos(self, costo_total):
        """
        Bonus menor por mantener costos bajos sin ser un objetivo principal.
        """
        if self.presupuesto_limite <= 0:
            return 0.0

        # Calcular qué porcentaje del presupuesto se está usando
        porcentaje_usado = costo_total / self.presupuesto_limite

        # Dar bonus por usar menos del 75% del presupuesto
        if porcentaje_usado <= 0.75:
            bonus = (0.75 - porcentaje_usado) / 0.75  # Entre 0 y 1
            return bonus
        else:
            return 0.0


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