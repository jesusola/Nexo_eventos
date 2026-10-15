from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.database import engine


def ahora(): return datetime.now(ZoneInfo("America/Bogota")).replace(tzinfo=None, microsecond=0)


def crear(client, db, **cambios):
    inicio = ahora().replace(hour=9, minute=0, second=0) + timedelta(days=1000)
    datos = {"cliente_id": db.scalar(text("SELECT MIN(id) FROM clientes")),
             "salon_id": db.scalar(text("SELECT id FROM salones WHERE nombre='Salón Heliconia'")),
             "coordinador_id": db.scalar(text("SELECT MIN(id) FROM staff")),
             "nombre": "Evento de prueba", "tipo": "Seminario", "aforo_esperado": 50,
             "inicio": inicio.isoformat(), "fin": (inicio + timedelta(hours=2)).isoformat()}
    datos.update(cambios)
    r = client.post("/eventos", json=datos)
    assert r.status_code == 201, r.text
    return r.json()


def cafe(db): return db.scalar(text("SELECT id FROM servicios WHERE nombre='Estación de café'"))
def asistente(db, n=0): return db.execute(text("SELECT id, documento FROM asistentes ORDER BY id OFFSET :n LIMIT 1"), {"n": n}).mappings().one()


def cerrar(client, evento):
    assert client.patch(f"/eventos/{evento['id']}/estado", json={"estado": "Confirmado"}).status_code == 200
    return client.patch(f"/eventos/{evento['id']}/estado", json={"estado": "Finalizado"})


def test_catalogo_y_datos(client, db):
    assert len(client.get("/salones").json()) == 6
    assert len(client.get("/servicios").json()) == 9
    assert db.scalar(text("SELECT COUNT(*) FROM clientes")) == 8
    assert db.scalar(text("SELECT COUNT(*) FROM staff")) == 15
    assert db.scalar(text("SELECT COUNT(*) FROM asistentes")) == 60
    assert db.scalar(text("SELECT COUNT(*) FROM eventos")) == 12
    assert set(db.execute(text("SELECT DISTINCT estado FROM eventos")).scalars()) == {"Cotizado", "Confirmado", "Finalizado", "Cancelado"}


@pytest.mark.parametrize("minutos,esperado", [(59, 409), (60, 201), (61, 201)])
def test_separacion_una_hora(client, db, minutos, esperado):
    primero = crear(client, db)
    inicio = datetime.fromisoformat(primero["fin"]) + timedelta(minutes=minutos)
    datos = {k: primero[k] for k in ("cliente_id", "salon_id", "coordinador_id", "nombre", "tipo", "aforo_esperado")}
    datos.update(inicio=inicio.isoformat(), fin=(inicio + timedelta(hours=1)).isoformat())
    r = client.post("/eventos", json=datos)
    assert r.status_code == esperado
    if esperado == 409: assert str(primero["id"]) in r.json()["detail"]


def test_capacidad_al_reprogramar(client, db):
    e = crear(client, db)
    assert client.patch(f"/eventos/{e['id']}", json={"aforo_esperado": 61}).status_code == 409


def test_salon_inactivo(client, db):
    salon = db.scalar(text("SELECT id FROM salones WHERE nombre='Salón Heliconia'"))
    assert client.patch(f"/salones/{salon}/activo?activo=false").status_code == 200
    inicio = ahora() + timedelta(days=1000)
    datos = {"cliente_id": 1, "coordinador_id": 1, "salon_id": salon, "nombre": "Inactivo", "tipo": "Social", "aforo_esperado": 1, "inicio": inicio.isoformat(), "fin": (inicio + timedelta(hours=1)).isoformat()}
    assert client.post("/eventos", json=datos).status_code == 409


def test_cancelado_libera_y_no_se_reactiva(client, db):
    e = crear(client, db)
    assert client.patch(f"/eventos/{e['id']}/estado", json={"estado": "Cancelado"}).status_code == 200
    crear(client, db)
    assert client.patch(f"/eventos/{e['id']}/estado", json={"estado": "Confirmado"}).status_code == 409


def test_finalizado_sigue_contando_en_cruces(client, db):
    inicio = ahora() - timedelta(days=1000)
    e = crear(client, db, inicio=inicio.isoformat(), fin=(inicio + timedelta(hours=2)).isoformat())
    assert cerrar(client, e).status_code == 200
    datos = {k: e[k] for k in ("cliente_id", "salon_id", "coordinador_id", "nombre", "tipo", "aforo_esperado", "inicio", "fin")}
    assert client.post("/eventos", json=datos).status_code == 409


