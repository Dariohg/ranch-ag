// JavaScript para la página de configuración de RANCHERSPACE-GA

document.addEventListener('DOMContentLoaded', function() {
    initializeConfiguracion();
});

function initializeConfiguracion() {
    // Configurar event listeners
    setupEventListeners();

    // Calcular valores iniciales
    calcularAreaTerreno();
    calcularAreaAnimales();
    actualizarPesos();
    validarTerreno();

    // Cargar materiales por especie
    cargarMaterialesPorEspecie();
}

function cargarMaterialesPorEspecie() {
    const especies = ['gallinas', 'cerdos', 'vacas', 'cabras'];

    especies.forEach(especie => {
        fetch(`/api/materiales/${especie}`)
        .then(response => response.json())
        .then(materiales => {
            const select = document.getElementById(`material_${especie}`);
            select.innerHTML = ''; // Limpiar opciones

            // Agregar opciones de materiales compatibles
            for (const [materialId, materialInfo] of Object.entries(materiales)) {
                const option = document.createElement('option');
                option.value = materialId;
                option.textContent = `${materialInfo.nombre} (${materialInfo.costo_por_metro}/m)`;

                // Seleccionar el primer material por defecto
                if (select.children.length === 0) {
                    option.selected = true;
                }

                select.appendChild(option);
            }
        })
        .catch(error => {
            console.error(`Error cargando materiales para ${especie}:`, error);
            // Fallback
            const select = document.getElementById(`material_${especie}`);
            select.innerHTML = `<option value="material_${especie}">Material para ${especie} ($75/m)</option>`;
        });
    });
}

function setupEventListeners() {
    // Terreno
    document.getElementById('anchoTerreno').addEventListener('input', calcularAreaTerreno);
    document.getElementById('largoTerreno').addEventListener('input', calcularAreaTerreno);

    // Animales
    const inputsAnimales = document.querySelectorAll('.animal-input');
    inputsAnimales.forEach(input => {
        input.addEventListener('input', function() {
            calcularAreaAnimales();
            validarTerreno();
        });
    });

    // Pesos de objetivos
    const slidersPesos = document.querySelectorAll('input[type="range"][data-objetivo]');
    slidersPesos.forEach(slider => {
        slider.addEventListener('input', actualizarPesos);
    });

    // Formulario principal
    document.getElementById('configuracionForm').addEventListener('submit', function(e) {
        e.preventDefault();
        ejecutarOptimizacion();
    });
}

function calcularAreaTerreno() {
    const ancho = parseFloat(document.getElementById('anchoTerreno').value) || 0;
    const largo = parseFloat(document.getElementById('largoTerreno').value) || 0;
    const areaTotal = ancho * largo;

    document.getElementById('areaTotalTerreno').textContent = areaTotal.toLocaleString('es-MX') + ' m²';
    validarTerreno();
}

function calcularAreaAnimales() {
    const animales = {
        gallinas: parseInt(document.getElementById('animales_gallinas').value) || 0,
        cerdos: parseInt(document.getElementById('animales_cerdos').value) || 0,
        vacas: parseInt(document.getElementById('animales_vacas').value) || 0,
        cabras: parseInt(document.getElementById('animales_cabras').value) || 0
    };

    // Hacer petición al backend para calcular áreas
    fetch('/api/calcular_areas', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ animales: animales })
    })
    .then(response => response.json())
    .then(data => {
        if (data.area_total_minima !== undefined) {
            document.getElementById('areaMinimaTotalAnimales').textContent =
                data.area_total_minima.toLocaleString('es-MX') + ' m²';
        }
    })
    .catch(error => {
        console.error('Error calculando áreas:', error);
    });
}

