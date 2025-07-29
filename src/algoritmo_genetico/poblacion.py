"""
Manejo de la población del algoritmo genético.
Controla la generación inicial, evolución y criterios de parada.
"""

import time
import random
from concurrent.futures import ThreadPoolExecutor
from src.algoritmo_genetico.individuo import Individuo
from src.algoritmo_genetico.fitness import evaluar_individuo
from src.algoritmo_genetico.operadores import ControladorEvolucion


class Poblacion:
    """
    Maneja la población del algoritmo genético.
    """

    def __init__(self, configuracion):
        self.config = configuracion
        self.individuos = []
        self.generacion_actual = 0
        self.mejor_individuo = None
        self.historial_fitness = []
        self.tiempo_inicio = None
        self.controlador_evolucion = ControladorEvolucion(configuracion)

    def generar_poblacion_inicial(self):
        """
        Genera la población inicial aleatoria.
        """
        print("Generando población inicial...")
        self.individuos = []

        for i in range(self.config.algoritmo_genetico.tamano_poblacion):
            individuo = Individuo()  # Se genera aleatoriamente
            self.individuos.append(individuo)

            if (i + 1) % 20 == 0:
                print(f"Generados {i + 1} individuos...")

        print(f"Población inicial generada: {len(self.individuos)} individuos")

    def evaluar_poblacion(self, usar_paralelismo=True):
        """
        Evalúa el fitness de toda la población.

        Args:
            usar_paralelismo: Si usar procesamiento paralelo
        """
        if usar_paralelismo and len(self.individuos) > 20:
            self._evaluar_poblacion_paralela()
        else:
            self._evaluar_poblacion_secuencial()

        # Actualizar mejor individuo
        self._actualizar_mejor_individuo()

    def _evaluar_poblacion_secuencial(self):
        """Evalúa la población de forma secuencial."""
        for i, individuo in enumerate(self.individuos):
            if individuo.fitness is None:
                evaluar_individuo(individuo, self.config)

                if (i + 1) % 25 == 0:
                    print(f"Evaluados {i + 1}/{len(self.individuos)} individuos")

    def _evaluar_poblacion_paralela(self):
        """Evalúa la población usando múltiples hilos."""
        individuos_sin_evaluar = [ind for ind in self.individuos if ind.fitness is None]

        if not individuos_sin_evaluar:
            return

        print(f"Evaluando {len(individuos_sin_evaluar)} individuos en paralelo...")

        def evaluar_individuo_wrapper(individuo):
            evaluar_individuo(individuo, self.config)
            return individuo

        with ThreadPoolExecutor(max_workers=4) as executor:
            list(executor.map(evaluar_individuo_wrapper, individuos_sin_evaluar))

    def _actualizar_mejor_individuo(self):
        """Actualiza el mejor individuo de la población."""
        if not self.individuos:
            return

        mejor_actual = max(self.individuos,
                           key=lambda x: x.fitness if x.fitness is not None else 0)

        if (self.mejor_individuo is None or
                mejor_actual.fitness > self.mejor_individuo.fitness):
            self.mejor_individuo = mejor_actual.clonar()

    def evolucionar_generacion(self):
        """
        Evoluciona una generación completa.

        Returns:
            dict: Estadísticas de la generación
        """
        # Evolucionar población
        nueva_poblacion = self.controlador_evolucion.evolucionar_generacion(
            self.individuos,
            self.generacion_actual
        )

        # Reemplazar población
        self.individuos = nueva_poblacion
        self.generacion_actual += 1

        # Evaluar nueva población
        self.evaluar_poblacion()

        # Calcular estadísticas
        estadisticas = self.controlador_evolucion.obtener_estadisticas_poblacion(self.individuos)
        self.historial_fitness.append(estadisticas)

        return estadisticas

    def ejecutar_algoritmo(self, callback_progreso=None):
        """
        Ejecuta el algoritmo genético completo.

        Args:
            callback_progreso: Función que se llama en cada generación

        Returns:
            dict: Resultados finales del algoritmo
        """
        print("=== INICIANDO ALGORITMO GENÉTICO ===")
        self.tiempo_inicio = time.time()

        # Generar población inicial
        self.generar_poblacion_inicial()

        # Evaluar población inicial
        print("Evaluando población inicial...")
        self.evaluar_poblacion()

        # Estadísticas iniciales
        estadisticas_inicial = self.controlador_evolucion.obtener_estadisticas_poblacion(self.individuos)
        self.historial_fitness.append(estadisticas_inicial)

        print(f"Fitness inicial - Mejor: {estadisticas_inicial['mejor']:.4f}, "
              f"Promedio: {estadisticas_inicial['promedio']:.4f}")

        # Variables para criterios de parada
        generaciones_sin_mejora = 0
        mejor_fitness_anterior = 0

        # Ciclo principal de evolución
        for generacion in range(self.config.algoritmo_genetico.numero_generaciones):
            print(f"\n--- Generación {generacion + 1} ---")

            # Evolucionar una generación
            estadisticas = self.evolucionar_generacion()

            # Mostrar progreso
            print(f"Fitness - Mejor: {estadisticas['mejor']:.4f}, "
                  f"Promedio: {estadisticas['promedio']:.4f}, "
                  f"Desviación: {estadisticas['desviacion']:.4f}")

            # Callback de progreso para la interfaz web
            if callback_progreso:
                progreso = {
                    'generacion': self.generacion_actual,
                    'estadisticas': estadisticas,
                    'mejor_individuo': self.mejor_individuo,
                    'tiempo_transcurrido': time.time() - self.tiempo_inicio
                }
                callback_progreso(progreso)

            # Verificar criterios de parada
            if self._verificar_criterios_parada(estadisticas,
                                                mejor_fitness_anterior,
                                                generaciones_sin_mejora):
                break

            # Actualizar contador de mejora
            if estadisticas['mejor'] > mejor_fitness_anterior + 0.001:  # Mejora mínima
                generaciones_sin_mejora = 0
                mejor_fitness_anterior = estadisticas['mejor']
            else:
                generaciones_sin_mejora += 1

        # Resultados finales
        tiempo_total = time.time() - self.tiempo_inicio
        resultado = self._generar_resultado_final(tiempo_total)

        print(f"\n=== ALGORITMO COMPLETADO ===")
        print(f"Tiempo total: {tiempo_total:.2f} segundos")
        print(f"Generaciones: {self.generacion_actual}")
        print(f"Mejor fitness: {self.mejor_individuo.fitness:.4f}")

        return resultado

    def _verificar_criterios_parada(self, estadisticas, mejor_anterior, sin_mejora):
        """
        Verifica si se debe parar el algoritmo.

        Args:
            estadisticas: Estadísticas actuales
            mejor_anterior: Mejor fitness anterior
            sin_mejora: Generaciones sin mejora

        Returns:
            bool: True si se debe parar
        """
        config_ag = self.config.algoritmo_genetico

        # Criterio 1: Convergencia (sin mejora por muchas generaciones)
        if sin_mejora >= config_ag.convergencia_generaciones:
            print(f"Parada por convergencia: {sin_mejora} generaciones sin mejora")
            return True

        # Criterio 2: Fitness objetivo alcanzado
        if (config_ag.fitness_objetivo is not None and
                estadisticas['mejor'] >= config_ag.fitness_objetivo):
            print(f"Parada por fitness objetivo alcanzado: {estadisticas['mejor']:.4f}")
            return True

        # Criterio 3: Tiempo máximo
        if (config_ag.tiempo_maximo is not None and
                time.time() - self.tiempo_inicio >= config_ag.tiempo_maximo):
            print(f"Parada por tiempo máximo alcanzado")
            return True

        # Criterio 4: Diversidad muy baja (población convergió)
        if estadisticas['desviacion'] < 0.001:
            print("Parada por baja diversidad en la población")
            return True

        return False

    def _generar_resultado_final(self, tiempo_total):
        """
        Genera el resultado final del algoritmo.

        Args:
            tiempo_total: Tiempo total de ejecución

        Returns:
            dict: Resultado completo
        """
        return {
            'exito': True,
            'mejor_individuo': self.mejor_individuo,
            'mejor_fitness': self.mejor_individuo.fitness,
            'generaciones_ejecutadas': self.generacion_actual,
            'tiempo_total': tiempo_total,
            'estadisticas_finales': self.historial_fitness[-1] if self.historial_fitness else None,
            'historial_fitness': self.historial_fitness,
            'poblacion_final': self.individuos.copy(),
            'configuracion_utilizada': self.config.exportar_a_json()
        }

    def obtener_mejores_individuos(self, cantidad=10):
        """
        Obtiene los mejores individuos de la población actual.

        Args:
            cantidad: Número de individuos a retornar

        Returns:
            list: Los mejores individuos ordenados
        """
        poblacion_ordenada = sorted(
            self.individuos,
            key=lambda x: x.fitness if x.fitness is not None else 0,
            reverse=True
        )

        return poblacion_ordenada[:cantidad]

    def exportar_poblacion(self, archivo):
        """
        Exporta la población actual a un archivo.

        Args:
            archivo: Ruta del archivo donde guardar
        """
        import json

        datos_poblacion = {
            'generacion': self.generacion_actual,
            'mejor_fitness': self.mejor_individuo.fitness if self.mejor_individuo else None,
            'individuos': [
                {
                    'vector': ind.vector.tolist(),
                    'fitness': ind.fitness
                }
                for ind in self.individuos
            ],
            'historial_fitness': self.historial_fitness
        }

        with open(archivo, 'w') as f:
            json.dump(datos_poblacion, f, indent=2)

        print(f"Población exportada a: {archivo}")

    def cargar_poblacion(self, archivo):
        """
        Carga una población desde un archivo.

        Args:
            archivo: Ruta del archivo a cargar
        """
        import json

        with open(archivo, 'r') as f:
            datos = json.load(f)

        self.generacion_actual = datos['generacion']
        self.historial_fitness = datos['historial_fitness']

        # Recrear individuos
        self.individuos = []
        for datos_ind in datos['individuos']:
            individuo = Individuo(datos_ind['vector'])
            individuo.fitness = datos_ind['fitness']
            self.individuos.append(individuo)

        # Actualizar mejor individuo
        self._actualizar_mejor_individuo()

        print(f"Población cargada desde: {archivo}")
        print(f"Generación: {self.generacion_actual}, Individuos: {len(self.individuos)}")


def ejecutar_optimizacion(configuracion, callback_progreso=None):
    """
    Función de conveniencia para ejecutar la optimización completa.

    Args:
        configuracion: Configuración del sistema
        callback_progreso: Función de callback para progreso

    Returns:
        dict: Resultado de la optimización
    """
    # Validar configuración
    es_valida, errores = configuracion.validar_configuracion()
    if not es_valida:
        return {
            'exito': False,
            'errores': errores
        }

    # Crear y ejecutar población
    poblacion = Poblacion(configuracion)
    resultado = poblacion.ejecutar_algoritmo(callback_progreso)

    return resultado