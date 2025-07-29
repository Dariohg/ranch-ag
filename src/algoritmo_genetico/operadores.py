"""
Operadores genéticos: selección, cruza y mutación.
Implementa los mecanismos de evolución del algoritmo genético.
"""

import random
import numpy as np
from src.algoritmo_genetico.individuo import Individuo


class OperadoresGeneticos:
    """
    Implementa todos los operadores genéticos del algoritmo.
    """

    def __init__(self, configuracion):
        self.config = configuracion.algoritmo_genetico

    def seleccion_torneo(self, poblacion):
        """
        Selecciona individuos usando selección por torneo.

        Args:
            poblacion: Lista de individuos

        Returns:
            list: Individuos seleccionados para reproducción
        """
        seleccionados = []
        tamano_seleccion = len(poblacion)

        for _ in range(tamano_seleccion):
            # Crear torneo
            participantes = random.sample(poblacion, self.config.tamano_torneo)

            # Seleccionar el mejor del torneo
            ganador = max(participantes, key=lambda x: x.fitness if x.fitness is not None else 0)
            seleccionados.append(ganador)

        return seleccionados

    def seleccion_ruleta(self, poblacion):
        """
        Selecciona individuos usando selección por ruleta.

        Args:
            poblacion: Lista de individuos

        Returns:
            list: Individuos seleccionados para reproducción
        """
        # Calcular fitness total
        fitness_total = sum(ind.fitness for ind in poblacion if ind.fitness is not None)

        if fitness_total == 0:
            # Si no hay fitness, selección aleatoria
            return random.choices(poblacion, k=len(poblacion))

        # Calcular probabilidades
        probabilidades = [ind.fitness / fitness_total for ind in poblacion]

        # Seleccionar con probabilidades proporcionales al fitness
        seleccionados = random.choices(poblacion, weights=probabilidades, k=len(poblacion))

        return seleccionados

    def seleccion_elite(self, poblacion):
        """
        Selecciona los mejores individuos (elite).

        Args:
            poblacion: Lista de individuos

        Returns:
            list: Los mejores individuos
        """
        poblacion_ordenada = sorted(poblacion,
                                    key=lambda x: x.fitness if x.fitness is not None else 0,
                                    reverse=True)

        return poblacion_ordenada[:self.config.numero_elite]

    def cruza_uniforme(self, padre1, padre2):
        """
        Realiza cruza uniforme entre dos padres.

        Args:
            padre1, padre2: Individuos padre

        Returns:
            tuple: (hijo1, hijo2)
        """
        vector_hijo1 = np.zeros(52)
        vector_hijo2 = np.zeros(52)

        for i in range(52):
            if random.random() < 0.5:
                # Heredar del padre1
                vector_hijo1[i] = padre1.vector[i]
                vector_hijo2[i] = padre2.vector[i]
            else:
                # Heredar del padre2
                vector_hijo1[i] = padre2.vector[i]
                vector_hijo2[i] = padre1.vector[i]

        hijo1 = Individuo(vector_hijo1)
        hijo2 = Individuo(vector_hijo2)

        return hijo1, hijo2

    def cruza_por_bloques(self, padre1, padre2):
        """
        Realiza cruza por bloques funcionales.

        Args:
            padre1, padre2: Individuos padre

        Returns:
            tuple: (hijo1, hijo2)
        """
        # Definir bloques funcionales
        bloques = {
            'corrales': (0, 32),  # Posiciones 0-31
            'comederos': (32, 40),  # Posiciones 32-39
            'bebederos': (40, 48),  # Posiciones 40-47
            'infraestructura': (48, 52)  # Posiciones 48-51
        }

        vector_hijo1 = padre1.vector.copy()
        vector_hijo2 = padre2.vector.copy()

        # Intercambiar bloques aleatoriamente
        for nombre_bloque, (inicio, fin) in bloques.items():
            if random.random() < 0.5:
                # Intercambiar este bloque
                vector_hijo1[inicio:fin] = padre2.vector[inicio:fin]
                vector_hijo2[inicio:fin] = padre1.vector[inicio:fin]

        hijo1 = Individuo(vector_hijo1)
        hijo2 = Individuo(vector_hijo2)

        return hijo1, hijo2

    def cruza_aritmetica(self, padre1, padre2, alfa=0.5):
        """
        Realiza cruza aritmética (promedio ponderado).

        Args:
            padre1, padre2: Individuos padre
            alfa: Factor de combinación (0.5 = promedio)

        Returns:
            tuple: (hijo1, hijo2)
        """
        vector_hijo1 = alfa * padre1.vector + (1 - alfa) * padre2.vector
        vector_hijo2 = (1 - alfa) * padre1.vector + alfa * padre2.vector

        hijo1 = Individuo(vector_hijo1)
        hijo2 = Individuo(vector_hijo2)

        return hijo1, hijo2

    def aplicar_cruza(self, padre1, padre2):
        """
        Aplica el tipo de cruza configurado.

        Args:
            padre1, padre2: Individuos padre

        Returns:
            tuple: (hijo1, hijo2)
        """
        if self.config.tipo_cruza == 'uniforme':
            return self.cruza_uniforme(padre1, padre2)
        elif self.config.tipo_cruza == 'bloques':
            return self.cruza_por_bloques(padre1, padre2)
        elif self.config.tipo_cruza == 'aritmetica':
            return self.cruza_aritmetica(padre1, padre2)
        else:
            return self.cruza_uniforme(padre1, padre2)  # Por defecto

    def mutacion_gaussiana(self, individuo, intensidad=None):
        """
        Aplica mutación gaussiana a un individuo.

        Args:
            individuo: Individuo a mutar
            intensidad: Intensidad de la mutación (opcional)
        """
        if intensidad is None:
            intensidad = self.config.intensidad_mutacion

        for i in range(len(individuo.vector)):
            if random.random() < self.config.probabilidad_mutacion:
                # Agregar ruido gaussiano
                ruido = np.random.normal(0, intensidad)
                individuo.vector[i] += ruido

                # Mantener en rango [0, 1]
                individuo.vector[i] = np.clip(individuo.vector[i], 0, 1)

        # Invalidar fitness después de mutación
        individuo.fitness = None

    def mutacion_uniforme(self, individuo, intensidad=None):
        """
        Aplica mutación uniforme a un individuo.

        Args:
            individuo: Individuo a mutar
            intensidad: Rango de la mutación (opcional)
        """
        if intensidad is None:
            intensidad = self.config.intensidad_mutacion

        for i in range(len(individuo.vector)):
            if random.random() < self.config.probabilidad_mutacion:
                # Cambio uniforme en el rango [-intensidad, +intensidad]
                cambio = random.uniform(-intensidad, intensidad)
                individuo.vector[i] += cambio

                # Mantener en rango [0, 1]
                individuo.vector[i] = np.clip(individuo.vector[i], 0, 1)

        individuo.fitness = None

    def mutacion_por_reemplazo(self, individuo):
        """
        Aplica mutación por reemplazo (valores completamente nuevos).

        Args:
            individuo: Individuo a mutar
        """
        for i in range(len(individuo.vector)):
            if random.random() < self.config.probabilidad_mutacion:
                # Reemplazar con valor aleatorio
                individuo.vector[i] = random.random()

        individuo.fitness = None

    def mutacion_adaptativa(self, individuo, generacion_actual, generaciones_totales):
        """
        Aplica mutación con intensidad adaptativa.

        Args:
            individuo: Individuo a mutar
            generacion_actual: Generación actual
            generaciones_totales: Total de generaciones
        """
        # Reducir intensidad con el tiempo
        factor_reduccion = 1.0 - (generacion_actual / generaciones_totales)
        intensidad_adaptativa = self.config.intensidad_mutacion * factor_reduccion

        # Asegurar intensidad mínima
        intensidad_adaptativa = max(intensidad_adaptativa, 0.01)

        self.mutacion_gaussiana(individuo, intensidad_adaptativa)

    def aplicar_mutacion(self, individuo, generacion_actual=None, generaciones_totales=None):
        """
        Aplica mutación según la configuración.

        Args:
            individuo: Individuo a mutar
            generacion_actual: Generación actual (para mutación adaptativa)
            generaciones_totales: Total de generaciones (para mutación adaptativa)
        """
        if self.config.mutacion_adaptativa and generacion_actual is not None:
            self.mutacion_adaptativa(individuo, generacion_actual, generaciones_totales)
        else:
            self.mutacion_gaussiana(individuo)

    def reproducir_poblacion(self, poblacion_seleccionada, tamano_objetivo):
        """
        Genera nueva población a través de cruza y mutación.

        Args:
            poblacion_seleccionada: Individuos seleccionados para reproducción
            tamano_objetivo: Tamaño deseado de la nueva población

        Returns:
            list: Nueva población
        """
        nueva_poblacion = []

        # Preservar elite
        elite = self.seleccion_elite(poblacion_seleccionada)
        nueva_poblacion.extend([ind.clonar() for ind in elite])

        # Generar resto de la población
        while len(nueva_poblacion) < tamano_objetivo:
            # Seleccionar padres
            padre1 = random.choice(poblacion_seleccionada)
            padre2 = random.choice(poblacion_seleccionada)

            # Aplicar cruza si cumple probabilidad
            if random.random() < self.config.probabilidad_cruza:
                hijo1, hijo2 = self.aplicar_cruza(padre1, padre2)
            else:
                # Si no hay cruza, clonar padres
                hijo1 = padre1.clonar()
                hijo2 = padre2.clonar()

            # Agregar hijos a la población
            if len(nueva_poblacion) < tamano_objetivo:
                nueva_poblacion.append(hijo1)
            if len(nueva_poblacion) < tamano_objetivo:
                nueva_poblacion.append(hijo2)

        return nueva_poblacion[:tamano_objetivo]

    def aplicar_mutacion_poblacion(self, poblacion, generacion_actual=None):
        """
        Aplica mutación a toda la población (excepto elite).

        Args:
            poblacion: Lista de individuos
            generacion_actual: Generación actual
        """
        # No mutar la elite
        inicio_mutacion = self.config.numero_elite

        for i in range(inicio_mutacion, len(poblacion)):
            self.aplicar_mutacion(poblacion[i],
                                  generacion_actual,
                                  self.config.numero_generaciones)


