from sqlalchemy import func
from database import SessionLocal
from models import MovimientoCaja, CierreCaja, MetodoPago, Proveedor, MovimientoProveedor
from datetime import datetime
import shutil

def registrar_ingreso_caja(monto: float, metodo: MetodoPago, descripcion: str = ""):
    session = SessionLocal()
    mov = MovimientoCaja(tipo='INGRESO', monto=monto, metodo_pago=metodo, descripcion=descripcion)
    session.add(mov)
    session.commit()
    session.close()

def registrar_egreso_caja(monto: float, metodo: MetodoPago, descripcion: str = ""):
    session = SessionLocal()
    mov = MovimientoCaja(tipo='EGRESO', monto=monto, metodo_pago=metodo, descripcion=descripcion)
    session.add(mov)
    session.commit()
    session.close()

def registrar_apertura_caja(monto: float):
    session = SessionLocal()
    existe = session.query(MovimientoCaja).filter(MovimientoCaja.cierre_id == None, MovimientoCaja.tipo == 'APERTURA').first()
    if existe:
        existe.monto = monto
    else:
        mov = MovimientoCaja(tipo='APERTURA', monto=monto, metodo_pago=MetodoPago.EFECTIVO, descripcion="Fondo Inicial")
        session.add(mov)
    session.commit()
    session.close()

def obtener_resumen_caja_abierta():
    session = SessionLocal()
    movimientos = session.query(MovimientoCaja).filter(MovimientoCaja.cierre_id == None).all()
    ingresos_por_metodo = {metodo.value: 0.0 for metodo in MetodoPago}
    total_ingresos = 0.0
    total_egresos = 0.0
    saldo_inicial = 0.0
    for mov in movimientos:
        if mov.tipo == 'INGRESO':
            ingresos_por_metodo[mov.metodo_pago.value] += mov.monto
            total_ingresos += mov.monto
        elif mov.tipo == 'EGRESO':
            total_egresos += mov.monto
        elif mov.tipo == 'APERTURA':
            saldo_inicial += mov.monto
    saldo_final = saldo_inicial + total_ingresos - total_egresos
    session.close()
    return ingresos_por_metodo, total_ingresos, total_egresos, saldo_inicial, saldo_final

def cerrar_caja():
    session = SessionLocal()
    movimientos_abiertos = session.query(MovimientoCaja).filter(MovimientoCaja.cierre_id == None).all()
    if not movimientos_abiertos:
        session.close()
        return None
    saldo_inicial = sum(m.monto for m in movimientos_abiertos if m.tipo == 'APERTURA')
    total_ingresos = sum(m.monto for m in movimientos_abiertos if m.tipo == 'INGRESO')
    total_egresos = sum(m.monto for m in movimientos_abiertos if m.tipo == 'EGRESO')
    saldo_final = saldo_inicial + total_ingresos - total_egresos
    nuevo_cierre = CierreCaja(total_ingresos=total_ingresos, total_egresos=total_egresos, saldo_final=saldo_final)
    session.add(nuevo_cierre)
    session.flush()
    for mov in movimientos_abiertos:
        mov.cierre_id = nuevo_cierre.id
    session.commit()
    cierre_id = nuevo_cierre.id
    session.close()
    return cierre_id

def obtener_historial_cierres(fecha_desde=None, fecha_hasta=None):
    session = SessionLocal()
    query = session.query(CierreCaja)
    if fecha_desde:
        try:
            d_desde = datetime.strptime(fecha_desde, "%d/%m/%Y")
            query = query.filter(CierreCaja.fecha_cierre >= d_desde)
        except ValueError:
            pass
    if fecha_hasta:
        try:
            d_hasta = datetime.strptime(fecha_hasta, "%d/%m/%Y").replace(hour=23, minute=59, second=59)
            query = query.filter(CierreCaja.fecha_cierre <= d_hasta)
        except ValueError:
            pass
    cierres = query.order_by(CierreCaja.fecha_cierre.desc()).all()
    resultado = [{"id": c.id, "fecha": c.fecha_cierre.strftime("%d/%m/%Y %H:%M"), "ingresos": c.total_ingresos, "egresos": c.total_egresos, "saldo_final": c.saldo_final} for c in cierres]
    session.close()
    return resultado

def obtener_detalle_cierre(cierre_id: int):
    session = SessionLocal()
    movimientos = session.query(MovimientoCaja).filter(MovimientoCaja.cierre_id == cierre_id).order_by(MovimientoCaja.fecha.asc()).all()
    resultado = []
    saldo_acumulado = 0.0
    for m in movimientos:
        if m.tipo == 'INGRESO': saldo_acumulado += m.monto
        elif m.tipo == 'EGRESO': saldo_acumulado -= m.monto
        elif m.tipo == 'APERTURA': saldo_acumulado += m.monto
        resultado.append({"id": m.id, "fecha": m.fecha.strftime("%H:%M:%S"), "tipo": m.tipo, "monto": m.monto, "metodo": m.metodo_pago.value, "descripcion": m.descripcion or "", "saldo_momento": saldo_acumulado})
    session.close()
    return resultado

