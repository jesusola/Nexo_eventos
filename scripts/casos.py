from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from uuid import uuid4

import requests

CASOS = {
    "A1 permitido": {"descripcion": "Crear un evento en un salón libre con aforo válido.", "status": 201},
    "A1 bloqueado": {"descripcion": "Crear otro evento dejando solo media hora de separación.", "status": 409},
    "A2 permitido": {"descripcion": "Inscribir un asistente cuando quedan cupos.", "status": 201},
    "A2 bloqueado": {"descripcion": "Inscribir una segunda persona en un evento con aforo uno.", "status": 409},
    "A3 permitido": {"descripcion": "Contratar café sin cantidad: se toma el aforo y se actualiza el total.", "status": 201},
    "A3 bloqueado": {"descripcion": "Contratar servicios en un evento finalizado.", "status": 409},
    "A4 permitido": {"descripcion": "Finalizar un evento pasado con tres llegadas de cuatro inscritos.", "status": 200},
    "A4 bloqueado": {"descripcion": "Finalizar un evento que todavía no termina.", "status": 409},
    "A5 permitido": {"descripcion": "Consultar salones libres para cincuenta personas.", "status": 200},
    "A5 sin opciones": {"descripcion": "Solicitar aforo dos mil: ningún salón cumple.", "status": 200},
}


def ejecutar(api, usuario, caso):
    sesion = requests.Session()
    sesion.headers["X-Usuario"] = usuario

    def peticion(metodo, ruta, datos=None, parametros=None, preparar=False):
        r = sesion.request(metodo, api.rstrip("/") + ruta, json=datos, params=parametros, timeout=15)
        contenido = r.json() if r.content else None
        if preparar and r.status_code >= 400:
            raise RuntimeError(f"Preparación: {contenido}")
        return {"metodo": metodo, "ruta": ruta, "datos": datos, "parametros": parametros,
                "status": r.status_code, "respuesta": contenido}

    def get(ruta): return peticion("GET", ruta, preparar=True)["respuesta"]
    clientes, staff, salones, servicios, asistentes = [get(r) for r in ("/clientes", "/staff", "/salones", "/servicios", "/asistentes")]
    if not all((clientes, staff, salones, servicios, asistentes)):
        raise RuntimeError("Cargue primero los datos con python init_db.py --con-datos.")
    salon = next(s for s in salones if s["nombre"] == "Salón Heliconia")

    def crear(pasado=False, aforo=50, horas=2):
        base = datetime.now(ZoneInfo("America/Bogota")).replace(tzinfo=None, hour=9, minute=0, second=0, microsecond=0)
        base += timedelta(days=-100 if pasado else 100)
        for _ in range(30):
            fin = base + timedelta(hours=horas)
            libres = peticion("GET", "/salones/disponibles", parametros={"inicio": base.isoformat(), "fin": fin.isoformat(), "aforo": aforo}, preparar=True)["respuesta"]
            if any(s["salon_id"] == salon["id"] for s in libres): break
            base += timedelta(days=-1 if pasado else 1)
        else: raise RuntimeError("No se encontró una fecha libre para preparar el caso.")
        datos = {"cliente_id": clientes[0]["id"], "salon_id": salon["id"], "coordinador_id": staff[0]["id"],
                 "nombre": f"Prueba {caso} {uuid4().hex[:6]}", "tipo": "Seminario", "aforo_esperado": aforo,
                 "inicio": base.isoformat(), "fin": fin.isoformat()}
        return peticion("POST", "/eventos", datos, preparar=True), datos

    def confirmar(eid): peticion("PATCH", f"/eventos/{eid}/estado", {"estado": "Confirmado"}, preparar=True)

    if caso.startswith("A5"):
        base = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=200)
        return peticion("GET", "/salones/disponibles", parametros={"inicio": base.isoformat(), "fin": (base + timedelta(hours=1.5)).isoformat(), "aforo": 2000 if caso.endswith("opciones") else 50})

    creado, datos = crear(pasado=caso in ("A3 bloqueado", "A4 permitido"), aforo=1 if caso == "A2 bloqueado" else 50,
                         horas=1.5 if caso == "A3 permitido" else 2)
    eid = creado["respuesta"]["id"]
    if caso == "A1 permitido": return creado
    if caso == "A1 bloqueado":
        datos["inicio"] = (datetime.fromisoformat(datos["fin"]) + timedelta(minutes=30)).isoformat()
        datos["fin"] = (datetime.fromisoformat(datos["inicio"]) + timedelta(hours=1)).isoformat()
        datos["nombre"] = "Intento con media hora de separación"
        return peticion("POST", "/eventos", datos)
    if caso.startswith("A2"):
        if caso.endswith("bloqueado"):
            peticion("POST", f"/eventos/{eid}/inscripciones", {"asistente_id": asistentes[0]["id"]}, preparar=True)
        return peticion("POST", f"/eventos/{eid}/inscripciones", {"asistente_id": asistentes[1]["id"]})
    if caso.startswith("A3"):
        if caso.endswith("bloqueado"):
            confirmar(eid)
            peticion("PATCH", f"/eventos/{eid}/estado", {"estado": "Finalizado"}, preparar=True)
        cafe = next(s for s in servicios if s["nombre"] == "Estación de café")
        resultado = peticion("POST", f"/eventos/{eid}/servicios", {"servicio_id": cafe["id"]})
        if resultado["status"] == 201: resultado["comprobacion"] = get(f"/eventos/{eid}/cotizacion")
        return resultado
    if caso.startswith("A4"):
        confirmar(eid)
        if caso.endswith("permitido"):
            for i, a in enumerate(asistentes[:4]):
                peticion("POST", f"/eventos/{eid}/inscripciones", {"asistente_id": a["id"]}, preparar=True)
                if i < 3:
                    peticion("POST", f"/eventos/{eid}/checkin", {"documento": a["documento"],
                             "hora_checkin": (datetime.fromisoformat(datos["inicio"]) + timedelta(minutes=20)).isoformat()}, preparar=True)
        resultado = peticion("PATCH", f"/eventos/{eid}/estado", {"estado": "Finalizado"})
        resultado["comprobacion"] = get(f"/eventos/{eid}/auditoria")
        return resultado
    raise ValueError("Caso desconocido")
