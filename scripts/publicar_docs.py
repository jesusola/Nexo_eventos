"""Exporta los documentos locales a HTML y el esquema a SVG."""
from html import escape
from pathlib import Path
import re

from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[1]


def diagrama():
    from app.database import Base
    from app import models
    from sqlalchemy.dialects.postgresql import dialect

    posiciones = {'clientes': (45, 125), 'staff': (45, 395), 'salones': (45, 745),
                  'eventos': (465, 320), 'auditoria': (465, 790),
                  'servicios_evento': (895, 160), 'inscripciones': (895, 575),
                  'servicios': (1300, 125), 'asistentes': (1300, 575)}
    ancho = 345
    alturas = {n: 55 + 24 * len(Base.metadata.tables[n].columns) for n in posiciones}
    partes = ['<svg xmlns="http://www.w3.org/2000/svg" width="1690" height="1110" viewBox="0 0 1690 1110">',
              '<rect width="1690" height="1110" fill="#f6f8fa"/>',
              '<style>text{font-family:Segoe UI,Arial,sans-serif}.nombre{font-size:21px;font-weight:600;fill:white}.campo{font-size:13px;fill:#1c303b}.rel{font-size:13px;fill:#174a5a}</style>',
              '<text x="45" y="50" font-size="30" fill="#132e3c">NexoEventos · diagrama relacional</text>',
              '<text x="45" y="83" font-size="17" fill="#41515e">PK: clave primaria · FK: clave foránea · UK: única · cada línea une una FK con su tabla referenciada</text>']

    def linea(puntos, etiqueta, x, y):
        partes.append(f'<polyline points="{puntos}" fill="none" stroke="#62899d" stroke-width="2.5"/>')
        partes.append(f'<rect x="{x-6}" y="{y-16}" width="{len(etiqueta)*7+14}" height="23" rx="4" fill="#f6f8fa"/><text class="rel" x="{x}" y="{y}">{escape(etiqueta)}</text>')

    linea('390,230 430,230 430,400 465,400', '1 → N', 402, 282)
    linea('390,460 465,460', '1 → N', 400, 450)
    linea('390,840 435,840 435,520 465,520', '1 → N', 400, 687)
    linea('390,540 413,540 413,680 18,680 18,540 45,540', 'jefe 0..1 → N', 115, 681)
    linea('810,385 850,385 850,250 895,250', '1 → N', 830, 301)
    linea('1300,220 1240,220', '1 → N', 1244, 209)
    linea('810,600 895,650', '1 → N', 832, 610)
    linea('1300,650 1240,650', '1 → N', 1244, 639)
    linea('640,687 640,790', '1 → N', 650, 746)

    for nombre, (x, y) in posiciones.items():
        tabla = Base.metadata.tables[nombre]
        partes.append(f'<rect x="{x}" y="{y}" width="{ancho}" height="{alturas[nombre]}" rx="7" fill="white" stroke="#bacbd4"/>')
        partes.append(f'<path d="M{x+7} {y} H{x+ancho-7} Q{x+ancho} {y} {x+ancho} {y+7} V{y+38} H{x} V{y+7} Q{x} {y} {x+7} {y}" fill="#245269"/>')
        partes.append(f'<text class="nombre" x="{x+13}" y="{y+27}">{nombre}</text>')
        for i, c in enumerate(tabla.columns):
            claves = ('PK ' if c.primary_key else '') + ('FK ' if c.foreign_keys else '') + ('UK ' if c.unique else '')
            tipo = c.type.compile(dialect=dialect()).replace('TIMESTAMP WITHOUT TIME ZONE', 'TIMESTAMP')
            partes.append(f'<text class="campo" x="{x+12}" y="{y+62+24*i}">{escape(claves+c.name+" : "+tipo)}</text>')
    partes.append('<text x="45" y="1080" font-size="15" fill="#41515e">UNIQUE compuestas: servicios_evento(evento_id, servicio_id) e inscripciones(evento_id, asistente_id). jefe_id admite NULL.</text></svg>')
    (ROOT / 'docs/diagrama_relacional.svg').write_text(''.join(partes), encoding='utf-8')


if __name__ == '__main__':
    diagrama()
    md = MarkdownIt('commonmark', {'html': True}).enable('table')
    css = 'body{font:16px/1.6 Segoe UI,Arial,sans-serif;color:#17303d;background:#f4f6f8;margin:0}main{background:white;max-width:1200px;margin:32px auto;padding:38px}h1{font-size:30px}h2{margin-top:36px;border-bottom:1px solid #d0dce3}table{border-collapse:collapse;display:block;overflow:auto;margin:20px 0;font-size:14px}td,th{padding:9px 12px;border:1px solid #ccd8df;text-align:left}th{background:#edf3f6}pre{background:#edf3f6;padding:18px;overflow:auto;font-size:14px}img{max-width:100%;height:auto;border:1px solid #ccd8df}a{color:#126791}nav{display:flex;gap:18px;flex-wrap:wrap}code{font-family:Consolas,monospace}@media print{body{background:white}main{margin:0;padding:0}h2,h3{break-after:avoid}img{max-height:23cm;object-fit:contain}pre{white-space:pre-wrap;word-break:break-word}table{font-size:11px}}'
    for archivo in list((ROOT / 'docs').glob('*.md')) + [ROOT / 'README.md']:
        contenido = archivo.read_text(encoding='utf-8')
        contenido = re.sub(r'```mermaid\n.*?```', '<img src="diagrama_relacional.svg" alt="Diagrama relacional">', contenido, flags=re.S)
        html = md.render(contenido)
        html = re.sub(r'href="([^"#]*?)\.md([#\"]?)', r'href="\1.html\2', html)
        destino = archivo.with_suffix('.html')
        nav = '<nav><a href="../README.html">Ejecutar y usar</a><a href="decisiones.html">Decisiones</a><a href="reporte_evidencias.html">Evidencias</a><a href="diagrama_relacional.html">Diagrama</a><a href="diccionario_datos.html">Diccionario</a><a href="endpoints.html">Endpoints</a></nav>' if archivo.parent.name == 'docs' else '<nav><a href="docs/decisiones.html">Decisiones</a><a href="docs/reporte_evidencias.html">Evidencias</a></nav>'
        destino.write_text(f'<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{escape(archivo.stem)} · NexoEventos</title><style>{css}</style><main>{nav}{html}</main></html>', encoding='utf-8')
    print('Documentos HTML y diagrama SVG exportados.')
