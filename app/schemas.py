from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

Area = Literal["Dirección", "Operaciones", "Comercial", "Logística", "Alimentos y Bebidas", "Audiovisuales"]
TipoEvento = Literal["Congreso", "Conferencia", "Feria", "Seminario", "Corporativo", "Social"]
Estado = Literal["Cotizado", "Confirmado", "Finalizado", "Cancelado"]


def fecha_bogota(valor: datetime) -> datetime:
    if valor.tzinfo is not None:
        return valor.astimezone(ZoneInfo("America/Bogota")).replace(tzinfo=None)
    return valor


class Respuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ClienteCreate(BaseModel):
    documento: str = Field(min_length=5, max_length=20)
    tipo_documento: Literal["NIT", "Cedula"]
    nombre_razon_social: str = Field(min_length=2, max_length=150)
    correo: EmailStr = Field(max_length=150)
    telefono: str = Field(min_length=5, max_length=20)


class ClienteResponse(ClienteCreate, Respuesta):
    id: int
    fecha_registro: datetime


class StaffCreate(BaseModel):
    nombre: str = Field(min_length=2, max_length=150)
    cargo: str = Field(min_length=2, max_length=100)
    area: Area
    correo: EmailStr = Field(max_length=150)
    fecha_ingreso: date
    jefe_id: int | None = Field(None, gt=0)


class StaffResponse(StaffCreate, Respuesta):
    id: int


class AsistenteCreate(BaseModel):
    documento: str = Field(min_length=5, max_length=20)
    nombre: str = Field(min_length=2, max_length=150)
    correo: EmailStr = Field(max_length=150)
    empresa: str | None = Field(None, max_length=150)


class AsistenteResponse(AsistenteCreate, Respuesta):
    id: int


class SalonResponse(Respuesta):
    id: int
    nombre: str
    tamano: str
    capacidad_maxima: int
    precio_hora: Decimal
    activo: bool


class ServicioResponse(Respuesta):
    id: int
    nombre: str
    categoria: str
    unidad_cobro: str
    precio_unitario: Decimal


class EventoCreate(BaseModel):
    cliente_id: int = Field(gt=0)
    salon_id: int = Field(gt=0)
    coordinador_id: int = Field(gt=0)
    nombre: str = Field(min_length=2, max_length=150)
    tipo: TipoEvento
    aforo_esperado: int = Field(gt=0)
    inicio: datetime
    fin: datetime

    _fechas = field_validator("inicio", "fin")(fecha_bogota)

    @model_validator(mode="after")
    def validar_fechas(self):
        if self.fin <= self.inicio:
            raise ValueError("La fecha de fin debe ser posterior a la de inicio")
        return self


class EventoUpdate(BaseModel):
    salon_id: int | None = Field(None, gt=0)
    coordinador_id: int | None = Field(None, gt=0)
    aforo_esperado: int | None = Field(None, gt=0)
    inicio: datetime | None = None
    fin: datetime | None = None

    @field_validator("inicio", "fin")
    @classmethod
    def normalizar(cls, valor):
        return fecha_bogota(valor) if valor else valor

    @model_validator(mode="after")
    def validar_campos(self):
        if any(getattr(self, campo) is None for campo in self.model_fields_set):
            raise ValueError("Los campos enviados no pueden ser null")
        if self.inicio and self.fin and self.fin <= self.inicio:
            raise ValueError("La fecha de fin debe ser posterior a la de inicio")
        return self


class EstadoUpdate(BaseModel):
    estado: Literal["Confirmado", "Finalizado", "Cancelado"]


class EventoResponse(Respuesta):
    id: int
    cliente_id: int
    salon_id: int
    coordinador_id: int
    nombre: str
    tipo: str
    aforo_esperado: int
    inicio: datetime
    fin: datetime
    estado: Estado
    valor_total: Decimal
    precio_salon_congelado: Decimal
    tasa_asistencia: Decimal | None


class ServicioEventoCreate(BaseModel):
    servicio_id: int = Field(gt=0)
    cantidad: Decimal | None = Field(None, gt=0, max_digits=10, decimal_places=2)


class ServicioEventoUpdate(BaseModel):
    cantidad: Decimal = Field(gt=0, max_digits=10, decimal_places=2)


class ServicioEventoResponse(Respuesta):
    id: int
    evento_id: int
    servicio_id: int
    cantidad: Decimal
    precio_congelado: Decimal


class InscripcionCreate(BaseModel):
    asistente_id: int = Field(gt=0)


class InscripcionResponse(Respuesta):
    id: int
    evento_id: int
    asistente_id: int
    fecha_inscripcion: datetime
    hora_checkin: datetime | None


class CheckinRequest(BaseModel):
    documento: str = Field(min_length=5, max_length=20)
    hora_checkin: datetime | None = None

    @field_validator("hora_checkin")
    @classmethod
    def normalizar(cls, valor):
        return fecha_bogota(valor) if valor else valor


class AuditoriaResponse(Respuesta):
    id: int
    evento_id: int
    campo: str
    valor_anterior: str | None
    valor_nuevo: str | None
    usuario_app: str
    fecha: datetime


class SalonDisponibleResponse(BaseModel):
    salon_id: int
    nombre: str
    tamano: str
    capacidad: int
    precio_hora: Decimal
    costo_estimado: Decimal


class EventoDetalleResponse(EventoResponse):
    servicios: list[ServicioEventoResponse]
    inscritos: int
    llegaron: int


class LineaCotizacion(BaseModel):
    id: int
    servicio_id: int
    nombre: str
    unidad_cobro: str
    cantidad: Decimal
    precio_congelado: Decimal
    subtotal: Decimal


class CotizacionResponse(BaseModel):
    evento_id: int
    nombre: str
    estado: Estado
    salon: str
    horas: Decimal
    precio_hora: Decimal
    costo_salon: Decimal
    servicios: list[LineaCotizacion]
    subtotal_servicios: Decimal
    total: Decimal
