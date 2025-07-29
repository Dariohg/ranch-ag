// JavaScript para la página de resultados de RANCHERSPACE-GA

let datosResultado = null;
let graficoEvolucion = null;

document.addEventListener('DOMContentLoaded', function() {
    initializeResultados();
});

function initializeResultados() {
    // Configurar event listeners
    setupEventListeners();

    // Cargar resultados
    cargarResultados();
}

function setupEventListeners() {
    // Botones de acción
    document.getElementById('btnExportarPlano').addEventListener('click', exportarPlano);
    document.getElementById('btnExportarCompleto').addEventListener('click', exportarReporteCompleto);
    document.getElementById('btnGuardarProyecto').addEventListener('click', guardarProyecto);
}

function cargarResultados() {
    fetch('/api/resultado')
    .then(response => {
        if (!response.ok) {
            throw new Error('No hay resultados disponibles');
        }
        return response.json();
    })
    .then(data => {
        datosResultado = data;
        mostrarResultados(data);
        ocultarEstadoCarga();
    })
    .catch(error => {
        console.error('Error cargando resultados:', error);
        mostrarSinResultados();
        ocultarEstadoCarga();
    });
}

function mostrarResultados(resultado) {
    // Mostrar resumen ejecutivo
    mostrarResumenEjecutivo(resultado);

    // Mostrar detalles de corrales
    mostrarDetallesCorreales(resultado);

    // Mostrar infraestructura
    mostrarInfraestructura(resultado);

    // Mostrar análisis técnico
    mostrarAnalisisTecnico(resultado);

    // Mostrar lista de materiales (USANDO BACKEND)
    mostrarListaMateriales(resultado);

    // Mostrar recomendaciones
    mostrarRecomendaciones(resultado);

    // Dibujar plano
    dibujarPlano2D(resultado);

    // Crear gráfico de evolución
    crearGraficoEvolucion(resultado);

    // Mostrar contenido
    document.getElementById('contenidoResultados').style.display = 'block';
}

function mostrarResumenEjecutivo(resultado) {
    document.getElementById('fitnessAlcanzado').textContent = resultado.mejor_fitness.toFixed(4);
    document.getElementById('generacionesEjecutadas').textContent = resultado.generaciones_ejecutadas;
    document.getElementById('tiempoTotal').textContent = resultado.tiempo_total.toFixed(1) + 's';

    // Calcular métricas del resumen
    calcularMetricasResumen(resultado);
}

function calcularMetricasResumen(resultado) {
    const config = resultado.configuracion_utilizada;
    const areaTerreno = config.rancho.terreno.ancho * config.rancho.terreno.largo;

    document.getElementById('areaOptimizada').textContent = areaTerreno.toLocaleString('es-MX');

    // Estimar costo (se actualizará cuando se cargue la lista de materiales)
    const costoEstimado = config.rancho.presupuesto * 0.7;
    document.getElementById('costoEstimado').textContent = '$' + costoEstimado.toLocaleString('es-MX');
}

function mostrarDetallesCorreales(resultado) {
    const corrales = resultado.mejor_individuo.corrales;
    const config = resultado.configuracion_utilizada;
    const container = document.getElementById('detallesCorreales');

    let html = '';

    for (const [especie, datos] of Object.entries(corrales)) {
        const cantidad = config.rancho.animales[especie];
        if (cantidad > 0) {
            // Convertir valores normalizados a reales
            const posX = datos.posicion_x * config.rancho.terreno.ancho;
            const posY = datos.posicion_y * config.rancho.terreno.largo;
            const factorAgrand = 1.0 + datos.factor_agrandamiento;

            html += `
                <div class="border rounded p-3 mb-3">
                    <h6 class="text-capitalize fw-bold">${especie}</h6>
                    <div class="row text-sm">
                        <div class="col-6">
                            <strong>Cantidad:</strong> ${cantidad}<br>
                            <strong>Posición:</strong> (${posX.toFixed(1)}m, ${posY.toFixed(1)}m)<br>
                            <strong>Factor agrand.:</strong> ${factorAgrand.toFixed(2)}x
                        </div>
                        <div class="col-6">
                            <strong>Proporción:</strong> ${datos.proporcion.toFixed(2)}<br>
                            <strong>Orientación:</strong> ${(datos.orientacion * 360).toFixed(0)}°<br>
                            <strong>Material:</strong> ${config.rancho.materiales[especie] || 'N/A'}
                        </div>
                    </div>
                </div>
            `;
        }
    }

    container.innerHTML = html;
}

