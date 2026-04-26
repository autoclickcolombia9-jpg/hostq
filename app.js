const API_URL = '/api';

// Utilidades para formatear moneda
const formatter = new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    minimumFractionDigits: 2
});

// Variables globales para la tienda
let currentTiendaId = null;
let inventarioLocal = [];
let carrito = [];
let html5QrcodeScanner = null;
let scanning = false;

// --- FUNCIONES DEL ADMIN ---
async function loadAdminData() {
    try {
        const invRes = await fetch(`${API_URL}/inventario`);
        const inventario = await invRes.json();
        
        let totalItems = 0;
        let totalValue = 0;
        const invBody = document.getElementById('admin-inventario-body');
        if(!invBody) return; // Not on admin page
        
        invBody.innerHTML = '';

        inventario.forEach(item => {
            totalItems += item.cantidad;
            totalValue += item.cantidad * item.precio;
            
            invBody.innerHTML += `
                <tr>
                    <td><strong>${item.tienda}</strong></td>
                    <td>${item.sku}</td>
                    <td>${item.producto}</td>
                    <td>${item.cantidad}</td>
                    <td>${formatter.format(item.precio)}</td>
                </tr>
            `;
        });

        document.getElementById('admin-total-items').innerText = totalItems;
        document.getElementById('admin-total-value').innerText = formatter.format(totalValue);

        const finRes = await fetch(`${API_URL}/finanzas`);
        const finanzas = await finRes.json();
        const finBody = document.getElementById('admin-finanzas-body');
        finBody.innerHTML = '';

        finanzas.forEach(f => {
            const date = new Date(f.fecha).toLocaleString('es-ES');
            const badgeClass = f.tipo === 'Ingreso' ? 'badge-ingreso' : 'badge-gasto';
            finBody.innerHTML += `
                <tr>
                    <td>${date}</td>
                    <td>${f.tienda}</td>
                    <td><span class="badge ${badgeClass}">${f.tipo}</span></td>
                    <td>${f.descripcion}</td>
                    <td><strong>${formatter.format(f.monto)}</strong></td>
                </tr>
            `;
        });
    } catch (error) {
        console.error('Error cargando datos del admin', error);
    }
}

// --- FUNCIONES DE TIENDA Y POS ---
async function initTienda() {
    const params = new URLSearchParams(window.location.search);
    currentTiendaId = params.get('id');
    const nombre = params.get('nombre');

    if (!currentTiendaId) {
        window.location.href = 'index.html';
        return;
    }

    if(document.getElementById('tienda-nombre')) {
        document.getElementById('tienda-nombre').innerText = nombre;
    }
    await loadTiendaInventario();
}

async function loadTiendaInventario() {
    try {
        const res = await fetch(`${API_URL}/inventario/${currentTiendaId}`);
        inventarioLocal = await res.json();
        
        const invBody = document.getElementById('tienda-inventario-body');
        if(!invBody) return;
        
        invBody.innerHTML = '';

        inventarioLocal.forEach(item => {
            invBody.innerHTML += `
                <tr>
                    <td>${item.sku}</td>
                    <td>${item.producto}</td>
                    <td><strong>${item.cantidad}</strong></td>
                    <td>${formatter.format(item.precio)}</td>
                </tr>
            `;
        });
    } catch (error) {
        console.error('Error cargando inventario de la tienda', error);
    }
}

async function buscarRed() {
    const query = document.getElementById('search-input').value;
    if (!query) return;

    try {
        const res = await fetch(`${API_URL}/buscar?sku=${encodeURIComponent(query)}`);
        const resultados = await res.json();
        
        const resultDiv = document.getElementById('search-results');
        resultDiv.innerHTML = '';

        if (resultados.length === 0) {
            resultDiv.innerHTML = '<p style="color: var(--danger);">No se encontró el mueble en ninguna tienda.</p>';
            return;
        }

        let html = '<ul style="list-style:none; padding:0;">';
        resultados.forEach(r => {
            html += `<li style="background: rgba(255,255,255,0.05); padding: 0.75rem; border-radius: 8px; margin-bottom: 0.5rem; display: flex; justify-content: space-between;">
                <span><strong>${r.tienda}</strong> - ${r.producto}</span>
                <span class="badge ${r.cantidad > 0 ? 'badge-ingreso' : 'badge-gasto'}">Stock: ${r.cantidad}</span>
            </li>`;
        });
        html += '</ul>';
        resultDiv.innerHTML = html;
    } catch (error) {
        console.error('Error en búsqueda cruzada', error);
    }
}

