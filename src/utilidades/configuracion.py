"""
Configuración del sistema RANCHERSPACE-GA.
Maneja tanto los datos configurables por el usuario como los parámetros del AG.
"""

class ConfiguracionRancho:
    """
    Configuración específica de un rancho.
    Contiene todos los datos que el usuario puede modificar.
    """

    def __init__(self):
        # TERRENO - Configurable por usuario
        self.ancho_terreno = 40.0  # metros
        self.largo_terreno = 30.0  # metros

        # ESPACIOS DE CIRCULACIÓN - Configurable por usuario
        self.espacio_circulacion = 2.0  # metros mínimos entre corrales

        # ANIMALES - Configurable por usuario
        self.cantidad_animales = {
            'gallinas': 50,
            'cerdos': 8,
            'vacas': 3,
            'cabras': 15
        }

        # MATERIALES - Se usan los materiales por defecto del sistema
        # Materiales por defecto para cada especie (se puede cambiar desde web)
        self.material_por_especie = {
            'gallinas': 'malla_gallinera_estandar',
            'cerdos': 'cerca_metal_soldada',
            'vacas': 'cerca_madera_roble',
            'cabras': 'cerca_alambre_reforzada'
        }

        # PRESUPUESTO - Configurable por usuario
        self.presupuesto_maximo = 50000.0  # pesos mexicanos

        # PRIORIDADES DE OPTIMIZACIÓN - Configurable por usuario
        self.pesos_objetivos = {
            'espacio_extra': 0.3,      # Maximizar espacio por corral
            'costo_construccion': 0.25, # Minimizar costos
            'cantidad_materiales': 0.2, # Minimizar materiales
            'eficiencia_manejo': 0.15,  # Maximizar eficiencia
            'aprovechamiento_terreno': 0.1  # Optimizar terreno
        }

class ConfiguracionAlgoritmoGenetico:
    """
    Parámetros del Algoritmo Genético.
    El usuario puede modificar estos valores desde la interfaz web.
    """

    def __init__(self):
        # PARÁMETROS BÁSICOS DEL AG
        self.tamano_poblacion = 100      # Número de individuos
        self.numero_generaciones = 500   # Iteraciones máximas
        self.numero_elite = 10           # Individuos que pasan directamente

        # PARÁMETROS DE SELECCIÓN
        self.tamano_torneo = 5           # Individuos por torneo
        self.presion_seleccion = 0.8     # Intensidad de selección

        # PARÁMETROS DE CRUZA
        self.probabilidad_cruza = 0.9    # Probabilidad de cruza
        self.tipo_cruza = 'uniforme'     # 'uniforme' o 'bloques'

        # PARÁMETROS DE MUTACIÓN
        self.probabilidad_mutacion = 0.1  # Probabilidad por gen
        self.intensidad_mutacion = 0.1    # Intensidad inicial
        self.mutacion_adaptativa = True   # Si cambia la intensidad

        # CRITERIOS DE PARADA
        self.convergencia_generaciones = 50  # Generaciones sin mejora
        self.fitness_objetivo = None      # Fitness mínimo (opcional)
        self.tiempo_maximo = 300         # Segundos máximos (opcional)

