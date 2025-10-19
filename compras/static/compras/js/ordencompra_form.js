document.addEventListener('DOMContentLoaded', function () {
    // =============== CONFIGURACIÓN INICIAL ===============
    let formCount = parseInt(document.getElementById('id_detalles-TOTAL_FORMS').value);
    const emptyFormContainer = document.getElementById('empty-form');
    let currentDetalleIndex = null;

    // =============== FUNCIONES AUXILIARES ===============
    function updateManagementForm() {
        document.getElementById('id_detalles-TOTAL_FORMS').value = formCount;
    }

    function addNewLine() {
        if (!emptyFormContainer) {
            console.error("No se encontró el contenedor #empty-form");
            return;
        }

        // Clonar y reemplazar __prefix__ por el índice actual
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
                // Encontrar el índice de esta fila
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

        // Agregar al DOM
        document.getElementById('detalles-container').appendChild(newRow);
        formCount++;
        updateManagementForm();
    }

    // =============== EVENTOS ===============
    // Botón "Agregar línea"
    const addLineBtn = document.getElementById('add-line');
    if (addLineBtn) {
        addLineBtn.addEventListener('click', addNewLine);
    }

    // Eliminar filas existentes (al cargar la página)
    document.querySelectorAll('.remove-line').forEach(btn => {
        btn.addEventListener('click', function () {
            this.closest('.detalle-row').remove();
            formCount--;
            updateManagementForm();
        });
    });

    // === PROVEEDORES ===
    document.querySelectorAll('.select-proveedor').forEach(button => {
        button.addEventListener('click', function () {
            const id = this.dataset.id;
            const nombre = this.dataset.nombre;
            const display = document.getElementById('proveedor_display');
            const select = document.querySelector('select[name="proveedor"]');

            if (display) display.value = nombre;
            if (select) select.value = id;

            const modal = bootstrap.Modal.getInstance(document.getElementById('modalProveedores'));
            if (modal) modal.hide();
        });
    });

    // === MATERIALES ===
    const modalMateriales = document.getElementById('modalMateriales');
    if (modalMateriales) {
        modalMateriales.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            const row = button.closest('.detalle-row');
            if (row) {
                const allRows = Array.from(document.querySelectorAll('.detalle-row'));
                currentDetalleIndex = allRows.indexOf(row);
            } else {
                currentDetalleIndex = null;
            }
        });
    }

    document.querySelectorAll('.select-material').forEach(button => {
        button.addEventListener('click', function () {
            if (currentDetalleIndex === null) return;

            const id = this.dataset.id;
            const nombre = this.dataset.nombre;
            const allRows = document.querySelectorAll('.detalle-row');

            if (currentDetalleIndex >= allRows.length) return;

            const row = allRows[currentDetalleIndex];
            const nombreInput = row.querySelector('.material-nombre');
            const selectMaterial = row.querySelector('select[name$="material"]');

            if (nombreInput) nombreInput.value = nombre;
            if (selectMaterial) selectMaterial.value = id;

            const modal = bootstrap.Modal.getInstance(document.getElementById('modalMateriales'));
            if (modal) modal.hide();
        });
    });

    // === BÚSQUEDA EN MODALES ===
    const searchProveedor = document.getElementById('searchProveedor');
    if (searchProveedor) {
        searchProveedor.addEventListener('input', function () {
            const query = this.value.toLowerCase();
            document.querySelectorAll('#proveedoresTableBody tr').forEach(row => {
                row.style.display = row.textContent.toLowerCase().includes(query) ? '' : 'none';
            });
        });
    }

    const searchMaterial = document.getElementById('searchMaterial');
    if (searchMaterial) {
        searchMaterial.addEventListener('input', function () {
            const query = this.value.toLowerCase();
            document.querySelectorAll('#materialesTableBody tr').forEach(row => {
                row.style.display = row.textContent.toLowerCase().includes(query) ? '' : 'none';
            });
        });
    }
});