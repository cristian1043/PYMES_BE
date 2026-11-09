# PYMES_BE - Backend REST API (PYMESOFT)

API RESTful multi-empresa (`X-Empresa-ID`) de **PYMESOFT**, desarrollada en **Python 3**, **Flask 3**, **SQLAlchemy 2**, **Flask-JWT-Extended**, **Flask-Limiter**, **PyMySQL / SQLite** y **Cryptography (Fernet)**.

---

## 🏗️ Arquitectura del Proyecto

```text
PYMES_BE/
├── Dockerfile
├── requirements.txt
└── src/
    ├── app.py                              # Punto de entrada Flask, JWT, CORS, Rate Limiter y registro de 19 Blueprints
    ├── models/                             # Modelos ORM SQLAlchemy (Empresas, PagosMembresia, Facturas, TransaccionesPago, etc.)
    ├── controllers/                        # Controladores de lógica de negocio y persistencia
    ├── routes/                             # Endpoints REST (/api/auth, /api/empresas, /api/membresias, /api/facturas, /api/cobros, /api/webhooks, etc.)
    ├── services/
    │   └── pagos/                          # Orquestadores de cobros de facturas y membresías ($19.900 COP/mes) con Wompi, Bold POS y Simulado
    └── utils/                              # Migraciones automáticas, seguridad multi-tenant, cifrado Fernet, paginación y correo SMTP
```
