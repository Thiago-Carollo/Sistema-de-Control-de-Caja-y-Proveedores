import enum
from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class MetodoPago(enum.Enum):
    EFECTIVO = "Efectivo"
    QR = "QR"
    TRANSFERENCIA = "Transferencia"
    DEBITO = "Tarjeta de Débito"
    CREDITO = "Tarjeta de Crédito"

class CierreCaja(Base):
    __tablename__ = 'cierres_caja'
    id = Column(Integer, primary_key=True)
    fecha_cierre = Column(DateTime, default=datetime.now)
    total_ingresos = Column(Float, default=0.0)
    total_egresos = Column(Float, default=0.0)
    saldo_final = Column(Float, default=0.0)
    movimientos = relationship("MovimientoCaja", back_populates="cierre")

class MovimientoCaja(Base):
    __tablename__ = 'movimientos_caja'
    id = Column(Integer, primary_key=True)
    cierre_id = Column(Integer, ForeignKey('cierres_caja.id'), nullable=True)
    tipo = Column(String(20), nullable=False)
    monto = Column(Float, nullable=False)
    metodo_pago = Column(Enum(MetodoPago), nullable=False)
    fecha = Column(DateTime, default=datetime.now)
    descripcion = Column(String(200), nullable=True)
    cierre = relationship("CierreCaja", back_populates="movimientos")

class Proveedor(Base):
    __tablename__ = 'proveedores'
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    saldo_deuda = Column(Float, default=0.0)
    movimientos = relationship("MovimientoProveedor", back_populates="proveedor", cascade="all, delete-orphan")

class MovimientoProveedor(Base):
    __tablename__ = 'movimientos_proveedor'
    id = Column(Integer, primary_key=True)
    proveedor_id = Column(Integer, ForeignKey('proveedores.id'))
    tipo = Column(String(20), nullable=False)
    monto = Column(Float, nullable=False)
    fecha = Column(DateTime, default=datetime.now)
    descripcion = Column(String(200), nullable=True)
    numero_factura = Column(String(50), nullable=True)
    numero_remito = Column(String(50), nullable=True)
    fecha_vencimiento = Column(String(20), nullable=True) 
    saldo_historico = Column(Float, default=0.0)
    proveedor = relationship("Proveedor", back_populates="movimientos")
