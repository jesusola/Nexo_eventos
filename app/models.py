from sqlalchemy import Column, Integer, String, Boolean, Numeric, Date, DateTime, Text, ForeignKey, CheckConstraint, UniqueConstraint, text
from sqlalchemy.orm import relationship
from .database import Base

class ClienteEntity(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True, index=True)
    documento = Column(String(20), nullable=False, unique=True)
    tipo_documento = Column(String(10), nullable=False)
    nombre_razon_social = Column(String(150), nullable=False)
    correo = Column(String(150), nullable=False)
    telefono = Column(String(20), nullable=False)
    fecha_registro = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    eventos = relationship("EventoEntity", back_populates="cliente")
    __table_args__ = (
        CheckConstraint("tipo_documento IN ('NIT', 'Cedula')", name="check_tipo_documento"),
    )


class SalonEntity(Base):
    __tablename__ = "salones"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True)
    tamano = Column(String(10), nullable=False)
    capacidad_maxima = Column(Integer, nullable=False)
    precio_hora = Column(Numeric(12, 2), nullable=False)
    activo = Column(Boolean, nullable=False, server_default=text("TRUE"))
    eventos = relationship("EventoEntity", back_populates="salon")
    __table_args__ = (
        CheckConstraint("tamano IN ('Pequeño', 'Mediano', 'Grande')", name="check_tamano_salon"),
        CheckConstraint("capacidad_maxima > 0", name="check_capacidad_maxima"),
        CheckConstraint("precio_hora > 0", name="check_precio_hora"),
    )


class ServicioEntity(Base):
    __tablename__ = "servicios"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False, unique=True)
    categoria = Column(String(30), nullable=False)
    unidad_cobro = Column(String(15), nullable=False)
    precio_unitario = Column(Numeric(12, 2), nullable=False)
    servicios_evento = relationship("ServicioEventoEntity", back_populates="servicio")
    __table_args__ = (
        CheckConstraint("categoria IN ('Bebidas', 'Refrigerios', 'Audiovisuales')", name="check_categoria_servicio"),
        CheckConstraint("unidad_cobro IN ('Por persona', 'Por hora', 'Por unidad')", name="check_unidad_cobro"),
        CheckConstraint("precio_unitario > 0", name="check_precio_unitario"),
    )

class StaffEntity(Base):
    __tablename__ = "staff"
    id = Column(Integer, primary_key=True, index=True)
    correo = Column(String(150), nullable=False, unique=True)
    jefe_id = Column(Integer, ForeignKey("staff.id"), nullable=True)
    nombre = Column(String(150), nullable=False)
    cargo = Column(String(100), nullable=False)
    area = Column(String(30), nullable=False)
    fecha_ingreso = Column(Date, nullable=False)

    jefe = relationship("StaffEntity", remote_side=[id], back_populates="subordinados")
    subordinados = relationship("StaffEntity", back_populates="jefe")
    eventos_coordinados = relationship("EventoEntity", back_populates="coordinador")

    __table_args__ = (
        CheckConstraint("jefe_id <> id", name="check_jefe_diferente"),
        CheckConstraint("area IN ('Dirección', 'Operaciones', 'Comercial', 'Logística', 'Alimentos y Bebidas', 'Audiovisuales')", name="check_area_staff"),
    )

