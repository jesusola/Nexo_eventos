from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ServicioEntity
from ..schemas import ServicioResponse

router = APIRouter(prefix="/servicios", tags=["Servicios"])


@router.get("", response_model=list[ServicioResponse])
def listar_servicios(db: Session = Depends(get_db)):
    return db.query(ServicioEntity).order_by(ServicioEntity.categoria, ServicioEntity.nombre).all()


@router.get("/{servicio_id}", response_model=ServicioResponse)
def obtener_servicio(servicio_id: int, db: Session = Depends(get_db)):
    servicio = db.get(ServicioEntity, servicio_id)
    if servicio is None:
        raise HTTPException(status_code=404, detail=f"Servicio {servicio_id} no encontrado.")
    return servicio
