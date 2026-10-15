from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import StaffEntity
from ..utils import obtener_o_404

router = APIRouter(prefix="/reportes", tags=["Reportes"])


def filas(db, consulta, parametros=None):
    resultado = db.execute(text(consulta), parametros or {}).mappings().all()
    return [{k: str(v) if isinstance(v, Decimal) else v for k, v in fila.items()} for fila in resultado]


@router.get("/organigrama")
def organigrama(staff_id: int | None = None, db: Session = Depends(get_db)):
    """Lista toda la organización o los subordinados de un empleado."""
    if staff_id is None:
        return filas(db, "SELECT * FROM vw_organigrama ORDER BY ruta_ids")
    obtener_o_404(db, StaffEntity, staff_id, "Empleado")
    return filas(db, "SELECT * FROM vw_organigrama WHERE :id = ANY(ruta_ids) AND id <> :id ORDER BY ruta_ids", {"id": staff_id})


@router.get("/escalamiento/{staff_id}")
def escalamiento(staff_id: int, db: Session = Depends(get_db)):
    """Devuelve los jefes desde el inmediato hasta la dirección."""
    obtener_o_404(db, StaffEntity, staff_id, "Empleado")
    return filas(db, "SELECT * FROM fn_escalamiento(:id)", {"id": staff_id})


@router.get("/ranking-clientes")
def ranking(db: Session = Depends(get_db)):
    """Facturación, ranking y Pareto de eventos no cancelados."""
    return filas(db, "SELECT * FROM vw_ranking_clientes ORDER BY ranking, cliente_id")


@router.get("/ocupacion-salones")
def ocupacion(db: Session = Depends(get_db)):
    """Eventos por salón, días libres y horas reservadas acumuladas."""
    return filas(db, "SELECT * FROM vw_ocupacion_salones ORDER BY salon_id, num_evento_salon")