def agregar_proveedor(nombre: str):
    session = SessionLocal()
    nuevo = Proveedor(nombre=nombre)
    session.add(nuevo)
    session.commit()
    session.close()

def modificar_proveedor(prov_id: int, nombre: str):
    session = SessionLocal()
    prov = session.query(Proveedor).filter(Proveedor.id == prov_id).first()
    if prov:
        prov.nombre = nombre
        session.commit()
    session.close()

def obtener_proveedores(busqueda: str = ""):
    session = SessionLocal()
    query = session.query(Proveedor)
    if busqueda:
        query = query.filter(Proveedor.nombre.ilike(f"%{busqueda}%"))
    proveedores = query.all()
    resultado = [{"id": p.id, "nombre": p.nombre, "saldo": p.saldo_deuda} for p in proveedores]
    session.close()
    return resultado

def obtener_proveedor(prov_id: int):
    session = SessionLocal()
    p = session.query(Proveedor).filter(Proveedor.id == prov_id).first()
    resultado = {"id": p.id, "nombre": p.nombre, "saldo": p.saldo_deuda} if p else None
    session.close()
    return resultado

def registrar_pedido_proveedor(prov_id: int, monto: float, desc: str, factura: str, remito: str, vencimiento: str):
    session = SessionLocal()
    proveedor = session.query(Proveedor).filter(Proveedor.id == prov_id).first()
    if proveedor:
        proveedor.saldo_deuda += monto
        movimiento = MovimientoProveedor(
            proveedor_id=prov_id, tipo='PEDIDO', monto=monto, descripcion=desc,
            numero_factura=factura, numero_remito=remito, fecha_vencimiento=vencimiento,
            saldo_historico=proveedor.saldo_deuda
        )
        session.add(movimiento)
        session.commit()
    session.close()

def pagar_deuda_proveedor(prov_id: int, monto: float, metodo_pago: MetodoPago, registrar_en_caja: bool = True, desc: str = "Pago en cuenta"):
    session = SessionLocal()
    proveedor = session.query(Proveedor).filter(Proveedor.id == prov_id).first()
    if proveedor:
        proveedor.saldo_deuda -= monto
        movimiento = MovimientoProveedor(proveedor_id=prov_id, tipo='PAGO', monto=monto, descripcion=desc, saldo_historico=proveedor.saldo_deuda)
        session.add(movimiento)
        if registrar_en_caja:
            mov_caja = MovimientoCaja(tipo='EGRESO', monto=monto, metodo_pago=metodo_pago, descripcion=f"Pago Proveedor: {proveedor.nombre} - {desc}")
            session.add(mov_caja)
        session.commit()
    session.close()

def obtener_historial_proveedor(prov_id: int):
    session = SessionLocal()
    movimientos = session.query(MovimientoProveedor).filter(MovimientoProveedor.proveedor_id == prov_id).order_by(MovimientoProveedor.fecha.desc()).all()
    resultado = []
    for m in movimientos:
        resultado.append({
            "id": m.id, "fecha": m.fecha.strftime("%d/%m/%Y %H:%M"), "tipo": m.tipo, "monto": m.monto, "descripcion": m.descripcion or "",
            "factura": m.numero_factura or "-", "remito": m.numero_remito or "-", "vencimiento": m.fecha_vencimiento or "-", "saldo_momento": m.saldo_historico
        })
    session.close()
    return resultado

def obtener_vencimientos_calendario():
    session = SessionLocal()
    pedidos = session.query(MovimientoProveedor, Proveedor).join(Proveedor).filter(
        MovimientoProveedor.tipo == 'PEDIDO', 
        MovimientoProveedor.fecha_vencimiento != None,
        MovimientoProveedor.fecha_vencimiento != ""
    ).all()
    vencimientos = {}
    for mov, prov in pedidos:
        if prov.saldo_deuda <= 0:
            continue
        fecha_str = mov.fecha_vencimiento.strip()
        try:
            if '/' in fecha_str:
                d = datetime.strptime(fecha_str, "%d/%m/%Y").date()
            elif '-' in fecha_str:
                d = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            else:
                continue
            if d not in vencimientos:
                vencimientos[d] = []
            nro_fact = mov.numero_factura or "S/N"
            vencimientos[d].append(f"• {prov.nombre} | Fact: {nro_fact} (${mov.monto:,.2f})")
        except ValueError:
            continue
    session.close()
    return vencimientos