class ControladorEvolucion:
    """
    Controla el proceso de evolución de la población.
    """

    def __init__(self, configuracion):
        self.config = configuracion
        self.operadores = OperadoresGeneticos(configuracion)

    def evolucionar_generacion(self, poblacion_actual, generacion):
        """
        Evoluciona una generación completa.

        Args:
            poblacion_actual: Población actual
            generacion: Número de generación

        Returns:
            list: Nueva población evolucionada
        """
        # 1. Selección
        poblacion_seleccionada = self.operadores.seleccion_torneo(poblacion_actual)

        # 2. Reproducción (cruza)
        nueva_poblacion = self.operadores.reproducir_poblacion(
            poblacion_seleccionada,
            self.config.algoritmo_genetico.tamano_poblacion
        )

        # 3. Mutación
        self.operadores.aplicar_mutacion_poblacion(nueva_poblacion, generacion)

        return nueva_poblacion

    def obtener_estadisticas_poblacion(self, poblacion):
        """
        Calcula estadísticas de la población.

        Args:
            poblacion: Lista de individuos

        Returns:
            dict: Estadísticas de fitness
        """
        fitness_valores = [ind.fitness for ind in poblacion if ind.fitness is not None]

        if not fitness_valores:
            return {
                'mejor': 0,
                'promedio': 0,
                'peor': 0,
                'desviacion': 0
            }

        return {
            'mejor': max(fitness_valores),
            'promedio': sum(fitness_valores) / len(fitness_valores),
            'peor': min(fitness_valores),
            'desviacion': np.std(fitness_valores)
        }