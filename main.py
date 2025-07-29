"""
Archivo principal de RANCHERSPACE-GA
Punto de entrada para ejecutar el algoritmo genético.
"""

import sys
import os
import time

# Agregar el directorio actual al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utilidades.configuracion import ConfiguracionSistema
from src.algoritmo_genetico.poblacion import ejecutar_optimizacion
from src.rancho.especies import obtener_especies_disponibles

def mostrar_bienvenida():
    """Muestra mensaje de bienvenida."""
    print("=" * 60)
    print("         RANCHERSPACE-GA")
    print("  Sistema de Optimización de Ranchos Mixtos")
    print("         Algoritmo Genético")
    print("=" * 60)
    print()

def mostrar_configuracion_actual(config):
    """
    Muestra la configuración actual del sistema.

    Args:
        config: Configuración del sistema
    """
    print("CONFIGURACIÓN ACTUAL:")
    print("-" * 40)

    # Terreno
    print(f"Terreno: {config.rancho.ancho_terreno}m x {config.rancho.largo_terreno}m")
    print(f"Área total: {config.rancho.ancho_terreno * config.rancho.largo_terreno} m²")

    # Animales
    print("\nAnimales:")
    total_animales = 0
    for especie, cantidad in config.rancho.cantidad_animales.items():
        if cantidad > 0:
            print(f"  {especie.capitalize()}: {cantidad}")
            total_animales += cantidad
    print(f"  Total: {total_animales} animales")

    # Presupuesto
    print(f"\nPresupuesto máximo: ${config.rancho.presupuesto_maximo:,.2f}")

    # Algoritmo
    print(f"\nAlgoritmo Genético:")
    print(f"  Población: {config.algoritmo_genetico.tamano_poblacion}")
    print(f"  Generaciones: {config.algoritmo_genetico.numero_generaciones}")
    print(f"  Mutación: {config.algoritmo_genetico.probabilidad_mutacion}")

    print("-" * 40)

def configurar_terreno(config):
    """
    Permite al usuario configurar las dimensiones del terreno.

    Args:
        config: Configuración del sistema
    """
    print("\n=== CONFIGURACIÓN DEL TERRENO ===")

    try:
        ancho = float(input(f"Ancho del terreno (metros) [{config.rancho.ancho_terreno}]: ")
                     or config.rancho.ancho_terreno)
        largo = float(input(f"Largo del terreno (metros) [{config.rancho.largo_terreno}]: ")
                     or config.rancho.largo_terreno)

        if ancho > 0 and largo > 0:
            config.rancho.ancho_terreno = ancho
            config.rancho.largo_terreno = largo
            print(f"✓ Terreno configurado: {ancho}m x {largo}m")
        else:
            print("✗ Las dimensiones deben ser positivas")
    except ValueError:
        print("✗ Valores inválidos")

def configurar_animales(config):
    """
    Permite al usuario configurar la cantidad de animales.

    Args:
        config: Configuración del sistema
    """
    print("\n=== CONFIGURACIÓN DE ANIMALES ===")

    especies = obtener_especies_disponibles()

    for especie in especies:
        try:
            cantidad_actual = config.rancho.cantidad_animales[especie]
            cantidad = int(input(f"Cantidad de {especie} [{cantidad_actual}]: ")
                          or cantidad_actual)

            if cantidad >= 0:
                config.rancho.cantidad_animales[especie] = cantidad
                print(f"✓ {especie.capitalize()}: {cantidad}")
            else:
                print(f"✗ La cantidad no puede ser negativa")
        except ValueError:
            print(f"✗ Valor inválido para {especie}")

def configurar_presupuesto(config):
    """
    Permite al usuario configurar el presupuesto.

    Args:
        config: Configuración del sistema
    """
    print("\n=== CONFIGURACIÓN DEL PRESUPUESTO ===")

    try:
        presupuesto = float(input(f"Presupuesto máximo (pesos) [{config.rancho.presupuesto_maximo}]: ")
                           or config.rancho.presupuesto_maximo)

        if presupuesto > 0:
            config.rancho.presupuesto_maximo = presupuesto
            print(f"✓ Presupuesto configurado: ${presupuesto:,.2f}")
        else:
            print("✗ El presupuesto debe ser positivo")
    except ValueError:
        print("✗ Valor inválido")

