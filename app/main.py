from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from sqlalchemy.exc import DBAPIError
from fastapi.responses import JSONResponse

from .database import Base, engine
from . import models
from .errors import http_desde_db
from .routers import asistentes, clientes, eventos, inscripciones, reportes, salones, servicios, staff


def preparar_base():
    Base.metadata.create_all(bind=engine)
    carpeta = Path(__file__).resolve().parents[1] / "sql"
    conexion = engine.raw_connection()
    try:
        with conexion.cursor() as cursor:
            for archivo in sorted(carpeta.glob("0[2-7]_*.sql")):
                cursor.execute(archivo.read_text(encoding="utf-8"))
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


@asynccontextmanager
async def lifespan(app):
    preparar_base()
    yield


app = FastAPI(title="NexoEventos", version="1.0.0", lifespan=lifespan,
              description="Gestión del centro de convenciones. Fechas en hora de Bogotá. "
                          "Envía X-Usuario al modificar eventos.")


@app.exception_handler(DBAPIError)
async def error_base(request, exc):
    error = http_desde_db(exc)
    return JSONResponse(status_code=error.status_code, content={"detail": error.detail})


for router in (clientes, salones, servicios, staff, asistentes, eventos, inscripciones, reportes):
    app.include_router(router.router)


@app.get("/", tags=["General"])
def inicio():
    return {"servicio": "NexoEventos", "docs": "/docs"}
