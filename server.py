from flask import Flask, request, jsonify
from flask_cors import CORS
from database import get_db, init_db

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

@app.route('/')
def serve_index():
    return app.send_static_file('index.html')

@app.route('/<path:path>')
def serve_static(path):
    import os
    if os.path.exists(path):
        return app.send_static_file(path)
    return jsonify({"error": "Not found"}), 404


# Iniciar la BD si no existe
init_db()

@app.route('/api/tiendas', methods=['GET'])
def get_tiendas():
    conn = get_db()
    tiendas = conn.execute('SELECT * FROM tiendas').fetchall()
    conn.close()
    return jsonify([dict(t) for t in tiendas])

@app.route('/api/inventario', methods=['GET'])
def get_inventario_global():
    conn = get_db()
    query = '''
        SELECT t.nombre as tienda, p.nombre as producto, p.sku, i.cantidad, p.precio 
        FROM inventario i
        JOIN tiendas t ON i.tienda_id = t.id
        JOIN productos p ON i.producto_id = p.id
    '''
    items = conn.execute(query).fetchall()
    conn.close()
    return jsonify([dict(i) for i in items])

@app.route('/api/inventario/<int:tienda_id>', methods=['GET'])
def get_inventario_tienda(tienda_id):
    conn = get_db()
    query = '''
        SELECT p.id as producto_id, p.nombre as producto, p.sku, i.cantidad, p.precio 
        FROM inventario i
        JOIN productos p ON i.producto_id = p.id
        WHERE i.tienda_id = ?
    '''
    items = conn.execute(query, (tienda_id,)).fetchall()
    conn.close()
    return jsonify([dict(i) for i in items])

@app.route('/api/buscar', methods=['GET'])
def buscar_producto():
    # Buscar disponibilidad en otras tiendas
    sku = request.args.get('sku', '')
    conn = get_db()
    query = '''
        SELECT t.nombre as tienda, i.cantidad, p.nombre as producto, p.sku
        FROM inventario i
        JOIN tiendas t ON i.tienda_id = t.id
        JOIN productos p ON i.producto_id = p.id
        WHERE p.sku = ? OR p.nombre LIKE ?
    '''
    items = conn.execute(query, (sku, f'%{sku}%')).fetchall()
    conn.close()
    return jsonify([dict(i) for i in items])

@app.route('/api/finanzas', methods=['GET'])
def get_finanzas_global():
    conn = get_db()
    items = conn.execute('SELECT f.*, t.nombre as tienda FROM finanzas f JOIN tiendas t ON f.tienda_id = t.id ORDER BY f.fecha DESC').fetchall()
    conn.close()
    return jsonify([dict(i) for i in items])

@app.route('/api/finanzas/<int:tienda_id>', methods=['GET', 'POST'])
def handle_finanzas_tienda(tienda_id):
    if request.method == 'GET':
        conn = get_db()
        items = conn.execute('SELECT * FROM finanzas WHERE tienda_id = ? ORDER BY fecha DESC', (tienda_id,)).fetchall()
        conn.close()
        return jsonify([dict(i) for i in items])
    elif request.method == 'POST':
        data = request.json
        conn = get_db()
        conn.execute('INSERT INTO finanzas (tienda_id, tipo, monto, descripcion) VALUES (?, ?, ?, ?)',
                     (tienda_id, data['tipo'], data['monto'], data.get('descripcion', '')))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"}), 201

@app.route('/api/venta/<int:tienda_id>', methods=['POST'])
def procesar_venta(tienda_id):
    data = request.json
    carrito = data.get('carrito', [])
    descuento = float(data.get('descuento', 0))
    total_final = float(data.get('total_final', 0))

    if not carrito:
        return jsonify({"error": "Carrito vacío"}), 400

    conn = get_db()
    try:
        # Verificar y restar inventario
        for item in carrito:
            producto_id = item['producto_id']
            cantidad_vendida = item['cantidad']
            
            # Chequear disponibilidad
            stock = conn.execute('SELECT cantidad FROM inventario WHERE tienda_id = ? AND producto_id = ?', (tienda_id, producto_id)).fetchone()
            if not stock or stock['cantidad'] < cantidad_vendida:
                raise Exception(f"Stock insuficiente para {item.get('producto', 'producto desconocido')}")
                
            # Restar stock
            conn.execute('UPDATE inventario SET cantidad = cantidad - ? WHERE tienda_id = ? AND producto_id = ?', (cantidad_vendida, tienda_id, producto_id))

        # Registrar en finanzas
        descripcion_venta = f"Venta POS ({len(carrito)} items). Desc: {descuento}%"
        conn.execute('INSERT INTO finanzas (tienda_id, tipo, monto, descripcion) VALUES (?, ?, ?, ?)',
                     (tienda_id, 'Ingreso', total_final, descripcion_venta))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 400
        
    conn.close()
    return jsonify({"status": "success", "mensaje": "Venta procesada y stock actualizado"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)