def test_liquidacion_cantidades_y_precio(client, db):
    inicio = ahora() + timedelta(days=1000)
    e = crear(client, db, inicio=inicio.isoformat(), fin=(inicio + timedelta(hours=1.5)).isoformat())
    assert Decimal(e["valor_total"]) == Decimal("480000")
    linea = client.post(f"/eventos/{e['id']}/servicios", json={"servicio_id": cafe(db)}).json()
    assert Decimal(linea["cantidad"]) == 50
    assert Decimal(client.get(f"/eventos/{e['id']}").json()["valor_total"]) == Decimal("805000")
    db.execute(text("UPDATE servicios SET precio_unitario=7000 WHERE id=:id"), {"id": cafe(db)})
    db.commit()
    r = client.put(f"/eventos/{e['id']}/servicios/{linea['id']}", json={"cantidad": "10"})
    assert r.status_code == 200
    assert Decimal(r.json()["precio_congelado"]) == 6500
    assert Decimal(client.get(f"/eventos/{e['id']}/cotizacion").json()["total"]) == Decimal("545000")
    assert client.delete(f"/eventos/{e['id']}/servicios/{linea['id']}").status_code == 204
    assert Decimal(client.get(f"/eventos/{e['id']}").json()["valor_total"]) == Decimal("480000")


def test_servicio_por_hora_redondea(client, db):
    inicio = ahora() + timedelta(days=1000)
    e = crear(client, db, inicio=inicio.isoformat(), fin=(inicio + timedelta(hours=1.25)).isoformat())
    servicio = db.scalar(text("SELECT id FROM servicios WHERE nombre='Multimedia (proyector + pantalla)'"))
    r = client.post(f"/eventos/{e['id']}/servicios", json={"servicio_id": servicio})
    assert Decimal(r.json()["cantidad"]) == 2


def test_reprogramar_total_y_auditoria(client, db):
    e = crear(client, db)
    fin = datetime.fromisoformat(e["fin"]) + timedelta(hours=1)
    r = client.patch(f"/eventos/{e['id']}", json={"fin": fin.isoformat()}, headers={"X-Usuario": "shalem"})
    assert r.status_code == 200
    assert Decimal(r.json()["valor_total"]) == Decimal("960000")
    log = client.get(f"/eventos/{e['id']}/auditoria").json()
    assert log[-1]["campo"] == "fin" and log[-1]["usuario_app"] == "shalem"


def test_tarifa_salon_conservada(client, db):
    e = crear(client, db)
    db.execute(text("UPDATE salones SET precio_hora=999999 WHERE id=:id"), {"id": e["salon_id"]})
    db.commit()
    r = client.get(f"/eventos/{e['id']}/cotizacion").json()
    assert Decimal(r["total"]) == 640000 and Decimal(r["precio_hora"]) == 320000


@pytest.mark.parametrize("estado", ["Finalizado", "Cancelado"])
@pytest.mark.parametrize("metodo", ["POST", "PUT", "DELETE"])
def test_servicios_cerrados(client, db, estado, metodo):
    inicio = ahora() - timedelta(days=1000)
    e = crear(client, db, inicio=inicio.isoformat(), fin=(inicio + timedelta(hours=2)).isoformat())
    linea = client.post(f"/eventos/{e['id']}/servicios", json={"servicio_id": cafe(db)}).json()
    if estado == "Finalizado": assert cerrar(client, e).status_code == 200
    else: client.patch(f"/eventos/{e['id']}/estado", json={"estado": estado})
    ruta = f"/eventos/{e['id']}/servicios" + (f"/{linea['id']}" if metodo != "POST" else "")
    datos = {"servicio_id": cafe(db)} if metodo == "POST" else {"cantidad": "2"}
    assert client.request(metodo, ruta, json=datos).status_code == 409


def test_cupo_y_reduccion(client, db):
    e = crear(client, db, aforo_esperado=1)
    assert client.post(f"/eventos/{e['id']}/inscripciones", json={"asistente_id": asistente(db)["id"]}).status_code == 201
    assert client.post(f"/eventos/{e['id']}/inscripciones", json={"asistente_id": asistente(db, 1)["id"]}).status_code == 409
    e2 = crear(client, db, inicio=(ahora() + timedelta(days=1001)).isoformat(), fin=(ahora() + timedelta(days=1001, hours=2)).isoformat(), aforo_esperado=2)
    for n in range(2): client.post(f"/eventos/{e2['id']}/inscripciones", json={"asistente_id": asistente(db, n)["id"]})
    assert client.patch(f"/eventos/{e2['id']}", json={"aforo_esperado": 1}).status_code == 409