function validarTerreno() {
    const ancho = parseFloat(document.getElementById('anchoTerreno').value) || 0;
    const largo = parseFloat(document.getElementById('largoTerreno').value) || 0;

    const animales = {
        gallinas: parseInt(document.getElementById('animales_gallinas').value) || 0,
        cerdos: parseInt(document.getElementById('animales_cerdos').value) || 0,
        vacas: parseInt(document.getElementById('animales_vacas').value) || 0,
        cabras: parseInt(document.getElementById('animales_cabras').value) || 0
    };

    fetch('/api/validar_terreno', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            ancho: ancho,
            largo: largo,
            animales: animales
        })
    })
    .then(response => response.json())
    .then(data => {
        const validacionDiv = document.getElementById('validacionTerreno');
        const btnEjecutar = document.getElementById('btnEjecutar');

        if (data.es_suficiente) {
            validacionDiv.innerHTML = `
                <div class="alert alert-success">
                    <i class="fas fa-check-circle me-2"></i>
                    <strong>Terreno válido:</strong> El terreno es suficiente para los animales configurados.
                    <br><small>Uso estimado: ${data.porcentaje_uso.toFixed(1)}% del terreno</small>
                </div>
            `;
            btnEjecutar.disabled = false;
        } else {
            validacionDiv.innerHTML = `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>Terreno insuficiente:</strong> Se requieren al menos ${data.area_minima_requerida.toFixed(0)} m².
                    <br><small>Terreno actual: ${data.area_terreno.toFixed(0)} m²</small>
                </div>
            `;
            btnEjecutar.disabled = true;
        }
    })
    .catch(error => {
        console.error('Error validando terreno:', error);
    });
}

function actualizarPesos() {
    const pesos = {
        espacio: parseInt(document.getElementById('peso_espacio').value),
        costo: parseInt(document.getElementById('peso_costo').value),
        materiales: parseInt(document.getElementById('peso_materiales').value),
        manejo: parseInt(document.getElementById('peso_manejo').value),
        terreno: parseInt(document.getElementById('peso_terreno').value)
    };

    // Actualizar labels con valores
    document.getElementById('valor_peso_espacio').textContent = pesos.espacio + '%';
    document.getElementById('valor_peso_costo').textContent = pesos.costo + '%';
    document.getElementById('valor_peso_materiales').textContent = pesos.materiales + '%';
    document.getElementById('valor_peso_manejo').textContent = pesos.manejo + '%';
    document.getElementById('valor_peso_terreno').textContent = pesos.terreno + '%';

    // Calcular total
    const total = pesos.espacio + pesos.costo + pesos.materiales + pesos.manejo + pesos.terreno;
    const totalElement = document.getElementById('totalPesos');

    totalElement.textContent = total + '%';

    // Solo mostrar color informativo, sin restricción
    totalElement.className = 'text-info fw-bold';
}

function recopilarConfiguracion() {
    // Recopilar todos los datos del formulario
    const configuracion = {
        terreno: {
            ancho: parseFloat(document.getElementById('anchoTerreno').value),
            largo: parseFloat(document.getElementById('largoTerreno').value)
        },
        animales: {
            gallinas: parseInt(document.getElementById('animales_gallinas').value) || 0,
            cerdos: parseInt(document.getElementById('animales_cerdos').value) || 0,
            vacas: parseInt(document.getElementById('animales_vacas').value) || 0,
            cabras: parseInt(document.getElementById('animales_cabras').value) || 0
        },
        materiales: {
            gallinas: document.getElementById('material_gallinas').value,
            cerdos: document.getElementById('material_cerdos').value,
            vacas: document.getElementById('material_vacas').value,
            cabras: document.getElementById('material_cabras').value
        },
        presupuesto: parseFloat(document.getElementById('presupuestoMaximo').value),
        objetivos: {
            espacio_extra: parseInt(document.getElementById('peso_espacio').value) / 100,
            costo_construccion: parseInt(document.getElementById('peso_costo').value) / 100,
            cantidad_materiales: parseInt(document.getElementById('peso_materiales').value) / 100,
            eficiencia_manejo: parseInt(document.getElementById('peso_manejo').value) / 100,
            aprovechamiento_terreno: parseInt(document.getElementById('peso_terreno').value) / 100
        },
        algoritmo: {
            poblacion: parseInt(document.getElementById('tamañoPoblacion').value),
            generaciones: parseInt(document.getElementById('numeroGeneraciones').value),
            mutacion: parseFloat(document.getElementById('probabilidadMutacion').value),
            cruza: 0.9, // Valor fijo
            tipo_cruza: document.getElementById('tipoCruza').value
        }
    };

    return configuracion;
}

function ejecutarOptimizacion() {
    const configuracion = recopilarConfiguracion();

    // Validar configuración
    if (!validarConfiguracion(configuracion)) {
        return;
    }

    // Mostrar modal de progreso
    const modal = new bootstrap.Modal(document.getElementById('modalProgreso'));
    modal.show();

    // Resetear progreso
    resetearProgreso();

    // Iniciar optimización
    fetch('/api/iniciar_optimizacion', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(configuracion)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }

        // Iniciar seguimiento del progreso
        iniciarSeguimientoProgreso();
    })
    .catch(error => {
        console.error('Error iniciando optimización:', error);
        alert('Error al iniciar la optimización: ' + error.message);
        modal.hide();
    });
}

