document.addEventListener('DOMContentLoaded', function () {
    // Obtiene el número inicial de formularios
    let formCount = window.formsetTotalForms || 0;
    const emptyFormContainer = document.getElementById('empty-form');
    let currentDetalleIndex = null;

    // === Función para crear una nueva línea ===
    function createNewLine() {
        if (!emptyFormContainer) {
            console.error("No se encontró el contenedor #empty-form");
            return null;
        }

        // Clonar y reemplazar __prefix__ por el índice actual
        const newHtml = emptyFormContainer.innerHTML.replace(/__prefix__/g, formCount);
        const newRow = document.createElement('div');
        newRow.className = 'detalle-row border p-3 mb-3 rounded';
        newRow.innerHTML = newHtml;

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
                const allRows = Array.from(document.querySelectorAll('.detalle-row'));
                currentDetalleIndex = allRows.indexOf(newRow);
            });
        }

        // Limpiar campos de la nueva fila
        newRow.querySelectorAll('input[type="text"], input[type="number"]').forEach(input => {
            if (!input.hasAttribute('readonly')) {
                input.value = '';
            }
        });
        const materialSelect = newRow.querySelector('select[name$="material"]');
        if (materialSelect) materialSelect.value = '';

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

    // === Materiales ===
    document.querySelectorAll('[data-bs-toggle="modal"]').forEach(btn => {
        btn.addEventListener('click', function() {
            // Encontrar la fila padre
            const row = this.closest('.detalle-row');
            if (row) {
                window.currentDetalleRow = row;
            }
        });
    });

    document.querySelectorAll('.select-material').forEach(button => {
        button.addEventListener('click', function () {
            if (!window.currentDetalleRow) return;

            const id = this.dataset.id;
            const nombre = this.dataset.nombre;

            const nombreInput = window.currentDetalleRow.querySelector('.material-nombre');
            const selectMaterial = window.currentDetalleRow.querySelector('select[name$="material"]');

            if (nombreInput) nombreInput.value = nombre;
            if (selectMaterial) selectMaterial.value = id;

            bootstrap.Modal.getInstance(document.getElementById('modalMateriales')).hide();
            window.currentDetalleRow = null;
        });
    });

    // === Búsqueda en modales ===
    document.getElementById('searchCliente').addEventListener('input', function () {
        const query = this.value.toLowerCase();
        document.querySelectorAll('#clientesTableBody tr').forEach(row => {
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