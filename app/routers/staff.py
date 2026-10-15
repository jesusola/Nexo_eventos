from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..errors import commit_o_http
from ..models import StaffEntity
from ..schemas import StaffCreate, StaffResponse
from ..utils import obtener_o_404

router = APIRouter(prefix="/staff", tags=["Staff"])


@router.post("", response_model=StaffResponse, status_code=status.HTTP_201_CREATED)
def crear_staff(payload: StaffCreate, db: Session = Depends(get_db)):
    if payload.jefe_id:
        obtener_o_404(db, StaffEntity, payload.jefe_id, "Jefe")
    data = payload.model_dump(exclude_none=True)
    empleado = StaffEntity(**data)
    db.add(empleado)
    commit_o_http(db)
    db.refresh(empleado)
    return empleado


@router.get("", response_model=list[StaffResponse])
def listar_staff(db: Session = Depends(get_db)):
    return db.query(StaffEntity).order_by(StaffEntity.id).all()


@router.get("/{staff_id}", response_model=StaffResponse)
def obtener_staff(staff_id: int, db: Session = Depends(get_db)):
    empleado = db.get(StaffEntity, staff_id)
    if empleado is None:
        raise HTTPException(status_code=404, detail=f"Empleado {staff_id} no encontrado.")
    return empleado
