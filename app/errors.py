from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError


def _mensaje_limpio(exc) -> str:
    """Extrae el mensaje primario del error de PostgreSQL, sin el CONTEXT."""
    orig = getattr(exc, "orig", None)
    diag = getattr(orig, "diag", None)
    if diag is not None and getattr(diag, "message_primary", None):
        return diag.message_primary
    return str(orig) if orig is not None else str(exc)


def http_desde_db(exc: SQLAlchemyError) -> HTTPException:
    """Convierte un error de base en la HTTPException equivalente."""
    orig = getattr(exc, "orig", None)
    pgcode = getattr(orig, "pgcode", None)
    msg = _mensaje_limpio(exc)

    if pgcode == "P0001":
        return HTTPException(status_code=409, detail=msg)
    if pgcode == "23505":
        return HTTPException(status_code=409, detail="Registro duplicado. " + msg)
    if pgcode == "23503":
        return HTTPException(status_code=409, detail="Referencia inexistente. " + msg)
    if pgcode == "23514":
        return HTTPException(status_code=422, detail="Valor fuera de dominio. " + msg)
    if pgcode == "23502":
        return HTTPException(status_code=422, detail="Falta un campo obligatorio. " + msg)
    if pgcode in ("22001", "22003", "22P02"):
        return HTTPException(status_code=422, detail="El valor enviado no cabe en el campo o tiene un formato inválido.")
    return HTTPException(status_code=500, detail="No se pudo completar la operación en la base de datos.")


def commit_o_http(db) -> None:
    """Hace commit; si la base rechaza (trigger/constraint), revierte y
    levanta la HTTPException correspondiente. Centraliza el patron para
    que cada router no repita el try/except."""
    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise http_desde_db(exc)
