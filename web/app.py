"""
Aplicación web Flask para RANCHERSPACE-GA
Interfaz web para configurar y ejecutar optimizaciones de ranchos.
SISTEMA SIMPLIFICADO - 2 OBJETIVOS + PRESUPUESTO INTELIGENTE
"""

import sys
import os
import json
import threading
import time
import math
from flask import Flask, render_template, request, jsonify, session

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utilidades.configuracion import ConfiguracionSistema
from src.algoritmo_genetico.poblacion import ejecutar_optimizacion
from src.rancho.especies import (obtener_especies_disponibles, obtener_info_especie,
                                obtener_materiales_para_especie, obtener_todos_los_materiales,
                                obtener_info_material, calcular_costo_cerca_corral,
                                calcular_area_minima_corral)

app = Flask(__name__)
app.secret_key = 'rancherspace_ga_secret_key_2025'

# Variables globales para el progreso
progreso_actual = {}
ejecutando_optimizacion = False

class ProgressoOptimizacion:
    """Maneja el progreso de la optimización en tiempo real."""

    def __init__(self):
        self.datos = {
            'estado': 'esperando',  # esperando, ejecutando, completado, error
            'generacion_actual': 0,
            'total_generaciones': 0,
            'mejor_fitness': 0,
            'fitness_promedio': 0,
            'tiempo_transcurrido': 0,
            'mensaje': 'Esperando configuración...',
            # NUEVO: Métricas específicas de objetivos
            'metricas_objetivos': {
                'aprovechamiento_terreno': 0,
                'eficiencia_manejo': 0
            },
            'dentro_presupuesto': True
        }
        self.resultado_final = None

    def callback_progreso(self, progreso):
        """Callback que recibe el progreso del algoritmo genético."""
        self.datos.update({
            'estado': 'ejecutando',
            'generacion_actual': progreso['generacion'],
            'mejor_fitness': progreso['estadisticas']['mejor'],
            'fitness_promedio': progreso['estadisticas']['promedio'],
            'tiempo_transcurrido': progreso['tiempo_transcurrido'],
            'mensaje': f'Generación {progreso["generacion"]} - Fitness: {progreso["estadisticas"]["mejor"]:.4f}'
        })

        # NUEVO: Extraer métricas de objetivos específicos si están disponibles
        if 'mejor_individuo' in progreso:
            try:
                # Estimación de métricas basadas en el fitness
                fitness = progreso['estadisticas']['mejor']

                # Estimación de métricas (en implementación real calcularías desde el individuo)
                self.datos['metricas_objetivos'] = {
                    'aprovechamiento_terreno': min(fitness * 1.2, 1.0),  # Estimación
                    'eficiencia_manejo': min(fitness * 0.8, 1.0)        # Estimación
                }
            except Exception as e:
                print(f"[DEBUG] Error calculando métricas de objetivos: {e}")

    def iniciar(self, total_generaciones):
        """Inicia el seguimiento del progreso."""
        self.datos.update({
            'estado': 'ejecutando',
            'generacion_actual': 0,
            'total_generaciones': total_generaciones,
            'mejor_fitness': 0,
            'fitness_promedio': 0,
            'tiempo_transcurrido': 0,
            'mensaje': 'Iniciando optimización...'
        })

    def completar(self, resultado):
        """Marca la optimización como completada."""
        self.resultado_final = resultado
        self.datos.update({
            'estado': 'completado' if resultado['exito'] else 'error',
            'mensaje': 'Optimización completada' if resultado['exito'] else 'Error en optimización'
        })

    def obtener_datos(self):
        """Obtiene los datos actuales del progreso."""
        return self.datos.copy()

# Instancia global del progreso
progreso_optimizacion = ProgressoOptimizacion()

@app.route('/')
def index():
    """Página principal - Configuración."""
    especies = obtener_especies_disponibles()
    config = ConfiguracionSistema()

    # Información de especies para el frontend
    especies_info = {}
    for especie in especies:
        info = obtener_info_especie(especie)
        especies_info[especie] = {
            'nombre': info.nombre,
            'area_minima': info.area_minima_por_animal,
            'distancia_minima': info.distancia_minima_otras_especies
        }

    return render_template('index.html',
                         especies=especies,
                         especies_info=especies_info,
                         configuracion_default=config.exportar_a_json())

@app.route('/resultados')
def resultados():
    """Página de resultados y visualización."""
    return render_template('resultados.html')