class ConfiguracionSistema:
    """
    Configuración completa del sistema.
    Combina la configuración del rancho y del algoritmo genético.
    """

    def __init__(self):
        self.rancho = ConfiguracionRancho()
        self.algoritmo_genetico = ConfiguracionAlgoritmoGenetico()

    def actualizar_desde_web(self, datos_web):
        """
        Actualiza la configuración con datos de la interfaz web.

        Args:
            datos_web: Diccionario con los datos del formulario web
        """
        # Actualizar terreno
        if 'terreno' in datos_web:
            self.rancho.ancho_terreno = float(datos_web['terreno']['ancho'])
            self.rancho.largo_terreno = float(datos_web['terreno']['largo'])

        # Actualizar espacios de circulación
        if 'espacios' in datos_web and 'circulacion' in datos_web['espacios']:
            self.rancho.espacio_circulacion = float(datos_web['espacios']['circulacion'])

        # Actualizar animales
        if 'animales' in datos_web:
            for especie, cantidad in datos_web['animales'].items():
                self.rancho.cantidad_animales[especie] = int(cantidad)

        # Actualizar materiales seleccionados
        if 'materiales' in datos_web:
            for especie, material in datos_web['materiales'].items():
                self.rancho.material_por_especie[especie] = material

        # Actualizar presupuesto
        if 'presupuesto' in datos_web:
            self.rancho.presupuesto_maximo = float(datos_web['presupuesto'])

        # Actualizar pesos de objetivos
        if 'objetivos' in datos_web:
            # Normalizar los pesos automáticamente
            pesos_raw = datos_web['objetivos']
            suma_pesos = sum(pesos_raw.values())

            if suma_pesos > 0:
                # Normalizar para que sumen 1.0
                for objetivo, peso in pesos_raw.items():
                    self.rancho.pesos_objetivos[objetivo] = peso / suma_pesos
            else:
                # Si todos son 0, usar pesos iguales
                peso_igual = 1.0 / len(self.rancho.pesos_objetivos)
                for objetivo in self.rancho.pesos_objetivos:
                    self.rancho.pesos_objetivos[objetivo] = peso_igual

        # Actualizar parámetros del AG
        if 'algoritmo' in datos_web:
            ag_datos = datos_web['algoritmo']
            self.algoritmo_genetico.tamano_poblacion = int(ag_datos.get('poblacion', 100))
            self.algoritmo_genetico.numero_generaciones = int(ag_datos.get('generaciones', 500))
            self.algoritmo_genetico.probabilidad_mutacion = float(ag_datos.get('mutacion', 0.1))

    def obtener_info_material(self, especie):
        """
        Obtiene la información del material seleccionado para una especie.

        Args:
            especie: Nombre de la especie

        Returns:
            dict: Información del material (compatible con código existente)
        """
        try:
            from src.rancho.especies import obtener_info_material as obtener_material

            material_id = self.rancho.material_por_especie[especie]
            material_info = obtener_material(material_id)

            # Convertir a formato compatible
            return {
                'costo_por_metro': material_info.costo_por_metro,
                'nombre': material_info.nombre,
                'durabilidad': material_info.durabilidad
            }
        except Exception as e:
            # Fallback con datos por defecto
            return {
                'costo_por_metro': 85.0,
                'nombre': f'Material para {especie}',
                'durabilidad': 'media'
            }

    def validar_configuracion(self):
        """
        Valida que la configuración sea coherente.

        Returns:
            tuple: (es_valida, lista_errores)
        """
        errores = []

        # Validar terreno
        if self.rancho.ancho_terreno <= 0 or self.rancho.largo_terreno <= 0:
            errores.append("Las dimensiones del terreno deben ser positivas")

        # Validar espacios de circulación
        if self.rancho.espacio_circulacion < 1.0:
            errores.append("El espacio de circulación debe ser de al menos 1.0 metro")
        elif self.rancho.espacio_circulacion > 5.0:
            errores.append("El espacio de circulación no debería exceder 5.0 metros")

        # Validar animales
        for especie, cantidad in self.rancho.cantidad_animales.items():
            if cantidad < 0:
                errores.append(f"La cantidad de {especie} no puede ser negativa")

        # Validar que haya al menos un animal
        total_animales = sum(self.rancho.cantidad_animales.values())
        if total_animales == 0:
            errores.append("Debe haber al menos un animal configurado")

        # Validar presupuesto
        if self.rancho.presupuesto_maximo <= 0:
            errores.append("El presupuesto debe ser positivo")

        # Validar pesos de objetivos (solo que sean positivos)
        for objetivo, peso in self.rancho.pesos_objetivos.items():
            if peso < 0:
                errores.append(f"El peso de {objetivo} no puede ser negativo")

        # Validar que al menos un peso sea mayor que 0
        suma_pesos = sum(self.rancho.pesos_objetivos.values())
        if suma_pesos <= 0:
            errores.append("Al menos un objetivo debe tener peso mayor que 0")

        # Validar parámetros del AG
        if self.algoritmo_genetico.tamano_poblacion < 10:
            errores.append("El tamaño de población debe ser al menos 10")

        if self.algoritmo_genetico.numero_generaciones < 1:
            errores.append("El número de generaciones debe ser al menos 1")

        # Validar que el terreno sea suficiente considerando espacios de circulación
        if total_animales > 0:
            area_terreno = self.rancho.ancho_terreno * self.rancho.largo_terreno

            # Área mínima para animales
            area_minima_animales = (
                self.rancho.cantidad_animales.get('gallinas', 0) * 0.5 +
                self.rancho.cantidad_animales.get('cerdos', 0) * 2.5 +
                self.rancho.cantidad_animales.get('vacas', 0) * 15 +
                self.rancho.cantidad_animales.get('cabras', 0) * 3
            )

            # Agregar estimación de espacios de circulación (40% adicional con espacios)
            area_con_circulacion = area_minima_animales * 1.4

            if area_con_circulacion > area_terreno * 0.85:
                errores.append(f"El terreno es muy pequeño considerando los espacios de circulación requeridos. "
                             f"Se necesitan aproximadamente {area_con_circulacion:.0f} m² "
                             f"pero solo hay {area_terreno:.0f} m² disponibles.")

        return len(errores) == 0, errores

    def exportar_a_json(self):
        """
        Exporta la configuración a formato JSON.

        Returns:
            dict: Configuración en formato serializable
        """
        return {
            'rancho': {
                'terreno': {
                    'ancho': self.rancho.ancho_terreno,
                    'largo': self.rancho.largo_terreno
                },
                'espacios': {
                    'circulacion': self.rancho.espacio_circulacion
                },
                'animales': self.rancho.cantidad_animales,
                'materiales': self.rancho.material_por_especie,
                'presupuesto': self.rancho.presupuesto_maximo,
                'objetivos': self.rancho.pesos_objetivos
            },
            'algoritmo': {
                'poblacion': self.algoritmo_genetico.tamano_poblacion,
                'generaciones': self.algoritmo_genetico.numero_generaciones,
                'mutacion': self.algoritmo_genetico.probabilidad_mutacion,
                'cruza': self.algoritmo_genetico.probabilidad_cruza
            }
        }

# Instancia global de configuración
configuracion_sistema = ConfiguracionSistema()