function mostrarInfraestructura(resultado) {
    const infra = resultado.mejor_individuo.infraestructura;
    const container = document.getElementById('detallesInfraestructura');

    // Convertir valores normalizados
    const anchoPasillos = 1.5 + (infra.ancho_pasillos * 2.5);

    const html = `
        <div class="border rounded p-3">
            <div class="row">
                <div class="col-6">
                    <strong>Ancho de pasillos:</strong><br>
                    <span class="text-primary">${anchoPasillos.toFixed(2)} metros</span>
                </div>
                <div class="col-6">
                    <strong>Configuración:</strong><br>
                    <span class="text-secondary">${(infra.configuracion * 100).toFixed(0)}%</span>
                </div>
            </div>
            <div class="row mt-2">
                <div class="col-6">
                    <strong>Acceso principal:</strong><br>
                    <span class="text-info">${(infra.acceso_principal * 100).toFixed(0)}%</span>
                </div>
                <div class="col-6">
                    <strong>Conectividad:</strong><br>
                    <span class="text-success">${(infra.conectividad * 100).toFixed(0)}%</span>
                </div>
            </div>
        </div>
    `;

    container.innerHTML = html;
}

function mostrarAnalisisTecnico(resultado) {
    // Métricas
    const metricas = document.getElementById('metricas');
    const stats = resultado.estadisticas_finales;

    metricas.innerHTML = `
        <div class="row">
            <div class="col-6 mb-2">
                <small class="text-muted">Mejor fitness:</small><br>
                <strong>${stats.mejor.toFixed(4)}</strong>
            </div>
            <div class="col-6 mb-2">
                <small class="text-muted">Promedio:</small><br>
                <strong>${stats.promedio.toFixed(4)}</strong>
            </div>
            <div class="col-6 mb-2">
                <small class="text-muted">Peor fitness:</small><br>
                <strong>${stats.peor.toFixed(4)}</strong>
            </div>
            <div class="col-6 mb-2">
                <small class="text-muted">Desviación:</small><br>
                <strong>${stats.desviacion.toFixed(4)}</strong>
            </div>
        </div>
    `;

    // Vector genético
    const vector = document.getElementById('vectorGenetico');
    const vectorStr = resultado.mejor_individuo.vector.map(v => v.toFixed(3)).join(', ');
    vector.textContent = '[' + vectorStr + ']';

    // Parámetros del algoritmo
    const params = document.getElementById('parametrosAlgoritmo');
    const config = resultado.configuracion_utilizada.algoritmo;

    params.innerHTML = `
        <div class="row">
            <div class="col-6 mb-2">
                <small class="text-muted">Población:</small><br>
                <strong>${config.poblacion}</strong>
            </div>
            <div class="col-6 mb-2">
                <small class="text-muted">Generaciones:</small><br>
                <strong>${config.generaciones}</strong>
            </div>
            <div class="col-6 mb-2">
                <small class="text-muted">Prob. mutación:</small><br>
                <strong>${config.mutacion}</strong>
            </div>
            <div class="col-6 mb-2">
                <small class="text-muted">Prob. cruza:</strong><br>
                <strong>${config.cruza}</strong>
            </div>
        </div>
    `;

    // Estadísticas de convergencia
    const convergencia = document.getElementById('estadisticasConvergencia');
    convergencia.innerHTML = `
        <div class="row">
            <div class="col-12 mb-2">
                <small class="text-muted">Tiempo total:</small><br>
                <strong>${resultado.tiempo_total.toFixed(2)} segundos</strong>
            </div>
            <div class="col-12 mb-2">
                <small class="text-muted">Generaciones ejecutadas:</small><br>
                <strong>${resultado.generaciones_ejecutadas} de ${config.generaciones}</strong>
            </div>
            <div class="col-12 mb-2">
                <small class="text-muted">Velocidad:</small><br>
                <strong>${(resultado.generaciones_ejecutadas / resultado.tiempo_total).toFixed(1)} gen/seg</strong>
            </div>
        </div>
    `;
}

