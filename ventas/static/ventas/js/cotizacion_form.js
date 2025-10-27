document.addEventListener('DOMContentLoaded', function () {
    let formCount = window.formsetTotalForms || 0;
    const emptyFormContainer = document.getElementById('empty-form');
    let currentDetalleIndex = null;

    // === Función para agregar nueva línea ===
    function addNewLine() {
        if (!emptyFormContainer) {
            console.error("No se encontró el contenedor #empty-form");
            return;
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
                const allRows = Array.from(document.querySelectorAll('.detalle-row'));
                currentDetalleIndex = allRows.indexOf(newRow);
            });
        }

        // Limpiar campos
        newRow.querySelectorAll('input[type="text"], input[type="number"]').forEach(input => {
            if (!input.hasAttribute('readonly')) {
                input.value = '';
            }
        });
        const materialSelect = newRow.querySelector('select[name$="material"]');
        if (materialSelect) materialSelect.value = '';

        document.getElementById('detalles-container').appendChild(newRow);
        formCount++;
        updateManagementForm();
    }

    // === Actualizar management form ===
    function updateManagementForm() {
        document.getElementById('id_detalles-TOTAL_FORMS').value = formCount;
    }

    // === Botón para agregar línea ===
    const addLineBtn = document.getElementById('add-line');
    if (addLineBtn) {
        addLineBtn.addEventListener('click', addNewLine);
    }

    // === Eliminar líneas existentes ===
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
    document.getElementById('modalMateriales').addEventListener('show.bs.modal', function (event) {
        const button = event.relatedTarget;
        currentDetalleIndex = button.dataset.detalleIndex;
    });

    document.querySelectorAll('.select-material').forEach(button => {
        button.addEventListener('click', function () {
            const id = this.dataset.id;
            const nombre = this.dataset.nombre;

            if (currentDetalleIndex === null) return;

            const detalleRow = document.querySelectorAll('.detalle-row')[currentDetalleIndex];
            detalleRow.querySelector('.material-nombre').value = nombre;
            detalleRow.querySelector('select[name$="material"]').value = id;

            bootstrap.Modal.getInstance(document.getElementById('modalMateriales')).hide();
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