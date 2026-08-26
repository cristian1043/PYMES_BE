import os
import sys

# Añadir el directorio src al sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.models import session
from src.models.productos import Productos
from src.models.proveedores import Proveedores
from src.utils.migrations import DatabaseMigrations

def sembrar_stock_y_costos_demo():
    print("[MIGRACIONES] Ejecutando migraciones iniciales de base de datos...")
    DatabaseMigrations.ejecutar_migraciones()

    # Asegurar que existan proveedores de prueba
    provs = session.query(Proveedores).all()
    if not provs:
        p1 = Proveedores()
        p1.nit = "900.111.222-3"
        p1.nombre = "Mayorista Tecnologico de Colombia"
        p1.telefono = "6014445566"
        p1.direccion = "Calle 26 # 69-76, Bogota"
        p1.email = "ventas@mayortecno.com"
        p1.detalle_servicios = "Distribucion oficial de laptops, servidores y tecnologia de consumo."
        p1.save()

        p2 = Proveedores()
        p2.nit = "800.333.444-5"
        p2.nombre = "Suministros Industriales y de Oficina S.A.S."
        p2.telefono = "6045558899"
        p2.direccion = "Carrera 43A # 1-50, Medellin"
        p2.email = "contacto@suministrosind.com"
        p2.detalle_servicios = "Insumos de oficina, papeleria al por mayor y mobiliario corporativo."
        p2.save()
        provs = [p1, p2]

    id_prov_1 = provs[0].id
    id_prov_2 = provs[1].id if len(provs) > 1 else id_prov_1

    print("[STOCK DEMO] Configurando productos demo con niveles estrategicos de Stock y Costos...")

    productos = session.query(Productos).all()
    
    # Datos demostrativos deseados
    datos_demo = [
        {"codigo": "PROD-001", "nombre": "Laptop HP ProBook 450", "precio": 3500000.0, "costo": 2450000.0, "stock": 1200, "id_prov": id_prov_1},   # STOCK BAJO
        {"codigo": "PROD-002", "nombre": "Monitor Gamer LG 27 Inch", "precio": 1200000.0, "costo": 840000.0, "stock": 850, "id_prov": id_prov_1},    # STOCK BAJO
        {"codigo": "PROD-003", "nombre": "Teclado Mecanico RGB Redragon", "precio": 250000.0, "costo": 175000.0, "stock": 5500, "id_prov": id_prov_2},# STOCK OPTIMO
        {"codigo": "PROD-004", "nombre": "Mouse Inalambrico Logitech MX", "precio": 180000.0, "costo": 126000.0, "stock": 8000, "id_prov": id_prov_2},# STOCK OPTIMO
        {"codigo": "PROD-005", "nombre": "Cable HDMI 4K Trenzado 2m", "precio": 35000.0, "costo": 21000.0, "stock": 12500, "id_prov": id_prov_1},   # SOBRE-STOCK
        {"codigo": "PROD-006", "nombre": "Adaptador USB-C a Ethernet RJ45", "precio": 65000.0, "costo": 42000.0, "stock": 16000, "id_prov": id_prov_2} # SOBRE-STOCK
    ]

    for idx, d in enumerate(datos_demo):
        if idx < len(productos):
            p = productos[idx]
            p.nombre = d["nombre"]
            p.precio = d["precio"]
            p.costo = d["costo"]
            p.stock = d["stock"]
            p.id_proveedor = d["id_prov"]
            p.update()
        else:
            p = Productos()
            p.codigo = d["codigo"]
            p.nombre = d["nombre"]
            p.descripcion = f"Descripcion demostrativa de {d['nombre']}"
            p.unidad_medida = "UND"
            p.precio = d["precio"]
            p.costo = d["costo"]
            p.stock = d["stock"]
            p.id_categoria = 1
            p.id_proveedor = d["id_prov"]
            p.create()

    print("[SUCCESS] Sembrado completado exitosamente:")
    print("   * 2 Productos en STOCK BAJO (<= 2500 unds)")
    print("   * 2 Productos en STOCK OPTIMO (2501 - 10000 unds)")
    print("   * 2 Productos en SOBRE-STOCK (> 10000 unds)")

if __name__ == "__main__":
    sembrar_stock_y_costos_demo()