function mostrarListaMateriales(resultado) {
    const container = document.getElementById('listaMateriales');
    const config = resultado.configuracion_utilizada;

    // Obtener materiales seleccionados por el usuario
    const materialesSeleccionados = config.rancho.materiales || config.rancho.material_por_especie || {};

    console.log("=== DEBUG LISTA DE MATERIALES ===");
    console.log("Materiales seleccionados:", materialesSeleccionados);
    console.log("Rancho físico disponible:", !!resultado.rancho_fisico);

    // USAR ENDPOINT DEL BACKEND PARA CALCULAR COSTOS CORRECTOS
    fetch('/api/calcular_costos_resultado', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            rancho_fisico: resultado.rancho_fisico || {},
            materiales_seleccionados: materialesSeleccionados
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error("Error calculando costos:", data.error);
            mostrarListaMaterialesFallback(resultado);
            return;
        }

        let html = '';
        const costos = data.costos_por_especie;

        console.log("Costos calculados por backend:", costos);

        for (const [especie, datos] of Object.entries(costos)) {
            html += `
                <div class="material-item">
                    <div>
                        <div class="material-name">${datos.material_nombre}</div>
                        <div class="material-quantity">
                            ${especie.charAt(0).toUpperCase() + especie.slice(1)}: 
                            ${datos.perimetro_metros.toFixed(1)} metros lineales
                            ${datos.ancho_corral && datos.alto_corral ? 
                                `(${datos.ancho_corral.toFixed(1)}m × ${datos.alto_corral.toFixed(1)}m)` : ''}
                        </div>
                    </div>
                    <div class="material-cost">$${datos.costo_total.toLocaleString('es-MX')}</div>
                </div>
            `;
        }

        container.innerHTML = html;
        document.getElementById('costoTotalMateriales').textContent =
            '$' + data.costo_total.toLocaleString('es-MX');

        // Actualizar costo estimado en resumen ejecutivo
        document.getElementById('costoEstimado').textContent =
            '$' + data.costo_total.toLocaleString('es-MX');

        console.log("Costo total calculado por backend:", data.costo_total);
    })
    .catch(error => {
        console.error('Error obteniendo costos de materiales:', error);
        mostrarListaMaterialesFallback(resultado);
    });
}

function mostrarListaMaterialesFallback(resultado) {
    /**
     * Función de respaldo si falla el cálculo del backend
     */
    const container = document.getElementById('listaMateriales');

    container.innerHTML = `
        <div class="alert alert-warning">
            <i class="fas fa-exclamation-triangle me-2"></i>
            Error calculando costos exactos. Mostrando estimación.
        </div>
        <div class="material-item">
            <div>
                <div class="material-name">Costo estimado total</div>
                <div class="material-quantity">Basado en configuración</div>
            </div>
            <div class="material-cost">$50,000</div>
        </div>
    `;

    document.getElementById('costoTotalMateriales').textContent = '$50,000';
    console.log("Usando cálculo de respaldo por error en backend");
}

function mostrarRecomendaciones(resultado) {
    const recomendaciones = document.getElementById('recomendacionesGenerales');
    const secuencia = document.getElementById('secuenciaConstruccion');

    recomendaciones.innerHTML = `
        <li>Marcar el terreno según las coordenadas proporcionadas</li>
        <li>Verificar niveles del terreno antes de construir</li>
        <li>Considerar drenaje en áreas de mayor concentración animal</li>
        <li>Instalar puntos de agua cerca de cada corral</li>
        <li>Mantener las distancias mínimas entre especies</li>
    `;

    secuencia.innerHTML = `
        <li>Delimitar y nivelar el terreno</li>
        <li>Instalar infraestructura de pasillos principales</li>
        <li>Construir corrales empezando por las vacas (mayor tamaño)</li>
        <li>Instalar comederos y bebederos</li>
        <li>Verificar todas las medidas y ajustar si es necesario</li>
    `;
}

