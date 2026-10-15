"""Guarda peticiones reales y compara los reportes con cuentas independientes."""
import argparse
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from html import escape
import json
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

from scripts.casos import CASOS, ejecutar

ROOT = Path(__file__).resolve().parents[1]
D = Decimal


def redondear(valor):
    return D(valor).quantize(D("0.01"), rounding=ROUND_HALF_UP)


def verificar_reportes(api):
    def get(ruta, **parametros):
        r = requests.get(api + ruta, params=parametros, timeout=15)
        r.raise_for_status()
        return r.json()

    staff = get("/staff")
    clientes = get("/clientes")
    eventos = get("/eventos")
    empleados = {s["id"]: s for s in staff}

    def cadena(sid):
        ids = []
        while sid is not None:
            assert sid not in ids, "Ciclo en el personal"
            ids.append(sid)
            sid = empleados[sid]["jefe_id"]
        return ids

    manual_b1 = []
    for s in staff:
        ruta = list(reversed(cadena(s["id"])))
        a_cargo = [otro["id"] for otro in staff if s["id"] in cadena(otro["id"])[1:]]
        manual_b1.append({"id": s["id"], "nivel": len(ruta), "ruta_ids": ruta,
                          "ruta_mando": " > ".join(empleados[i]["nombre"] for i in ruta),
                          "a_cargo_directos": sum(otro["jefe_id"] == s["id"] for otro in staff),
                          "total_a_cargo": len(a_cargo)})
    manual_b1.sort(key=lambda s: s["ruta_ids"])
    plataforma_b1 = get("/reportes/organigrama")
    for m, p in zip(manual_b1, plataforma_b1):
        assert all(m[k] == p[k] for k in m), (m, p)
    assert len(manual_b1) == len(plataforma_b1)
    for s in staff:
        ids = [m["id"] for m in manual_b1 if s["id"] in m["ruta_ids"][:-1]]
        assert ids == [p["id"] for p in get("/reportes/organigrama", staff_id=s["id"])]

    b2 = []
    for s in staff:
        manual = cadena(s["id"])[1:]
        plataforma = get(f"/reportes/escalamiento/{s['id']}")
        assert manual == [p["id"] for p in plataforma]
        assert list(range(1, len(manual) + 1)) == [p["orden"] for p in plataforma]
        b2.append({"empleado_id": s["id"], "empleado": s["nombre"], "manual": manual, "plataforma": plataforma})

    no_cancelados = [e for e in eventos if e["estado"] != "Cancelado"]
    facturacion = defaultdict(lambda: D(0))
    conteo = defaultdict(int)
    liquidaciones = []
    for e in no_cancelados:
        horas = D(str((datetime.fromisoformat(e["fin"]) - datetime.fromisoformat(e["inicio"])).total_seconds())) / D(3600)
        lineas = get(f"/eventos/{e['id']}/servicios")
        salon = horas * D(e["precio_salon_congelado"])
        servicios = sum((D(l["cantidad"]) * D(l["precio_congelado"]) for l in lineas), D(0))
        total = redondear(salon + servicios)
        assert total == D(e["valor_total"])
        facturacion[e["cliente_id"]] += total
        conteo[e["cliente_id"]] += 1
        liquidaciones.append({"evento": e["nombre"], "cliente_id": e["cliente_id"], "horas": horas,
                              "salon": salon, "servicios": servicios, "total": total})
    total_general = sum(facturacion.values(), D(0))
    manual_b3 = []
    acumulado = D(0)
    for c in sorted(clientes, key=lambda c: (-facturacion[c["id"]], c["id"])):
        cid = c["id"]
        valor = facturacion[cid]
        segmento = "A (80%)" if valor > 0 and total_general and acumulado / total_general < D("0.8") else "B (resto)"
        acumulado += valor
        manual_b3.append({"cliente_id": cid, "nombre": c["nombre_razon_social"], "eventos_no_cancelados": conteo[cid],
                          "facturacion": valor, "ranking": 1 + sum(facturacion[o["id"]] > valor for o in clientes),
                          "participacion_pct": redondear(100 * valor / total_general) if total_general else D(0),
                          "acumulado_pct": redondear(100 * acumulado / total_general) if total_general else D(0),
                          "segmento_pareto": segmento})
    plataforma_b3 = get("/reportes/ranking-clientes")
    assert len(manual_b3) == len(plataforma_b3)
    for m, p in zip(manual_b3, plataforma_b3):
        assert all(m[k] == (D(p[k]) if isinstance(m[k], D) else p[k]) for k in m), (m, p)

    manual_b4 = []
    for sid in sorted({e["salon_id"] for e in no_cancelados}):
        anteriores = None
        horas_acumuladas = D(0)
        for n, e in enumerate(sorted((e for e in no_cancelados if e["salon_id"] == sid), key=lambda e: (e["inicio"], e["id"])), 1):
            inicio, fin = datetime.fromisoformat(e["inicio"]), datetime.fromisoformat(e["fin"])
            horas = D(str((fin - inicio).total_seconds())) / D(3600)
            horas_acumuladas += horas
            dias = None if anteriores is None else redondear(D(str((inicio - datetime.fromisoformat(anteriores["fin"])).total_seconds())) / D(86400))
            manual_b4.append({"salon_id": sid, "evento_id": e["id"], "evento": e["nombre"], "num_evento_salon": n,
                              "evento_anterior_id": anteriores["id"] if anteriores else None,
                              "evento_anterior": anteriores["nombre"] if anteriores else None,
                              "dias_libres": dias, "horas_reservadas": redondear(horas), "horas_acumuladas": redondear(horas_acumuladas)})
            anteriores = e
    plataforma_b4 = get("/reportes/ocupacion-salones")
    assert len(manual_b4) == len(plataforma_b4)
    for m, p in zip(manual_b4, plataforma_b4):
        assert all(m[k] == (D(p[k]) if isinstance(m[k], D) else p[k]) for k in m), (m, p)
    return {"conteos_iniciales": {"clientes": len(clientes), "staff": len(staff), "eventos": len(eventos),
            "asistentes": len(get('/asistentes')), "salones": len(get('/salones')), "servicios": len(get('/servicios'))},
            "B1": {"coincide": True, "manual": manual_b1, "plataforma": plataforma_b1},
            "B2": {"coincide": True, "comparaciones": b2},
            "B3": {"coincide": True, "total_general": total_general, "liquidaciones": liquidaciones,
                   "manual": manual_b3, "plataforma": plataforma_b3},
            "B4": {"coincide": True, "manual": manual_b4, "plataforma": plataforma_b4}}


