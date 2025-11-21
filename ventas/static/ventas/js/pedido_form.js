// ventas/static/ventas/js/pedido_form.js
document.addEventListener('DOMContentLoaded', function () {
    let formCount = window.formsetTotalForms || 0;
    const emptyFormContainer = document.getElementById('empty-form');
    let currentDetalleRow = null;

    // === Función para crear una nueva línea ===
    function createNewLine(detalleData = null) {
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

        //ESTABLECER VALORES SI SE PROPORCIONAN
        if (detalleData) {
            // Esperar a que los elementos estén disponibles
            setTimeout(() => {
                const materialNombre = newRow.querySelector('.material-nombre');
                const materialSelect = newRow.querySelector('select[name$="material"]');
                const cantidadInput = newRow.querySelector('.cantidad-input');
                const precioInput = newRow.querySelector('.precio-input');
                const descuentoInput = newRow.querySelector('.descuento-input');

                if (materialNombre) materialNombre.value = detalleData.material_nombre;
                if (materialSelect) materialSelect.value = detalleData.material_id;
                if (cantidadInput) cantidadInput.value = detalleData.cantidad;
                if (precioInput) precioInput.value = detalleData.precio_unitario;
                if (descuentoInput) descuentoInput.value = detalleData.descuento;
            }, 0);
        } else {
            // Si no hay datos, establecer valores por defecto
            setTimeout(() => {
                const descuentoInput = newRow.querySelector('.descuento-input');
                if (descuentoInput) descuentoInput.value = '0';

                const cantidadInput = newRow.querySelector('.cantidad-input');
                if (cantidadInput) cantidadInput.value = '1';

                const precioInput = newRow.querySelector('.precio-input');
                if (precioInput) precioInput.value = '0.00';
            }, 0);
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

            // ✅ CARGAR COTIZACIONES DEL CLIENTE SELECCIONADO
            cargarCotizacionesCliente(id);

            bootstrap.Modal.getInstance(document.getElementById('modalClientes')).hide();
        });
    });

    // === Cargar cotizaciones por cliente (AJAX) ===
    function cargarCotizacionesCliente(clienteId) {
        fetch(`/ventas/pedidos/cotizaciones-cliente/?cliente_id=${clienteId}`)
            .then(response => response.json())
            .then(data => {
                const tbody = document.getElementById('cotizacionesTableBody');
                tbody.innerHTML = ''; // Limpiar tabla

                data.cotizaciones.forEach(cot => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${cot.folio}</td>
                        <td>${cot.cliente_nombre}</td>
                        <td>${cot.fecha}</td>
                        <td>$${cot.total.toFixed(2)}</td>
                        <td>
                            <button class="btn btn-sm btn-primary select-cotizacion"
                                data-id="${cot.id}"
                                data-nombre="${cot.folio}">
                                Seleccionar
                            </button>
                        </td>
                    `;
                    tbody.appendChild(row);
                });
            })
            .catch(error => console.error('Error:', error));
    }
    // ventas/static/ventas/js/pedido_form.js

    // === Cargar detalles de cotización ===
    function cargarDetallesCotizacion(cotizacionId) {
        fetch(`/ventas/cotizaciones/${cotizacionId}/detalles/`)
            .then(response => response.json())
            .then(data => {
                // Limpiar líneas existentes
                const detallesContainer = document.getElementById('detalles-container');
                detallesContainer.innerHTML = '';

                // Agregar cada detalle como una nueva línea con datos
                data.detalles.forEach((detalle, index) => {
                    const newRow = createNewLine(detalle);  //Pasar datos
                    if (newRow) {
                        detallesContainer.appendChild(newRow);
                    }
                });

                updateManagementForm();
            })
            .catch(error => console.error('Error al cargar detalles:', error));
    }

    // === Cotizaciones ===
    // Delegar evento para botones dinámicos
    document.getElementById('cotizacionesTableBody').addEventListener('click', function(e) {
        if (e.target.classList.contains('select-cotizacion')) {
            const id = e.target.dataset.id;
            const nombre = e.target.dataset.nombre;

            document.getElementById('cotizacion_display').value = nombre;
            document.querySelector('select[name="cotizacion"]').value = id;

            //CARGAR DETALLES DE LA COTIZACIÓN SELECCIONADA
            cargarDetallesCotizacion(id);

            bootstrap.Modal.getInstance(document.getElementById('modalCotizaciones')).hide();
        }
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