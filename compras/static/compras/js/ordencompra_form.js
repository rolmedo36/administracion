document.addEventListener('DOMContentLoaded', function () {
    // =============== CONFIGURACIÓN INICIAL ===============
    let formCount = parseInt(document.getElementById('id_detalles-TOTAL_FORMS').value);
    const emptyFormContainer = document.getElementById('empty-form');
    let currentDetalleIndex = null;
    const materialesData = window.materialesData || {};

    // =============== FUNCIONES DE CÁLCULO ===============
    function calcularPrecios(row) {
        const precioBaseInput = row.querySelector('.precio-base');
        const precioIvaInput = row.querySelector('.precio-con-iva');
        const aplicaIvaInput = row.querySelector('input[name$="aplica_iva"]');

        if (!precioBaseInput || !precioIvaInput || !aplicaIvaInput) return;

        const precioBase = parseFloat(precioBaseInput.value) || 0;
        const aplicaIva = aplicaIvaInput.value === 'true';
        const precioConIva = aplicaIva ? precioBase * 1.16 : precioBase;

        precioIvaInput.value = precioConIva.toFixed(2);
        calcularSubtotal(row);
    }

    function calcularSubtotal(row) {
        const cantidadInput = row.querySelector('input[name$="cantidad"]');
        const precioIvaInput = row.querySelector('.precio-con-iva');
        const subtotalInput = row.querySelector('input[name$="subtotal"]');

        if (!cantidadInput || !precioIvaInput || !subtotalInput) return;

        const cantidad = parseFloat(cantidadInput.value) || 0;
        const precioIva = parseFloat(precioIvaInput.value) || 0;
        const subtotal = cantidad * precioIva;

        subtotalInput.value = subtotal.toFixed(2);
    }

    // =============== FUNCIONES AUXILIARES ===============
    function updateManagementForm() {
        document.getElementById('id_detalles-TOTAL_FORMS').value = formCount;
    }

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
        const precioConIvaInput = newRow.querySelector('.precio-con-iva');
        if (precioConIvaInput) precioConIvaInput.value = '0.00';
        const materialSelect = newRow.querySelector('select[name$="material"]');
        if (materialSelect) materialSelect.value = '';
        const aplicaIvaInput = newRow.querySelector('input[name$="aplica_iva"]');
        if (aplicaIvaInput) aplicaIvaInput.value = 'false';

        // Configurar eventos de cálculo
        const precioBaseInput = newRow.querySelector('.precio-base');
        if (precioBaseInput) {
            precioBaseInput.addEventListener('input', function() {
                calcularPrecios(newRow);
            });
        }
        const cantidadInput = newRow.querySelector('input[name$="cantidad"]');
        if (cantidadInput) {
            cantidadInput.addEventListener('input', function() {
                calcularSubtotal(newRow);
            });
        }

        document.getElementById('detalles-container').appendChild(newRow);
        formCount++;
        updateManagementForm();
    }

    // =============== EVENTOS ===============
    const addLineBtn = document.getElementById('add-line');
    if (addLineBtn) {
        addLineBtn.addEventListener('click', addNewLine);
    }

    // Eliminar filas existentes
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
            const aplicaIvaInput = row.querySelector('input[name$="aplica_iva"]');

            if (nombreInput) nombreInput.value = nombre;
            if (selectMaterial) selectMaterial.value = id;

            // Actualizar aplica_iva y recalcular
            if (aplicaIvaInput && materialesData[id]) {
                aplicaIvaInput.value = materialesData[id].aplica_iva ? 'true' : 'false';
                calcularPrecios(row);
            }

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

    // === INICIALIZAR CÁLCULOS EN FILAS EXISTENTES ===
    document.querySelectorAll('.detalle-row').forEach(row => {
        const precioBaseInput = row.querySelector('.precio-base');
        if (precioBaseInput) {
            precioBaseInput.addEventListener('input', function() {
                calcularPrecios(row);
            });
            // Calcular inicial
            calcularPrecios(row);
        }
        const cantidadInput = row.querySelector('input[name$="cantidad"]');
        if (cantidadInput) {
            cantidadInput.addEventListener('input', function() {
                calcularSubtotal(row);
            });
        }
        calcularPrecios(row);
    });
});