function validarConfiguracion(config) {
    // Validar que haya al menos un animal
    const totalAnimales = Object.values(config.animales).reduce((a, b) => a + b, 0);
    if (totalAnimales === 0) {
        alert('Debe configurar al menos un animal.');
        return false;
    }

    // Validar terreno
    if (config.terreno.ancho <= 0 || config.terreno.largo <= 0) {
        alert('Las dimensiones del terreno deben ser positivas.');
        return false;
    }

    // Validar presupuesto
    if (config.presupuesto <= 0) {
        alert('El presupuesto debe ser positivo.');
        return false;
    }

    return true;
}

function resetearProgreso() {
    document.getElementById('progresoGeneraciones').style.width = '0%';
    document.getElementById('generacionActual').textContent = 'Generación 0';
    document.getElementById('tiempoTranscurrido').textContent = '0s';
    document.getElementById('mejorFitness').textContent = '0.0000';
    document.getElementById('fitnessPromedio').textContent = '0.0000';
    document.getElementById('mensajeProgreso').textContent = 'Iniciando optimización...';
}

function iniciarSeguimientoProgreso() {
    const intervalo = setInterval(() => {
        fetch('/api/progreso')
        .then(response => response.json())
        .then(data => {
            actualizarProgreso(data);

            // Si terminó, detener seguimiento
            if (data.estado === 'completado' || data.estado === 'error') {
                clearInterval(intervalo);
                finalizarOptimizacion(data);
            }
        })
        .catch(error => {
            console.error('Error obteniendo progreso:', error);
            clearInterval(intervalo);
        });
    }, 1000); // Actualizar cada segundo
}

function actualizarProgreso(data) {
    if (data.total_generaciones > 0) {
        const porcentaje = (data.generacion_actual / data.total_generaciones) * 100;
        document.getElementById('progresoGeneraciones').style.width = porcentaje + '%';
    }

    document.getElementById('generacionActual').textContent = `Generación ${data.generacion_actual}`;
    document.getElementById('tiempoTranscurrido').textContent = `${data.tiempo_transcurrido.toFixed(1)}s`;
    document.getElementById('mejorFitness').textContent = data.mejor_fitness.toFixed(4);
    document.getElementById('fitnessPromedio').textContent = data.fitness_promedio.toFixed(4);
    document.getElementById('mensajeProgreso').textContent = data.mensaje;
}

function finalizarOptimizacion(data) {
    const modal = bootstrap.Modal.getInstance(document.getElementById('modalProgreso'));

    setTimeout(() => {
        modal.hide();

        if (data.estado === 'completado') {
            // Redirigir a resultados
            window.location.href = '/resultados';
        } else {
            alert('Error en la optimización: ' + data.mensaje);
        }
    }, 2000); // Esperar 2 segundos para mostrar resultado final
}

// Funciones auxiliares para mejorar UX
function mostrarTooltip(elemento, mensaje) {
    elemento.setAttribute('title', mensaje);
    elemento.setAttribute('data-bs-toggle', 'tooltip');

    const tooltip = new bootstrap.Tooltip(elemento);
    tooltip.show();

    setTimeout(() => {
        tooltip.hide();
    }, 3000);
}

function animarElemento(elemento, clase = 'fade-in') {
    elemento.classList.add(clase);
    setTimeout(() => {
        elemento.classList.remove(clase);
    }, 500);
}

// Configuraciones predeterminadas
function aplicarConfiguracionRapida() {
    // Configuración para prueba rápida
    document.getElementById('tamañoPoblacion').value = 50;
    document.getElementById('numeroGeneraciones').value = 100;
    document.getElementById('probabilidadMutacion').value = 0.2;

    animarElemento(document.getElementById('configAvanzada'));
}

function aplicarConfiguracionCompleta() {
    // Configuración para optimización completa
    document.getElementById('tamañoPoblacion').value = 100;
    document.getElementById('numeroGeneraciones').value = 500;
    document.getElementById('probabilidadMutacion').value = 0.1;

    animarElemento(document.getElementById('configAvanzada'));
}

// Exportar funciones para uso global
window.aplicarConfiguracionRapida = aplicarConfiguracionRapida;
window.aplicarConfiguracionCompleta = aplicarConfiguracionCompleta;