"""Genera el diccionario desde las entidades y registra ejemplos reales de las rutas."""
import argparse
from datetime import datetime, timedelta
import json
from pathlib import Path
from uuid import uuid4

import requests

ROOT = Path(__file__).resolve().parents[1]


def diccionario():
    from app.database import Base
    from app import models
    from sqlalchemy import CheckConstraint, UniqueConstraint
    from sqlalchemy.dialects.postgresql import dialect

    texto = ['# Diccionario de datos', '', 'Origen: entidades de `app/models.py`. Dinero en COP; los campos NUMERIC son exactos. Las fechas con hora se almacenan en hora local de Bogotá, sin zona horaria. Los ids son enteros generados por PostgreSQL.', '']
    for tabla in Base.metadata.sorted_tables:
        texto.extend([f'## {tabla.name}', '', '| Campo | Tipo SQL | Acepta NULL | Claves y valor inicial |', '|---|---|---|---|'])
        for c in tabla.columns:
            notas = []
            if c.primary_key: notas.append('PK, autoincremento')
            if c.unique: notas.append('UNIQUE')
            notas.extend('FK → ' + fk.target_fullname for fk in c.foreign_keys)
            if c.server_default: notas.append('DEFAULT ' + str(c.server_default.arg))
            if c.name == 'precio_salon_congelado': notas.append('Trigger A3 copia la tarifa del salón')
            if c.name == 'precio_congelado': notas.append('Trigger A3 copia la tarifa del servicio')
            if c.name == 'cantidad': notas.append('Trigger A3 asigna aforo, techo de horas o 1 si se omite')
            if c.name == 'tasa_asistencia': notas.append('NULL sin inscritos; porcentaje al finalizar')
            if c.name == 'hora_checkin': notas.append('NULL mientras no llegue; A2 valida ventana y unicidad')
            texto.append(f'| `{c.name}` | `{c.type.compile(dialect=dialect())}` | {"Sí" if c.nullable else "No"} | {"; ".join(notas) or "—"} |')
        texto.extend(['', 'Restricciones:', ''])
        for restriccion in sorted(tabla.constraints, key=lambda r: r.name or ''):
            if isinstance(restriccion, CheckConstraint): texto.append(f'- `{restriccion.name}`: `{restriccion.sqltext}`.')
            elif isinstance(restriccion, UniqueConstraint): texto.append('- UNIQUE: ' + ', '.join(f'`{c.name}`' for c in restriccion.columns) + '.')
        texto.append('')
    texto.extend(['## Reglas entre filas', '', '| Regla | Validación en PostgreSQL |', '|---|---|',
        '| A1 | Salón activo, capacidad, una hora entre eventos no cancelados y aforo no menor que inscritos |',
        '| A2 | Evento abierto, cupo, inscripción única, llegada en ventana y una sola llegada |',
        '| A3 | Total automático; precio y cantidad del servicio; bloqueo de líneas de eventos cerrados |',
        '| A4 | Inicio Cotizado, transiciones, fecha de cierre, porcentaje y auditoría |',
        '| Staff | Autorreferencia válida y ausencia de ciclos en la cadena de jefes |', '',
        'Las llaves foráneas no tienen borrado en cascada. La API no publica rutas para borrar clientes, salones, asistentes ni eventos. El historial queda asociado a su evento.', '',
        'En las respuestas JSON, los importes y porcentajes decimales se representan como cadenas para conservar precisión. Esto no cambia el tipo NUMERIC de PostgreSQL.', ''])
    (ROOT / 'docs/diccionario_datos.md').write_text('\n'.join(texto), encoding='utf-8')


