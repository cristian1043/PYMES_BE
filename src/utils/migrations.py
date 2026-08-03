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
                    "ALTER TABLE usuarios ADD COLUMN numero_cuenta VARCHAR(50)"
                ]
                for query in columnas_usuarios:
                    try:
                        conn.execute(text(query))
                        conn.commit()
                    except Exception:
                        pass
        except Exception:
            pass
