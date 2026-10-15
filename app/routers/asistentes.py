from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..errors import commit_o_http
from ..models import AsistenteEntity
from ..schemas import AsistenteCreate, AsistenteResponse

router = APIRouter(prefix="/asistentes", tags=["Asistentes"])


@router.post("", response_model=AsistenteResponse, status_code=status.HTTP_201_CREATED)
def crear_asistente(payload: AsistenteCreate, db: Session = Depends(get_db)):
    asistente = AsistenteEntity(**payload.model_dump())
    db.add(asistente)
    commit_o_http(db)          # 409 si el documento ya existe
    db.refresh(asistente)
    return asistente


@router.get("", response_model=list[AsistenteResponse])
def listar_asistentes(q: str | None = None, db: Session = Depends(get_db)):
    consulta = db.query(AsistenteEntity)
    if q:
        consulta = consulta.filter(AsistenteEntity.nombre.ilike(f"%{q}%") | AsistenteEntity.documento.ilike(f"%{q}%"))
    return consulta.order_by(AsistenteEntity.id).all()


@router.get("/{asistente_id}", response_model=AsistenteResponse)
def obtener_asistente(asistente_id: int, db: Session = Depends(get_db)):
    asistente = db.get(AsistenteEntity, asistente_id)
    if asistente is None:
        raise HTTPException(status_code=404, detail=f"Asistente {asistente_id} no encontrado.")
    return asistente
