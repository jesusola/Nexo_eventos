from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..errors import commit_o_http
from ..models import SalonEntity
from ..schemas import SalonResponse, SalonDisponibleResponse, fecha_bogota

router = APIRouter(prefix="/salones", tags=["Salones"])


@router.get("", response_model=list[SalonResponse])
def listar_salones(
    activo: Optional[bool] = Query(None, description="Filtra por habilitado/deshabilitado"),
    db: Session = Depends(get_db),
):
    q = db.query(SalonEntity)
    if activo is not None:
        q = q.filter(SalonEntity.activo == activo)
    return q.order_by(SalonEntity.capacidad_maxima).all()


@router.get("/disponibles", response_model=list[SalonDisponibleResponse])
def salones_disponibles(
    inicio: datetime = Query(..., description="Inicio de la franja (ISO 8601)"),
    fin: datetime = Query(..., description="Fin de la franja (ISO 8601)"),
    aforo: int = Query(1, ge=1, description="Aforo requerido"),
    db: Session = Depends(get_db),
):
    """A5: salones habilitados, con capacidad y libres en la franja,
    ordenados de menor a mayor con su costo estimado."""
    inicio, fin = fecha_bogota(inicio), fecha_bogota(fin)
    if fin <= inicio:
        raise HTTPException(status_code=422, detail="La fecha/hora de fin debe ser posterior a la de inicio.")
    filas = db.execute(
        text("SELECT * FROM fn_salones_disponibles(:ini, :fin, :aforo)"),
        {"ini": inicio, "fin": fin, "aforo": aforo},
    ).mappings().all()
    return [dict(f) for f in filas]


@router.get("/{salon_id}", response_model=SalonResponse)
def obtener_salon(salon_id: int, db: Session = Depends(get_db)):
    salon = db.get(SalonEntity, salon_id)
    if salon is None:
        raise HTTPException(status_code=404, detail=f"Salón {salon_id} no encontrado.")
    return salon


@router.patch("/{salon_id}/activo", response_model=SalonResponse)
def cambiar_estado_salon(
    salon_id: int,
    activo: bool = Query(..., description="true habilita, false deshabilita"),
    db: Session = Depends(get_db),
):
    salon = db.get(SalonEntity, salon_id)
    if salon is None:
        raise HTTPException(status_code=404, detail=f"Salón {salon_id} no encontrado.")
    salon.activo = activo
    commit_o_http(db)
    db.refresh(salon)
    return salon