function dibujarPlano2D(resultado) {
    const canvas = document.getElementById('canvasRancho');
    const ctx = canvas.getContext('2d');
    const config = resultado.configuracion_utilizada;

    // Limpiar canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Configurar escala
    const escalaX = canvas.width / config.rancho.terreno.ancho;
    const escalaY = canvas.height / config.rancho.terreno.largo;
    const escala = Math.min(escalaX, escalaY) * 0.9;

    const offsetX = (canvas.width - (config.rancho.terreno.ancho * escala)) / 2;
    const offsetY = (canvas.height - (config.rancho.terreno.largo * escala)) / 2;

    // Dibujar borde del terreno
    ctx.strokeStyle = '#000000';
    ctx.lineWidth = 2;
    ctx.strokeRect(offsetX, offsetY,
                   config.rancho.terreno.ancho * escala,
                   config.rancho.terreno.largo * escala);

    // Colores por especie
    const colores = {
        gallinas: '#ffc107',
        cerdos: '#dc3545',
        vacas: '#007bff',
        cabras: '#28a745'
    };

    // Dibujar corrales usando datos calculados en Python
    if (resultado.rancho_fisico && resultado.rancho_fisico.corrales) {
        for (const [especie, corral] of Object.entries(resultado.rancho_fisico.corrales)) {
            const canvasX = offsetX + (corral.posicion_x * escala);
            const canvasY = offsetY + (corral.posicion_y * escala);
            const canvasAncho = corral.ancho * escala;
            const canvasAlto = corral.alto * escala;

            // Dibujar corral
            ctx.fillStyle = colores[especie];
            ctx.fillRect(canvasX, canvasY, canvasAncho, canvasAlto);

            // Borde del corral
            ctx.strokeStyle = '#000000';
            ctx.lineWidth = 1;
            ctx.strokeRect(canvasX, canvasY, canvasAncho, canvasAlto);

            // Etiqueta
            ctx.fillStyle = '#000000';
            ctx.font = '12px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(especie.charAt(0).toUpperCase() + especie.slice(1),
                        canvasX + canvasAncho/2,
                        canvasY + canvasAlto/2);
        }
    }
}

function crearGraficoEvolucion(resultado) {
    const ctx = document.getElementById('graficoEvolucion').getContext('2d');

    // Datos del historial de fitness
    const historial = resultado.historial_fitness || [];
    const generaciones = historial.map((_, i) => i);
    const mejorFitness = historial.map(h => h.mejor);
    const promedioFitness = historial.map(h => h.promedio);

    graficoEvolucion = new Chart(ctx, {
        type: 'line',
        data: {
            labels: generaciones,
            datasets: [{
                label: 'Mejor Fitness',
                data: mejorFitness,
                borderColor: '#28a745',
                backgroundColor: 'rgba(40, 167, 69, 0.1)',
                borderWidth: 2,
                fill: false
            }, {
                label: 'Fitness Promedio',
                data: promedioFitness,
                borderColor: '#17a2b8',
                backgroundColor: 'rgba(23, 162, 184, 0.1)',
                borderWidth: 2,
                fill: false
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Evolución del Fitness por Generación'
                },
                legend: {
                    position: 'top'
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Generación'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Fitness'
                    },
                    min: 0,
                    max: 1
                }
            }
        }
    });
}

function exportarPlano() {
    const canvas = document.getElementById('canvasRancho');
    const link = document.createElement('a');
    link.download = 'plano_rancho_optimizado.png';
    link.href = canvas.toDataURL();
    link.click();
}

