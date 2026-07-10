document.addEventListener('DOMContentLoaded', function () {
    let formCount = window.formsetTotalForms || document.querySelectorAll('.detalle-row').length;

    // === Función para crear nueva línea ===
    function createNewLine() {
        const emptyFormContainer = document.getElementById('empty-form');
        if (!emptyFormContainer) {
            console.error("No se encontró el contenedor #empty-form");
            return null;
        }

        const newHtml = emptyFormContainer.innerHTML.replace(/__prefix__/g, formCount);
        const newRow = document.createElement('div');
        newRow.className = 'detalle-row border p-3 mb-3 rounded';
        newRow.innerHTML = newHtml;

        // Restablecer valores por defecto
        const descuentoInput = newRow.querySelector('.descuento-input');
        if (descuentoInput) descuentoInput.value = '0';

        const cantidadInput = newRow.querySelector('.cantidad-input');
        if (cantidadInput) cantidadInput.value = '1';

        const precioInput = newRow.querySelector('.precio-input');
        if (precioInput) precioInput.value = '0.00';

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

    // === Variables globales para seguimiento ===
    let currentActiveRow = null;

    // === Evento: Modal de materiales abierto ===
    document.getElementById('modalMateriales').addEventListener('shown.bs.modal', function (event) {
        // Encontrar el botón que abrió el modal
        const button = event.relatedTarget;
        // Encontrar la fila padre
        currentActiveRow = button.closest('.detalle-row');
    });

    // === Evento: Modal de materiales cerrado ===
    document.getElementById('modalMateriales').addEventListener('hidden.bs.modal', function () {
        currentActiveRow = null;
    });

    // === Selección de material ===
    document.getElementById('modalMateriales').addEventListener('click', function(e) {
        if (e.target.classList.contains('select-material')) {
            if (!currentActiveRow) {
                console.warn("No hay fila activa seleccionada");
                return;
            }

            const id = e.target.dataset.id;
            const nombre = e.target.dataset.nombre;

            const nombreInput = currentActiveRow.querySelector('.material-nombre');
            const selectMaterial = currentActiveRow.querySelector('select[name$="material"]');

            if (nombreInput) nombreInput.value = nombre;
            if (selectMaterial) selectMaterial.value = id;

            // Cerrar modal
            bootstrap.Modal.getInstance(this).hide();
        }
    });

    // === Clientes (opcional, mismo patrón) ===
    let currentActiveClient = null;

    document.getElementById('modalClientes').addEventListener('shown.bs.modal', function (event) {
        currentActiveClient = true; // Solo necesitamos saber que está abierto
    });

    document.getElementById('modalClientes').addEventListener('click', function(e) {
        if (e.target.classList.contains('select-cliente')) {
            const id = e.target.dataset.id;
            const nombre = e.target.dataset.nombre;

            document.getElementById('cliente_display').value = nombre;
            document.querySelector('select[name="cliente"]').value = id;

            bootstrap.Modal.getInstance(this).hide();
        }
    });

    // === Agregar línea ===
    document.getElementById('add-line')?.addEventListener('click', function () {
        const newRow = createNewLine();
        if (newRow) {
            document.getElementById('detalles-container').appendChild(newRow);
            updateManagementForm();
        }
    });

    // === Eliminar líneas ===
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('remove-line')) {
            const row = e.target.closest('.detalle-row');
            if (row) {
                row.remove();
                formCount--;
                updateManagementForm();
            }
        }
    });

    // === Búsqueda en modales ===
    document.getElementById('searchCliente')?.addEventListener('input', function () {
        const query = this.value.toLowerCase();
        document.querySelectorAll('#clientesTableBody tr').forEach(row => {
            row.style.display = row.textContent.toLowerCase().includes(query) ? '' : 'none';
        });
    });

    document.getElementById('searchMaterial')?.addEventListener('input', function () {
        const query = this.value.toLowerCase();
        document.querySelectorAll('#materialesTableBody tr').forEach(row => {
            row.style.display = row.textContent.toLowerCase().includes(query) ? '' : 'none';
        });
    });

    // Inicializar
    updateManagementForm();
});