@pytest.mark.parametrize("minutos,esperado", [(-61,409),(-60,200),(0,200),(120,200),(121,409)])
def test_ventana_checkin(client, db, minutos, esperado):
    e = crear(client, db)
    a = asistente(db)
    client.post(f"/eventos/{e['id']}/inscripciones", json={"asistente_id": a["id"]})
    fecha = datetime.fromisoformat(e["inicio"]) + timedelta(minutes=minutos)
    r = client.post(f"/eventos/{e['id']}/checkin", json={"documento": a["documento"], "hora_checkin": fecha.isoformat()})
    assert r.status_code == esperado


def test_doble_checkin_y_borrado_sql(client, db):
    e = crear(client, db)
    a = asistente(db)
    ins = client.post(f"/eventos/{e['id']}/inscripciones", json={"asistente_id": a["id"]}).json()
    datos = {"documento": a["documento"], "hora_checkin": e["inicio"]}
    assert client.post(f"/eventos/{e['id']}/checkin", json=datos).status_code == 200
    assert client.post(f"/eventos/{e['id']}/checkin", json=datos).status_code == 409
    with pytest.raises(DBAPIError, match="CHECKIN"):
        db.execute(text("UPDATE inscripciones SET hora_checkin=NULL WHERE id=:id"), {"id": ins["id"]})


def test_insert_checkin_sql_fuera_ventana(client, db):
    e = crear(client, db)
    with pytest.raises(DBAPIError, match="CHECKIN"):
        db.execute(text("INSERT INTO inscripciones(evento_id,asistente_id,hora_checkin) VALUES(:e,:a,:hora)"), {"e": e["id"], "a": asistente(db)["id"], "hora": datetime.fromisoformat(e["inicio"]) - timedelta(hours=2)})


def test_cierre_temprano(client, db):
    e = crear(client, db)
    r = cerrar(client, e)
    assert r.status_code == 409 and "CIERRE" in r.json()["detail"]


@pytest.mark.parametrize("inscritos,llegadas,tasa", [(0,0,None),(4,0,"0.00"),(4,3,"75.00")])
def test_tasa_final(client, db, inscritos, llegadas, tasa):
    inicio = ahora() - timedelta(days=1000)
    e = crear(client, db, inicio=inicio.isoformat(), fin=(inicio + timedelta(hours=2)).isoformat())
    for n in range(inscritos):
        a = asistente(db, n)
        client.post(f"/eventos/{e['id']}/inscripciones", json={"asistente_id": a["id"]})
        if n < llegadas: client.post(f"/eventos/{e['id']}/checkin", json={"documento": a["documento"], "hora_checkin": e["inicio"]})
    r = cerrar(client, e)
    assert r.status_code == 200 and r.json()["tasa_asistencia"] == tasa
    assert client.post(f"/eventos/{e['id']}/inscripciones", json={"asistente_id": asistente(db, 10)["id"]}).status_code == 409
    assert client.patch(f"/eventos/{e['id']}", json={"aforo_esperado": 1}).status_code == 409


def test_insert_estado_final_sql(client, db):
    with pytest.raises(DBAPIError, match="Cotizado"):
        db.execute(text("INSERT INTO eventos(cliente_id,salon_id,coordinador_id,nombre,tipo,aforo_esperado,inicio,fin,estado) VALUES(1,2,1,'No permitido','Social',1,:i,:f,'Finalizado')"), {"i": ahora(), "f": ahora()+timedelta(hours=1)})


def test_disponibilidad_y_medianoche(client, db):
    inicio = (ahora() + timedelta(days=1000)).replace(hour=23, minute=0, second=0)
    e = crear(client, db, inicio=inicio.isoformat(), fin=(inicio + timedelta(hours=2)).isoformat())
    assert Decimal(e["valor_total"]) == 640000
    datos = {"inicio": e["inicio"], "fin": e["fin"], "aforo": 50}
    libres = client.get("/salones/disponibles", params=datos).json()
    assert e["salon_id"] not in [s["salon_id"] for s in libres]
    datos["aforo"] = 2000
    assert client.get("/salones/disponibles", params=datos).json() == []
    datos["fin"] = datos["inicio"]
    assert client.get("/salones/disponibles", params=datos).status_code == 422


def test_disponibilidad_normaliza_zonas(client, db):
    inicio = (ahora() + timedelta(days=1100)).replace(hour=9, minute=0, second=0)
    r = client.get("/salones/disponibles", params={"inicio": inicio.isoformat(),
                   "fin": (inicio + timedelta(hours=7)).isoformat() + "+00:00", "aforo": 50})
    assert r.status_code == 200
    assert Decimal(r.json()[0]["costo_estimado"]) == Decimal("640000")


