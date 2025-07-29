// JavaScript para la página de configuración SIMPLIFICADA de RANCHERSPACE-GA

document.addEventListener('DOMContentLoaded', function() {
    initializeConfiguracion();
});

function initializeConfiguracion() {
    // Configurar event listeners
    setupEventListeners();

    // Calcular valores iniciales
    calcularAreaTerreno();
    calcularAreaAnimales();
    actualizarPesosSimplificados(); // NUEVO: Solo 2 objetivos
    validarTerreno();

    // Cargar materiales por especie
    cargarMaterialesPorEspecie();
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
            calcularPresupuestoInteligente(); // NUEVO: Presupuesto inteligente
            validarTerreno();
        });
    });

    // Materiales
    const selectsMateriales = document.querySelectorAll('select[id^="material_"]');
    selectsMateriales.forEach(select => {
        select.addEventListener('change', function() {
            calcularPresupuestoInteligente(); // NUEVO: Recalcular presupuesto
        });
    });

    // Presupuesto inteligente
    document.getElementById('presupuestoMaximo').addEventListener('input', function() {
        calcularPresupuestoInteligente();
    });

    // Pesos simplificados (SOLO 2 OBJETIVOS)
    document.getElementById('peso_terreno').addEventListener('input', actualizarPesosSimplificados);
    document.getElementById('peso_manejo').addEventListener('input', actualizarPesosSimplificados);

    // Formulario principal
    document.getElementById('configuracionForm').addEventListener('submit', function(e) {
        e.preventDefault();
        ejecutarOptimizacion();
    });
}

function cargarMaterialesPorEspecie() {
    const especies = ['gallinas', 'cerdos', 'vacas', 'cabras'];

    especies.forEach(especie => {
        fetch(`/api/materiales/${especie}`)
        .then(response => response.json())
        .then(materiales => {
            const select = document.getElementById(`material_${especie}`);
            select.innerHTML = '';

            for (const [materialId, materialInfo] of Object.entries(materiales)) {
                const option = document.createElement('option');
                option.value = materialId;
                option.textContent = `${materialInfo.nombre} ($${materialInfo.costo_por_metro}/m)`;

                if (select.children.length === 0) {
                    option.selected = true;
                }

                select.appendChild(option);
            }

            if (select.children.length > 0) {
                calcularPresupuestoInteligente(); // NUEVO: Calcular presupuesto al cargar materiales
            }
        })
        .catch(error => {
            console.error(`Error cargando materiales para ${especie}:`, error);
            const select = document.getElementById(`material_${especie}`);
            select.innerHTML = `<option value="material_${especie}">Material para ${especie} ($75/m)</option>`;
        });
    });
}

function calcularAreaTerreno() {
    const ancho = parseFloat(document.getElementById('anchoTerreno').value) || 0;
    const largo = parseFloat(document.getElementById('largoTerreno').value) || 0;
    const areaTotal = ancho * largo;

    document.getElementById('areaTotalTerreno').textContent = areaTotal.toLocaleString('es-MX') + ' m²';
    validarTerreno();
    calcularPresupuestoInteligente(); // NUEVO: Recalcular presupuesto si cambia terreno
}

function calcularAreaAnimales() {
    const animales = {
        gallinas: parseInt(document.getElementById('animales_gallinas').value) || 0,
        cerdos: parseInt(document.getElementById('animales_cerdos').value) || 0,
        vacas: parseInt(document.getElementById('animales_vacas').value) || 0,
        cabras: parseInt(document.getElementById('animales_cabras').value) || 0
    };

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

// NUEVA FUNCIÓN: Presupuesto Inteligente
function calcularPresupuestoInteligente() {
    const animales = {
        gallinas: parseInt(document.getElementById('animales_gallinas').value) || 0,
        cerdos: parseInt(document.getElementById('animales_cerdos').value) || 0,
        vacas: parseInt(document.getElementById('animales_vacas').value) || 0,
        cabras: parseInt(document.getElementById('animales_cabras').value) || 0
    };

    const materiales = {
        gallinas: document.getElementById('material_gallinas').value,
        cerdos: document.getElementById('material_cerdos').value,
        vacas: document.getElementById('material_vacas').value,
        cabras: document.getElementById('material_cabras').value
    };

    const presupuestoUsuario = parseFloat(document.getElementById('presupuestoMaximo').value) || 50000;

    // Verificar que todos los materiales estén seleccionados
    const materialesCompletos = Object.values(materiales).every(material => material && material !== '');
    const totalAnimales = Object.values(animales).reduce((a, b) => a + b, 0);

    if (!materialesCompletos || totalAnimales === 0) {
        document.getElementById('resultadoPresupuestoInteligente').style.display = 'none';
        return;
    }

    // Llamar al backend para calcular presupuesto inteligente
    fetch('/api/calcular_presupuesto_inteligente', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            animales: animales,
            materiales: materiales,
            presupuesto_usuario: presupuestoUsuario
        })
    })
    .then(response => response.json())
    .then(data => {
        mostrarResultadoPresupuestoInteligente(data);
    })
    .catch(error => {
        console.error('Error calculando presupuesto inteligente:', error);
    });
}