class EventoEntity(Base):
    __tablename__ = "eventos"
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    salon_id = Column(Integer, ForeignKey("salones.id"), nullable=False)
    coordinador_id = Column(Integer, ForeignKey("staff.id"), nullable=False)
    nombre = Column(String(150), nullable=False)
    tipo = Column(String(30), nullable=False)
    aforo_esperado = Column(Integer, nullable=False)
    inicio = Column(DateTime, nullable=False)
    fin = Column(DateTime, nullable=False)
    estado = Column(String(15), nullable=False, server_default=text("'Cotizado'"))
    valor_total = Column(Numeric(14, 2), nullable=False, server_default=text("0"))
    precio_salon_congelado = Column(Numeric(12, 2), nullable=False)
    tasa_asistencia = Column(Numeric(5, 2), nullable=True)

    cliente = relationship("ClienteEntity", back_populates="eventos")
    salon = relationship("SalonEntity", back_populates="eventos")
    coordinador = relationship("StaffEntity", back_populates="eventos_coordinados")
    inscripciones = relationship("InscripcionEntity", back_populates="evento")
    servicios_evento = relationship("ServicioEventoEntity", back_populates="evento")
    auditorias = relationship("AuditoriaEntity", back_populates="evento")

    __table_args__ = (
        CheckConstraint("tipo IN ('Congreso', 'Conferencia', 'Feria', 'Seminario', 'Corporativo', 'Social')", name="check_tipo_evento"),
        CheckConstraint("aforo_esperado > 0", name="check_aforo_esperado"),
        CheckConstraint("fin > inicio", name="check_fechas_evento"),
        CheckConstraint("estado IN ('Cotizado', 'Confirmado', 'Finalizado', 'Cancelado')", name="check_estado_evento"),
        CheckConstraint("valor_total >= 0", name="check_valor_total"),
        CheckConstraint("precio_salon_congelado > 0", name="check_tarifa_salon"),
        CheckConstraint("tasa_asistencia IS NULL OR (tasa_asistencia >= 0 AND tasa_asistencia <= 100)", name="check_tasa_asistencia"),
    )

class AsistenteEntity(Base):
    __tablename__ = "asistentes"
    id = Column(Integer, primary_key=True, index=True)
    documento = Column(String(20), nullable=False, unique=True)
    nombre = Column(String(150), nullable=False)
    correo = Column(String(150), nullable=False)
    empresa = Column(String(150), nullable=True)

    inscripciones = relationship("InscripcionEntity", back_populates="asistente")

class InscripcionEntity(Base):
    __tablename__ = "inscripciones"
    id = Column(Integer, primary_key=True, index=True)
    evento_id = Column(Integer, ForeignKey("eventos.id"), nullable=False)
    asistente_id = Column(Integer, ForeignKey("asistentes.id"), nullable=False)
    fecha_inscripcion = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    hora_checkin = Column(DateTime, nullable=True)

    evento = relationship("EventoEntity", back_populates="inscripciones")
    asistente = relationship("AsistenteEntity", back_populates="inscripciones")

    __table_args__ = (
        UniqueConstraint("evento_id", "asistente_id", name="unique_evento_asistente"),
    )

class ServicioEventoEntity(Base):
    __tablename__ = "servicios_evento"
    id = Column(Integer, primary_key=True, index=True)
    evento_id = Column(Integer, ForeignKey("eventos.id"), nullable=False)
    servicio_id = Column(Integer, ForeignKey("servicios.id"), nullable=False)
    cantidad = Column(Numeric(10, 2), nullable=False)
    precio_congelado = Column(Numeric(12, 2), nullable=False)

    evento = relationship("EventoEntity", back_populates="servicios_evento")
    servicio = relationship("ServicioEntity", back_populates="servicios_evento")

    __table_args__ = (
        CheckConstraint("cantidad > 0", name="check_cantidad_servicio"),
        CheckConstraint("precio_congelado > 0", name="check_precio_congelado"),
        UniqueConstraint("evento_id", "servicio_id", name="unique_evento_servicio"),
    )

class AuditoriaEntity(Base):
    __tablename__ = "auditoria"
    id = Column(Integer, primary_key=True, index=True)
    evento_id = Column(Integer, ForeignKey("eventos.id"), nullable=False)
    campo = Column(String(30), nullable=False)
    valor_anterior = Column(Text, nullable=True)
    valor_nuevo = Column(Text, nullable=True)
    fecha = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    usuario_app = Column(String(150), nullable=False)

    evento = relationship("EventoEntity", back_populates="auditorias")

    __table_args__ = (
        CheckConstraint("campo IN ('estado', 'salon_id', 'inicio', 'fin')", name="check_campo_auditoria"),
    )
