"""
Aplicación web Flask para RANCHERSPACE-GA
Interfaz web para configurar y ejecutar optimizaciones de ranchos.
"""

import sys
import os
import json
import threading
import time
from flask import Flask, render_template, request, jsonify, session

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utilidades.configuracion import ConfiguracionSistema
from src.algoritmo_genetico.poblacion import ejecutar_optimizacion
from src.rancho.especies import obtener_especies_disponibles, obtener_info_especie

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
            'mensaje': 'Esperando configuración...'
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

@app.route('/api/iniciar_optimizacion', methods=['POST'])
def iniciar_optimizacion():
    """API para iniciar la optimización."""
    global ejecutando_optimizacion

    if ejecutando_optimizacion:
        return jsonify({'error': 'Ya hay una optimización en progreso'}), 400

    try:
        # Obtener configuración del request
        datos_config = request.json

        # Crear configuración del sistema
        config = ConfiguracionSistema()
        config.actualizar_desde_web(datos_config)

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
                print("[DEBUG] Iniciando optimización en hilo separado...")
                resultado = ejecutar_optimizacion(config, progreso_optimizacion.callback_progreso)
                print(f"[DEBUG] Optimización completada. Exito: {resultado.get('exito', False)}")
                print(f"[DEBUG] Fitness: {resultado.get('mejor_fitness', 'N/A')}")

                # Agregar datos físicos del rancho usando el evaluador de fitness
                if resultado.get('exito') and 'mejor_individuo' in resultado:
                    from src.algoritmo_genetico.fitness import EvaluadorFitness
                    evaluador = EvaluadorFitness(config)
                    rancho_fisico = evaluador._decodificar_individuo(resultado['mejor_individuo'])
                    resultado['rancho_fisico'] = rancho_fisico
                    print("[DEBUG] Datos físicos del rancho agregados")

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

        return jsonify({'mensaje': 'Optimización iniciada correctamente'})

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

                # Crear estructura serializable
                individuo_serializable = {
                    'vector': mejor_individuo.vector.tolist() if hasattr(mejor_individuo.vector, 'tolist') else list(mejor_individuo.vector),
                    'fitness': float(mejor_individuo.fitness) if mejor_individuo.fitness else 0.0,
                    'corrales': mejor_individuo.obtener_datos_corrales(),
                    'comederos': mejor_individuo.obtener_datos_comederos(),
                    'bebederos': mejor_individuo.obtener_datos_bebederos(),
                    'infraestructura': mejor_individuo.obtener_datos_infraestructura()
                }

                resultado['mejor_individuo'] = individuo_serializable

            # Limpiar otros objetos no serializables
            if 'poblacion_final' in resultado:
                del resultado['poblacion_final']

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

@app.route('/api/materiales/<especie>')
def obtener_materiales_especie(especie):
    """API para obtener materiales compatibles con una especie específica."""
    try:
        from src.rancho.especies import obtener_materiales_para_especie
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
        from src.rancho.especies import MATERIALES_DISPONIBLES

        # Convertir a formato compatible
        materiales_json = {}
        for material_id, material_info in MATERIALES_DISPONIBLES.items():
            materiales_json[material_id] = {
                'nombre': material_info.nombre,
                'costo_por_metro': material_info.costo_por_metro,
                'durabilidad': material_info.durabilidad,
                'especies_recomendadas': material_info.especies_compatibles,
                'descripcion': material_info.descripcion
            }

        return jsonify(materiales_json)
    except Exception as e:
        print(f"Error obteniendo materiales: {e}")
        return jsonify({})

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

        from src.rancho.especies import calcular_area_minima_corral

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
        from src.rancho.especies import calcular_area_minima_corral
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
    print("=== RANCHERSPACE-GA - Interfaz Web ===")
    print("Iniciando servidor Flask...")
    print("Accede a: http://localhost:8080")
    print("Para detener: Ctrl+C")
    print("=" * 40)

    app.run(debug=True, host='0.0.0.0', port=8080)