def guardar(resultados, carpeta):
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / "verificacion.json").write_text(json.dumps(resultados, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    estilo = "body{font:16px Segoe UI,sans-serif;background:#f3f5f7;color:#17252e;margin:40px}main{max-width:1250px;margin:auto}pre{background:white;padding:22px;border:1px solid #ccd5da;border-radius:8px;white-space:pre-wrap;word-break:break-word;font:15px Consolas,monospace}h1{font-size:28px}h2{font-size:20px}.estado{font-size:20px;font-weight:600}small{color:#415462}"
    paginas = []
    for nombre, r in resultados["A"].items():
        archivo = nombre.replace(" ", "_")
        solicitud = {"metodo": r["metodo"], "ruta": r["ruta"], "X-Usuario": resultados["usuario"],
                     "parametros": r.get("parametros"), "cuerpo": r.get("datos")}
        cuerpo = f'<h1>{escape(nombre)} · petición real a la API</h1><small>Registrada: {resultados["fecha"]}. Cliente HTTP: scripts/evidencias.py.</small><p>{escape(CASOS[nombre]["descripcion"])}</p><h2>Petición</h2><pre>{escape(json.dumps(solicitud, ensure_ascii=False, indent=2))}</pre><p class="estado">Respuesta HTTP {r["status"]}</p><pre>{escape(json.dumps(r["respuesta"], ensure_ascii=False, indent=2))}</pre>'
        if "comprobacion" in r:
            cuerpo += f'<h2>Consulta posterior</h2><pre>{escape(json.dumps(r["comprobacion"], ensure_ascii=False, indent=2))}</pre>'
        (carpeta / f"{archivo}.html").write_text(f'<!doctype html><html lang="es"><meta charset="utf-8"><title>{escape(nombre)}</title><style>{estilo}</style><main>{cuerpo}</main></html>', encoding="utf-8")
        paginas.append(f'<li><a href="{archivo}.html">{escape(nombre)}</a> · HTTP {r["status"]}</li>')
    (carpeta / "visor_api.html").write_text(f'<!doctype html><html lang="es"><meta charset="utf-8"><title>Evidencias API</title><style>{estilo}</style><main><h1>Evidencias de peticiones HTTP</h1><p>Resultados registrados contra la API, sin sustituir las respuestas.</p><ul>{"".join(paginas)}</ul></main></html>', encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ejecutar únicamente en una base de demostración recién cargada: añade eventos de prueba.")
    parser.add_argument("--api", default="http://localhost:8000")
    parser.add_argument("--usuario", default="grupo_shalem_dayro_juan_jesus")
    parser.add_argument("--salida", type=Path, default=ROOT / "docs")
    args = parser.parse_args()
    resultados = {"fecha": datetime.now(ZoneInfo("America/Bogota")).isoformat(), "api": args.api,
                  "usuario": args.usuario, "B": verificar_reportes(args.api.rstrip('/')), "A": {}}
    for nombre, esperado in CASOS.items():
        r = ejecutar(args.api, args.usuario, nombre)
        assert r["status"] == esperado["status"], (nombre, r)
        if nombre == "A3 permitido": assert D(r["comprobacion"]["total"]) == D("805000")
        if nombre == "A4 permitido":
            assert D(r["respuesta"]["tasa_asistencia"]) == D("75")
            assert r["comprobacion"][-1]["usuario_app"] == args.usuario
        if nombre == "A5 sin opciones": assert r["respuesta"] == []
        if nombre == "A5 permitido":
            assert len(r["respuesta"]) > 0
            assert [s["capacidad"] for s in r["respuesta"]] == sorted(s["capacidad"] for s in r["respuesta"])
        resultados["A"][nombre] = r
    guardar(resultados, args.salida)
    print("A1–A5: 10 resultados correctos. B1–B4: todas las filas coinciden.")