function exportarReporteCompleto() {
    if (!datosResultado) {
        alert('No hay datos para exportar');
        return;
    }

    // Crear datos del reporte
    const reporte = {
        fecha: new Date().toLocaleDateString('es-MX'),
        fitness: datosResultado.mejor_fitness,
        generaciones: datosResultado.generaciones_ejecutadas,
        tiempo: datosResultado.tiempo_total,
        configuracion: datosResultado.configuracion_utilizada,
        vector_solucion: datosResultado.mejor_individuo.vector
    };

    // Descargar como JSON
    const blob = new Blob([JSON.stringify(reporte, null, 2)], {type: 'application/json'});
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.download = `reporte_rancho_${new Date().toISOString().split('T')[0]}.json`;
    link.href = url;
    link.click();
    URL.revokeObjectURL(url);
}

function guardarProyecto() {
    if (!datosResultado) {
        alert('No hay proyecto para guardar');
        return;
    }

    const nombreProyecto = prompt('Nombre del proyecto:', 'Mi Rancho Optimizado');
    if (!nombreProyecto) return;

    const proyecto = {
        nombre: nombreProyecto,
        fecha_creacion: new Date().toISOString(),
        resultado: datosResultado
    };

    // Guardar en localStorage (temporal)
    const proyectosGuardados = JSON.parse(localStorage.getItem('proyectos_rancho') || '[]');
    proyectosGuardados.push(proyecto);
    localStorage.setItem('proyectos_rancho', JSON.stringify(proyectosGuardados));

    alert('Proyecto guardado correctamente');
}

function ocultarEstadoCarga() {
    document.getElementById('estadoCarga').style.display = 'none';
}

function mostrarSinResultados() {
    document.getElementById('sinResultados').style.display = 'block';
}

// Funciones auxiliares
function getAreaMinimaPorEspecie(especie) {
    const areas = {
        gallinas: 0.5,
        cerdos: 2.5,
        vacas: 15,
        cabras: 3
    };
    return areas[especie] || 1;
}

function getCostoMaterial(material) {
    const costos = {
        malla_gallinera_economica: 280,
        malla_gallinera_estandar: 420,
        malla_gallinera_premium: 680,
        cerca_alambre_basica: 320,
        cerca_alambre_reforzada: 480,
        cerca_alambre_electrica: 750,
        tubo_galvanizado_ligero: 850,
        cerca_metal_soldada: 1200,
        cerca_metal_premium: 1800,
        postes_madera_pino: 950,
        cerca_madera_roble: 1400,
        sistema_metal_pesado: 2200
    };
    return costos[material] || 75;
}

function getNombreMaterial(material) {
    const nombres = {
        malla_gallinera_economica: 'Malla Gallinera Económica',
        malla_gallinera_estandar: 'Malla Gallinera Estándar',
        malla_gallinera_premium: 'Malla Gallinera Premium',
        cerca_alambre_basica: 'Cerca Alambre Básica',
        cerca_alambre_reforzada: 'Cerca Alambre Reforzada',
        cerca_alambre_electrica: 'Cerca Alambre Eléctrica',
        tubo_galvanizado_ligero: 'Tubo Galvanizado Ligero',
        cerca_metal_soldada: 'Cerca Metálica Soldada',
        cerca_metal_premium: 'Cerca Metálica Premium',
        postes_madera_pino: 'Postes Madera Pino',
        cerca_madera_roble: 'Cerca Madera Roble',
        sistema_metal_pesado: 'Sistema Metálico Pesado'
    };
    return nombres[material] || material;
}

// Animaciones y efectos
function animarCarga() {
    const elementos = document.querySelectorAll('.card');
    elementos.forEach((elemento, index) => {
        setTimeout(() => {
            elemento.classList.add('fade-in');
        }, index * 100);
    });
}

// Auto-refresh para resultados en tiempo real (opcional)
function habilitarAutoRefresh() {
    setInterval(() => {
        // Solo refrescar si no hay resultados cargados
        if (!datosResultado) {
            cargarResultados();
        }
    }, 5000); // Cada 5 segundos
}