def test_ciclo_staff_sql(client, db):
    with pytest.raises(DBAPIError, match="ciclo"):
        db.execute(text("UPDATE staff SET jefe_id=12 WHERE id=1"))


def test_reportes(client, db):
    b1 = client.get("/reportes/organigrama").json()
    assert len(b1) == 15 and b1[0]["total_a_cargo"] == 14
    assert len(client.get("/reportes/organigrama?staff_id=2").json()) == 9
    b2 = client.get("/reportes/escalamiento/12").json()
    assert [x["id"] for x in b2] == [6,2,1]
    b3 = client.get("/reportes/ranking-clientes").json()
    assert len(b3) == 8 and Decimal(b3[-1]["acumulado_pct"]) == 100
    total = db.scalar(text("SELECT SUM(valor_total) FROM eventos WHERE estado <> 'Cancelado'"))
    assert sum(Decimal(c["facturacion"]) for c in b3) == total
    b4 = client.get("/reportes/ocupacion-salones").json()
    assert len(b4) == 10 and any(e["estado"] == "Cotizado" for e in b4)


def test_404_422_y_duplicado(client, db):
    assert client.get("/eventos/999999").status_code == 404
    e = crear(client, db)
    assert client.patch(f"/eventos/{e['id']}", json={"fin": e["inicio"]}).status_code == 422
    assert client.patch(f"/eventos/{e['id']}", json={"inicio": None}).status_code == 422
    assert client.patch(f"/eventos/{e['id']}/estado", json={"estado": "Confirmado"}, headers={"X-Usuario": ""}).status_code == 422
    cliente = client.get("/clientes").json()[0]
    datos = {k: cliente[k] for k in ("documento", "tipo_documento", "nombre_razon_social", "correo", "telefono")}
    assert client.post("/clientes", json=datos).status_code == 409


def test_cupo_concurrente(preparar):
    inicio = ahora() + timedelta(days=3000)
    with engine.begin() as conn:
        eid = conn.scalar(text("INSERT INTO eventos(cliente_id,salon_id,coordinador_id,nombre,tipo,aforo_esperado,inicio,fin) VALUES(1,2,1,'Cupo concurrente','Social',1,:i,:f) RETURNING id"), {"i": inicio, "f": inicio+timedelta(hours=2)})
    def inscribir(a):
        try:
            with engine.begin() as conn:
                conn.execute(text("INSERT INTO inscripciones(evento_id,asistente_id) VALUES(:e,:a)"), {"e": eid, "a": a})
            return True
        except DBAPIError: return False
    try:
        with ThreadPoolExecutor(max_workers=2) as pool: resultados = list(pool.map(inscribir, [1,2]))
        assert sum(resultados) == 1
    finally:
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM inscripciones WHERE evento_id=:e"), {"e": eid})
            conn.execute(text("DELETE FROM eventos WHERE id=:e"), {"e": eid})


def test_reserva_concurrente(preparar):
    inicio = ahora() + timedelta(days=4000)
    def reservar(nombre):
        try:
            with engine.begin() as conn:
                return conn.scalar(text("INSERT INTO eventos(cliente_id,salon_id,coordinador_id,nombre,tipo,aforo_esperado,inicio,fin) VALUES(1,2,1,:n,'Social',20,:i,:f) RETURNING id"),
                                   {"n": nombre, "i": inicio, "f": inicio + timedelta(hours=2)})
        except DBAPIError as exc:
            assert "DISPONIBILIDAD" in str(exc)
            return None
    ids = []
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            ids = list(pool.map(reservar, ["Reserva simultánea A", "Reserva simultánea B"]))
        assert sum(eid is not None for eid in ids) == 1
    finally:
        with engine.begin() as conn:
            for eid in ids:
                if eid is not None: conn.execute(text("DELETE FROM eventos WHERE id=:e"), {"e": eid})


def test_sql_directo_no_permite_cruces_ni_total_falso(client, db):
    e = crear(client, db)
    db.execute(text("UPDATE eventos SET valor_total=1 WHERE id=:id"), {"id": e["id"]})
    assert db.scalar(text("SELECT valor_total FROM eventos WHERE id=:id"), {"id": e["id"]}) == Decimal("640000")
    with pytest.raises(DBAPIError, match="DISPONIBILIDAD"):
        db.execute(text("INSERT INTO eventos(cliente_id,salon_id,coordinador_id,nombre,tipo,aforo_esperado,inicio,fin) VALUES(1,:s,1,'Cruce SQL','Social',1,:i,:f)"),
                   {"s": e["salon_id"], "i": datetime.fromisoformat(e["inicio"]), "f": datetime.fromisoformat(e["fin"])})
