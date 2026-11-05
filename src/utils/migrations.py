from sqlalchemy import text
from src.models import engine

class DatabaseMigrations:
    """
    Módulo exclusivo para la gestión y actualización del esquema de tablas en la base de datos MySQL (SRP).
    """

    @staticmethod
    def ejecutar_migraciones():
        """Verifica y aplica columnas faltantes en las tablas de MySQL."""
        try:
            with engine.connect() as conn:
                # Columnas adicionales para la tabla usuarios
                columnas_usuarios = [
                    "ALTER TABLE usuarios ADD COLUMN username VARCHAR(50) UNIQUE",
                    "ALTER TABLE usuarios ADD COLUMN estado VARCHAR(20) DEFAULT 'Activo'",
                    "ALTER TABLE usuarios ADD COLUMN banco VARCHAR(100)",
                    "ALTER TABLE usuarios ADD COLUMN tipo_cuenta VARCHAR(50)",
                    "ALTER TABLE usuarios ADD COLUMN numero_cuenta VARCHAR(50)",
                    "ALTER TABLE usuarios ADD COLUMN fecha_nacimiento VARCHAR(20)",
                    "ALTER TABLE usuarios ADD COLUMN lugar_residencia VARCHAR(200)",
                    "ALTER TABLE usuarios ADD COLUMN estado_civil VARCHAR(50)",
                    "ALTER TABLE usuarios ADD COLUMN sesion_version INT DEFAULT 1",
                    "ALTER TABLE usuarios ADD COLUMN foto TEXT"
                ]
                for query in columnas_usuarios:
                    try:
                        conn.execute(text(query))
                        conn.commit()
                    except Exception:
                        pass

                # Columnas adicionales para la tabla empresas
                try:
                    conn.execute(text("ALTER TABLE empresas ADD COLUMN estado VARCHAR(20) DEFAULT 'Activo'"))
                    conn.commit()
                except Exception:
                    pass

                # Columnas adicionales para la tabla facturas
                columnas_facturas = [
                    "ALTER TABLE facturas ADD COLUMN estado VARCHAR(20) DEFAULT 'Emitida'",
                    "ALTER TABLE facturas ADD COLUMN id_empresa INT",
                    "ALTER TABLE facturas ADD COLUMN pasarela VARCHAR(50)",
                    "ALTER TABLE facturas ADD COLUMN referencia_pago VARCHAR(100)"
                ]
                for query in columnas_facturas:
                    try:
                        conn.execute(text(query))
                        conn.commit()
                    except Exception:
                        pass

                # Columnas adicionales para la tabla productos
                columnas_productos = [
                    "ALTER TABLE productos ADD COLUMN id_proveedor INT",
                    "ALTER TABLE productos ADD COLUMN costo FLOAT DEFAULT 0.0",
                    "ALTER TABLE productos ADD COLUMN estado VARCHAR(20) DEFAULT 'Activo'",
                    "ALTER TABLE productos ADD COLUMN imagen TEXT",
                    "ALTER TABLE productos ADD COLUMN id_empresa INT"
                ]
                for query in columnas_productos:
                    try:
                        conn.execute(text(query))
                        conn.commit()
                    except Exception:
                        pass

                # Columnas adicionales para la tabla clientes
                columnas_clientes = [
                    "ALTER TABLE clientes ADD COLUMN apellido VARCHAR(100)",
                    "ALTER TABLE clientes ADD COLUMN codigo VARCHAR(50)",
                    "ALTER TABLE clientes ADD COLUMN tipo_documento VARCHAR(20) DEFAULT 'CC'",
                    "ALTER TABLE clientes ADD COLUMN estado VARCHAR(20) DEFAULT 'Activo'",
                    "ALTER TABLE clientes ADD COLUMN tiene_tarjeta VARCHAR(5) DEFAULT 'No'",
                    "ALTER TABLE clientes ADD COLUMN tipo_tarjeta VARCHAR(50)",
                    "ALTER TABLE clientes ADD COLUMN banco_tarjeta VARCHAR(100)",
                    "ALTER TABLE clientes ADD COLUMN franquicia_tarjeta VARCHAR(50)",
                    "ALTER TABLE clientes ADD COLUMN ultimos_digitos_tarjeta VARCHAR(4)",
                    "ALTER TABLE clientes ADD COLUMN numero_tarjeta VARCHAR(20)",
                    "ALTER TABLE clientes ADD COLUMN titular_tarjeta VARCHAR(100)",
                    "ALTER TABLE clientes ADD COLUMN fecha_expiracion VARCHAR(10)",
                    "ALTER TABLE clientes ADD COLUMN cvc_tarjeta VARCHAR(10)",
                    "ALTER TABLE clientes ADD COLUMN id_empresa INT"
                ]
                for query in columnas_clientes:
                    try:
                        conn.execute(text(query))
                        conn.commit()
                    except Exception:
                        pass

                # Columnas adicionales para la tabla proveedores
                columnas_proveedores = [
                    "ALTER TABLE proveedores ADD COLUMN codigo VARCHAR(50)",
                    "ALTER TABLE proveedores ADD COLUMN contacto VARCHAR(100)",
                    "ALTER TABLE proveedores ADD COLUMN detalle_servicios VARCHAR(500)",
                    "ALTER TABLE proveedores ADD COLUMN estado VARCHAR(20) DEFAULT 'Activo'",
                    "ALTER TABLE proveedores ADD COLUMN id_empresa INT"
                ]
                for query in columnas_proveedores:
                    try:
                        conn.execute(text(query))
                        conn.commit()
                    except Exception:
                        pass

                # Columnas adicionales para la tabla compras
                columnas_compras = [
                    "ALTER TABLE compras ADD COLUMN numero VARCHAR(50)",
                    "ALTER TABLE compras ADD COLUMN estado VARCHAR(20) DEFAULT 'Completada'",
                    "ALTER TABLE compras ADD COLUMN id_empresa INT",
                    "ALTER TABLE compras ADD COLUMN id_metodo_pago INT DEFAULT 1",
                    "ALTER TABLE compras ADD COLUMN metodo_pago VARCHAR(100) DEFAULT 'Efectivo'",
                    "ALTER TABLE compras ADD COLUMN referencia_pago VARCHAR(100)"
                ]
                for query in columnas_compras:
                    try:
                        conn.execute(text(query))
                        conn.commit()
                    except Exception:
                        pass

                # Columnas de integración con pasarelas para la tabla metodos_pago
                # (bases de datos creadas antes de que existieran estos campos)
                columnas_metodos_pago = [
                    "ALTER TABLE metodos_pago ADD COLUMN pasarela VARCHAR(50) DEFAULT 'ninguna'",
                    "ALTER TABLE metodos_pago ADD COLUMN api_key_publica VARCHAR(255)",
                    "ALTER TABLE metodos_pago ADD COLUMN api_key_privada VARCHAR(255)",
                    "ALTER TABLE metodos_pago ADD COLUMN webhook_secret VARCHAR(255)",
                    "ALTER TABLE metodos_pago ADD COLUMN integrity_secret VARCHAR(255)",
                    "ALTER TABLE metodos_pago ADD COLUMN modo VARCHAR(20) DEFAULT 'sandbox'"
                ]
                for query in columnas_metodos_pago:
                    try:
                        conn.execute(text(query))
                        conn.commit()
                    except Exception:
                        pass

                # Seguridad PCI-DSS: eliminar cualquier dato de tarjeta almacenado en clientes.
                # Las columnas se conservan (sin uso) para no romper bases de datos existentes,
                # pero su contenido se borra y la API ya no las lee ni las escribe.
                try:
                    conn.execute(text(
                        "UPDATE clientes SET numero_tarjeta = NULL, cvc_tarjeta = NULL, fecha_expiracion = NULL, "
                        "titular_tarjeta = NULL, ultimos_digitos_tarjeta = NULL, franquicia_tarjeta = NULL, "
                        "banco_tarjeta = NULL, tipo_tarjeta = NULL, tiene_tarjeta = 'No' "
                        "WHERE numero_tarjeta IS NOT NULL OR cvc_tarjeta IS NOT NULL OR fecha_expiracion IS NOT NULL "
                        "OR titular_tarjeta IS NOT NULL OR ultimos_digitos_tarjeta IS NOT NULL OR franquicia_tarjeta IS NOT NULL "
                        "OR banco_tarjeta IS NOT NULL OR tipo_tarjeta IS NOT NULL OR (tiene_tarjeta IS NOT NULL AND tiene_tarjeta <> 'No')"
                    ))
                    conn.commit()
                except Exception:
                    pass

                # Reparación y saneamiento automático de registros huérfanos sin id_empresa
                reparaciones = [
                    "UPDATE clientes SET id_empresa = 1 WHERE id_empresa IS NULL",
                    "UPDATE facturas SET id_empresa = 1 WHERE id_empresa IS NULL",
                    "UPDATE proveedores SET id_empresa = 1 WHERE id_empresa IS NULL",
                    "UPDATE productos SET id_empresa = 1 WHERE id_empresa IS NULL",
                    "UPDATE compras SET id_empresa = 1 WHERE id_empresa IS NULL",
                    "UPDATE compras SET metodo_pago = 'Efectivo' WHERE metodo_pago IS NULL OR metodo_pago = ''",
                    "UPDATE compras SET id_metodo_pago = 1 WHERE id_metodo_pago IS NULL"
                ]
                for rep in reparaciones:
                    try:
                        conn.execute(text(rep))
                        conn.commit()
                    except Exception:
                        pass

            # Semilla automática e idempotente de métodos de pago integrados y terminales de pago iniciales
            DatabaseMigrations._sembrar_pasarelas_y_terminales()
        except Exception:
            pass

    @staticmethod
    def _sembrar_pasarelas_y_terminales():
        """
        Garantiza que existan métodos de pago integrados (Bold, Wompi y modo Simulado para pruebas sin llaves)
        y terminales de pago (datáfonos) iniciales para que el comercio pueda operar de inmediato.
        No modifica ni elimina métodos ni terminales ya creados.
        """
        try:
            from src.models import session
            from src.models.metodos_pago import MetodosPago
            from src.models.terminales import Terminales
            from src.models.empresas import Empresas

            existentes = session.query(MetodosPago).all()
            nombres_lower = {(m.nombre or "").strip().lower() for m in existentes}

            # 1. Asegurar métodos base si la tabla está vacía
            if not existentes:
                base_efectivo = MetodosPago(
                    nombre="Efectivo",
                    descripcion="Pago en efectivo en caja",
                    tipo="Efectivo",
                    pasarela="ninguna",
                    modo="sandbox",
                    estado="Activo",
                    id_empresa=None
                )
                base_transf = MetodosPago(
                    nombre="Transferencia Bancaria / Nequi",
                    descripcion="Transferencia directa a cuenta o billetera digital",
                    tipo="Transferencia",
                    banco="Bancolombia / Nequi",
                    pasarela="ninguna",
                    modo="sandbox",
                    estado="Activo",
                    id_empresa=None
                )
                session.add(base_efectivo)
                session.add(base_transf)
                session.commit()
                existentes = session.query(MetodosPago).all()
                nombres_lower = {(m.nombre or "").strip().lower() for m in existentes}

            # 2. Asegurar métodos integrados en modo simulado (pruebas sin llaves) y plantillas Bold / Wompi
            metodo_sim_datafono = next(
                (m for m in existentes if (m.pasarela or "").lower() == "simulado" and (m.tipo or "") == "Tarjeta"),
                None
            )
            if not metodo_sim_datafono and "datáfono bold (simulado)" not in nombres_lower:
                metodo_sim_datafono = MetodosPago(
                    nombre="Datáfono Bold (Simulado)",
                    descripcion="Cobro en terminal física en modo pruebas (sin llaves reales)",
                    tipo="Tarjeta",
                    banco="Bold",
                    pasarela="simulado",
                    modo="sandbox",
                    estado="Activo",
                    id_empresa=None
                )
                session.add(metodo_sim_datafono)
                session.commit()

            metodo_sim_link = next(
                (m for m in existentes if (m.pasarela or "").lower() == "simulado" and (m.tipo or "") == "Pasarela"),
                None
            )
            if not metodo_sim_link and "pasarela wompi / pse / nequi (simulado)" not in nombres_lower:
                metodo_sim_link = MetodosPago(
                    nombre="Pasarela Wompi / PSE / Nequi (Simulado)",
                    descripcion="Link de cobro online (PSE, Nequi, Tarjeta) en modo pruebas",
                    tipo="Pasarela",
                    banco="Wompi Bancolombia",
                    pasarela="simulado",
                    modo="sandbox",
                    estado="Activo",
                    id_empresa=None
                )
                session.add(metodo_sim_link)
                session.commit()

            # 3. Si una empresa activa aún no tiene ninguna terminal de pago registrada, crear sus datáfonos iniciales
            metodo_para_terminal = metodo_sim_datafono or next(
                (m for m in session.query(MetodosPago).all() if (m.pasarela or "").lower() in ("simulado", "bold")),
                None
            )
            if metodo_para_terminal:
                ids_empresas = [1]
                try:
                    for emp in session.query(Empresas).all():
                        if emp.id and int(emp.id) not in ids_empresas:
                            ids_empresas.append(int(emp.id))
                except Exception:
                    pass

                for eid in ids_empresas:
                    tiene_terminales = session.query(Terminales).filter(Terminales.id_empresa == eid).first() is not None
                    if not tiene_terminales:
                        t1 = Terminales(
                            id_empresa=eid,
                            nombre="Caja Principal - Datáfono 1",
                            proveedor="simulado",
                            id_metodo_pago=metodo_para_terminal.id,
                            terminal_serial="SIM-0001",
                            terminal_model="Bold Smart Pro",
                            email_usuario="caja1@pymesoft.co",
                            estado="Activo"
                        )
                        t2 = Terminales(
                            id_empresa=eid,
                            nombre="Caja Auxiliar - Datáfono 2",
                            proveedor="simulado",
                            id_metodo_pago=metodo_para_terminal.id,
                            terminal_serial="SIM-0002",
                            terminal_model="Bold Smart",
                            email_usuario="caja2@pymesoft.co",
                            estado="Activo"
                        )
                        session.add(t1)
                        session.add(t2)
                session.commit()
        except Exception as e:
            try:
                from src.models import session
                session.rollback()
            except Exception:
                pass
            print(f"[migrations] Aviso al sembrar pasarelas/terminales: {e}")