// POS LOGIC
function toggleScanner() {
    const btn = document.getElementById('btn-scan');
    if (!scanning) {
        scanning = true;
        btn.innerText = "Detener Cámara";
        btn.classList.remove('btn-success');
        btn.classList.add('btn-danger');
        
        html5QrcodeScanner = new Html5QrcodeScanner(
            "reader", { fps: 10, qrbox: 250 });
        html5QrcodeScanner.render(onScanSuccess, onScanError);
    } else {
        scanning = false;
        btn.innerText = "Activar Cámara Escáner";
        btn.classList.remove('btn-danger');
        btn.classList.add('btn-success');
        if(html5QrcodeScanner) {
            html5QrcodeScanner.clear();
        }
    }
}

function onScanSuccess(decodedText, decodedResult) {
    // Decoded text will be the SKU (e.g. MBL-SOFA-001)
    console.log(`Scan result: ${decodedText}`);
    agregarProductoAlCarrito(decodedText);
}

function onScanError(errorMessage) {
    // console.warn(errorMessage);
}

function agregarAlCarritoManual() {
    const sku = document.getElementById('manual-sku').value.trim();
    if(sku) {
        agregarProductoAlCarrito(sku);
        document.getElementById('manual-sku').value = '';
    }
}

function agregarProductoAlCarrito(sku) {
    // Buscar en inventario local
    const producto = inventarioLocal.find(p => p.sku === sku);
    if (!producto) {
        alert("Producto no encontrado en el inventario local.");
        return;
    }

    // Verificar si ya está en el carrito
    const itemCarrito = carrito.find(c => c.producto_id === producto.producto_id);
    if (itemCarrito) {
        if (itemCarrito.cantidad + 1 > producto.cantidad) {
            alert(`No hay suficiente stock. Disponible: ${producto.cantidad}`);
            return;
        }
        itemCarrito.cantidad += 1;
    } else {
        if (producto.cantidad < 1) {
            alert("No hay stock disponible para este producto.");
            return;
        }
        carrito.push({
            producto_id: producto.producto_id,
            sku: producto.sku,
            producto: producto.producto,
            precio: producto.precio,
            cantidad: 1
        });
    }
    
    renderizarCarrito();
}

function removerDelCarrito(index) {
    carrito.splice(index, 1);
    renderizarCarrito();
}

function renderizarCarrito() {
    const tbody = document.getElementById('cart-body');
    if(!tbody) return;
    
    tbody.innerHTML = '';
    let subtotal = 0;

    carrito.forEach((item, index) => {
        const itemTotal = item.cantidad * item.precio;
        subtotal += itemTotal;
        tbody.innerHTML += `
            <tr>
                <td><small>${item.sku}</small><br>${item.producto}</td>
                <td>${item.cantidad}</td>
                <td>${formatter.format(itemTotal)}</td>
                <td><button onclick="removerDelCarrito(${index})" style="background:var(--danger); color:white; border:none; padding:4px 8px; border-radius:4px; cursor:pointer;">X</button></td>
            </tr>
        `;
    });

    document.getElementById('pos-subtotal').dataset.val = subtotal;
    document.getElementById('pos-subtotal').innerText = formatter.format(subtotal);
    actualizarTotales();
}

function actualizarTotales() {
    const subtotalEl = document.getElementById('pos-subtotal');
    if(!subtotalEl) return;
    
    let subtotal = parseFloat(subtotalEl.dataset.val) || 0;
    
    // Regla de descuento automático: Si subtotal > 3,000,000 sugerimos 10%
    let descManual = parseFloat(document.getElementById('pos-descuento').value) || 0;
    
    // Aplicar descuento
    let total = subtotal - (subtotal * (descManual / 100));
    document.getElementById('pos-total').innerText = formatter.format(total);
    document.getElementById('pos-total').dataset.val = total;
}

async function procesarVenta() {
    if (carrito.length === 0) {
        alert("El carrito está vacío");
        return;
    }

    const desc = parseFloat(document.getElementById('pos-descuento').value) || 0;
    const totalFinal = parseFloat(document.getElementById('pos-total').dataset.val);

    try {
        const res = await fetch(`${API_URL}/venta/${currentTiendaId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                carrito: carrito,
                descuento: desc,
                total_final: totalFinal
            })
        });

        const result = await res.json();
        
        if (res.ok) {
            alert('¡Venta completada con éxito!');
            carrito = [];
            document.getElementById('pos-descuento').value = 0;
            renderizarCarrito();
            await loadTiendaInventario(); // Recargar inventario local para reflejar que hay menos
        } else {
            alert(`Error: ${result.error}`);
        }
    } catch (error) {
        console.error('Error procesando venta', error);
        alert('Ocurrió un error al procesar la venta');
    }
}