def configurar_algoritmo(config):
    """
    Permite al usuario configurar parámetros del algoritmo genético.

    Args:
        config: Configuración del sistema
    """
    print("\n=== CONFIGURACIÓN DEL ALGORITMO GENÉTICO ===")

    try:
        # Población
        poblacion = int(input(f"Tamaño de población [{config.algoritmo_genetico.tamano_poblacion}]: ")
                       or config.algoritmo_genetico.tamano_poblacion)
        if poblacion >= 10:
            config.algoritmo_genetico.tamano_poblacion = poblacion
            print(f"✓ Población: {poblacion}")

        # Generaciones
        generaciones = int(input(f"Número de generaciones [{config.algoritmo_genetico.numero_generaciones}]: ")
                          or config.algoritmo_genetico.numero_generaciones)
        if generaciones >= 1:
            config.algoritmo_genetico.numero_generaciones = generaciones
            print(f"✓ Generaciones: {generaciones}")

        # Mutación
        mutacion = float(input(f"Probabilidad de mutación (0-1) [{config.algoritmo_genetico.probabilidad_mutacion}]: ")
                        or config.algoritmo_genetico.probabilidad_mutacion)
        if 0 <= mutacion <= 1:
            config.algoritmo_genetico.probabilidad_mutacion = mutacion
            print(f"✓ Mutación: {mutacion}")

    except ValueError:
        print("✗ Valores inválidos")

def callback_progreso(progreso):
    """
    Función callback para mostrar progreso del algoritmo.

    Args:
        progreso: Diccionario con información de progreso
    """
    generacion = progreso['generacion']
    stats = progreso['estadisticas']
    tiempo = progreso['tiempo_transcurrido']

    print(f"Gen {generacion:3d} | "
          f"Mejor: {stats['mejor']:.4f} | "
          f"Promedio: {stats['promedio']:.4f} | "
          f"Tiempo: {tiempo:.1f}s")

def mostrar_resultados(resultado):
    """
    Muestra los resultados finales del algoritmo.

    Args:
        resultado: Resultado del algoritmo genético
    """
    if not resultado['exito']:
        print("\n✗ ERROR EN LA OPTIMIZACIÓN:")
        for error in resultado.get('errores', []):
            print(f"  - {error}")
        return

    print("\n" + "=" * 60)
    print("              RESULTADOS FINALES")
    print("=" * 60)

    print(f"✓ Optimización completada exitosamente")
    print(f"  Generaciones ejecutadas: {resultado['generaciones_ejecutadas']}")
    print(f"  Tiempo total: {resultado['tiempo_total']:.2f} segundos")
    print(f"  Mejor fitness alcanzado: {resultado['mejor_fitness']:.4f}")

    # Mostrar información del mejor rancho
    mejor_individuo = resultado['mejor_individuo']
    config = ConfiguracionSistema()

    # Importar módulos necesarios
    from src.rancho.especies import mapear_valor_del_vector, calcular_area_minima_corral

    print(f"\n--- MEJOR CONFIGURACIÓN DE RANCHO ---")

    # Obtener datos del mejor individuo
    corrales = mejor_individuo.obtener_datos_corrales()
    infraestructura = mejor_individuo.obtener_datos_infraestructura()

    print("Corrales encontrados:")
    for especie, datos in corrales.items():
        if config.rancho.cantidad_animales[especie] > 0:
            # Convertir valores normalizados a valores reales
            pos_x_real = datos['posicion_x'] * config.rancho.ancho_terreno
            pos_y_real = datos['posicion_y'] * config.rancho.largo_terreno
            factor_agrand_real = mapear_valor_del_vector('factor_agrandamiento', datos['factor_agrandamiento'])
            proporcion_real = mapear_valor_del_vector('proporcion', datos['proporcion'])
            orientacion_real = mapear_valor_del_vector('orientacion', datos['orientacion'])

            # Calcular área real
            area_minima = calcular_area_minima_corral(especie, config.rancho.cantidad_animales[especie])
            area_real = area_minima * factor_agrand_real

            print(f"  {especie.capitalize()} ({config.rancho.cantidad_animales[especie]} animales):")
            print(f"    Posición: ({pos_x_real:.1f}m, {pos_y_real:.1f}m)")
            print(f"    Área: {area_real:.1f} m² (mínimo: {area_minima:.1f} m²)")
            print(f"    Factor agrandamiento: {factor_agrand_real:.2f}x")
            print(f"    Proporción ancho/alto: {proporcion_real:.2f}")
            print(f"    Orientación: {orientacion_real:.0f}°")

    # Convertir infraestructura a valores reales
    ancho_pasillos_real = mapear_valor_del_vector('ancho_pasillos', infraestructura['ancho_pasillos'])

    print(f"\nInfraestructura:")
    print(f"  Ancho de pasillos: {ancho_pasillos_real:.2f} metros")
    print(f"  Configuración: {infraestructura['configuracion']:.2f}")
    print(f"  Acceso principal: {infraestructura['acceso_principal']:.2f}")
    print(f"  Conectividad: {infraestructura['conectividad']:.2f}")

    # Preguntar si guardar resultados
    guardar = input("\n¿Desea guardar los resultados? (s/n): ").lower().strip()
    if guardar in ['s', 'si', 'sí', 'y', 'yes']:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        archivo = f"resultado_rancho_{timestamp}.json"

        import json
        import numpy as np

        def convertir_a_serializable(obj):
            """Convierte objetos no serializables a formato JSON."""
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif hasattr(obj, '__dict__'):
                return obj.__dict__
            else:
                return str(obj)

        with open(archivo, 'w') as f:
            # Preparar datos serializables
            resultado_serializable = {
                'exito': resultado['exito'],
                'mejor_fitness': float(resultado['mejor_fitness']),
                'generaciones_ejecutadas': int(resultado['generaciones_ejecutadas']),
                'tiempo_total': float(resultado['tiempo_total']),
                'mejor_vector': resultado['mejor_individuo'].vector.tolist(),
                'estadisticas_finales': resultado['estadisticas_finales'],
                'configuracion_utilizada': resultado['configuracion_utilizada']
            }

            json.dump(resultado_serializable, f, indent=2, default=convertir_a_serializable)

        print(f"✓ Resultados guardados en: {archivo}")

