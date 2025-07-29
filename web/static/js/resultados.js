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

    // Mostrar lista de materiales
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

    // Calcular área y costo (requiere procesamiento adicional)
    calcularMetricasResumen(resultado);
}

function calcularMetricasResumen(resultado) {
    const config = resultado.configuracion_utilizada;
    const areaTerreno = config.rancho.terreno.ancho * config.rancho.terreno.largo;

    document.getElementById('areaOptimizada').textContent = areaTerreno.toLocaleString('es-MX');

    // Estimar costo (simplificado)
    const costoEstimado = config.rancho.presupuesto * 0.7; // Estimación
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
            const factorAgrand = 1.0 + datos.factor_agrandamiento; // Simplificado

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
                            <strong>Material:</strong> ${config.rancho.materiales[especie]}
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
    const anchoPasillos = 1.5 + (infra.ancho_pasillos * 2.5); // 1.5m a 4m

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

    let html = '';
    let costoTotal = 0;

    // Simplificado - calcular materiales básicos
    for (const [especie, material] of Object.entries(config.rancho.materiales)) {
        const cantidad = config.rancho.animales[especie];
        if (cantidad > 0) {
            // Estimación de perímetro (simplificada)
            const perimetroEstimado = Math.sqrt(cantidad * 2.5) * 4; // Estimación
            const costoMaterial = getCostoMaterial(material);
            const costoEspecie = perimetroEstimado * costoMaterial;

            costoTotal += costoEspecie;

            html += `
                <div class="material-item">
                    <div>
                        <div class="material-name">${getNombreMaterial(material)}</div>
                        <div class="material-quantity">${perimetroEstimado.toFixed(1)} metros lineales</div>
                    </div>
                    <div class="material-cost">$${costoEspecie.toLocaleString('es-MX')}</div>
                </div>
            `;
        }
    }

    container.innerHTML = html;
    document.getElementById('costoTotalMateriales').textContent = '$' + costoTotal.toLocaleString('es-MX');
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

function dibujarConexionesInternas(ctx, corrales, config, escala, offsetX, offsetY, anchoPasillos) {
    // Dibujar conexiones entre corrales evitando solapamientos
    ctx.strokeStyle = '#6c757d';
    ctx.lineWidth = anchoPasillos;
    ctx.setLineDash([3, 3]);

    for (let i = 0; i < corrales.length; i++) {
        for (let j = i + 1; j < corrales.length; j++) {
            const corral1 = corrales[i];
            const corral2 = corrales[j];

            // Calcular centros de corrales
            const centro1X = corral1.x + corral1.ancho / 2;
            const centro1Y = corral1.y + corral1.alto / 2;
            const centro2X = corral2.x + corral2.ancho / 2;
            const centro2Y = corral2.y + corral2.alto / 2;

            // Solo dibujar conexión si hay suficiente espacio
            const distancia = Math.sqrt(Math.pow(centro2X - centro1X, 2) + Math.pow(centro2Y - centro1Y, 2));

            if (distancia > 8) { // Solo si están suficientemente separados
                // Buscar ruta que evite otros corrales
                const rutaLibre = encontrarRutaLibre(centro1X, centro1Y, centro2X, centro2Y, corrales, i, j);

                if (rutaLibre.length > 0) {
                    ctx.beginPath();
                    ctx.moveTo(offsetX + rutaLibre[0].x * escala, offsetY + rutaLibre[0].y * escala);

                    for (let k = 1; k < rutaLibre.length; k++) {
                        ctx.lineTo(offsetX + rutaLibre[k].x * escala, offsetY + rutaLibre[k].y * escala);
                    }
                    ctx.stroke();
                }
            }
        }
    }
}

function encontrarRutaLibre(x1, y1, x2, y2, corrales, excluir1, excluir2) {
    // Algoritmo simple para encontrar ruta L que evite corrales
    const ruta = [];

    // Probar ruta en L (horizontal primero, luego vertical)
    const puntoIntermedio1 = { x: x2, y: y1 };

    if (!hayObstaculoEnLinea(x1, y1, puntoIntermedio1.x, puntoIntermedio1.y, corrales, excluir1, excluir2) &&
        !hayObstaculoEnLinea(puntoIntermedio1.x, puntoIntermedio1.y, x2, y2, corrales, excluir1, excluir2)) {
        ruta.push({ x: x1, y: y1 });
        if (Math.abs(x2 - x1) > 1) ruta.push(puntoIntermedio1);
        ruta.push({ x: x2, y: y2 });
        return ruta;
    }

    // Probar ruta en L invertida (vertical primero, luego horizontal)
    const puntoIntermedio2 = { x: x1, y: y2 };

    if (!hayObstaculoEnLinea(x1, y1, puntoIntermedio2.x, puntoIntermedio2.y, corrales, excluir1, excluir2) &&
        !hayObstaculoEnLinea(puntoIntermedio2.x, puntoIntermedio2.y, x2, y2, corrales, excluir1, excluir2)) {
        ruta.push({ x: x1, y: y1 });
        if (Math.abs(y2 - y1) > 1) ruta.push(puntoIntermedio2);
        ruta.push({ x: x2, y: y2 });
        return ruta;
    }

    return []; // No se encontró ruta libre
}

function hayObstaculoEnLinea(x1, y1, x2, y2, corrales, excluir1, excluir2) {
    // Verificar si la línea intersecta con algún corral
    for (let i = 0; i < corrales.length; i++) {
        if (i === excluir1 || i === excluir2) continue;

        const corral = corrales[i];
        const margen = 1; // 1 metro de margen

        // Expandir el corral con margen
        const corralExpandido = {
            x: corral.x - margen,
            y: corral.y - margen,
            ancho: corral.ancho + 2 * margen,
            alto: corral.alto + 2 * margen
        };

        if (lineaIntersectaRectangulo(x1, y1, x2, y2, corralExpandido)) {
            return true;
        }
    }
    return false;
}

function lineaIntersectaRectangulo(x1, y1, x2, y2, rect) {
    // Verificar si la línea intersecta con el rectángulo
    // Algoritmo simplificado: verificar si algún extremo está dentro o si cruza algún borde

    // Verificar si los puntos están dentro del rectángulo
    if ((x1 >= rect.x && x1 <= rect.x + rect.ancho && y1 >= rect.y && y1 <= rect.y + rect.alto) ||
        (x2 >= rect.x && x2 <= rect.x + rect.ancho && y2 >= rect.y && y2 <= rect.y + rect.alto)) {
        return true;
    }

    // Verificar intersección con los bordes del rectángulo (simplificado)
    const rectCentroX = rect.x + rect.ancho / 2;
    const rectCentroY = rect.y + rect.alto / 2;
    const lineaCentroX = (x1 + x2) / 2;
    const lineaCentroY = (y1 + y2) / 2;

    // Si la línea pasa cerca del centro del rectángulo, considerar intersección
    const distanciaAlCentro = Math.sqrt(Math.pow(lineaCentroX - rectCentroX, 2) + Math.pow(lineaCentroY - rectCentroY, 2));
    const umbral = Math.max(rect.ancho, rect.alto) / 2;

    return distanciaAlCentro < umbral;
}

function hayColision(x1, y1, w1, h1, x2, y2, w2, h2) {
    // Agregar margen de separación de 1 metro
    const margen = 1;
    return !(x1 + w1 + margen <= x2 ||
             x2 + w2 + margen <= x1 ||
             y1 + h1 + margen <= y2 ||
             y2 + h2 + margen <= y1);
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
        malla_gallinera: 45,
        cerca_alambre: 65,
        cerca_metal: 85,
        cerca_madera: 120
    };
    return costos[material] || 50;
}

function getNombreMaterial(material) {
    const nombres = {
        malla_gallinera: 'Malla Gallinera',
        cerca_alambre: 'Cerca de Alambre',
        cerca_metal: 'Cerca Metálica',
        cerca_madera: 'Cerca de Madera'
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

// Inicializar auto-refresh si es necesario
// habilitarAutoRefresh();