def obtener_alertas_vencimiento():
    session = SessionLocal()
    pedidos = session.query(MovimientoProveedor, Proveedor).join(Proveedor).filter(
        MovimientoProveedor.tipo == 'PEDIDO', 
        MovimientoProveedor.fecha_vencimiento != None,
        MovimientoProveedor.fecha_vencimiento != ""
    ).all()
    alertas = []
    hoy = datetime.now().date()
    for mov, prov in pedidos:
        if prov.saldo_deuda <= 0:
            continue
        fecha_str = mov.fecha_vencimiento.strip()
        try:
            if '/' in fecha_str:
                d = datetime.strptime(fecha_str, "%d/%m/%Y").date()
            elif '-' in fecha_str:
                d = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            else:
                continue
            diferencia = (d - hoy).days
            if 0 <= diferencia <= 2:
                dias_txt = f"en {diferencia} día(s)" if diferencia > 0 else "¡HOY!"
                nro_fact = mov.numero_factura or "S/N"
                alertas.append(f"• {prov.nombre} | Fact: {nro_fact} | Vence {dias_txt} (${mov.monto:,.2f})")
            elif diferencia < 0:
                nro_fact = mov.numero_factura or "S/N"
                alertas.append(f"• {prov.nombre} | Fact: {nro_fact} | ¡VENCIDA hace {abs(diferencia)} día(s)! (${mov.monto:,.2f})")
        except ValueError:
            continue
    session.close()
    return alertas

def obtener_estadisticas_generales():
    session = SessionLocal()
    total_deuda = session.query(func.sum(Proveedor.saldo_deuda)).scalar() or 0.0
    movimientos = session.query(MovimientoCaja).all()
    tot_ingresos = sum(m.monto for m in movimientos if m.tipo == 'INGRESO')
    tot_egresos = sum(m.monto for m in movimientos if m.tipo == 'EGRESO')
    metodos_ingreso = {metodo.value: 0.0 for metodo in MetodoPago}
    for m in movimientos:
        if m.tipo == 'INGRESO':
            metodos_ingreso[m.metodo_pago.value] += m.monto
    session.close()
    return {
        "total_deuda": total_deuda,
        "tot_ingresos": tot_ingresos,
        "tot_egresos": tot_egresos,
        "metodos_ingreso": metodos_ingreso
    }

def anular_movimiento_caja(mov_id: int):
    session = SessionLocal()
    mov = session.query(MovimientoCaja).filter(MovimientoCaja.id == mov_id, MovimientoCaja.cierre_id == None).first()
    if mov:
        session.delete(mov)
        session.commit()
    session.close()

def obtener_movimientos_caja_abierta():
    session = SessionLocal()
    movimientos = session.query(MovimientoCaja).filter(MovimientoCaja.cierre_id == None).order_by(MovimientoCaja.fecha.desc()).all()
    resultado = [{
        "id": m.id, "fecha": m.fecha.strftime("%d/%m/%Y %H:%M:%S"),
        "tipo": m.tipo, "monto": m.monto, "metodo": m.metodo_pago.value,
        "descripcion": m.descripcion or ""
    } for m in movimientos]
    session.close()
    return resultado

def hacer_backup_base_datos(ruta_destino: str):
    try:
        shutil.copy("caja_ventas.db", ruta_destino)
        return True
    except Exception:
        return False

def recalcular_saldos_proveedor(prov_id: int, session):
    movimientos = session.query(MovimientoProveedor).filter(MovimientoProveedor.proveedor_id == prov_id).order_by(MovimientoProveedor.fecha.asc(), MovimientoProveedor.id.asc()).all()
    saldo = 0.0
    for m in movimientos:
        if m.tipo == 'PEDIDO':
            saldo += m.monto
        elif m.tipo == 'PAGO':
            saldo -= m.monto
        m.saldo_historico = saldo
    prov = session.query(Proveedor).filter(Proveedor.id == prov_id).first()
    if prov:
        prov.saldo_deuda = saldo

def modificar_pedido_proveedor(mov_id: int, nuevo_monto: float, nueva_desc: str, nueva_fact: str, nuevo_remito: str, nuevo_venc: str):
    session = SessionLocal()
    mov = session.query(MovimientoProveedor).filter(MovimientoProveedor.id == mov_id).first()
    if mov and mov.tipo == 'PEDIDO':
        mov.monto = nuevo_monto
        mov.descripcion = nueva_desc
        mov.numero_factura = nueva_fact
        mov.numero_remito = nuevo_remito
        mov.fecha_vencimiento = nuevo_venc
        session.commit()
        recalcular_saldos_proveedor(mov.proveedor_id, session)
        session.commit()
    session.close()