def menu_principal():
    """
    Muestra el menú principal y maneja la interacción con el usuario.
    """
    config = ConfiguracionSistema()

    while True:
        print("\n" + "=" * 40)
        print("           MENÚ PRINCIPAL")
        print("=" * 40)
        print("1. Ver configuración actual")
        print("2. Configurar terreno")
        print("3. Configurar animales")
        print("4. Configurar presupuesto")
        print("5. Configurar algoritmo genético")
        print("6. Ejecutar optimización")
        print("7. Ejecutar optimización rápida (parámetros por defecto)")
        print("8. Salir")
        print("-" * 40)

        opcion = input("Seleccione una opción (1-8): ").strip()

        if opcion == '1':
            mostrar_configuracion_actual(config)

        elif opcion == '2':
            configurar_terreno(config)

        elif opcion == '3':
            configurar_animales(config)

        elif opcion == '4':
            configurar_presupuesto(config)

        elif opcion == '5':
            configurar_algoritmo(config)

        elif opcion == '6':
            print("\n🚀 Iniciando optimización...")
            resultado = ejecutar_optimizacion(config, callback_progreso)
            mostrar_resultados(resultado)

        elif opcion == '7':
            print("\n🚀 Iniciando optimización rápida...")
            # Configuración rápida
            config.algoritmo_genetico.tamano_poblacion = 50
            config.algoritmo_genetico.numero_generaciones = 100
            resultado = ejecutar_optimizacion(config, callback_progreso)
            mostrar_resultados(resultado)

        elif opcion == '8':
            print("\n¡Gracias por usar RANCHERSPACE-GA!")
            print("¡Que tenga éxito con su rancho! 🐄🐷🐔🐐")
            break

        else:
            print("✗ Opción inválida. Seleccione 1-8.")

def main():
    """Función principal del programa."""
    try:
        mostrar_bienvenida()

        # Verificar que las especies estén disponibles
        especies = obtener_especies_disponibles()
        print(f"Especies disponibles: {', '.join(especies)}")
        print()

        # Ejecutar menú principal
        menu_principal()

    except KeyboardInterrupt:
        print("\n\n⚠️  Programa interrumpido por el usuario")
        print("¡Hasta luego!")

    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        print("Por favor reporte este error.")

if __name__ == "__main__":
    main()