// NUEVA FUNCIÓN: Mostrar resultado del presupuesto inteligente
function mostrarResultadoPresupuestoInteligente(data) {
    const resultadoDiv = document.getElementById('resultadoPresupuestoInteligente');
    const alertaDiv = document.getElementById('alertaPresupuesto');

    // Mostrar valores
    document.getElementById('costoEstimadoShow').textContent = '$' + data.costo_estimado.toLocaleString('es-MX');
    document.getElementById('minimoRecomendadoShow').textContent = '$' + data.presupuesto_minimo_recomendado.toLocaleString('es-MX');

    // Configurar mensaje y estilo según si es suficiente
    const mensajeDiv = document.getElementById('mensajePresupuesto');

    if (data.es_suficiente) {
        alertaDiv.className = 'border rounded p-3 mt-3 border-success bg-light';
        mensajeDiv.innerHTML = `
            <i class="fas fa-check-circle text-success me-2"></i>
            <span class="text-success">Presupuesto suficiente</span><br>
            <small>Presupuesto efectivo para el AG: $${data.presupuesto_efectivo.toLocaleString('es-MX')}</small>
        `;
    } else {
        alertaDiv.className = 'border rounded p-3 mt-3 border-warning bg-warning bg-opacity-10';
        mensajeDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle text-warning me-2"></i>
            <span class="text-warning">Se recomienda aumentar presupuesto</span><br>
            <small>Diferencia: $${data.diferencia.toLocaleString('es-MX')} adicionales</small><br>
            <small class="text-muted">El AG usará $${data.presupuesto_efectivo.toLocaleString('es-MX')} como límite</small>
        `;
    }

    resultadoDiv.style.display = 'block';
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

function actualizarPesosSimplificados() {
    const pesoTerreno = parseInt(document.getElementById('peso_terreno').value);
    const pesoManejo = parseInt(document.getElementById('peso_manejo').value);

    // Actualizar labels con valores actuales (SIN NORMALIZAR)
    document.getElementById('valor_peso_terreno').textContent = pesoTerreno + '%';
    document.getElementById('valor_peso_manejo').textContent = pesoManejo + '%';

    // Calcular total para mostrar información
    const total = pesoTerreno + pesoManejo;
    document.getElementById('totalPesos').textContent = total + '%';

    // QUITAR la validación restrictiva y cambiar el mensaje
    const alertaDiv = document.querySelector('.alert-info');
    if (alertaDiv) {
        alertaDiv.innerHTML = `
            <i class="fas fa-info-circle me-2"></i>
            Total actual: <span id="totalPesos">${total}%</span>
            <br><small>Los valores se normalizan automáticamente en el algoritmo (no es necesario que sumen 100%)</small>
        `;
    }
}

function recopilarConfiguracion() {
    // Recopilar todos los datos del formulario (SIMPLIFICADO)
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
        // SOLO 2 OBJETIVOS
        objetivos: {
            aprovechamiento_terreno: parseInt(document.getElementById('peso_terreno').value) / 100,
            eficiencia_manejo: parseInt(document.getElementById('peso_manejo').value) / 100
        },
        algoritmo: {
            poblacion: parseInt(document.getElementById('tamañoPoblacion').value),
            generaciones: parseInt(document.getElementById('numeroGeneraciones').value),
            mutacion: parseFloat(document.getElementById('probabilidadMutacion').value),
            cruza: 0.9,
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

    // Validar que todos los materiales estén seleccionados
    for (const [especie, cantidad] of Object.entries(config.animales)) {
        if (cantidad > 0 && (!config.materiales[especie] || config.materiales[especie] === '')) {
            alert(`Debe seleccionar un material para ${especie}.`);
            return false;
        }
    }

    // NUEVA VALIDACIÓN: Solo verificar que al menos un objetivo tenga valor > 0
    const sumaObjetivos = config.objetivos.aprovechamiento_terreno + config.objetivos.eficiencia_manejo;
    if (sumaObjetivos <= 0) {
        alert('Al menos un objetivo debe tener un valor mayor que 0.');
        return false;
    }

    // QUITAR COMPLETAMENTE la validación de que sume 100%
    // El sistema normaliza automáticamente los pesos

    return true;
}

function resetearProgreso() {
    document.getElementById('progresoGeneraciones').style.width = '0%';
    document.getElementById('generacionActual').textContent = 'Generación 0';
    document.getElementById('tiempoTranscurrido').textContent = '0s';
    document.getElementById('mejorFitness').textContent = '0.0000';
    document.getElementById('fitnessPromedio').textContent = '0.0000';

    // NUEVO: Resetear métricas de objetivos simplificados
    document.getElementById('aprovechamientoTerreno').textContent = '0.0000';
    document.getElementById('eficienciaManejo').textContent = '0.0000';
    document.getElementById('statusPresupuesto').textContent = 'OK';

    document.getElementById('mensajeProgreso').textContent = 'Iniciando optimización con sistema simplificado...';
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
    }, 1000);
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

    // NUEVO: Actualizar métricas específicas si están disponibles
    if (data.metricas_objetivos) {
        document.getElementById('aprovechamientoTerreno').textContent =
            (data.metricas_objetivos.aprovechamiento_terreno || 0).toFixed(4);
        document.getElementById('eficienciaManejo').textContent =
            (data.metricas_objetivos.eficiencia_manejo || 0).toFixed(4);
    }

    // Actualizar estado del presupuesto
    if (data.dentro_presupuesto !== undefined) {
        document.getElementById('statusPresupuesto').textContent = data.dentro_presupuesto ? 'OK' : 'EXCESO';
        document.getElementById('statusPresupuesto').className = data.dentro_presupuesto ? 'text-success' : 'text-danger';
    }

    document.getElementById('mensajeProgreso').textContent = data.mensaje;
}

function finalizarOptimizacion(data) {
    const modal = bootstrap.Modal.getInstance(document.getElementById('modalProgreso'));

    setTimeout(() => {
        modal.hide();

        if (data.estado === 'completado') {
            window.location.href = '/resultados';
        } else {
            alert('Error en la optimización: ' + data.mensaje);
        }
    }, 2000);
}

// Funciones auxiliares
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

// Configuraciones predeterminadas para sistema simplificado
function aplicarConfiguracionRapida() {
    document.getElementById('tamañoPoblacion').value = 50;
    document.getElementById('numeroGeneraciones').value = 100;
    document.getElementById('probabilidadMutacion').value = 0.2;

    // Configurar pesos para optimización rápida (más terreno)
    document.getElementById('peso_terreno').value = 70;
    document.getElementById('peso_manejo').value = 30;
    actualizarPesosSimplificados();

    animarElemento(document.getElementById('configAvanzada'));
}

function aplicarConfiguracionCompleta() {
    document.getElementById('tamañoPoblacion').value = 100;
    document.getElementById('numeroGeneraciones').value = 500;
    document.getElementById('probabilidadMutacion').value = 0.1;

    // Configurar pesos balanceados
    document.getElementById('peso_terreno').value = 60;
    document.getElementById('peso_manejo').value = 40;
    actualizarPesosSimplificados();

    animarElemento(document.getElementById('configAvanzada'));
}

// Exportar funciones para uso global
window.aplicarConfiguracionRapida = aplicarConfiguracionRapida;
window.aplicarConfiguracionCompleta = aplicarConfiguracionCompleta;