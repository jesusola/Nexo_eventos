from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..errors import commit_o_http
from ..models import EventoEntity, AsistenteEntity, InscripcionEntity
from ..schemas import InscripcionCreate, InscripcionResponse, CheckinRequest
from ..utils import obtener_o_404

router = APIRouter(prefix="/eventos", tags=["Inscripciones"])


def _get_evento(db: Session, evento_id: int) -> EventoEntity:
    evento = db.get(EventoEntity, evento_id)
    if evento is None:
        raise HTTPException(status_code=404, detail=f"Evento {evento_id} no encontrado.")
    return evento


@router.post("/{evento_id}/inscripciones", response_model=InscripcionResponse,
             status_code=status.HTTP_201_CREATED)
def inscribir(evento_id: int, payload: InscripcionCreate, db: Session = Depends(get_db)):
    _get_evento(db, evento_id)
    obtener_o_404(db, AsistenteEntity, payload.asistente_id, "Asistente")
    inscripcion = InscripcionEntity(evento_id=evento_id, asistente_id=payload.asistente_id)
    db.add(inscripcion)
    commit_o_http(db)          # A2: 409 si evento cerrado, aforo lleno o ya inscrito
    db.refresh(inscripcion)
    return inscripcion


@router.get("/{evento_id}/inscripciones", response_model=list[InscripcionResponse])
def listar_inscripciones(evento_id: int, db: Session = Depends(get_db)):
    _get_evento(db, evento_id)
    return (db.query(InscripcionEntity)
              .filter(InscripcionEntity.evento_id == evento_id)
              .order_by(InscripcionEntity.id).all())


@router.post("/{evento_id}/checkin", response_model=InscripcionResponse)
def registrar_checkin(evento_id: int, payload: CheckinRequest, db: Session = Depends(get_db)):
    """Registra la asistencia real de un asistente (por su documento).
    Usa la hora indicada o el instante actual. A2 valida la ventana y el
    'una sola vez'."""
    _get_evento(db, evento_id)
    asistente = (db.query(AsistenteEntity)
                   .filter(AsistenteEntity.documento == payload.documento).first())
    if asistente is None:
        raise HTTPException(status_code=404,
                            detail=f"Asistente con documento {payload.documento} no existe.")
    inscripcion = (db.query(InscripcionEntity)
                     .filter(InscripcionEntity.evento_id == evento_id,
                             InscripcionEntity.asistente_id == asistente.id).first())
    if inscripcion is None:
        raise HTTPException(status_code=404,
                            detail="El asistente no está inscrito en este evento.")
    if inscripcion.hora_checkin is not None:
        raise HTTPException(status_code=409, detail="CHECKIN: El asistente ya registró su llegada.")
    inscripcion.hora_checkin = payload.hora_checkin or datetime.now(ZoneInfo("America/Bogota")).replace(tzinfo=None)
    commit_o_http(db)          # A2: 409 fuera de ventana o check-in repetido
    db.refresh(inscripcion)
    return inscripcion
