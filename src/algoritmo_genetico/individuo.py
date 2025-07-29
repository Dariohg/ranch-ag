import numpy as np
import random


class Individuo:

    def __init__(self, vector=None):
        """
        Inicializa un individuo.

        Args:
            vector: Vector de 52 números. Si es None, se genera aleatoriamente.
        """
        if vector is None:
            self.vector = self._generar_vector_aleatorio()
        else:
            if len(vector) != 52:
                raise ValueError("El vector debe tener exactamente 52 elementos")
            self.vector = np.array(vector)

        self.fitness = None  # Se calcula después

    def _generar_vector_aleatorio(self):
        """
        Genera un vector aleatorio de 52 números entre 0 y 1.
        Después se mapean a los rangos específicos de cada parámetro.
        """
        return np.random.random(52)

    def obtener_datos_corrales(self):
        """
        Extrae los datos de los corrales del vector.
        Posiciones 0-31: 8 parámetros × 4 especies

        Returns:
            dict: Datos organizados por especie
        """
        especies = ['gallinas', 'cerdos', 'vacas', 'cabras']
        datos_corrales = {}

        for i, especie in enumerate(especies):
            inicio = i * 8
            fin = inicio + 8

            datos_corrales[especie] = {
                'posicion_x': self.vector[inicio],
                'posicion_y': self.vector[inicio + 1],
                'factor_agrandamiento': self.vector[inicio + 2],
                'proporcion': self.vector[inicio + 3],
                'orientacion': self.vector[inicio + 4],
                'densidad': self.vector[inicio + 5],
                'acceso': self.vector[inicio + 6],
                'ventilacion': self.vector[inicio + 7]
            }

        return datos_corrales

    def obtener_datos_comederos(self):
        """
        Extrae los datos de comederos del vector.
        Posiciones 32-39: 2 parámetros × 4 especies

        Returns:
            dict: Posiciones de comederos por especie
        """
        especies = ['gallinas', 'cerdos', 'vacas', 'cabras']
        datos_comederos = {}

        for i, especie in enumerate(especies):
            inicio = 32 + (i * 2)

            datos_comederos[especie] = {
                'posicion_x_relativa': self.vector[inicio],
                'posicion_y_relativa': self.vector[inicio + 1]
            }

        return datos_comederos

    def obtener_datos_bebederos(self):
        """
        Extrae los datos de bebederos del vector.
        Posiciones 40-47: 2 parámetros × 4 especies

        Returns:
            dict: Posiciones de bebederos por especie
        """
        especies = ['gallinas', 'cerdos', 'vacas', 'cabras']
        datos_bebederos = {}

        for i, especie in enumerate(especies):
            inicio = 40 + (i * 2)

            datos_bebederos[especie] = {
                'posicion_x_relativa': self.vector[inicio],
                'posicion_y_relativa': self.vector[inicio + 1]
            }

        return datos_bebederos

    def obtener_datos_infraestructura(self):
        """
        Extrae los datos de infraestructura general del vector.
        Posiciones 48-51: 4 parámetros

        Returns:
            dict: Datos de infraestructura general
        """
        return {
            'ancho_pasillos': self.vector[48],
            'configuracion': self.vector[49],
            'acceso_principal': self.vector[50],
            'conectividad': self.vector[51]
        }

    def clonar(self):
        """
        Crea una copia exacta del individuo.

        Returns:
            Individuo: Nueva instancia con el mismo vector
        """
        nuevo_individuo = Individuo(self.vector.copy())
        nuevo_individuo.fitness = self.fitness
        return nuevo_individuo

    def mutar(self, tasa_mutacion=0.1, intensidad=0.1):
        """
        Aplica mutación gaussiana al vector.

        Args:
            tasa_mutacion: Probabilidad de que cada gen mute
            intensidad: Intensidad de la mutación
        """
        for i in range(len(self.vector)):
            if random.random() < tasa_mutacion:
                # Mutación gaussiana
                cambio = np.random.normal(0, intensidad)
                self.vector[i] += cambio

                # Mantener en rango [0, 1]
                self.vector[i] = np.clip(self.vector[i], 0, 1)

        # Invalidar fitness después de mutación
        self.fitness = None

    def __str__(self):
        """
        Representación en texto del individuo.
        """
        return f"Individuo(fitness={self.fitness}, vector={self.vector[:5]}...)"

    def __repr__(self):
        return self.__str__()