def calcular_perimetro_estimado_inicial(area):
    """
    Calcula el perímetro estimado inicial con factor de realismo.
    Usa forma cuadrada + 10% por imperfecciones prácticas.
    """
    lado_cuadrado = math.sqrt(area)
    perimetro_cuadrado = 4 * lado_cuadrado
    factor_realismo = 1.10  # 10% adicional por imperfecciones
    return perimetro_cuadrado * factor_realismo

@app.route('/api/calcular_presupuesto_inteligente', methods=['POST'])
def calcular_presupuesto_inteligente():
    """API para calcular presupuesto inteligente (estimado + 10%)."""
    try:
        datos = request.json
        animales = datos.get('animales', {})
        materiales_seleccionados = datos.get('materiales', {})
        presupuesto_usuario = float(datos.get('presupuesto_usuario', 50000))

        # Calcular costo estimado
        costo_estimado = 0

        for especie, cantidad in animales.items():
            if cantidad > 0 and especie in materiales_seleccionados:
                # Calcular área mínima
                area_minima = calcular_area_minima_corral(especie, cantidad)

                # Calcular perímetro usando método estimado inicial
                perimetro_estimado = calcular_perimetro_estimado_inicial(area_minima)

                # Obtener costo del material seleccionado
                material_id = materiales_seleccionados[especie]
                try:
                    material_info = obtener_info_material(material_id)
                    costo_por_metro = material_info.costo_por_metro
                except ValueError:
                    costo_por_metro = 75  # Fallback

                # Calcular costo para esta especie
                costo_especie = perimetro_estimado * costo_por_metro
                costo_estimado += costo_especie

        # Agregar costos de infraestructura (estimado 30% del total)
        costo_infraestructura = costo_estimado * 0.3
        costo_estimado_total = costo_estimado + costo_infraestructura

        # PRESUPUESTO INTELIGENTE: Estimado + 10%
        factor_seguridad = 1.10
        presupuesto_minimo_recomendado = costo_estimado_total * factor_seguridad

        # El presupuesto efectivo es el mayor entre el mínimo y lo que ingresó el usuario
        presupuesto_efectivo = max(presupuesto_minimo_recomendado, presupuesto_usuario)

        # Determinar si el presupuesto del usuario es suficiente
        es_suficiente = presupuesto_usuario >= presupuesto_minimo_recomendado
        diferencia = presupuesto_efectivo - presupuesto_usuario

        return jsonify({
            'costo_estimado': costo_estimado_total,
            'presupuesto_usuario': presupuesto_usuario,
            'presupuesto_minimo_recomendado': presupuesto_minimo_recomendado,
            'presupuesto_efectivo': presupuesto_efectivo,
            'es_suficiente': es_suficiente,
            'diferencia': diferencia,
            'factor_seguridad': factor_seguridad,
            'mensaje': 'Presupuesto calculado correctamente'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/iniciar_optimizacion', methods=['POST'])
def iniciar_optimizacion():
    """API para iniciar la optimización con presupuesto inteligente."""
    global ejecutando_optimizacion

    if ejecutando_optimizacion:
        return jsonify({'error': 'Ya hay una optimización en progreso'}), 400

    try:
        # Obtener configuración del request
        datos_config = request.json

        # Crear configuración del sistema
        config = ConfiguracionSistema()
        config.actualizar_desde_web(datos_config)

        # NUEVO: Calcular presupuesto inteligente ANTES de validar
        # Calcular costo estimado
        costo_estimado = 0
        for especie, cantidad in config.rancho.cantidad_animales.items():
            if cantidad > 0:
                area_minima = calcular_area_minima_corral(especie, cantidad)
                perimetro_estimado = calcular_perimetro_estimado_inicial(area_minima)

                try:
                    material_info = obtener_info_material(config.rancho.material_por_especie[especie])
                    costo_por_metro = material_info.costo_por_metro
                except:
                    costo_por_metro = 75

                costo_estimado += perimetro_estimado * costo_por_metro

        # Agregar infraestructura
        costo_estimado_total = costo_estimado * 1.3

        # Aplicar presupuesto inteligente
        info_presupuesto = config.calcular_y_ajustar_presupuesto(costo_estimado_total)
        print(f"[DEBUG] Presupuesto inteligente: {info_presupuesto}")

        # Validar configuración
        es_valida, errores = config.validar_configuracion()
        if not es_valida:
            return jsonify({'error': 'Configuración inválida', 'errores': errores}), 400

        # Iniciar progreso
        progreso_optimizacion.iniciar(config.algoritmo_genetico.numero_generaciones)
        ejecutando_optimizacion = True

        # Ejecutar optimización en hilo separado
        def ejecutar_en_hilo():
            global ejecutando_optimizacion
            try:
                print(f"[DEBUG] Iniciando optimización con presupuesto efectivo: ${config.rancho.presupuesto_efectivo:,.0f}")
                resultado = ejecutar_optimizacion(config, progreso_optimizacion.callback_progreso)
                print(f"[DEBUG] Optimización completada. Éxito: {resultado.get('exito', False)}")

                # Agregar datos físicos del rancho usando el evaluador de fitness
                if resultado.get('exito') and 'mejor_individuo' in resultado:
                    from src.algoritmo_genetico.fitness import EvaluadorFitness
                    evaluador = EvaluadorFitness(config)
                    rancho_fisico = evaluador._decodificar_individuo(resultado['mejor_individuo'])
                    resultado['rancho_fisico'] = rancho_fisico

                    # Calcular costo real final
                    costo_real = evaluador._calcular_costo_construccion(rancho_fisico)
                    resultado['costo_real_final'] = costo_real
                    resultado['dentro_presupuesto'] = costo_real <= config.rancho.presupuesto_efectivo

                    print(f"[DEBUG] Costo real final: ${costo_real:,.0f}")
                    print(f"[DEBUG] Dentro del presupuesto: {resultado['dentro_presupuesto']}")

                progreso_optimizacion.completar(resultado)
            except Exception as e:
                print(f"[ERROR] Error en optimización: {e}")
                import traceback
                traceback.print_exc()
                progreso_optimizacion.datos['estado'] = 'error'
                progreso_optimizacion.datos['mensaje'] = f'Error: {str(e)}'
            finally:
                ejecutando_optimizacion = False
                print("[DEBUG] Optimización finalizada")

        hilo = threading.Thread(target=ejecutar_en_hilo)
        hilo.daemon = True
        hilo.start()

        return jsonify({
            'mensaje': 'Optimización iniciada con presupuesto inteligente',
            'presupuesto_info': info_presupuesto
        })

    except Exception as e:
        ejecutando_optimizacion = False
        return jsonify({'error': f'Error al iniciar optimización: {str(e)}'}), 500

@app.route('/api/progreso')
def obtener_progreso():
    """API para obtener el progreso actual."""
    return jsonify(progreso_optimizacion.obtener_datos())


@app.route('/api/resultado')
def obtener_resultado():
    """API para obtener el resultado final."""
    try:
        if progreso_optimizacion.resultado_final:
            # Preparar resultado para enviar al frontend
            resultado = progreso_optimizacion.resultado_final.copy()

            if 'mejor_individuo' in resultado and resultado['mejor_individuo']:
                # Convertir el individuo a datos serializables
                mejor_individuo = resultado['mejor_individuo']

                # CORRECCIÓN: Convertir tipos de datos problemáticos
                individuo_serializable = {
                    'vector': mejor_individuo.vector.tolist() if hasattr(mejor_individuo.vector, 'tolist') else list(
                        mejor_individuo.vector),
                    'fitness': float(mejor_individuo.fitness) if mejor_individuo.fitness else 0.0,
                    'corrales': mejor_individuo.obtener_datos_corrales(),
                    'comederos': mejor_individuo.obtener_datos_comederos(),
                    'bebederos': mejor_individuo.obtener_datos_bebederos(),
                    'infraestructura': mejor_individuo.obtener_datos_infraestructura()
                }

                resultado['mejor_individuo'] = individuo_serializable

            # CORRECCIÓN CRÍTICA: Limpiar objetos no serializables y convertir tipos
            if 'poblacion_final' in resultado:
                del resultado['poblacion_final']

            # Convertir todos los valores booleanos y numpy a tipos nativos de Python
            resultado = convertir_a_json_serializable(resultado)

            print(f"[DEBUG] Enviando resultado: fitness={resultado.get('mejor_fitness', 'N/A')}")
            return jsonify(resultado)
        else:
            print("[DEBUG] No hay resultado_final disponible")
            return jsonify({'error': 'No hay resultado disponible'}), 404

    except Exception as e:
        print(f"[ERROR] Error obteniendo resultado: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error obteniendo resultado: {str(e)}'}), 500


def convertir_a_json_serializable(obj):
    """
    Convierte recursivamente objetos problemáticos a tipos serializables JSON.
    """
    import numpy as np

    if isinstance(obj, dict):
        return {k: convertir_a_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convertir_a_json_serializable(item) for item in obj]
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, bool):
        return obj  # Los bool nativos de Python son serializables
    else:
        return obj

@app.route('/api/materiales/<especie>')
def obtener_materiales_especie(especie):
    """API para obtener materiales compatibles con una especie específica."""
    try:
        materiales = obtener_materiales_para_especie(especie)

        # Convertir a formato JSON
        materiales_json = {}
        for material_id, material_info in materiales.items():
            materiales_json[material_id] = {
                'nombre': material_info.nombre,
                'costo_por_metro': material_info.costo_por_metro,
                'durabilidad': material_info.durabilidad,
                'descripcion': material_info.descripcion
            }

        return jsonify(materiales_json)
    except Exception as e:
        print(f"Error obteniendo materiales para {especie}: {e}")
        # Fallback con materiales por defecto
        return jsonify({
            f'material_{especie}': {
                'nombre': f'Material para {especie.capitalize()}',
                'costo_por_metro': 75,
                'durabilidad': 'media',
                'descripcion': f'Material estándar para {especie}'
            }
        })

@app.route('/api/materiales')
def obtener_materiales():
    """API para obtener información de materiales disponibles."""
    try:
        materiales = obtener_todos_los_materiales()

        # Convertir a formato compatible
        materiales_json = {}
        for material_id, material_info in materiales.items():
            materiales_json[material_id] = {
                'nombre': material_info.nombre,
                'costo_por_metro': material_info.costo_por_metro,
                'durabilidad': material_info.durabilidad,
                'especies_compatibles': material_info.especies_compatibles,
                'descripcion': material_info.descripcion
            }

        return jsonify(materiales_json)
    except Exception as e:
        print(f"Error obteniendo materiales: {e}")
        return jsonify({})

@app.route('/api/calcular_costos_estimados', methods=['POST'])
def calcular_costos_estimados():
    """API para calcular costos estimados basados en materiales seleccionados."""
    try:
        datos = request.json
        animales = datos.get('animales', {})
        materiales_seleccionados = datos.get('materiales', {})

        costos_por_especie = {}
        costo_total = 0

        for especie, cantidad in animales.items():
            if cantidad > 0 and especie in materiales_seleccionados:
                # Calcular área mínima
                area_minima = calcular_area_minima_corral(especie, cantidad)

                # Calcular perímetro usando método estimado inicial
                perimetro_estimado = calcular_perimetro_estimado_inicial(area_minima)

                # Obtener costo del material seleccionado
                material_id = materiales_seleccionados[especie]
                try:
                    material_info = obtener_info_material(material_id)
                    costo_por_metro = material_info.costo_por_metro
                    nombre_material = material_info.nombre
                except ValueError:
                    # Material no encontrado, usar costo por defecto
                    costo_por_metro = 75
                    nombre_material = f'Material para {especie}'

                # Calcular costo total para esta especie
                costo_especie = perimetro_estimado * costo_por_metro

                costos_por_especie[especie] = {
                    'cantidad_animales': cantidad,
                    'area_estimada': area_minima,
                    'perimetro_estimado': perimetro_estimado,
                    'material_nombre': nombre_material,
                    'costo_por_metro': costo_por_metro,
                    'costo_total': costo_especie
                }
                costo_total += costo_especie

        return jsonify({
            'costos_por_especie': costos_por_especie,
            'costo_total_estimado': costo_total
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def calcular_perimetro_optimizado_ag(area, factor_agrandamiento):
    """
    Calcula el perímetro después de optimización del AG.
    El AG usa áreas más grandes pero optimiza la forma.
    """
    area_optimizada = area * factor_agrandamiento
    lado_optimizado = math.sqrt(area_optimizada)
    return 4 * lado_optimizado

@app.route('/api/calcular_costos_resultado', methods=['POST'])
def calcular_costos_resultado():
    """API para calcular costos reales del resultado optimizado."""
    try:
        datos = request.json
        rancho_fisico = datos.get('rancho_fisico', {})
        materiales_seleccionados = datos.get('materiales_seleccionados', {})

        costos_por_especie = {}
        costo_total = 0

        for especie, corral in rancho_fisico.get('corrales', {}).items():
            if especie in materiales_seleccionados:
                try:
                    # Calcular perímetro real del corral optimizado
                    ancho = corral.get('ancho', 0)
                    alto = corral.get('alto', 0)
                    perimetro_real = 2 * (ancho + alto)

                    # Obtener información del material seleccionado
                    material_id = materiales_seleccionados[especie]
                    material_info = obtener_info_material(material_id)

                    # Calcular costo real
                    costo_especie = perimetro_real * material_info.costo_por_metro

                    costos_por_especie[especie] = {
                        'material_id': material_id,
                        'material_nombre': material_info.nombre,
                        'costo_por_metro': material_info.costo_por_metro,
                        'perimetro_metros': perimetro_real,
                        'ancho_corral': ancho,
                        'alto_corral': alto,
                        'area_corral': corral.get('area', 0),
                        'costo_total': costo_especie
                    }

                    costo_total += costo_especie

                except Exception as e:
                    print(f"Error calculando costo para {especie}: {e}")
                    # Usar valores estimados como fallback
                    area_estimada = corral.get('area', 25)  # Area por defecto
                    perimetro_estimado = calcular_perimetro_optimizado_ag(area_estimada, 1.4)

                    try:
                        material_info = obtener_info_material(materiales_seleccionados[especie])
                        costo_por_metro = material_info.costo_por_metro
                        nombre_material = material_info.nombre
                    except:
                        costo_por_metro = 75
                        nombre_material = f'Material para {especie}'

                    costo_especie = perimetro_estimado * costo_por_metro

                    costos_por_especie[especie] = {
                        'material_nombre': nombre_material,
                        'costo_por_metro': costo_por_metro,
                        'perimetro_metros': perimetro_estimado,
                        'costo_total': costo_especie,
                        'estimado': True,
                        'error': str(e)
                    }
                    costo_total += costo_especie

        return jsonify({
            'costos_por_especie': costos_por_especie,
            'costo_total': costo_total,
            'moneda': 'MXN'
        })

    except Exception as e:
        print(f"Error en calcular_costos_resultado: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/especies_info')
def obtener_especies_info():
    """API para obtener información detallada de especies."""
    especies = obtener_especies_disponibles()
    especies_info = {}

    for especie in especies:
        info = obtener_info_especie(especie)
        especies_info[especie] = {
            'nombre': info.nombre,
            'area_minima_por_animal': info.area_minima_por_animal,
            'distancia_minima_otras_especies': info.distancia_minima_otras_especies,
            'tipo_comedero': info.tipo_comedero,
            'tipo_bebedero': info.tipo_bebedero
        }

    return jsonify(especies_info)

@app.route('/api/calcular_areas', methods=['POST'])
def calcular_areas():
    """API para calcular áreas mínimas requeridas."""
    try:
        datos = request.json
        animales = datos.get('animales', {})

        areas = {}
        area_total_minima = 0

        for especie, cantidad in animales.items():
            if cantidad > 0:
                area = calcular_area_minima_corral(especie, cantidad)
                areas[especie] = {
                    'cantidad_animales': cantidad,
                    'area_minima': area,
                    'area_por_animal': obtener_info_especie(especie).area_minima_por_animal
                }
                area_total_minima += area

        return jsonify({
            'areas_por_especie': areas,
            'area_total_minima': area_total_minima
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/validar_terreno', methods=['POST'])
def validar_terreno():
    """API para validar si el terreno es suficiente."""
    try:
        datos = request.json
        ancho = float(datos.get('ancho', 0))
        largo = float(datos.get('largo', 0))
        animales = datos.get('animales', {})

        # Calcular área total del terreno
        area_terreno = ancho * largo

        # Calcular área mínima requerida
        area_minima_total = 0

        for especie, cantidad in animales.items():
            if cantidad > 0:
                area_minima_total += calcular_area_minima_corral(especie, cantidad)

        # Agregar espacio para pasillos e infraestructura (estimado 30%)
        area_con_infraestructura = area_minima_total * 1.3

        es_suficiente = area_terreno >= area_con_infraestructura
        porcentaje_uso = (area_con_infraestructura / area_terreno) * 100 if area_terreno > 0 else 0

        return jsonify({
            'es_suficiente': es_suficiente,
            'area_terreno': area_terreno,
            'area_minima_requerida': area_con_infraestructura,
            'porcentaje_uso': porcentaje_uso,
            'espacio_libre': max(0, area_terreno - area_con_infraestructura)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def pagina_no_encontrada(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def error_servidor(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    print("=== RANCHERSPACE-GA - Interfaz Web Simplificada ===")
    print("Iniciando servidor Flask...")
    print("Accede a: http://localhost:8080")
    print("Para detener: Ctrl+C")
    print("=" * 40)

    app.run(debug=True, host='0.0.0.0', port=8080)