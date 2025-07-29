"""
Configuración del sistema RANCHERSPACE-GA.
Maneja tanto los datos configurables por el usuario como los parámetros del AG.
SISTEMA SIMPLIFICADO - 2 OBJETIVOS + PRESUPUESTO INTELIGENTE
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

        # PRESUPUESTO INTELIGENTE - NUEVO SISTEMA
        self.presupuesto_usuario = 50000.0  # Lo que ingresa el usuario
        self.presupuesto_minimo_calculado = 0.0  # Se calcula automáticamente (estimado + 10%)
        self.presupuesto_efectivo = 0.0  # El que realmente se usa en el AG
        self.factor_seguridad_presupuesto = 1.10  # 10% adicional sobre el estimado

        # PRIORIDADES SIMPLIFICADAS - SOLO 2 OBJETIVOS
        self.pesos_objetivos = {
            'aprovechamiento_terreno': 0.6,  # 60% - Maximizar tamaño de corrales
            'eficiencia_manejo': 0.4,        # 40% - Maximizar espacios entre corrales
        }

    def calcular_presupuesto_inteligente(self, costo_estimado):
        """
        Calcula el presupuesto efectivo basado en el estimado y lo ingresado por el usuario.

        Args:
            costo_estimado: Costo estimado inicial de la construcción

        Returns:
            dict: Información completa del presupuesto
        """
        # Calcular presupuesto mínimo recomendado (estimado + 10%)
        self.presupuesto_minimo_calculado = costo_estimado * self.factor_seguridad_presupuesto

        # El presupuesto efectivo es el mayor entre el mínimo calculado y lo que ingresó el usuario
        self.presupuesto_efectivo = max(self.presupuesto_minimo_calculado, self.presupuesto_usuario)

        return {
            'presupuesto_usuario': self.presupuesto_usuario,
            'costo_estimado': costo_estimado,
            'presupuesto_minimo_recomendado': self.presupuesto_minimo_calculado,
            'presupuesto_efectivo': self.presupuesto_efectivo,
            'es_suficiente': self.presupuesto_usuario >= self.presupuesto_minimo_calculado,
            'diferencia': self.presupuesto_efectivo - self.presupuesto_usuario,
            'mensaje_recomendacion': self._generar_mensaje_presupuesto()
        }

    def _generar_mensaje_presupuesto(self):
        """
        Genera mensaje de recomendación sobre el presupuesto.
        """
        if self.presupuesto_usuario >= self.presupuesto_minimo_calculado:
            return f"✓ Presupuesto suficiente. Límite efectivo: ${self.presupuesto_efectivo:,.0f}"
        else:
            diferencia = self.presupuesto_minimo_calculado - self.presupuesto_usuario
            return (f"⚠️ Se recomienda aumentar el presupuesto en ${diferencia:,.0f} "
                   f"(mínimo recomendado: ${self.presupuesto_minimo_calculado:,.0f})")

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

        # Actualizar presupuesto del usuario
        if 'presupuesto' in datos_web:
            self.rancho.presupuesto_usuario = float(datos_web['presupuesto'])

        # ACTUALIZAR PESOS DE OBJETIVOS - SOLO 2 OBJETIVOS
        if 'objetivos' in datos_web:
            pesos_raw = datos_web['objetivos']

            # Solo procesar los objetivos que existen en el sistema simplificado
            objetivos_validos = {}
            if 'aprovechamiento_terreno' in pesos_raw:
                objetivos_validos['aprovechamiento_terreno'] = pesos_raw['aprovechamiento_terreno']
            if 'eficiencia_manejo' in pesos_raw:
                objetivos_validos['eficiencia_manejo'] = pesos_raw['eficiencia_manejo']

            # Normalizar los pesos para que sumen 1.0
            suma_pesos = sum(objetivos_validos.values())
            if suma_pesos > 0:
                for objetivo, peso in objetivos_validos.items():
                    self.rancho.pesos_objetivos[objetivo] = peso / suma_pesos
            else:
                # Si todos son 0, usar pesos por defecto
                self.rancho.pesos_objetivos = {
                    'aprovechamiento_terreno': 0.6,
                    'eficiencia_manejo': 0.4
                }

        # Actualizar parámetros del AG
        if 'algoritmo' in datos_web:
            ag_datos = datos_web['algoritmo']
            self.algoritmo_genetico.tamano_poblacion = int(ag_datos.get('poblacion', 100))
            self.algoritmo_genetico.numero_generaciones = int(ag_datos.get('generaciones', 500))
            self.algoritmo_genetico.probabilidad_mutacion = float(ag_datos.get('mutacion', 0.1))

    def calcular_y_ajustar_presupuesto(self, costo_estimado):
        """
        Calcula el presupuesto inteligente y ajusta la configuración.

        Args:
            costo_estimado: Costo estimado inicial

        Returns:
            dict: Información del presupuesto calculado
        """
        return self.rancho.calcular_presupuesto_inteligente(costo_estimado)

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
        Valida que la configuración sea coherente con el sistema simplificado.
        """
        errores = []

        # Validar terreno
        if self.rancho.ancho_terreno <= 0 or self.rancho.largo_terreno <= 0:
            errores.append("Las dimensiones del terreno deben ser positivas")

        # Validar espacios de circulación
        if self.rancho.espacio_circulacion < 1.0:
            errores.append("El espacio de circulación debe ser de al menos 1.0 metro")

        # Validar animales
        total_animales = sum(self.rancho.cantidad_animales.values())
        if total_animales == 0:
            errores.append("Debe haber al menos un animal configurado")

        # Validar presupuesto del usuario
        if self.rancho.presupuesto_usuario <= 0:
            errores.append("El presupuesto debe ser positivo")

        # NUEVA VALIDACIÓN: Solo verificar que al menos un peso sea > 0
        suma_pesos = sum(self.rancho.pesos_objetivos.values())
        if suma_pesos <= 0:
            errores.append("Al menos un objetivo debe tener peso mayor que 0")

        # QUITAR COMPLETAMENTE la validación de que sume 1.0 (100%)
        # El sistema normaliza automáticamente en actualizar_desde_web()

        # Verificar que solo existan los 2 objetivos permitidos
        objetivos_permitidos = {'aprovechamiento_terreno', 'eficiencia_manejo'}
        objetivos_actuales = set(self.rancho.pesos_objetivos.keys())
        if not objetivos_actuales.issubset(objetivos_permitidos):
            errores.append("Solo se permiten los objetivos: aprovechamiento_terreno y eficiencia_manejo")

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
                'presupuesto': {
                    'usuario': self.rancho.presupuesto_usuario,
                    'minimo_calculado': self.rancho.presupuesto_minimo_calculado,
                    'efectivo': self.rancho.presupuesto_efectivo
                },
                'objetivos': self.rancho.pesos_objetivos  # Solo 2 objetivos
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