from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..errors import commit_o_http
from ..models import ClienteEntity, EventoEntity
from ..schemas import ClienteCreate, ClienteResponse, EventoResponse
from ..utils import obtener_o_404

router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.post("", response_model=ClienteResponse, status_code=status.HTTP_201_CREATED)
def crear_cliente(payload: ClienteCreate, db: Session = Depends(get_db)):
    cliente = ClienteEntity(**payload.model_dump())
    db.add(cliente)
    commit_o_http(db)          # 409 si el documento ya existe (UNIQUE)
    db.refresh(cliente)
    return cliente


@router.get("", response_model=list[ClienteResponse])
def listar_clientes(q: str | None = None, db: Session = Depends(get_db)):
    consulta = db.query(ClienteEntity)
    if q:
        consulta = consulta.filter(ClienteEntity.nombre_razon_social.ilike(f"%{q}%") |
                                   ClienteEntity.documento.ilike(f"%{q}%"))
    return consulta.order_by(ClienteEntity.id).all()


@router.get("/{cliente_id}/eventos", response_model=list[EventoResponse])
def eventos_cliente(cliente_id: int, db: Session = Depends(get_db)):
    obtener_o_404(db, ClienteEntity, cliente_id, "Cliente")
    return db.query(EventoEntity).filter(EventoEntity.cliente_id == cliente_id).order_by(EventoEntity.inicio).all()


@router.get("/{cliente_id}", response_model=ClienteResponse)
def obtener_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.get(ClienteEntity, cliente_id)
    if cliente is None:
        raise HTTPException(status_code=404, detail=f"Cliente {cliente_id} no encontrado.")
    return cliente
