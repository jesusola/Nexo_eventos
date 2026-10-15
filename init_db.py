import argparse
from pathlib import Path

from sqlalchemy import text

from app.database import engine
from app.main import preparar_base


def main():
    parser = argparse.ArgumentParser(description="Crear tablas, reglas SQL y datos de NexoEventos")
    parser.add_argument("--con-datos", action="store_true", help="Cargar los datos de demostración en una base sin clientes")
    args = parser.parse_args()
    preparar_base()
    if args.con_datos:
        with engine.connect() as db:
            if db.scalar(text("SELECT COUNT(*) FROM clientes")):
                raise SystemExit("La base ya contiene clientes. No se cargaron datos ni se borró información.")
        conexion = engine.raw_connection()
        try:
            with conexion.cursor() as cursor:
                cursor.execute((Path(__file__).parent / "sql/08_datos_demo.sql").read_text(encoding="utf-8"))
            conexion.commit()
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()
    print("Base lista. Ejecuta: python -m uvicorn main:app --reload")


if __name__ == "__main__":
    main()
