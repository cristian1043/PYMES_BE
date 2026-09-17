import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from datetime import datetime, timedelta
from src.models import Base, engine, session
from src.models.empresas import Empresas
from src.models.clientes import Clientes
from src.models.proveedores import Proveedores
from src.models.productos import Productos
from src.models.facturas import Facturas
from src.models.detalle_facturas import DetalleFacturas
from src.models.compras import Compras
from src.models.detalle_compras import DetalleCompras
from src.models.usuarios import Usuarios

def sembrar_datos_abundantes():
    print('[*] Sembrando datos para Empresa 1 y Empresa 2...')
    
    clientes_demo_emp1 = [
        ('Carlos Alberto', 'Gómez Rincón', 'CC', '1019283741', '3114567890', 'carlos.gomez@gmail.com', 'Calle 45 # 12-34, Bogotá'),
        ('María Fernanda', 'López Castro', 'CC', '1028394857', '3129876543', 'mfernanda.lopez@hotmail.com', 'Carrera 15 # 85-20, Bogotá'),
        ('Distribuciones del Valle S.A.S.', '', 'NIT', '900887766-1', '6017654321', 'contacto@disvalle.com.co', 'Av. Esperanza # 68-40, Bogotá'),
        ('Juan David', 'Mendoza Herrera', 'CC', '1039485726', '3103456789', 'juan.mendoza@pyme.co', 'Calle 134 # 9-15, Bogotá'),
        ('Tecnología Andina Ltda.', '', 'NIT', '800123999-5', '6013216548', 'compras@tecnoandina.co', 'Calle 13 # 38-50, Bogotá'),
        ('Diana Marcela', 'Suárez Pardo', 'CC', '1048596031', '3182345678', 'diana.suarez@gmail.com', 'Carrera 7 # 72-10, Bogotá'),
        ('Andrés Felipe', 'Vargas Ospina', 'CC', '1059607182', '3158765432', 'andres.vargas@outlook.com', 'Calle 80 # 68-12, Bogotá'),
        ('Comercializadora El Triunfo', '', 'NIT', '901456789-3', '6018901234', 'gerencia@eltriunfo.com', 'Carrera 68D # 13-40, Bogotá'),
        ('Paola Andrea', 'Cárdenas Silva', 'CC', '1060718293', '3167890123', 'paola.cardenas@yahoo.com', 'Calle 53 # 24-18, Bogotá'),
        ('Inversiones Alpha Group', '', 'NIT', '900555666-8', '6014445566', 'facturacion@alphagroup.co', 'Calle 100 # 8A-49, Bogotá'),
        ('Sebastián', 'Ríos Morales', 'CC', '1071829304', '3176543210', 'sebastian.rios@gmail.com', 'Carrera 11 # 93-08, Bogotá'),
        ('Camila Sofía', 'Duque Ortiz', 'CC', '1082930415', '3145678901', 'camila.duque@gmail.com', 'Calle 116 # 18B-25, Bogotá'),
        ('Soluciones Gráficas Exprés', '', 'NIT', '901222333-4', '6015678901', 'ordenes@solugraficas.com', 'Carrera 30 # 45-02, Bogotá'),
        ('Gustavo Adolfo', 'Navarro Peña', 'CC', '1093041526', '3134567890', 'gustavo.navarro@hotmail.com', 'Calle 72 # 10-34, Bogotá')
    ]
    
    for nom, ape, tdoc, doc, tel, email, dir_ in clientes_demo_emp1:
        c = session.query(Clientes).filter_by(documento=doc, id_empresa=1).first()
        if not c:
            c = Clientes()
            c.nombre = nom
            c.apellido = ape
            c.tipo_documento = tdoc
            c.documento = doc
            c.telefono = tel
            c.email = email
            c.direccion = dir_
            c.id_empresa = 1
            c.estado = 'Activo'
            session.add(c)
    session.commit()
    print('[OK] Clientes de prueba para Empresa 1 actualizados.')

    productos_emp1 = [
        ('PROD-E1-001', 'Laptop Lenovo ThinkPad i7', 'Portátil corporativo 16GB RAM 512GB SSD', 'UND', 3800000.0, 2660000.0, 15, 1, 1, 1),
        ('PROD-E1-002', 'Impresora Multifuncional Epson', 'EcoTank sistema continuo WiFi', 'UND', 950000.0, 665000.0, 12, 1, 2, 1),
        ('PROD-E1-003', 'Paquete Lapiceros Gel (x12)', 'Tinta gel azul punta fina 0.5mm', 'PQ', 24000.0, 14000.0, 100, 2, 3, 1),
        ('PROD-E1-004', 'Kit de Aseo Desinfectante', 'Kit multiusos amonio cuaternario 4L', 'KIT', 45000.0, 28000.0, 50, 3, 4, 1),
        ('PROD-E1-005', 'Diadema USB Ergonómica CallCenter', 'Auriculares con micrófono cancelación ruido', 'UND', 180000.0, 110000.0, 2, 1, 1, 1),
        ('PROD-E1-006', 'Tóner Láser HP 85A Negro', 'Cartucho de tóner de alto rendimiento', 'UND', 120000.0, 75000.0, 4, 1, 2, 1),
        ('PROD-E1-007', 'Resma Papel Reprograf Carta', 'Papel bond 75g 500 hojas alta blancura', 'PQ', 22000.0, 15000.0, 0, 2, 3, 1),
        ('PROD-E1-008', 'Mouse Inalámbrico Logitech M185', 'Mouse óptico compacto nano receptor', 'UND', 65000.0, 42000.0, 25, 1, 4, 1),
        ('PROD-E1-009', 'Cable HDMI 4K Blindado 3M', 'Cable de alta velocidad trenzado', 'UND', 35000.0, 18000.0, 3, 1, 1, 1)
    ]
    
    for cod, nom, desc, um, pre, cos, stk, cat, prov, emp in productos_emp1:
        p = session.query(Productos).filter_by(codigo=cod).first()
        if not p:
            p = Productos()
            p.codigo = cod
            p.nombre = nom
            p.descripcion = desc
            p.unidad_medida = um
            p.precio = pre
            p.costo = cos
            p.stock = stk
            p.id_categoria = cat
            p.id_proveedor = prov
            p.id_empresa = emp
            p.estado = 'Activo'
            session.add(p)
        else:
            p.stock = stk
            p.costo = cos
            p.precio = pre
            p.id_empresa = emp
    session.commit()
    print('[OK] Productos variados (con stock crítico y normal) listos en Empresa 1.')

    clientes_e1 = session.query(Clientes).filter_by(id_empresa=1).all()
    prods_e1 = session.query(Productos).filter_by(id_empresa=1).all()
    user_admin = session.query(Usuarios).first()
    uid = user_admin.id if user_admin else 1

    for i in range(1, 16):
        num_fac = f'FAC-E1-{i:03d}'
        f = session.query(Facturas).filter_by(numero=num_fac).first()
        cli = clientes_e1[(i - 1) % len(clientes_e1)]
        
        subtotal = round(85000.0 * i * 0.75, 2)
        iva = round(subtotal * 0.19, 2)
        total = round(subtotal + iva, 2)
        fecha = datetime.now() - timedelta(days=(16 - i) * 2, hours=i)
        
        if not f:
            f = Facturas()
            f.numero = num_fac
            f.fecha = fecha
            f.subtotal = subtotal
            f.iva = iva
            f.descuento = 0.0
            f.total = total
            f.id_cliente = cli.id
            f.id_usuario = uid
            f.id_metodo_pago = 1 if i % 2 == 0 else 3
            f.id_empresa = 1
            f.estado = 'Emitida'
            session.add(f)
            session.commit()
            
            p_ref = prods_e1[i % len(prods_e1)]
            df = DetalleFacturas()
            df.id_factura = f.id
            df.id_producto = p_ref.id
            df.cantidad = 1 + (i % 3)
            df.precio_unitario = p_ref.precio
            df.subtotal = round(df.cantidad * p_ref.precio, 2)
            session.add(df)
            session.commit()
            
    print('[OK] Facturas y detalles en Empresa 1 generados (15 facturas).')

    provs = session.query(Proveedores).all()
    for j in range(1, 13):
        num_comp = f'COMP-E1-{j:03d}'
        c = session.query(Compras).filter_by(numero=num_comp).first()
        prov = provs[(j - 1) % len(provs)]
        
        sub = round(320000.0 * j * 0.65, 2)
        iva_c = round(sub * 0.19, 2)
        tot_c = round(sub + iva_c, 2)
        fecha_c = datetime.now() - timedelta(days=(13 - j) * 3, hours=j * 2)
        
        if not c:
            c = Compras()
            c.numero = num_comp
            c.fecha = fecha_c
            c.subtotal = sub
            c.iva = iva_c
            c.descuento = 0.0
            c.total = tot_c
            c.id_proveedor = prov.id
            c.id_usuario = uid
            c.id_empresa = 1
            c.estado = 'Completada'
            session.add(c)
            session.commit()
            
            p_comp = prods_e1[j % len(prods_e1)]
            dc = DetalleCompras()
            dc.id_compra = c.id
            dc.id_producto = p_comp.id
            dc.cantidad = 5 + (j * 2)
            dc.costo_unitario = p_comp.costo or (p_comp.precio * 0.7)
            dc.subtotal = round(dc.cantidad * dc.costo_unitario, 2)
            session.add(dc)
            session.commit()
            
    print('[OK] Compras y detalles en Empresa 1 generadas (12 compras).')
    print('[SUCCESS] Sembrado de datos finalizado con éxito.')

if __name__ == '__main__':
    sembrar_datos_abundantes()
