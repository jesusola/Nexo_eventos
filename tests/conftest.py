import os
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
url = os.getenv("NEXO_TEST_DB_URL")
if not url or not any(nombre in url.rsplit("/", 1)[-1] for nombre in ("pruebas", "test")):
    raise RuntimeError("Define NEXO_TEST_DB_URL con una base separada cuyo nombre contenga pruebas o test.")
os.environ["NEXO_DB_URL"] = url

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import engine, get_db
from app.main import app, preparar_base


@pytest.fixture(scope="session", autouse=True)
def preparar():
    preparar_base()
    with engine.connect() as conn:
        vacia = conn.scalar(text("SELECT COUNT(*) FROM clientes")) == 0
    if vacia:
        conn = engine.raw_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute((Path(__file__).resolve().parents[1] / "sql/08_datos_demo.sql").read_text(encoding="utf-8"))
            conn.commit()
        finally:
            conn.close()


@pytest.fixture
def db(preparar):
    conexion = engine.connect()
    transaccion = conexion.begin()
    sesion = Session(bind=conexion, join_transaction_mode="create_savepoint")
    try:
        yield sesion
    finally:
        sesion.close()
        transaccion.rollback()
        conexion.close()


@pytest.fixture
def client(db):
    def sesion_prueba(): yield db
    app.dependency_overrides[get_db] = sesion_prueba
    with TestClient(app, raise_server_exceptions=False) as cliente:
        yield cliente
    app.dependency_overrides.clear()
