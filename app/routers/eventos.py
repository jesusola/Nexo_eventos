from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_usuario, set_usuario_db
from ..errors import commit_o_http
from ..models import (ClienteEntity, SalonEntity, StaffEntity, EventoEntity, ServicioEntity,
                      ServicioEventoEntity, InscripcionEntity, AuditoriaEntity)
from ..schemas import (EventoCreate, EventoUpdate, EstadoUpdate, EventoResponse, EventoDetalleResponse,
                       ServicioEventoCreate, ServicioEventoUpdate, ServicioEventoResponse,
                       CotizacionResponse, AuditoriaResponse, Estado)
from ..utils import obtener_o_404

router = APIRouter(prefix="/eventos", tags=["Eventos"])


def obtener_evento(db, evento_id):
    return obtener_o_404(db, EventoEntity, evento_id, "Evento")


@router.post("", response_model=EventoResponse, status_code=201)
def crear(payload: EventoCreate, db: Session = Depends(get_db)):
    obtener_o_404(db, ClienteEntity, payload.cliente_id, "Cliente")
    obtener_o_404(db, SalonEntity, payload.salon_id, "Salón")
    obtener_o_404(db, StaffEntity, payload.coordinador_id, "Coordinador")
    evento = EventoEntity(**payload.model_dump())
    db.add(evento)
    commit_o_http(db)
    db.refresh(evento)
    return evento


@router.get("", response_model=list[EventoResponse])
def listar(estado: Estado | None = None, cliente_id: int | None = None, db: Session = Depends(get_db)):
    consulta = db.query(EventoEntity)
    if estado: consulta = consulta.filter(EventoEntity.estado == estado)
    if cliente_id: consulta = consulta.filter(EventoEntity.cliente_id == cliente_id)
    return consulta.order_by(EventoEntity.inicio).all()


@router.get("/{evento_id}", response_model=EventoDetalleResponse)
def detalle(evento_id: int, db: Session = Depends(get_db)):
    evento = obtener_evento(db, evento_id)
    inscritos = db.query(InscripcionEntity).filter(InscripcionEntity.evento_id == evento_id)
    datos = EventoResponse.model_validate(evento).model_dump()
    datos.update(servicios=evento.servicios_evento, inscritos=inscritos.count(),
                 llegaron=inscritos.filter(InscripcionEntity.hora_checkin.is_not(None)).count())
    return datos


@router.patch("/{evento_id}", response_model=EventoResponse)
def reprogramar(evento_id: int, payload: EventoUpdate, db: Session = Depends(get_db),
                usuario: str = Depends(get_usuario)):
    evento = obtener_evento(db, evento_id)
    cambios = payload.model_dump(exclude_unset=True)
    if not cambios: raise HTTPException(status_code=422, detail="No se enviaron campos para actualizar.")
    if "salon_id" in cambios: obtener_o_404(db, SalonEntity, cambios["salon_id"], "Salón")
    if "coordinador_id" in cambios: obtener_o_404(db, StaffEntity, cambios["coordinador_id"], "Coordinador")
    set_usuario_db(db, usuario)
    for campo, valor in cambios.items(): setattr(evento, campo, valor)
    commit_o_http(db)
    db.refresh(evento)
    return evento


@router.patch("/{evento_id}/estado", response_model=EventoResponse)
def cambiar_estado(evento_id: int, payload: EstadoUpdate, db: Session = Depends(get_db),
                   usuario: str = Depends(get_usuario)):
    evento = obtener_evento(db, evento_id)
    set_usuario_db(db, usuario)
    evento.estado = payload.estado
    commit_o_http(db)
    db.refresh(evento)
    return evento


@router.post("/{evento_id}/servicios", response_model=ServicioEventoResponse, status_code=201)
def contratar(evento_id: int, payload: ServicioEventoCreate, db: Session = Depends(get_db)):
    obtener_evento(db, evento_id)
    obtener_o_404(db, ServicioEntity, payload.servicio_id, "Servicio")
    linea = ServicioEventoEntity(evento_id=evento_id, **payload.model_dump())
    db.add(linea)
    commit_o_http(db)
    db.refresh(linea)
    return linea


@router.get("/{evento_id}/servicios", response_model=list[ServicioEventoResponse])
def listar_servicios(evento_id: int, db: Session = Depends(get_db)):
    return obtener_evento(db, evento_id).servicios_evento


@router.put("/{evento_id}/servicios/{linea_id}", response_model=ServicioEventoResponse)
def modificar_servicio(evento_id: int, linea_id: int, payload: ServicioEventoUpdate,
                       db: Session = Depends(get_db)):
    linea = obtener_o_404(db, ServicioEventoEntity, linea_id, "Servicio contratado")
    if linea.evento_id != evento_id: raise HTTPException(status_code=404, detail="La línea no pertenece al evento.")
    linea.cantidad = payload.cantidad
    commit_o_http(db)
    db.refresh(linea)
    return linea


@router.delete("/{evento_id}/servicios/{linea_id}", status_code=204)
def quitar_servicio(evento_id: int, linea_id: int, db: Session = Depends(get_db)):
    linea = obtener_o_404(db, ServicioEventoEntity, linea_id, "Servicio contratado")
    if linea.evento_id != evento_id: raise HTTPException(status_code=404, detail="La línea no pertenece al evento.")
    db.delete(linea)
    commit_o_http(db)


@router.get("/{evento_id}/cotizacion", response_model=CotizacionResponse)
def cotizacion(evento_id: int, db: Session = Depends(get_db)):
    evento = obtener_evento(db, evento_id)
    lineas = db.execute(text("""
        SELECT se.id, se.servicio_id, s.nombre, s.unidad_cobro, se.cantidad,
               se.precio_congelado, se.cantidad * se.precio_congelado AS subtotal
        FROM servicios_evento se JOIN servicios s ON s.id = se.servicio_id
        WHERE se.evento_id = :id ORDER BY se.id
    """), {"id": evento_id}).mappings().all()
    base = db.execute(text("""
        SELECT fn_horas_evento(inicio, fin) AS horas,
               ROUND(precio_salon_congelado * fn_horas_evento(inicio, fin), 2) AS costo_salon
        FROM eventos WHERE id = :id
    """), {"id": evento_id}).mappings().one()
    return {"evento_id": evento.id, "nombre": evento.nombre, "estado": evento.estado,
            "salon": evento.salon.nombre, "horas": base["horas"],
            "precio_hora": evento.precio_salon_congelado, "costo_salon": base["costo_salon"],
            "servicios": lineas, "subtotal_servicios": evento.valor_total - base["costo_salon"],
            "total": evento.valor_total}


@router.get("/{evento_id}/auditoria", response_model=list[AuditoriaResponse])
def auditoria(evento_id: int, db: Session = Depends(get_db)):
    obtener_evento(db, evento_id)
    return db.query(AuditoriaEntity).filter(AuditoriaEntity.evento_id == evento_id).order_by(AuditoriaEntity.id).all()
