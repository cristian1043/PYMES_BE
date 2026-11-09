from datetime import datetime, timedelta
import json
import secrets
from sqlalchemy import or_
from flask_jwt_extended import create_access_token, create_refresh_token

from src.models import session
from src.models.empresas import Empresas
from src.models.portal_config import ConfiguracionPortal, slugify_empresa
from src.models.productos import Productos
from src.models.categorias import Categorias
from src.models.servicios import Servicios
from src.models.clientes import Clientes
from src.models.cuentas_clientes import CuentasClientes, DireccionesClientes, VinculacionesClientes
from src.models.pedidos import Pedidos, DetallePedidos, HistorialPedidos
from src.models.reservas import Reservas
from src.models.facturas import Facturas
from src.models.detalle_facturas import DetalleFacturas
from src.models.metodos_pago import MetodosPago
from src.models.movimiento_inventario import MovimientosInventario
from src.models.notificaciones import Notificaciones, SolicitudesCliente
from src.models.tokens_seguridad import TokensSeguridad
from src.utils.security import hash_password, verify_password, validar_politica_password
from src.utils.mailer import Mailer


class PortalController:
    """
    Controlador integral de lógica de negocio para el Portal de Clientes (PYMES_CLIENTES)
    y la sección administrativa de Portal de Clientes (PYMES_FE).
    """

    # =========================================================================
    # 1. RESOLUCIÓN DE PORTAL Y CONFIGURACIÓN POR EMPRESA
    # =========================================================================
    @staticmethod
    def listar_portales_publicos():
        """Lista todas las empresas activas que tienen su portal de clientes habilitado."""
        empresas_activas = session.query(Empresas).filter(
            (Empresas.estado == "Activo") | (Empresas.estado == None)
        ).all()
        resultado = []
        for emp in empresas_activas:
            cfg = ConfiguracionPortal.get_or_create_for_empresa(emp)
            if cfg.activo:
                d = cfg.to_dict()
                d["empresa_nombre"] = emp.nombre
                d["empresa_nit"] = emp.nit
                resultado.append(d)
        return resultado

    @staticmethod
    def obtener_portal_publico(slug_o_id):
        """
        Resuelve una empresa y su configuración de portal por slug o ID.
        Valida que tanto la empresa como su portal estén activos.
        """
        if not slug_o_id:
            return None, None, "Identificador de empresa o portal requerido.", 400

        cfg = None
        empresa = None
        val_str = str(slug_o_id).strip()
        if val_str.isdigit():
            empresa = Empresas.get_by_id(int(val_str))
            if empresa:
                cfg = ConfiguracionPortal.get_or_create_for_empresa(empresa)
        else:
            cfg = ConfiguracionPortal.get_by_slug(val_str.lower())
            if cfg:
                empresa = Empresas.get_by_id(cfg.id_empresa)
            else:
                # Intentar buscar empresa cuyo slug generado coincida
                for emp_cand in Empresas.get():
                    if slugify_empresa(emp_cand.nombre, emp_cand.id) == val_str.lower():
                        empresa = emp_cand
                        cfg = ConfiguracionPortal.get_or_create_for_empresa(empresa)
                        break

        if not empresa or not cfg:
            return None, None, "El portal de la empresa solicitada no existe.", 404

        if (empresa.estado or "Activo") != "Activo":
            return None, None, "Esta empresa no se encuentra activa actualmente.", 403

        if not cfg.activo:
            return None, None, "El portal público de esta empresa se encuentra temporalmente desactivado.", 403

        return empresa, cfg, None, 200

    @staticmethod
    def obtener_config_admin(id_empresa):
        empresa = Empresas.get_by_id(int(id_empresa))
        if not empresa:
            raise ValueError("Empresa no encontrada.")
        cfg = ConfiguracionPortal.get_or_create_for_empresa(empresa)
        return cfg

    @staticmethod
    def actualizar_config_admin(id_empresa, data):
        empresa = Empresas.get_by_id(int(id_empresa))
        if not empresa:
            raise ValueError("Empresa no encontrada.")
        cfg = ConfiguracionPortal.get_or_create_for_empresa(empresa)

        if "slug" in data and str(data["slug"]).strip():
            nuevo_slug = slugify_empresa(data["slug"], empresa.id)
            if nuevo_slug != cfg.slug:
                dup = session.query(ConfiguracionPortal).filter(
                    ConfiguracionPortal.slug == nuevo_slug,
                    ConfiguracionPortal.id_empresa != empresa.id
                ).first()
                if dup:
                    raise ValueError(f"El identificador URL '{nuevo_slug}' ya está en uso por otra empresa.")
                cfg.slug = nuevo_slug

        # Mapear alias de campos provenientes del frontend administrativo
        alias_bool = {
            "catalogo_activo": "mostrar_catalogo",
            "carrito_activo": "permitir_pedidos",
            "servicios_activos": "mostrar_servicios",
            "reservas_activas": "permitir_reservas",
        }
        for k_alias, k_real in alias_bool.items():
            if k_alias in data and k_real not in data:
                data[k_real] = data[k_alias]

        alias_str = {
            "telefono_publico": "telefono_contacto",
            "correo_publico": "email_contacto",
            "direccion_publica": "direccion",
            "historia": "mensaje_promocional",
            "banner_url": "portada_url",
            "politicas_terminos": "condiciones_servicio",
        }
        for k_alias, k_real in alias_str.items():
            if k_alias in data and k_real not in data:
                data[k_real] = data[k_alias]

        for bool_field in (
            "activo", "mostrar_catalogo", "mostrar_precios",
            "permitir_pedidos", "mostrar_servicios", "permitir_reservas"
        ):
            if bool_field in data:
                val = data[bool_field]
                setattr(cfg, bool_field, 1 if val in (True, 1, "1", "true", "on", "si", "Activo") else 0)

        for str_field in (
            "nombre_publico", "eslogan", "descripcion", "logo_url", "portada_url",
            "color_primario", "color_secundario", "telefono_contacto", "email_contacto",
            "whatsapp", "direccion", "horario_atencion", "modalidades_entrega",
            "mensaje_promocional", "condiciones_servicio"
        ):
            if str_field in data and data[str_field] is not None:
                setattr(cfg, str_field, str(data[str_field]).strip())

        if "costo_envio_base" in data and data["costo_envio_base"] not in (None, ""):
            costo_env = float(data["costo_envio_base"])
            if costo_env < 0:
                raise ValueError("El costo de envío base no puede ser negativo.")
            cfg.costo_envio_base = costo_env

        if "redes_sociales" in data:
            redes = data["redes_sociales"]
            if isinstance(redes, dict):
                cfg.redes_sociales = json.dumps(redes)
            elif isinstance(redes, str):
                cfg.redes_sociales = redes

        cfg.update()
        return cfg

    # =========================================================================
    # 2. CATÁLOGO PÚBLICO DE PRODUCTOS Y SERVICIOS (SIN DATOS INTERNOS SENSIBLES)
    # =========================================================================
    @staticmethod
    def obtener_catalogo_publico(id_empresa, cfg=None, q=None, id_categoria=None, solo_destacados=False):
        eid = int(id_empresa)
        if cfg is None:
            cfg = ConfiguracionPortal.get_by_empresa(eid)
        if cfg and not cfg.mostrar_catalogo:
            return []

        mostrar_precios = True if not cfg else bool(cfg.mostrar_precios)
        query = Productos.get_query().filter(
            Productos.id_empresa == eid,
            Productos.estado == "Activo",
            or_(Productos.publicado_portal == 1, Productos.publicado_portal == None)
        )

        if id_categoria and str(id_categoria).isdigit():
            query = query.filter(Productos.id_categoria == int(id_categoria))

        if solo_destacados:
            query = query.filter(Productos.destacado == 1)

        if q and str(q).strip():
            term = f"%{str(q).strip()}%"
            query = query.filter(
                or_(
                    Productos.nombre.ilike(term),
                    Productos.descripcion.ilike(term),
                    Productos.descripcion_publica.ilike(term),
                    Productos.codigo.ilike(term)
                )
            )

        productos = query.order_by(Productos.destacado.desc(), Productos.id.desc()).all()
        return [p.to_public_dict(mostrar_precios=mostrar_precios) for p in productos]

    @staticmethod
    def obtener_producto_publico(id_empresa, producto_id, cfg=None):
        eid = int(id_empresa)
        if cfg is None:
            cfg = ConfiguracionPortal.get_by_empresa(eid)
        mostrar_precios = True if not cfg else bool(cfg.mostrar_precios)

        prod = Productos.get_by_id(int(producto_id))
        if not prod or prod.id_empresa != eid or prod.estado != "Activo":
            return None
        pub = getattr(prod, "publicado_portal", 1)
        if pub is not None and not bool(pub):
            return None
        return prod.to_public_dict(mostrar_precios=mostrar_precios)

    @staticmethod
    def obtener_servicios_publicos(id_empresa, cfg=None, categoria=None):
        eid = int(id_empresa)
        if cfg is None:
            cfg = ConfiguracionPortal.get_by_empresa(eid)
        if cfg and not cfg.mostrar_servicios:
            return []
        mostrar_precios = True if not cfg else bool(cfg.mostrar_precios)

        query = session.query(Servicios).filter(
            Servicios.id_empresa == eid,
            Servicios.estado == "Activo",
            Servicios.publicado == 1
        )
        if categoria and str(categoria).strip():
            query = query.filter(Servicios.categoria == str(categoria).strip())

        servicios = query.order_by(Servicios.id.desc()).all()
        return [s.to_public_dict(mostrar_precios=mostrar_precios) for s in servicios]

    # =========================================================================
    # 3. GESTIÓN ADMINISTRATIVA DE SERVICIOS
    # =========================================================================
    @staticmethod
    def crear_servicio(id_empresa, data):
        eid = int(id_empresa)
        nombre = str(data.get("nombre") or "").strip()
        if not nombre:
            raise ValueError("El nombre del servicio es obligatorio.")

        precio = float(data.get("precio", 0) or 0)
        if precio < 0:
            raise ValueError("El precio del servicio no puede ser negativo.")

        duracion = int(data.get("duracion_minutos") or data.get("duracion_estimada_min") or 60)
        if duracion <= 0:
            duracion = 60

        codigo = str(data.get("codigo") or "").strip()
        if not codigo:
            cnt = session.query(Servicios).filter_by(id_empresa=eid).count()
            codigo = f"SRV-E{eid}-{cnt + 1:03d}"

        pub_val = data.get("publicado") if "publicado" in data else data.get("publicado_portal", True)
        srv = Servicios(
            id_empresa=eid,
            codigo=codigo,
            nombre=nombre,
            descripcion=str(data.get("descripcion") or "").strip(),
            categoria=str(data.get("categoria") or "General").strip(),
            precio=precio,
            duracion_minutos=duracion,
            imagen=data.get("imagen") or data.get("imagen_url") or "",
            condiciones=str(data.get("condiciones") or "").strip(),
            estado=data.get("estado", "Activo"),
            publicado=1 if pub_val in (True, 1, "1", "true", "on", "si") else 0,
            disponible=1 if data.get("disponible", True) in (True, 1, "1", "true", "on", "si") else 0,
            requiere_reserva=1 if data.get("requiere_reserva", True) in (True, 1, "1", "true", "on", "si") else 0,
        )
        srv.create()
        return srv

    @staticmethod
    def actualizar_servicio(id_empresa, servicio_id, data):
        srv = Servicios.get_by_id(int(servicio_id))
        if not srv or srv.id_empresa != int(id_empresa):
            return None

        if "nombre" in data and str(data["nombre"]).strip():
            srv.nombre = str(data["nombre"]).strip()
        if "descripcion" in data:
            srv.descripcion = str(data["descripcion"] or "").strip()
        if "categoria" in data:
            srv.categoria = str(data["categoria"] or "General").strip()
        if "precio" in data and data["precio"] is not None:
            prec = float(data["precio"])
            if prec < 0:
                raise ValueError("El precio del servicio no puede ser negativo.")
            srv.precio = prec
        if "duracion_minutos" in data and data["duracion_minutos"] is not None:
            srv.duracion_minutos = max(15, int(data["duracion_minutos"]))
        if "imagen" in data:
            srv.imagen = data["imagen"]
        if "condiciones" in data:
            srv.condiciones = str(data["condiciones"] or "").strip()
        if "estado" in data:
            srv.estado = data["estado"]
        for bf in ("publicado", "disponible", "requiere_reserva"):
            if bf in data:
                setattr(srv, bf, 1 if data[bf] in (True, 1, "1", "true", "on", "si") else 0)

        srv.update()
        return srv

    # =========================================================================
    # 4. AUTENTICACIÓN Y CUENTAS DE CLIENTES EXTERNOS (SEPARADAS DE ADMIN)
    # =========================================================================
    @staticmethod
    def registrar_cuenta_cliente(data):
        email = str(data.get("email") or "").strip().lower()
        if not email or "@" not in email:
            raise ValueError("Ingresa un correo electrónico válido.")

        if CuentasClientes.get_by_email(email):
            raise ValueError(f"Ya existe una cuenta de cliente registrada con el correo '{email}'.")

        password = data.get("password")
        valida_pol, msg_pol = validar_politica_password(password)
        if not valida_pol:
            raise ValueError(msg_pol)

        nombre = str(data.get("nombre") or "").strip()
        if not nombre:
            raise ValueError("El nombre es obligatorio.")

        documento = str(data.get("documento") or "").strip()
        if not documento:
            raise ValueError("El número de documento es obligatorio.")

        telefono = str(data.get("telefono") or "").strip()
        if not telefono:
            raise ValueError("El teléfono de contacto es obligatorio.")

        direccion = str(data.get("direccion") or data.get("direccion_principal") or "").strip()
        ciudad = str(data.get("ciudad") or "").strip()

        cuenta = CuentasClientes(
            tipo_documento=str(data.get("tipo_documento") or "CC").strip().upper(),
            documento=documento,
            nombre=nombre,
            apellido=str(data.get("apellido") or "").strip(),
            email=email,
            telefono=telefono,
            direccion_principal=direccion,
            ciudad=ciudad,
            password_hash=hash_password(password),
            estado="Activo",
            email_verificado=1,
            sesion_version=1
        )
        cuenta.save()

        if direccion:
            dir_obj = DireccionesClientes(
                id_cuenta_cliente=cuenta.id,
                alias="Principal",
                direccion=direccion,
                ciudad=ciudad,
                telefono_contacto=telefono,
                es_principal=1
            )
            dir_obj.save()

        # Si el registro se originó en el portal de una empresa específica, asegurar su ficha comercial
        emp_id = data.get("id_empresa") or data.get("empresa_id")
        if emp_id and str(emp_id).isdigit():
            try:
                PortalController.asegurar_ficha_comercial_cliente(cuenta, int(emp_id))
            except Exception:
                pass

        return cuenta

    @staticmethod
    def login_cuenta_cliente(email, password, id_empresa=None):
        if not email or not password:
            return {"exito": False, "mensaje": "Correo electrónico y contraseña requeridos."}, 400

        cuenta = CuentasClientes.get_by_email(email)
        if not cuenta or not verify_password(cuenta.password_hash, password):
            return {"exito": False, "mensaje": "Correo o contraseña incorrectos."}, 401

        if (cuenta.estado or "Activo") != "Activo":
            return {"exito": False, "mensaje": "Tu cuenta se encuentra inactiva."}, 403

        if id_empresa and str(id_empresa).isdigit():
            try:
                PortalController.asegurar_ficha_comercial_cliente(cuenta, int(id_empresa))
            except Exception:
                pass

        claims = {
            "identity_type": "cliente",
            "cuenta_cliente_id": cuenta.id,
            "email": cuenta.email,
            "nombre": cuenta.nombre_completo,
            "documento": cuenta.documento,
            "sesion_version": cuenta.sesion_version or 1,
        }
        access_token = create_access_token(
            identity=str(cuenta.id),
            additional_claims=claims,
            expires_delta=timedelta(hours=4)
        )
        refresh_token = create_refresh_token(
            identity=str(cuenta.id),
            additional_claims=claims,
            expires_delta=timedelta(days=30)
        )

        return {
            "exito": True,
            "mensaje": "Bienvenido al portal de clientes",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "cliente": cuenta.to_dict()
        }, 200

    @staticmethod
    def solicitar_recuperacion_cliente(email):
        if not email or not str(email).strip():
            return {"exito": False, "mensaje": "Ingresa tu correo electrónico registrado."}, 400

        mensaje_generico = (
            "Si el correo electrónico corresponde a una cuenta activa, hemos enviado un código "
            "de verificación para restablecer tu contraseña."
        )
        cuenta = CuentasClientes.get_by_email(email)
        if not cuenta or (cuenta.estado or "Activo") != "Activo":
            return {"exito": True, "mensaje": mensaje_generico}, 200

        otp_codigo = f"{secrets.randbelow(900000) + 100000}"
        token = secrets.token_urlsafe(32)
        TokensSeguridad.crear_token(
            tipo="password_recovery",
            identidad_tipo="cliente",
            identidad_id=cuenta.id,
            codigo=otp_codigo,
            token=token,
            minutos_expiracion=30,
            max_intentos=5
        )
        Mailer.enviar_codigo_recuperacion(
            destinatario=cuenta.email,
            nombre=cuenta.nombre_completo,
            otp_codigo=otp_codigo,
            link_recuperacion=""
        )
        return {"exito": True, "mensaje": mensaje_generico}, 200

    @staticmethod
    def confirmar_recuperacion_cliente(token_o_codigo, password_nueva, email=None):
        if not token_o_codigo:
            return {"exito": False, "mensaje": "El código de verificación es obligatorio."}, 400

        valida_pol, msg_pol = validar_politica_password(password_nueva)
        if not valida_pol:
            return {"exito": False, "mensaje": msg_pol}, 400

        cid = None
        if email:
            c_obj = CuentasClientes.get_by_email(email)
            if c_obj:
                cid = c_obj.id

        clave = str(token_o_codigo).strip()
        if len(clave) > 12:
            reg, err = TokensSeguridad.validar_y_consumir("password_recovery", "cliente", token=clave)
        else:
            reg, err = TokensSeguridad.validar_y_consumir("password_recovery", "cliente", identidad_id=cid, codigo=clave)

        if err or not reg:
            return {"exito": False, "mensaje": err or "Código inválido o expirado."}, 400

        cuenta = CuentasClientes.get_by_id(reg.identidad_id)
        if not cuenta:
            return {"exito": False, "mensaje": "Cuenta no encontrada."}, 404

        cuenta.password_hash = hash_password(password_nueva)
        cuenta.sesion_version = (cuenta.sesion_version or 1) + 1
        cuenta.update()
        return {"exito": True, "mensaje": "Contraseña actualizada exitosamente. Ya puedes iniciar sesión."}, 200

    @staticmethod
    def asegurar_ficha_comercial_cliente(cuenta: CuentasClientes, id_empresa: int):
        """
        Obtiene o crea la ficha comercial (`Clientes`) de `cuenta` dentro de `id_empresa`,
        y registra la vinculación en `VinculacionesClientes`.
        Protección anti-suplantación:
        - Si ya existe una ficha en `Clientes` con el mismo documento en `id_empresa`,
          solo se marca como 'Verificado' para consultar facturas previas si el correo coincide.
          Si el correo no coincide, la vinculación queda con `estado_verificacion='Pendiente'` hasta
          que confirme el código OTP enviado al correo registrado en la ficha comercial.
        """
        eid = int(id_empresa)
        vinc = session.query(VinculacionesClientes).filter_by(
            id_cuenta_cliente=cuenta.id,
            id_empresa=eid
        ).first()
        if vinc:
            cli = Clientes.get_by_id(vinc.id_cliente)
            if cli:
                return cli, vinc

        cli_existente = Clientes.get_by_documento(cuenta.documento, empresa_id=eid)
        if cli_existente:
            email_ficha = (cli_existente.email or "").strip().lower()
            email_cuenta = (cuenta.email or "").strip().lower()
            es_email_autogenerado = email_ficha.endswith("@correo.com")
            verificado = (email_ficha == email_cuenta) or es_email_autogenerado

            if es_email_autogenerado:
                cli_existente.email = cuenta.email
                cli_existente.update()

            vinc = VinculacionesClientes(
                id_cuenta_cliente=cuenta.id,
                id_empresa=eid,
                id_cliente=cli_existente.id,
                estado_verificacion="Verificado" if verificado else "Pendiente",
                metodo_verificacion="coincidencia_email" if verificado else "requiere_otp_ficha",
                verified_at=datetime.now() if verificado else None
            )
            vinc.save()
            return cli_existente, vinc

        # Crear nueva ficha comercial para este cliente en esta empresa
        count = session.query(Clientes).filter(Clientes.id_empresa == eid).count()
        nuevo_cli = Clientes(
            documento=cuenta.documento,
            tipo_documento=cuenta.tipo_documento or "CC",
            nombre=cuenta.nombre,
            apellido=cuenta.apellido or "",
            codigo=f"CLI-E{eid}-{count + 1:03d}",
            direccion=cuenta.direccion_principal or "Dirección Portal",
            telefono=cuenta.telefono or "3000000000",
            email=cuenta.email,
            estado="Activo",
            id_empresa=eid
        )
        try:
            nuevo_cli.save()
        except Exception:
            session.rollback()
            nuevo_cli.documento = f"{cuenta.documento}#E{eid}"
            nuevo_cli.save()

        vinc = VinculacionesClientes(
            id_cuenta_cliente=cuenta.id,
            id_empresa=eid,
            id_cliente=nuevo_cli.id,
            estado_verificacion="Verificado",
            metodo_verificacion="creacion_portal",
            verified_at=datetime.now()
        )
        vinc.save()
        return nuevo_cli, vinc

    @staticmethod
    def solicitar_otp_vinculacion_ficha(cuenta: CuentasClientes, id_empresa: int):
        """Envía un código OTP al correo de la ficha comercial preexistente para verificar titularidad."""
        cli, vinc = PortalController.asegurar_ficha_comercial_cliente(cuenta, int(id_empresa))
        if vinc.estado_verificacion == "Verificado":
            return {"exito": True, "mensaje": "Tu perfil comercial en esta empresa ya se encuentra verificado."}, 200

        otp = f"{secrets.randbelow(900000) + 100000}"
        TokensSeguridad.crear_token(
            tipo="client_linking",
            identidad_tipo="cliente",
            identidad_id=cuenta.id,
            id_empresa=int(id_empresa),
            codigo=otp,
            minutos_expiracion=15,
            max_intentos=5
        )
        Mailer.enviar_codigo_recuperacion(
            destinatario=cli.email,
            nombre=cli.nombre,
            otp_codigo=otp,
            link_recuperacion=""
        )
        return {
            "exito": True,
            "mensaje": "Se envió un código de verificación al correo registrado en tu ficha comercial de la empresa."
        }, 200

    @staticmethod
    def confirmar_otp_vinculacion_ficha(cuenta: CuentasClientes, id_empresa: int, codigo_otp: str):
        reg, err = TokensSeguridad.validar_y_consumir(
            tipo="client_linking",
            identidad_tipo="cliente",
            identidad_id=cuenta.id,
            id_empresa=int(id_empresa),
            codigo=str(codigo_otp or "").strip()
        )
        if err or not reg:
            return {"exito": False, "mensaje": err or "Código inválido."}, 400

        vinc = session.query(VinculacionesClientes).filter_by(
            id_cuenta_cliente=cuenta.id,
            id_empresa=int(id_empresa)
        ).first()
        if vinc:
            vinc.estado_verificacion = "Verificado"
            vinc.metodo_verificacion = "otp_verificado"
            vinc.verified_at = datetime.now()
            vinc.update()
        return {"exito": True, "mensaje": "Vínculo comercial verificado correctamente."}, 200

    # =========================================================================
    # 5. VALIDACIÓN DE CARRITO Y PROCESAMIENTO TRANSACCIONAL DE PEDIDOS
    # =========================================================================
    @staticmethod
    def validar_carrito(id_empresa, items, modalidad_entrega="Domicilio"):
        """
        Valida cada ítem del carrito contra la base de datos en tiempo real:
        - Producto existente, activo, publicado, disponible y perteneciente a `id_empresa`.
        - Cantidad > 0 y stock suficiente.
        - Calcula precios, subtotales, costo de envío y total exclusivamente en el backend.
        """
        eid = int(id_empresa)
        empresa = Empresas.get_by_id(eid)
        if not empresa or (empresa.estado or "Activo") != "Activo":
            raise ValueError("La empresa seleccionada no se encuentra disponible.")

        cfg = ConfiguracionPortal.get_or_create_for_empresa(empresa)
        if not cfg.activo or not cfg.permitir_pedidos:
            raise ValueError("La recepción de pedidos en línea no está habilitada para esta empresa.")

        if not items or not isinstance(items, list):
            raise ValueError("El carrito de compras está vacío.")

        # Consolidar cantidades si el mismo producto viene repetido en el array
        cantidades_por_prod = {}
        for raw_item in items:
            if not isinstance(raw_item, dict):
                continue
            pid = raw_item.get("id_producto") or raw_item.get("id")
            if not pid or not str(pid).isdigit():
                raise ValueError("Identificador de producto inválido en el carrito.")
            try:
                cant = int(raw_item.get("cantidad", 1))
            except (ValueError, TypeError):
                raise ValueError("La cantidad solicitada debe ser un número entero válido.")
            if cant <= 0:
                raise ValueError("La cantidad de cada producto debe ser mayor a cero.")
            pid_int = int(pid)
            cantidades_por_prod[pid_int] = cantidades_por_prod.get(pid_int, 0) + cant

        if not cantidades_por_prod:
            raise ValueError("El carrito de compras no contiene productos válidos.")

        items_validados = []
        subtotal_general = 0.0

        for pid_int, cant_total in cantidades_por_prod.items():
            prod = Productos.get_by_id(pid_int)
            if not prod:
                raise ValueError(f"El producto #{pid_int} no existe.")
            if prod.id_empresa != eid:
                raise ValueError(f"El producto '{prod.nombre}' no pertenece a la empresa seleccionada.")
            if (prod.estado or "Activo") != "Activo":
                raise ValueError(f"El producto '{prod.nombre}' ya no está activo.")
            pub = getattr(prod, "publicado_portal", 1)
            disp = getattr(prod, "disponible_portal", 1)
            if (pub is not None and not bool(pub)) or (disp is not None and not bool(disp)):
                raise ValueError(f"El producto '{prod.nombre}' no está disponible para compra en línea.")
            if (prod.stock or 0) < cant_total:
                raise ValueError(
                    f"Stock insuficiente para '{prod.nombre}' (disponible: {prod.stock or 0}, solicitado: {cant_total})."
                )

            precio_pub = getattr(prod, "precio_publico", None)
            precio_u = float(precio_pub if (precio_pub is not None and precio_pub > 0) else (prod.precio or 0.0))
            if precio_u < 0:
                raise ValueError(f"Precio inválido para '{prod.nombre}'.")

            sub_item = round(precio_u * cant_total, 2)
            subtotal_general = round(subtotal_general + sub_item, 2)
            items_validados.append({
                "producto_obj": prod,
                "id_producto": prod.id,
                "codigo_producto": prod.codigo,
                "nombre_producto": prod.nombre,
                "unidad_medida": prod.unidad_medida or "UND",
                "cantidad": cant_total,
                "precio_unitario": precio_u,
                "subtotal": sub_item,
                "stock_disponible": prod.stock,
                "imagen": getattr(prod, "imagen_publica", None) or prod.imagen,
            })

        modalidades_permitidas = [m.strip() for m in (cfg.modalidades_entrega or "Domicilio,Recoger en tienda").split(",") if m.strip()]
        mod_entrega = str(modalidad_entrega or "Domicilio").strip()
        if modalidades_permitidas and mod_entrega not in modalidades_permitidas:
            mod_entrega = modalidades_permitidas[0]

        costo_envio = round(float(cfg.costo_envio_base or 0.0), 2) if mod_entrega.lower().startswith("domicilio") else 0.0
        iva = 0.0
        descuento = 0.0
        total = round(subtotal_general + iva - descuento + costo_envio, 2)

        return {
            "id_empresa": eid,
            "modalidad_entrega": mod_entrega,
            "subtotal": subtotal_general,
            "iva": iva,
            "descuento": descuento,
            "costo_envio": costo_envio,
            "total": total,
            "items": items_validados,
        }

    @staticmethod
    def obtener_siguiente_numero_pedido(id_empresa):
        eid = int(id_empresa)
        prefix = f"PED-E{eid}-"
        pedidos = session.query(Pedidos).filter(Pedidos.id_empresa == eid).all()
        max_num = 0
        for p in pedidos:
            if p.numero and p.numero.startswith(prefix):
                try:
                    n = int(p.numero.replace(prefix, "").strip())
                    if n > max_num:
                        max_num = n
                except ValueError:
                    pass
        return f"{prefix}{max_num + 1:04d}"

    @staticmethod
    def crear_pedido(cuenta: CuentasClientes, id_empresa: int, data: dict):
        """
        Registra un nuevo pedido del Portal de Clientes de forma transaccional:
        - Valida disponibilidad, precios y pertenencia de cada producto en el servidor.
        - Reserva/descuenta el stock para evitar sobreventa por concurrencia.
        - Guarda instantánea histórica en `DetallePedidos` y bitácora en `HistorialPedidos`.
        - Dispara notificaciones para la empresa y para el cliente.
        """
        eid = int(id_empresa)
        items_req = data.get("items") or data.get("detalles") or []
        modalidad = data.get("modalidad_entrega", "Domicilio")

        resumen = PortalController.validar_carrito(eid, items_req, modalidad_entrega=modalidad)
        mod_final = resumen["modalidad_entrega"]

        direccion_entrega = str(data.get("direccion_entrega") or cuenta.direccion_principal or "").strip()
        ciudad_entrega = str(data.get("ciudad_entrega") or cuenta.ciudad or "").strip()
        telefono_contacto = str(data.get("telefono_contacto") or cuenta.telefono or "").strip()

        if mod_final.lower().startswith("domicilio") and not direccion_entrega:
            raise ValueError("Debes indicar la dirección de entrega para pedidos a domicilio.")

        cli_comercial, _ = PortalController.asegurar_ficha_comercial_cliente(cuenta, eid)

        id_mp = data.get("id_metodo_pago")
        metodo_nombre = str(data.get("metodo_pago") or "Efectivo / Contraentrega").strip()
        if id_mp and str(id_mp).isdigit():
            mp_obj = MetodosPago.get_by_id(int(id_mp))
            if mp_obj:
                if mp_obj.id_empresa and int(mp_obj.id_empresa) != eid:
                    raise ValueError("El método de pago seleccionado no pertenece a esta empresa.")
                metodo_nombre = mp_obj.nombre
                id_mp = mp_obj.id
            else:
                id_mp = 1
        else:
            id_mp = 1

        try:
            numero_ped = PortalController.obtener_siguiente_numero_pedido(eid)
            pedido = Pedidos(
                numero=numero_ped,
                id_empresa=eid,
                id_cuenta_cliente=cuenta.id,
                id_cliente=cli_comercial.id,
                estado="Pendiente",
                modalidad_entrega=mod_final,
                direccion_entrega=direccion_entrega or "Recoger en tienda",
                ciudad_entrega=ciudad_entrega,
                telefono_contacto=telefono_contacto,
                notas_cliente=str(data.get("notas_cliente") or "").strip(),
                subtotal=resumen["subtotal"],
                iva=resumen["iva"],
                descuento=resumen["descuento"],
                costo_envio=resumen["costo_envio"],
                total=resumen["total"],
                id_metodo_pago=id_mp,
                metodo_pago_nombre=metodo_nombre,
                estado_pago="Pendiente",
                inventario_descontado=1,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            session.add(pedido)
            session.flush()

            for item in resumen["items"]:
                prod = item["producto_obj"]
                cant = item["cantidad"]
                if (prod.stock or 0) < cant:
                    raise ValueError(f"Stock insuficiente para '{prod.nombre}' al confirmar el pedido.")

                det = DetallePedidos(
                    id_pedido=pedido.id,
                    id_producto=prod.id,
                    codigo_producto=item["codigo_producto"],
                    nombre_producto=item["nombre_producto"],
                    unidad_medida=item["unidad_medida"],
                    cantidad=cant,
                    precio_unitario=item["precio_unitario"],
                    descuento_item=0.0,
                    subtotal=item["subtotal"]
                )
                session.add(det)

                prod.stock = (prod.stock or 0) - cant
                session.add(prod)

                mov = MovimientosInventario(
                    tipo_movimiento="SALIDA",
                    cantidad=cant,
                    observacion=f"Pedido Portal Clientes {pedido.numero}",
                    id_producto=prod.id,
                    id_usuario=1,
                    id_empresa=eid
                )
                session.add(mov)

            hist = HistorialPedidos(
                id_pedido=pedido.id,
                estado_anterior=None,
                estado_nuevo="Pendiente",
                comentario="Pedido registrado por el cliente desde el Portal Web.",
                actor_tipo="cliente",
                actor_id=cuenta.id,
                created_at=datetime.now()
            )
            session.add(hist)

            Notificaciones.registrar(
                id_empresa=eid,
                destinatario_tipo="empresa",
                tipo="pedido",
                titulo=f"Nuevo pedido recibido: {pedido.numero}",
                mensaje=f"El cliente {cuenta.nombre_completo} realizó el pedido {pedido.numero} por ${pedido.total:,.2f}.",
                referencia_id=pedido.id,
                commit=False
            )
            Notificaciones.registrar(
                id_empresa=eid,
                destinatario_tipo="cliente",
                id_cuenta_cliente=cuenta.id,
                tipo="pedido",
                titulo=f"Pedido {pedido.numero} recibido",
                mensaje=f"Hemos recibido tu pedido {pedido.numero} por ${pedido.total:,.2f}. Te notificaremos cada avance.",
                referencia_id=pedido.id,
                commit=False
            )

            session.commit()
            return pedido
        except Exception:
            session.rollback()
            raise

    @staticmethod
    def actualizar_estado_pedido(id_empresa, pedido_id, nuevo_estado, comentario=None,
                                 actor_tipo="admin", actor_id=None, estado_pago=None,
                                 notas_internas=None, generar_factura=False):
        eid = int(id_empresa)
        pedido = Pedidos.get_by_id(int(pedido_id))
        if not pedido or pedido.id_empresa != eid:
            return None

        normalizacion_estados = {
            "En preparacion": "En preparación",
            "Listo para entrega": "Listo para recoger",
        }
        if nuevo_estado in normalizacion_estados:
            nuevo_estado = normalizacion_estados[nuevo_estado]
        if nuevo_estado and nuevo_estado not in Pedidos.ESTADOS_VALIDOS:
            raise ValueError(f"Estado de pedido inválido: '{nuevo_estado}'.")

        estado_ant = pedido.estado

        # Si el cliente solicita cancelar, solo puede hacerlo si el pedido sigue Pendiente o Confirmado y no Enviado/Entregado
        if actor_tipo == "cliente" and nuevo_estado == "Cancelado":
            if estado_ant in ("Enviado", "Entregado", "Cancelado"):
                raise ValueError(f"No es posible cancelar un pedido que ya se encuentra en estado '{estado_ant}'.")

        try:
            if nuevo_estado and nuevo_estado != estado_ant:
                pedido.estado = nuevo_estado

                # Si pasa a Cancelado y tenía stock descontado, devolver stock al inventario
                if nuevo_estado == "Cancelado" and pedido.inventario_descontado:
                    detalles = session.query(DetallePedidos).filter_by(id_pedido=pedido.id).all()
                    for det in detalles:
                        prod = Productos.get_by_id(det.id_producto)
                        if prod and prod.id_empresa == eid:
                            prod.stock = (prod.stock or 0) + det.cantidad
                            session.add(prod)
                            session.add(MovimientosInventario(
                                tipo_movimiento="ENTRADA",
                                cantidad=det.cantidad,
                                observacion=f"Reverso por cancelación de Pedido {pedido.numero}",
                                id_producto=prod.id,
                                id_usuario=actor_id or 1,
                                id_empresa=eid
                            ))
                    pedido.inventario_descontado = 0

                # Si se reactiva un pedido cancelado, volver a descontar stock validando disponibilidad
                elif estado_ant == "Cancelado" and nuevo_estado != "Cancelado" and not pedido.inventario_descontado:
                    detalles = session.query(DetallePedidos).filter_by(id_pedido=pedido.id).all()
                    for det in detalles:
                        prod = Productos.get_by_id(det.id_producto)
                        if not prod or (prod.stock or 0) < det.cantidad:
                            raise ValueError(f"Stock insuficiente para reactivar el pedido ({det.nombre_producto}).")
                        prod.stock = (prod.stock or 0) - det.cantidad
                        session.add(prod)
                        session.add(MovimientosInventario(
                            tipo_movimiento="SALIDA",
                            cantidad=det.cantidad,
                            observacion=f"Reactivación de Pedido {pedido.numero}",
                            id_producto=prod.id,
                            id_usuario=actor_id or 1,
                            id_empresa=eid
                        ))
                    pedido.inventario_descontado = 1

                session.add(HistorialPedidos(
                    id_pedido=pedido.id,
                    estado_anterior=estado_ant,
                    estado_nuevo=nuevo_estado,
                    comentario=comentario or f"Estado actualizado a {nuevo_estado}",
                    actor_tipo=actor_tipo,
                    actor_id=actor_id,
                    created_at=datetime.now()
                ))

                if pedido.id_cuenta_cliente:
                    Notificaciones.registrar(
                        id_empresa=eid,
                        destinatario_tipo="cliente",
                        id_cuenta_cliente=pedido.id_cuenta_cliente,
                        tipo="pedido",
                        titulo=f"Actualización de tu pedido {pedido.numero}: {nuevo_estado}",
                        mensaje=comentario or f"Tu pedido {pedido.numero} ahora se encuentra en estado '{nuevo_estado}'.",
                        referencia_id=pedido.id,
                        commit=False
                    )

            if estado_pago in ("Pendiente", "Pagado", "Rechazado", "Reembolsado"):
                pedido.estado_pago = estado_pago

            if notas_internas is not None:
                pedido.notas_internas = str(notas_internas).strip()

            # Generación controlada de Factura Comercial si se solicita y el pedido aún no tiene factura
            if generar_factura and not pedido.id_factura and pedido.estado != "Cancelado":
                from src.controllers.facturas_controller import FacturasController
                num_fac = FacturasController.obtener_siguiente_numero(eid)
                fac = Facturas(
                    numero=num_fac,
                    fecha=datetime.now(),
                    subtotal=pedido.subtotal,
                    iva=pedido.iva,
                    descuento=pedido.descuento,
                    total=pedido.total,
                    id_cliente=pedido.id_cliente,
                    id_usuario=actor_id or 1,
                    id_metodo_pago=pedido.id_metodo_pago or 1,
                    estado="Pagada" if pedido.estado_pago == "Pagado" else "Emitida",
                    id_empresa=eid,
                    pasarela=pedido.pasarela or "portal",
                    referencia_pago=pedido.referencia_pago or pedido.numero
                )
                session.add(fac)
                session.flush()
                for det in session.query(DetallePedidos).filter_by(id_pedido=pedido.id).all():
                    session.add(DetalleFacturas(
                        id_factura=fac.id,
                        id_producto=det.id_producto,
                        cantidad=det.cantidad,
                        precio_unitario=det.precio_unitario,
                        subtotal=det.subtotal
                    ))
                pedido.id_factura = fac.id

            pedido.updated_at = datetime.now()
            session.commit()
            return pedido
        except Exception:
            session.rollback()
            raise

    # =========================================================================
    # 6. RESERVAS Y AGENDAMIENTO DE SERVICIOS CON CONTROL DE CONCURRENCIA
    # =========================================================================
    @staticmethod
    def _calcular_hora_fin(hora_inicio: str, duracion_minutos: int) -> str:
        partes = str(hora_inicio).strip().split(":")
        if len(partes) < 2:
            raise ValueError("Formato de hora inválido. Usa HH:MM.")
        h, m = int(partes[0]), int(partes[1])
        if h < 0 or h > 23 or m < 0 or m > 59:
            raise ValueError("Hora fuera de rango válido (00:00 - 23:59).")
        dt_ini = datetime(2026, 1, 1, h, m)
        dt_fin = dt_ini + timedelta(minutes=max(15, int(duracion_minutos or 60)))
        return dt_fin.strftime("%H:%M")

    @staticmethod
    def verificar_conflicto_horario(id_empresa, id_servicio, fecha_reserva, hora_inicio, hora_fin,
                                    profesional="General", exclude_reserva_id=None):
        """
        Verifica si existe otra reserva activa (no Cancelada) que se solape en la misma fecha,
        empresa y servicio/profesional: (inicio_existente < nuevo_fin) AND (fin_existente > nuevo_inicio).
        """
        q = session.query(Reservas).filter(
            Reservas.id_empresa == int(id_empresa),
            Reservas.fecha_reserva == str(fecha_reserva).strip(),
            Reservas.estado != "Cancelada"
        )
        if exclude_reserva_id:
            q = q.filter(Reservas.id != int(exclude_reserva_id))

        prof_clean = str(profesional or "General").strip().lower()
        existentes = q.all()
        for r in existentes:
            mismo_servicio = (r.id_servicio == int(id_servicio))
            mismo_prof = ((r.profesional or "General").strip().lower() == prof_clean)
            if mismo_servicio or mismo_prof:
                if r.hora_inicio < hora_fin and r.hora_fin > hora_inicio:
                    return r
        return None

    @staticmethod
    def obtener_horarios_disponibles(id_empresa, id_servicio, fecha_reserva):
        eid = int(id_empresa)
        srv = Servicios.get_by_id(int(id_servicio))
        if not srv or srv.id_empresa != eid:
            raise ValueError("Servicio no encontrado en esta empresa.")

        duracion = max(30, int(srv.duracion_minutos or 60))
        slots = []
        hora_actual = datetime(2026, 1, 1, 8, 0)
        hora_cierre = datetime(2026, 1, 1, 18, 0)

        while hora_actual + timedelta(minutes=duracion) <= hora_cierre:
            h_ini = hora_actual.strftime("%H:%M")
            h_fin = (hora_actual + timedelta(minutes=duracion)).strftime("%H:%M")
            conflicto = PortalController.verificar_conflicto_horario(eid, srv.id, fecha_reserva, h_ini, h_fin)
            slots.append({
                "hora_inicio": h_ini,
                "hora_fin": h_fin,
                "disponible": conflicto is None
            })
            hora_actual += timedelta(minutes=duracion)

        return slots

    @staticmethod
    def crear_reserva(cuenta: CuentasClientes, id_empresa: int, data: dict):
        eid = int(id_empresa)
        empresa = Empresas.get_by_id(eid)
        if not empresa or (empresa.estado or "Activo") != "Activo":
            raise ValueError("La empresa seleccionada no está disponible.")

        cfg = ConfiguracionPortal.get_or_create_for_empresa(empresa)
        if not cfg.activo or not cfg.permitir_reservas:
            raise ValueError("El agendamiento de reservas no está habilitado para esta empresa.")

        id_servicio = data.get("id_servicio")
        if not id_servicio or not str(id_servicio).isdigit():
            raise ValueError("Debes seleccionar un servicio válido.")

        srv = Servicios.get_by_id(int(id_servicio))
        if not srv or srv.id_empresa != eid or srv.estado != "Activo" or not srv.publicado or not srv.disponible:
            raise ValueError("El servicio seleccionado no está disponible para reservas en esta empresa.")

        fecha_reserva = str(data.get("fecha_reserva") or "").strip()
        hora_inicio = str(data.get("hora_inicio") or "").strip()
        if not fecha_reserva or not hora_inicio:
            raise ValueError("La fecha y hora de inicio son obligatorias para la reserva.")

        try:
            datetime.strptime(fecha_reserva, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Formato de fecha inválido. Utiliza AAAA-MM-DD.")

        hora_fin = PortalController._calcular_hora_fin(hora_inicio, srv.duracion_minutos)
        profesional = str(data.get("profesional") or "General").strip()

        conflicto = PortalController.verificar_conflicto_horario(
            eid, srv.id, fecha_reserva, hora_inicio, hora_fin, profesional=profesional
        )
        if conflicto:
            raise ValueError(
                f"El horario {hora_inicio} - {hora_fin} en la fecha {fecha_reserva} ya se encuentra reservado. "
                "Por favor elige otro horario disponible."
            )

        cli_comercial, _ = PortalController.asegurar_ficha_comercial_cliente(cuenta, eid)
        cnt = session.query(Reservas).filter_by(id_empresa=eid).count()
        numero_res = f"RES-E{eid}-{cnt + 1:04d}"

        reserva = Reservas(
            numero=numero_res,
            id_empresa=eid,
            id_servicio=srv.id,
            id_cuenta_cliente=cuenta.id,
            id_cliente=cli_comercial.id,
            nombre_servicio_historico=srv.nombre,
            precio_historico=float(srv.precio or 0.0),
            duracion_minutos=int(srv.duracion_minutos or 60),
            fecha_reserva=fecha_reserva,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            profesional=profesional,
            estado="Pendiente",
            notas_cliente=str(data.get("notas_cliente") or "").strip(),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        session.add(reserva)
        session.flush()

        Notificaciones.registrar(
            id_empresa=eid,
            destinatario_tipo="empresa",
            tipo="reserva",
            titulo=f"Nueva reserva solicitada: {reserva.numero}",
            mensaje=f"{cuenta.nombre_completo} agendó '{srv.nombre}' para el {fecha_reserva} a las {hora_inicio}.",
            referencia_id=reserva.id,
            commit=False
        )
        Notificaciones.registrar(
            id_empresa=eid,
            destinatario_tipo="cliente",
            id_cuenta_cliente=cuenta.id,
            tipo="reserva",
            titulo=f"Reserva {reserva.numero} registrada",
            mensaje=f"Tu solicitud de reserva para '{srv.nombre}' el {fecha_reserva} ({hora_inicio}) fue recibida.",
            referencia_id=reserva.id,
            commit=False
        )
        session.commit()
        return reserva

    @staticmethod
    def actualizar_reserva(id_empresa, reserva_id, data, actor_tipo="admin"):
        eid = int(id_empresa)
        reserva = Reservas.get_by_id(int(reserva_id))
        if not reserva or reserva.id_empresa != eid:
            return None

        nuevo_estado = data.get("estado")
        nueva_fecha = str(data.get("fecha_reserva") or reserva.fecha_reserva).strip()
        nueva_hora = str(data.get("hora_inicio") or reserva.hora_inicio).strip()
        nuevo_prof = str(data.get("profesional") or reserva.profesional or "General").strip()

        if nueva_fecha != reserva.fecha_reserva or nueva_hora != reserva.hora_inicio:
            nueva_hora_fin = PortalController._calcular_hora_fin(nueva_hora, reserva.duracion_minutos)
            conflicto = PortalController.verificar_conflicto_horario(
                eid, reserva.id_servicio, nueva_fecha, nueva_hora, nueva_hora_fin,
                profesional=nuevo_prof, exclude_reserva_id=reserva.id
            )
            if conflicto:
                raise ValueError(f"El nuevo horario {nueva_hora} - {nueva_hora_fin} del {nueva_fecha} ya está ocupado.")
            reserva.fecha_reserva = nueva_fecha
            reserva.hora_inicio = nueva_hora
            reserva.hora_fin = nueva_hora_fin
            if not nuevo_estado:
                nuevo_estado = "Reprogramada"

        if nuevo_estado == "Atendida":
            nuevo_estado = "Completada"
        if nuevo_estado:
            if nuevo_estado not in Reservas.ESTADOS_VALIDOS:
                raise ValueError(f"Estado de reserva inválido: '{nuevo_estado}'.")
            if actor_tipo == "cliente" and nuevo_estado not in ("Cancelada", "Reprogramada"):
                raise ValueError("Operación no permitida para el cliente.")
            if actor_tipo == "cliente" and reserva.estado in ("Completada", "Cancelada"):
                raise ValueError(f"No se puede modificar una reserva en estado '{reserva.estado}'.")
            reserva.estado = nuevo_estado

        if "profesional" in data:
            reserva.profesional = nuevo_prof
        if "notas_empresa" in data and actor_tipo == "admin":
            reserva.notas_empresa = str(data["notas_empresa"] or "").strip()
        if "notas_cliente" in data and actor_tipo == "cliente":
            reserva.notas_cliente = str(data["notas_cliente"] or "").strip()

        reserva.updated_at = datetime.now()
        if reserva.id_cuenta_cliente:
            Notificaciones.registrar(
                id_empresa=eid,
                destinatario_tipo="cliente",
                id_cuenta_cliente=reserva.id_cuenta_cliente,
                tipo="reserva",
                titulo=f"Reserva {reserva.numero}: {reserva.estado}",
                mensaje=f"Tu reserva de '{reserva.nombre_servicio_historico}' ({reserva.fecha_reserva} {reserva.hora_inicio}) está en estado '{reserva.estado}'.",
                referencia_id=reserva.id,
                commit=False
            )
        session.commit()
        return reserva

    # =========================================================================
    # 7. CONSULTAS / RECLAMOS (PQRS) E HISTORIAL DEL CLIENTE POR EMPRESA
    # =========================================================================
    @staticmethod
    def crear_solicitud_cliente(id_empresa, data, cuenta: CuentasClientes = None):
        eid = int(id_empresa)
        asunto = str(data.get("asunto") or "").strip()
        mensaje = str(data.get("mensaje") or "").strip()
        if not asunto or not mensaje:
            raise ValueError("El asunto y el mensaje son obligatorios.")

        nombre_c = cuenta.nombre_completo if cuenta else str(data.get("nombre_contacto") or "").strip()
        email_c = cuenta.email if cuenta else str(data.get("email_contacto") or "").strip()
        tel_c = cuenta.telefono if cuenta else str(data.get("telefono_contacto") or "").strip()
        if not nombre_c or not email_c:
            raise ValueError("Debes indicar tu nombre y correo electrónico de contacto.")

        id_cli = None
        if cuenta:
            cli_obj, _ = PortalController.asegurar_ficha_comercial_cliente(cuenta, eid)
            id_cli = cli_obj.id

        cnt = session.query(SolicitudesCliente).filter_by(id_empresa=eid).count()
        radicado = f"PQRS-E{eid}-{cnt + 1:04d}"

        sol = SolicitudesCliente(
            radicado=radicado,
            id_empresa=eid,
            id_cuenta_cliente=cuenta.id if cuenta else None,
            id_cliente=id_cli,
            id_pedido=int(data["id_pedido"]) if data.get("id_pedido") and str(data["id_pedido"]).isdigit() else None,
            id_reserva=int(data["id_reserva"]) if data.get("id_reserva") and str(data["id_reserva"]).isdigit() else None,
            nombre_contacto=nombre_c,
            email_contacto=email_c,
            telefono_contacto=tel_c,
            tipo=str(data.get("tipo") or "Consulta").strip(),
            asunto=asunto,
            mensaje=mensaje,
            estado="Abierta",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        session.add(sol)
        session.flush()

        Notificaciones.registrar(
            id_empresa=eid,
            destinatario_tipo="empresa",
            tipo="solicitud",
            titulo=f"Nueva {sol.tipo} recibida ({sol.radicado})",
            mensaje=f"{nombre_c}: {asunto}",
            referencia_id=sol.id,
            commit=False
        )
        session.commit()
        return sol

    @staticmethod
    def responder_solicitud_cliente(id_empresa, solicitud_id, data, usuario_id=None):
        eid = int(id_empresa)
        sol = session.query(SolicitudesCliente).filter_by(id=int(solicitud_id), id_empresa=eid).first()
        if not sol:
            return None

        resp_txt = data.get("respuesta") if "respuesta" in data else data.get("respuesta_empresa")
        if resp_txt and str(resp_txt).strip():
            sol.respuesta = str(resp_txt).strip()
            sol.estado = data.get("estado") or "Respondida"
            sol.respondido_por = int(usuario_id) if usuario_id and str(usuario_id).isdigit() else None
        elif "estado" in data:
            sol.estado = data["estado"]

        sol.updated_at = datetime.now()
        if sol.id_cuenta_cliente:
            Notificaciones.registrar(
                id_empresa=eid,
                destinatario_tipo="cliente",
                id_cuenta_cliente=sol.id_cuenta_cliente,
                tipo="solicitud",
                titulo=f"Respuesta a tu solicitud {sol.radicado}",
                mensaje=sol.respuesta or f"El estado de tu solicitud {sol.radicado} cambió a '{sol.estado}'.",
                referencia_id=sol.id,
                commit=False
            )
        session.commit()
        return sol

    @staticmethod
    def obtener_facturas_cliente_en_empresa(cuenta: CuentasClientes, id_empresa: int):
        """
        Retorna únicamente las facturas autorizadas del cliente dentro de `id_empresa`:
        - Facturas generadas a partir de pedidos realizados por su `id_cuenta_cliente`, o
        - Facturas de su ficha comercial `id_cliente` SIEMPRE Y CUANDO su `VinculacionesClientes`
          en `id_empresa` tenga `estado_verificacion == 'Verificado'`.
        """
        eid = int(id_empresa)
        vinc = session.query(VinculacionesClientes).filter_by(
            id_cuenta_cliente=cuenta.id,
            id_empresa=eid
        ).first()

        facturas_ids = set()
        # Facturas originadas por pedidos del propio cliente en esta empresa
        pedidos_mios = session.query(Pedidos).filter_by(
            id_cuenta_cliente=cuenta.id,
            id_empresa=eid
        ).all()
        for p in pedidos_mios:
            if p.id_factura:
                facturas_ids.add(p.id_factura)

        if vinc and vinc.estado_verificacion == "Verificado":
            facs_ficha = session.query(Facturas).filter_by(
                id_empresa=eid,
                id_cliente=vinc.id_cliente
            ).all()
            for f in facs_ficha:
                facturas_ids.add(f.id)

        if not facturas_ids:
            return []

        facturas = session.query(Facturas).filter(
            Facturas.id.in_(list(facturas_ids)),
            Facturas.id_empresa == eid
        ).order_by(Facturas.id.desc()).all()
        return [f.to_dict() for f in facturas]
