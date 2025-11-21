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

        const ivaInput = newRow.querySelector('.iva-porcentaje-input');
        if (ivaInput) {
            ivaInput.value = '16.00';
        }

        const cantidadInput = newRow.querySelector('.cantidad-input');
        if (cantidadInput) {
            cantidadInput.value = '1.00';
        }

        const precioInput = newRow.querySelector('.precio-unitario-input');
        if (precioInput) {
            precioInput.value = '0.00';
        }

        // ✅ CONFIGURAR CALCULO AUTOMATICO
        configurarCalculo(newRow);

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

    // === Pedidos ===
    document.querySelectorAll('.select-pedido').forEach(button => {
        button.addEventListener('click', function () {
            const id = this.dataset.id;
            const nombre = this.dataset.nombre;

            document.getElementById('pedido_display').value = nombre;
            document.querySelector('select[name="pedido"]').value = id;

            bootstrap.Modal.getInstance(document.getElementById('modalPedidos')).hide();
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

    document.getElementById('searchPedido').addEventListener('input', function () {
        const query = this.value.toLowerCase();
        document.querySelectorAll('#pedidosTableBody tr').forEach(row => {
            row.style.display = row.textContent.toLowerCase().includes(query) ? '' : 'none';
        });
    });

    document.getElementById('searchMaterial').addEventListener('input', function () {
        const query = this.value.toLowerCase();
        document.querySelectorAll('#materialesTableBody tr').forEach(row => {
            row.style.display = row.textContent.toLowerCase().includes(query) ? '' : 'none';
        });
    });

    // === Función para calcular el subtotal de una línea ===
    function calcularSubtotal(detalleRow) {
        const cantidadInput = detalleRow.querySelector('.cantidad-input');
        const precioInput = detalleRow.querySelector('.precio-unitario-input');
        const descuentoInput = detalleRow.querySelector('.descuento-input');
        const ivaInput = detalleRow.querySelector('.iva-porcentaje-input');
        const subtotalDisplay = detalleRow.querySelector('.subtotal-display');

        if (!cantidadInput || !precioInput || !descuentoInput || !subtotalDisplay) return;

        const cantidad = parseFloat(cantidadInput.value) || 0;
        const precio = parseFloat(precioInput.value) || 0;
        const descuento = parseFloat(descuentoInput.value) || 0;
        const ivaPorcentaje = parseFloat(ivaInput.value) || 0;

        // Calcular subtotal con descuento
        const subtotalConDescuento = cantidad * precio * (1 - descuento / 100);

        // Calcular IVA
        const ivaMonto = subtotalConDescuento * (ivaPorcentaje / 100);

        // Total de la línea = subtotal con descuento + IVA
        const totalLinea = subtotalConDescuento + ivaMonto;

        subtotalDisplay.value = totalLinea.toFixed(2);
    }

    // === Configurar eventos de cálculo en cada línea ===
    function configurarCalculo(detalleRow) {
        const inputs = [
            detalleRow.querySelector('.cantidad-input'),
            detalleRow.querySelector('.precio-unitario-input'),
            detalleRow.querySelector('.descuento-input'),
            detalleRow.querySelector('.iva-porcentaje-input')
        ];

        inputs.forEach(input => {
            if (input) {
                input.addEventListener('input', function() {
                    calcularSubtotal(detalleRow);
                });
            }
        });
    }

    // === Configurar cálculo para líneas existentes ===
    document.querySelectorAll('.detalle-row').forEach(row => {
        configurarCalculo(row);
    });

    // === Configurar cálculo para nuevas líneas ===
    document.addEventListener('DOMNodeInserted', function(e) {
        if (e.target.classList.contains('detalle-row')) {
            configurarCalculo(e.target);
        }
    }, false);
});