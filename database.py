import sqlite3
import os

DB_NAME = 'sistema.db'

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    
    # Tabla Tiendas
    c.execute('''
        CREATE TABLE IF NOT EXISTS tiendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            ubicacion TEXT
        )
    ''')
    
    # Tabla Productos
    c.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            precio REAL NOT NULL
        )
    ''')
    
    # Tabla Inventario (Relación Tienda - Producto)
    c.execute('''
        CREATE TABLE IF NOT EXISTS inventario (
            tienda_id INTEGER,
            producto_id INTEGER,
            cantidad INTEGER DEFAULT 0,
            PRIMARY KEY (tienda_id, producto_id),
            FOREIGN KEY (tienda_id) REFERENCES tiendas(id),
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        )
    ''')
    
    # Tabla Finanzas
    c.execute('''
        CREATE TABLE IF NOT EXISTS finanzas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tienda_id INTEGER,
            tipo TEXT CHECK(tipo IN ('Ingreso', 'Gasto')) NOT NULL,
            monto REAL NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            descripcion TEXT,
            FOREIGN KEY (tienda_id) REFERENCES tiendas(id)
        )
    ''')
    
    # Insertar datos de prueba si no existen
    c.execute('SELECT COUNT(*) FROM tiendas')
    if c.fetchone()[0] == 0:
        tiendas = [
            ('Muebles Central', 'Av. Principal 123'),
            ('Muebles Norte', 'Calle 45 Norte'),
            ('Muebles Sur', 'Av. del Sur 99'),
            ('Bodega Principal', 'Zona Industrial'),
            ('Outlet Muebles', 'Plaza Comercial')
        ]
        for t in tiendas:
            c.execute("INSERT INTO tiendas (nombre, ubicacion) VALUES (?, ?)", t)
        
        productos = [
            ('MBL-SOFA-001', 'Sofá Cuerina 3 Puestos', 1500000.00),
            ('MBL-MESA-002', 'Mesa de Comedor Roble', 850000.00),
            ('MBL-SILL-003', 'Silla Ergonómica Oficina', 350000.00),
            ('MBL-CAMA-004', 'Cama King Size', 2200000.00),
            ('MBL-CLST-005', 'Closet 4 Puertas', 1100000.00),
            ('MBL-MESA-006', 'Mesa de Centro de Vidrio', 250000.00),
            ('MBL-SOFA-007', 'Sofá Cama Modular', 1800000.00)
        ]
        for p in productos:
            c.execute("INSERT INTO productos (sku, nombre, precio) VALUES (?, ?, ?)", p)
        
        # Inventario inicial distribuido
        # Tienda 1
        c.execute("INSERT INTO inventario (tienda_id, producto_id, cantidad) VALUES (1, 1, 5)")
        c.execute("INSERT INTO inventario (tienda_id, producto_id, cantidad) VALUES (1, 2, 3)")
        c.execute("INSERT INTO inventario (tienda_id, producto_id, cantidad) VALUES (1, 3, 10)")
        c.execute("INSERT INTO inventario (tienda_id, producto_id, cantidad) VALUES (1, 6, 8)")
        # Tienda 2
        c.execute("INSERT INTO inventario (tienda_id, producto_id, cantidad) VALUES (2, 1, 2)")
        c.execute("INSERT INTO inventario (tienda_id, producto_id, cantidad) VALUES (2, 4, 5)")
        c.execute("INSERT INTO inventario (tienda_id, producto_id, cantidad) VALUES (2, 5, 4)")
        # Tienda 3
        c.execute("INSERT INTO inventario (tienda_id, producto_id, cantidad) VALUES (3, 3, 20)")
        c.execute("INSERT INTO inventario (tienda_id, producto_id, cantidad) VALUES (3, 7, 3)")
        # Bodega (4)
        c.execute("INSERT INTO inventario (tienda_id, producto_id, cantidad) VALUES (4, 1, 50)")
        c.execute("INSERT INTO inventario (tienda_id, producto_id, cantidad) VALUES (4, 2, 30)")
        c.execute("INSERT INTO inventario (tienda_id, producto_id, cantidad) VALUES (4, 3, 100)")
        c.execute("INSERT INTO inventario (tienda_id, producto_id, cantidad) VALUES (4, 4, 40)")
        c.execute("INSERT INTO inventario (tienda_id, producto_id, cantidad) VALUES (4, 5, 25)")
        c.execute("INSERT INTO inventario (tienda_id, producto_id, cantidad) VALUES (4, 6, 60)")
        c.execute("INSERT INTO inventario (tienda_id, producto_id, cantidad) VALUES (4, 7, 15)")
        # Outlet (5)
        c.execute("INSERT INTO inventario (tienda_id, producto_id, cantidad) VALUES (5, 6, 5)")
        c.execute("INSERT INTO inventario (tienda_id, producto_id, cantidad) VALUES (5, 7, 2)")
        
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Base de datos inicializada correctamente.")