def endpoints(api):
    sesion = requests.Session()
    sesion.headers['X-Usuario'] = 'grupo_shalem_dayro_juan_jesus'
    ejemplos = {}

    def registrar(metodo, ruta, plantilla=None, datos=None, parametros=None):
        r = sesion.request(metodo, api + ruta, json=datos, params=parametros, timeout=15)
        r.raise_for_status()
        respuesta = r.json() if r.content else None
        ejemplos[(plantilla or ruta, metodo.lower())] = {'ruta': ruta, 'parametros': parametros, 'cuerpo': datos,
                                                       'status': r.status_code, 'respuesta': respuesta}
        return respuesta

    from scripts.casos import ejecutar
    evento = ejecutar(api, sesion.headers['X-Usuario'], 'A1 permitido')
    ejemplos[('/eventos', 'post')] = {'ruta': '/eventos', 'parametros': None, 'cuerpo': evento['datos'],
                                    'status': evento['status'], 'respuesta': evento['respuesta']}
    eid = evento['respuesta']['id']
    sufijo = uuid4().hex[:8]
    cliente = registrar('POST', '/clientes', datos={'documento': 'demo' + sufijo, 'tipo_documento': 'NIT',
                        'nombre_razon_social': 'Cliente de documentación', 'correo': 'documentacion@example.com', 'telefono': '3001234567'})
    registrar('POST', '/staff', datos={'nombre': 'Apoyo de documentación', 'cargo': 'Auxiliar', 'area': 'Logística',
              'correo': f'apoyo{sufijo}@example.com', 'fecha_ingreso': '2026-10-01', 'jefe_id': 4})
    asistente = registrar('POST', '/asistentes', datos={'documento': 'doc' + sufijo, 'nombre': 'Asistente de documentación',
                          'correo': 'asistente@example.com', 'empresa': None})
    registrar('POST', f'/eventos/{eid}/inscripciones', '/eventos/{evento_id}/inscripciones', datos={'asistente_id': asistente['id']})
    registrar('POST', f'/eventos/{eid}/checkin', '/eventos/{evento_id}/checkin',
              datos={'documento': asistente['documento'], 'hora_checkin': evento['respuesta']['inicio']})
    servicios = registrar('GET', '/servicios')
    cafe = next(s for s in servicios if s['nombre'] == 'Estación de café')
    linea = registrar('POST', f'/eventos/{eid}/servicios', '/eventos/{evento_id}/servicios', datos={'servicio_id': cafe['id']})
    registrar('PUT', f'/eventos/{eid}/servicios/{linea["id"]}', '/eventos/{evento_id}/servicios/{linea_id}', datos={'cantidad': '25'})
    registrar('GET', f'/eventos/{eid}/servicios', '/eventos/{evento_id}/servicios')
    registrar('GET', f'/eventos/{eid}/cotizacion', '/eventos/{evento_id}/cotizacion')
    registrar('DELETE', f'/eventos/{eid}/servicios/{linea["id"]}', '/eventos/{evento_id}/servicios/{linea_id}')
    inicio = datetime.fromisoformat(evento['respuesta']['inicio'])
    registrar('PATCH', f'/eventos/{eid}', '/eventos/{evento_id}', datos={'fin': (inicio + timedelta(hours=2.5)).isoformat(), 'aforo_esperado': 40})
    registrar('PATCH', f'/eventos/{eid}/estado', '/eventos/{evento_id}/estado', datos={'estado': 'Confirmado'})
    registrar('PATCH', '/salones/1/activo', '/salones/{salon_id}/activo', parametros={'activo': 'true'})
    schema = sesion.get(api + '/openapi.json', timeout=10).json()
    for ruta, metodos in schema['paths'].items():
        for metodo in metodos:
            if (ruta, metodo) in ejemplos: continue
            if metodo != 'get': raise RuntimeError(f'Falta ejemplo de {metodo} {ruta}')
            concreta = ruta.replace('{cliente_id}', '1').replace('{staff_id}', '12').replace('{asistente_id}', str(asistente['id'])).replace('{salon_id}', '1').replace('{servicio_id}', str(cafe['id'])).replace('{evento_id}', str(eid))
            parametros = {'inicio': inicio.isoformat(), 'fin': (inicio + timedelta(hours=2)).isoformat(), 'aforo': 50} if ruta == '/salones/disponibles' else None
            registrar('GET', concreta, ruta, parametros=parametros)
    (ROOT / 'docs/ejemplos_endpoints.json').write_text(json.dumps([{'metodo': m.upper(), 'plantilla': p, **r} for (p, m), r in ejemplos.items()], ensure_ascii=False, indent=2), encoding='utf-8')
    texto = ['# Endpoints y ejemplos', '', 'Los ejemplos siguientes se registraron con la API encendida en una base de demostración. Los ids y las fechas cambian si se carga o ejecuta de nuevo. Antes de probar una mutación, consulta los catálogos e ids de tu propia base.', '',
             'Base habitual: `http://localhost:8000`. Documentación interactiva: `/docs`. Todas las consultas SQL que reciben valores usan parámetros. Encabezado de auditoría: `X-Usuario: grupo_shalem_dayro_juan_jesus`.', '',
             'Las colecciones grandes se muestran con su primer elemento para mantener legible este manual; la respuesta completa está en `ejemplos_endpoints.json`. Dinero y porcentajes usan cadenas decimales.', '',
             '| Método | Ruta | Operación |', '|---|---|---|']
    for ruta, metodos in schema['paths'].items():
        for metodo, info in metodos.items(): texto.append(f'| {metodo.upper()} | `{ruta}` | {info.get("summary", "")} |')
    for ruta, metodos in schema['paths'].items():
        for metodo, info in metodos.items():
            r = ejemplos[(ruta, metodo)]
            texto.extend(['', f'## {metodo.upper()} {ruta}', '', info.get('description', ''), '', 'Petición:', '', '```http', f'{metodo.upper()} {r["ruta"]}', 'X-Usuario: grupo_shalem_dayro_juan_jesus', '```'])
            if r['parametros']: texto.extend(['', 'Parámetros de consulta:', '', '```json', json.dumps(r['parametros'], ensure_ascii=False, indent=2), '```'])
            if r['cuerpo']: texto.extend(['', 'Cuerpo JSON:', '', '```json', json.dumps(r['cuerpo'], ensure_ascii=False, indent=2), '```'])
            respuesta = r['respuesta']
            if isinstance(respuesta, list) and len(respuesta) > 1: respuesta = respuesta[:1]
            texto.extend(['', f'Respuesta HTTP {r["status"]}:', '', '```json', json.dumps(respuesta, ensure_ascii=False, indent=2) if r['status'] != 204 else '(sin cuerpo)', '```'])
    texto.extend(['', '## Filtros y errores', '', '`GET /clientes?q=Tech` y `GET /asistentes?q=100000001` buscan por nombre o documento. `GET /eventos?estado=Confirmado&cliente_id=1` combina filtros. B1 admite `staff_id` opcional. A5 necesita `inicio`, `fin` y `aforo` positivo.', '',
                 '201: creación; 200: consulta o modificación; 204: servicio eliminado; 404: recurso inexistente; 409: regla de PostgreSQL, cupo o duplicado; 422: campos inválidos. Los ejemplos permitidos y bloqueados se documentan en `reporte_evidencias.md`.', ''])
    (ROOT / 'docs/endpoints.md').write_text('\n'.join(texto), encoding='utf-8')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Añade datos de ejemplo; usar en una base de demostración después de verificar B1–B4.')
    p.add_argument('--api', default='http://localhost:8000')
    args = p.parse_args()
    diccionario()
    endpoints(args.api.rstrip('/'))
    print('Diccionario y ejemplos de todas las rutas generados.')
