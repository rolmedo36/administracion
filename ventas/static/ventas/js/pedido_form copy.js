// ventas/static/ventas/js/pedido_form.js
document.addEventListener('DOMContentLoaded', function () {
    let formCount = window.formsetTotalForms || 0;
    const emptyFormContainer = document.getElementById('empty-form');
    let currentDetalleRow = null;

    // === Función para crear una nueva línea ===
    function createNewLine() {
        if (!emptyFormContainer) {
            console.error("No se encontró el contenedor #empty-form");
            return null;
        }

        const newHtml = emptyFormContainer.innerHTML.replace(/__prefix__/g, formCount);
        const newRow = document.createElement('div');
        newRow.className = 'detalle-row border p-3 mb-3 rounded';
        newRow.innerHTML = newHtml;

        // Configurar botón de eliminar
        const removeBtn = newRow.querySelector('.remove-line');
        if (removeBtn) {
            removeBtn.addEventListener('click', function () {
                newRow.remove();
                formCount--;
                updateManagementForm();
            });
        }

        // Configurar botón de búsqueda de material
        const searchBtn = newRow.querySelector('[data-bs-toggle="modal"]');
        if (searchBtn) {
            searchBtn.addEventListener('click', function () {
                currentDetalleRow = this.closest('.detalle-row');
            });
        }

        // FORZAR VALORES POR DEFECTO
        const descuentoInput = newRow.querySelector('.descuento-input');
        if (descuentoInput) {
            descuentoInput.value = '0';
        }

        const cantidadInput = newRow.querySelector('.cantidad-input');
        if (cantidadInput) {
            cantidadInput.value = '1';
        }

        const precioInput = newRow.querySelector('.precio-input');
        if (precioInput) {
            precioInput.value = '0.00';
        }

        formCount++;
        return newRow;
    }

    // === Actualizar management form ===
    function updateManagementForm() {
        const totalFormsInput = document.getElementById('id_detalles-TOTAL_FORMS');
        if (totalFormsInput) {
            totalFormsInput.value = formCount;
        }
    }

    // === Filtrar cotizaciones por cliente ===
    function filtrarCotizacionesPorCliente(clienteId) {
        // Ocultar todas las cotizaciones
        document.querySelectorAll('#cotizacionesTableBody tr').forEach(row => {
            row.style.display = 'none';
        });

        // Mostrar solo las del cliente seleccionado
        if (clienteId) {
            document.querySelectorAll('#cotizacionesTableBody tr').forEach(row => {
                const cotizacionClienteId = row.querySelector('button').dataset.clienteId;
                if (cotizacionClienteId === clienteId) {
                    row.style.display = '';
                }
            });
        } else {
            // Si no hay cliente seleccionado, mostrar todas
            document.querySelectorAll('#cotizacionesTableBody tr').forEach(row => {
                row.style.display = '';
            });
        }
    }

    // === Actualizar modal de cotizaciones al seleccionar cliente ===
    document.getElementById('modalClientes').addEventListener('hidden.bs.modal', function () {
        const clienteId = document.querySelector('select[name="cliente"]').value;
        filtrarCotizacionesPorCliente(clienteId);
    });

    // === Agregar data-cliente-id a los botones de cotizaciones ===
    // (Esto se hará en la plantilla)

    // === Evento: Agregar línea ===
    const addLineBtn = document.getElementById('add-line');
    if (addLineBtn) {
        addLineBtn.addEventListener('click', function () {
            const newRow = createNewLine();
            if (newRow) {
                document.getElementById('detalles-container').appendChild(newRow);
                updateManagementForm();
            }
        });
    }

    // === Configurar eliminación para filas existentes ===
    document.querySelectorAll('.remove-line').forEach(btn => {
        btn.addEventListener('click', function () {
            this.closest('.detalle-row').remove();
            formCount--;
            updateManagementForm();
        });
    });

    // === Clientes ===
    document.querySelectorAll('.select-cliente').forEach(button => {
        button.addEventListener('click', function () {
            const id = this.dataset.id;
            const nombre = this.dataset.nombre;

            document.getElementById('cliente_display').value = nombre;
            document.querySelector('select[name="cliente"]').value = id;

            bootstrap.Modal.getInstance(document.getElementById('modalClientes')).hide();
        });
    });

    // === Cotizaciones ===
    document.querySelectorAll('.select-cotizacion').forEach(button => {
        button.addEventListener('click', function () {
            const id = this.dataset.id;
            const nombre = this.dataset.nombre;

            document.getElementById('cotizacion_display').value = nombre;
            document.querySelector('select[name="cotizacion"]').value = id;

            bootstrap.Modal.getInstance(document.getElementById('modalCotizaciones')).hide();
        });
    });

    // === Materiales ===
    document.querySelectorAll('[data-bs-toggle="modal"]').forEach(btn => {
        btn.addEventListener('click', function() {
            currentDetalleRow = this.closest('.detalle-row');
        });
    });

    document.querySelectorAll('.select-material').forEach(button => {
        button.addEventListener('click', function () {
            if (!currentDetalleRow) return;

            const id = this.dataset.id;
            const nombre = this.dataset.nombre;

            const nombreInput = currentDetalleRow.querySelector('.material-nombre');
            const selectMaterial = currentDetalleRow.querySelector('select[name$="material"]');

            if (nombreInput) nombreInput.value = nombre;
            if (selectMaterial) selectMaterial.value = id;

            bootstrap.Modal.getInstance(document.getElementById('modalMateriales')).hide();
            currentDetalleRow = null;
        });
    });

    // === Búsqueda en modales ===
    document.getElementById('searchCliente').addEventListener('input', function () {
        const query = this.value.toLowerCase();
        document.querySelectorAll('#clientesTableBody tr').forEach(row => {
            row.style.display = row.textContent.toLowerCase().includes(query) ? '' : 'none';
        });
    });

    document.getElementById('searchCotizacion').addEventListener('input', function () {
        const query = this.value.toLowerCase();
        document.querySelectorAll('#cotizacionesTableBody tr').forEach(row => {
            row.style.display = row.textContent.toLowerCase().includes(query) ? '' : 'none';
        });
    });

    document.getElementById('searchMaterial').addEventListener('input', function () {
        const query = this.value.toLowerCase();
        document.querySelectorAll('#materialesTableBody tr').forEach(row => {
            row.style.display = row.textContent.toLowerCase().includes(query) ? '' : 'none';
        });
    });
});
