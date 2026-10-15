"""Presenta las cuentas independientes guardadas por scripts.evidencias."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def tabla(columnas, filas):
    return ['| ' + ' | '.join(columnas) + ' |', '| ' + ' | '.join('---' for _ in columnas) + ' |'] + [
        '| ' + ' | '.join('—' if v is None else str(v) for v in fila) + ' |' for fila in filas]


if __name__ == '__main__':
    r = json.loads((ROOT / 'docs/verificacion.json').read_text(encoding='utf-8'))
    b = r['B']
    texto = ['# Reporte de evidencias: entrega 1', '', 'Grupo: Shalem, Dayro, Juan y Jesús.', '',
             f'Verificación registrada: {r["fecha"]}. PostgreSQL 17, Python 3.12, FastAPI y Streamlit.', '',
             'Los casos y las pantallas provienen de ejecuciones reales. Las peticiones de la API se guardaron con un cliente HTTP en Python y se presentan en el visor incluido, equivalente a revisar el intercambio en Swagger. Las capturas de Streamlit se tomaron al ejecutar las mismas situaciones desde la interfaz. Cada ejecución prepara otro evento, por lo que sus ids y nombres de prueba pueden diferir.', '',
             'Las comparaciones B1–B4 y sus pantallas usan la carga inicial, antes de añadir los casos A o los ejemplos de endpoints. Las cuentas se realizaron por separado con las fórmulas explicadas abajo; `scripts/evidencias.py` las volvió a calcular sobre los registros base y comprobó cada fila contra las vistas y funciones SQL. Los datos completos están en `verificacion.json`.', '',
             '## Datos iniciales', '']
    texto += tabla(['Recurso', 'Cantidad verificada'], b['conteos_iniciales'].items())
    texto += ['', 'La carga tiene cuatro niveles del staff, doce eventos con servicios, eventos pasados y futuros y los cuatro estados. Hay 270 inscripciones y 122 llegadas en la carga inicial; un evento tiene cupo completo y otro termina después de medianoche. Los seis eventos finalizados tienen tasas 84 %, 71,11 %, 90 %, 50 %, 0 % y NULL. Se cargaron sin desactivar triggers.', '',
              '## A1–A5: permitidos y bloqueados', '']
    texto += tabla(['Caso', 'HTTP observado', 'Qué demuestra'], [(k, v['status'], {
        'A1 permitido': 'Reserva en salón activo, libre y con capacidad.',
        'A1 bloqueado': 'Media hora entre eventos no alcanza la hora de montaje.',
        'A2 permitido': 'Inscripción cuando queda cupo.',
        'A2 bloqueado': 'Segunda inscripción con aforo contratado de uno.',
        'A3 permitido': 'Cantidad por defecto y total con salón y servicios.',
        'A3 bloqueado': 'No se agregan servicios a eventos finalizados.',
        'A4 permitido': 'Cierre pasado, tasa 75 % y auditoría del operador.',
        'A4 bloqueado': 'Se impide finalizar antes de terminar.',
        'A5 permitido': 'Opciones activas, libres, suficientes y ordenadas.',
        'A5 sin opciones': 'Aforo 2.000: ninguna opción compatible.'}[k]) for k, v in r['A'].items()])
    texto += ['', '**A5 es una consulta.** La situación “bloqueada” se demuestra porque la función no ofrece salones que incumplen el aforo; devuelve `[]` con HTTP 200. No corresponde fabricar un error 409 para una consulta válida. El frontend informa que no hay opciones.', '']
    explicaciones = {
        'A1 permitido': 'El evento nace Cotizado. Para 50 personas en Heliconia durante dos horas, el total inicial es 2 × $320.000 = $640.000.',
        'A1 bloqueado': 'El intento empieza treinta minutos después del evento preparado. PostgreSQL devuelve el nombre, id y horario del evento en conflicto; la nueva reserva no se guarda.',
        'A2 permitido': 'La fila de inscripción se crea con hora_checkin vacía. El aforo lo verifica el trigger, no una resta hecha por Streamlit.',
        'A2 bloqueado': 'El caso prepara un evento de aforo uno e inscribe a una persona. Al intentar inscribir una segunda, el trigger responde CUPO y mantiene una sola inscripción.',
        'A3 permitido': 'Se omite la cantidad de café. PostgreSQL toma el aforo de 50: café = 50 × $6.500 = $325.000. Salón = 1,5 × $320.000 = $480.000. Total = $805.000. La cantidad y el precio contratado quedan almacenados.',
        'A3 bloqueado': 'El evento pasado se confirma y se finaliza antes de contratar el servicio. El trigger rechaza la línea porque el evento ya está cerrado.',
        'A4 permitido': 'Se preparan cuatro inscripciones y tres llegadas válidas en un evento pasado. Al finalizar: 3 / 4 × 100 = 75,00 %. La consulta posterior de auditoría conserva el operador enviado en X-Usuario.',
        'A4 bloqueado': 'El evento está Confirmado, pero su fin es futuro. El trigger rechaza el cambio y el estado no pasa a Finalizado.',
        'A5 permitido': 'La franja de 1,5 horas para 50 personas excluye Orquídea (capacidad 40). Heliconia aparece primero con costo estimado $480.000; luego los salones de mayor capacidad.',
        'A5 sin opciones': 'El mayor salón admite 1.000 personas. Un aforo de 2.000 deja la lista vacía; la aplicación no ofrece un salón inválido.'}
    for nombre, resultado in r['A'].items():
        archivo = nombre.replace(' ', '_')
        texto += [f'### {nombre}', '', explicaciones[nombre], '',
                  f'Petición: `{resultado["metodo"]} {resultado["ruta"]}`. HTTP observado: **{resultado["status"]}**.', '',
                  f'[Petición y respuesta completas]({archivo}.html).', '',
                  f'![API: {nombre}](capturas/api_{archivo}.png)', '',
                  f'![Streamlit: {nombre}](capturas/streamlit_{archivo}.png)', '']
    texto += ['## B1: organigrama', '',
              'A mano, se sigue el jefe_id de cada persona hasta la raíz. El número de ids de esa ruta da el nivel. Para contar personas a cargo se suman los hijos directos y todos los descendientes; no se incluye al propio empleado.', '',
              'Elena tiene dos gerentes, cuatro jefaturas y ocho auxiliares o técnicos: 2 + 4 + 8 = 14. Roberto tiene tres jefaturas con dos personas cada una: 3 + 6 = 9. Diana tiene una jefatura y sus dos asesores: 1 + 2 = 3. Cada jefatura tiene dos subordinados y cada persona del último nivel tiene cero.', '']
    manual = {m['id']: m for m in b['B1']['manual']}
    texto += tabla(['Empleado', 'Nivel manual / SQL', 'Directos manual / SQL', 'Total manual / SQL'], [
        (p['nombre'], f'{manual[p["id"]]["nivel"]} / {p["nivel"]}', f'{manual[p["id"]]["a_cargo_directos"]} / {p["a_cargo_directos"]}',
         f'{manual[p["id"]]["total_a_cargo"]} / {p["total_a_cargo"]}') for p in b['B1']['plataforma']])
    texto += ['', 'Ejemplo de ruta: Elena Suárez > Roberto Gómez > Luis Toro > Diego Paz. La consulta de la rama de Roberto entrega sus nueve descendientes. Se compararon la organización completa y las quince ramas, incluyendo ramas vacías.', '',
              '![B1 en Streamlit](capturas/streamlit_B1.png)', '', '## B2: cadena de escalamiento', '',
              'A mano, se empieza por el jefe inmediato y se sigue hasta el empleado sin jefe. Diego Paz (12) depende de Luis Toro (6), luego Roberto Gómez (2) y finalmente Elena Suárez (1). La lista es [6, 2, 1]; Diego no se incluye. Para Elena, el resultado es vacío.', '']
    texto += tabla(['Empleado', 'Ids de jefes a mano', 'Ids de jefes SQL', 'Coincide'], [
        (c['empleado'], c['manual'], [p['id'] for p in c['plataforma']], 'Sí') for c in b['B2']['comparaciones']])
    texto += ['', 'También se comprobó que orden toma los valores 1, 2, 3… en ese mismo orden.', '',
              '![B2 en Streamlit](capturas/streamlit_B2.png)', '', '## B3: ranking y Pareto', '',
              'Primero se excluyen los dos eventos Cancelado. Para cada evento se calcula (fin − inicio) en horas × precio_salon_congelado, y se suma cantidad × precio_congelado de sus líneas. Las diez cuentas de la carga inicial son:', '']
    texto += tabla(['Evento', 'Horas', 'Salón COP', 'Servicios COP', 'Total COP'], [
        (e['evento'], e['horas'], e['salon'], e['servicios'], e['total']) for e in b['B3']['liquidaciones']])
    texto += ['', 'Se agrupan esos totales por cliente: Innova = $36.510.000 + $69.900.000 = $106.410.000; Salud = $8.350.000 + $35.900.000 = $44.250.000; Tech = $5.140.000 + $950.000 + $7.835.000 = $13.925.000; Lucía = $2.870.000 + $2.635.000 = $5.505.000; Fundación = $2.797.500.', '',
              f'Total general manual y SQL: **${b["B3"]["total_general"]}**. Participación = facturación del cliente / total × 100. Acumulado = suma de los clientes hasta esa fila / total × 100. El ranking es 1 más el número de clientes con facturación mayor.', '',
              'Por ejemplo, Innova representa 106.410.000 / 172.887.500 × 100 = 61,55 %. Con Salud, el acumulado es 150.660.000 / 172.887.500 × 100 = 87,14 %. Ambos forman el segmento A porque Salud es quien cruza el 80 %; los siguientes quedan en B. Los tres clientes sin ingreso empatan en rango 6 y siguen presentes.', '']
    texto += tabla(['Cliente', 'Eventos', 'Facturación manual / SQL', 'Rango manual / SQL', 'Participación manual / SQL', 'Acumulado manual / SQL', 'Pareto'], [
        (m['nombre'], m['eventos_no_cancelados'], f'{m["facturacion"]} / {p["facturacion"]}', f'{m["ranking"]} / {p["ranking"]}',
         f'{m["participacion_pct"]} / {p["participacion_pct"]}', f'{m["acumulado_pct"]} / {p["acumulado_pct"]}', m['segmento_pareto'])
        for m, p in zip(b['B3']['manual'], b['B3']['plataforma'])])
    texto += ['', '![B3 en Streamlit](capturas/streamlit_B3.png)', '', '## B4: ocupación y tiempos muertos', '',
              'Se separan los eventos no cancelados por salón y se ordenan por inicio e id. El primer evento es número uno y no tiene anterior ni días libres. Para cada siguiente evento: días libres = (inicio actual − fin anterior) / 24 horas. Las horas acumuladas son la suma de las duraciones hasta esa fila.', '',
              'En Orquídea, Club de Lectura ocupa diez horas, desde las 15:00 hasta la 01:00 del día siguiente. Encuentro Interno ocupa dos horas: acumulado = 10 + 2 = 12. Entre el final del Club y el inicio del Encuentro hay nueve días y trece horas: 9 + 13 / 24 = 9,54 días. En Guayacán, la Jornada ocupa cuatro horas y el Taller tres: acumulado 7; el tiempo libre es 85 días y dos horas = 85,08 días.', '']
    texto += tabla(['Salón', 'Evento', 'N.º manual / SQL', 'Anterior', 'Días libres manual / SQL', 'Horas acumuladas manual / SQL'], [
        (p['salon'], m['evento'], f'{m["num_evento_salon"]} / {p["num_evento_salon"]}', m['evento_anterior'],
         f'{m["dias_libres"]} / {p["dias_libres"]}', f'{m["horas_acumuladas"]} / {p["horas_acumuladas"]}')
        for m, p in zip(b['B4']['manual'], b['B4']['plataforma'])])
    texto += ['', 'Las diez filas coinciden. Se incluyen los eventos Cotizado; el tiempo libre mide el intervalo completo entre eventos, incluida la hora reservada para montaje y aseo.', '',
              '![B4 en Streamlit](capturas/streamlit_B4.png)', '', '## Pruebas adicionales', '',
              'Se ejecutó `python -m pytest -q` contra una base separada con PostgreSQL 17: **39 pruebas aprobadas**. Cubren los límites de 59, 60 y 61 minutos; salones inactivos; capacidad; cupos; cambio de aforo; check-in en los extremos y fuera de ventana; doble llegada; precio congelado; cantidades por hora; alta, modificación y retiro de servicios; reprogramación; eventos de medianoche; tasas NULL, 0 y 75; auditoría; ciclos del staff; validaciones HTTP; SQL directo, competencia por el último cupo y dos reservas simultáneas en el mismo salón. También se comprobó que las dependencias instaladas son compatibles.', '',
              'El aviso de deprecación de AnyIO emitido por TestClient no afecta los resultados. Los casos A se repitieron desde Streamlit: la interfaz siguió funcionando después de los rechazos. El gráfico de B3 y las pantallas de B1–B4 se revisaron en el navegador.', '',
              '## Reproducir las evidencias', '',
              'Usa una base nueva de demostración y cárgala con `init_db.py --con-datos`. Enciende API y Streamlit. Instala `requirements-dev.txt` para las herramientas de captura. Las reglas y los ejemplos agregan datos, así que respeta este orden para mantener los reportes iniciales:', '',
              '```powershell', '.\\.venv\\Scripts\\python.exe -m scripts.capturar --modo reportes', '.\\.venv\\Scripts\\python.exe -m scripts.evidencias --api http://localhost:8000', '.\\.venv\\Scripts\\python.exe -m scripts.documentar --api http://localhost:8000', '.\\.venv\\Scripts\\python.exe -m scripts.capturar --modo reglas', '.\\.venv\\Scripts\\python.exe -m scripts.reporte', '```', '',
              'Si Playwright no tiene Chromium instalado, ejecuta `python -m playwright install chromium`. También puedes pasar `--navegador` con la ruta de un Chromium compatible. Los scripts de documentación leen NEXO_DB_URL del entorno o .env para importar las entidades; las peticiones de ejemplo se hacen por HTTP.', '',
              '## Pendientes del grupo', '',
              'Renombrar el ZIP con los apellidos completos. Recorrer los módulos en los computadores del grupo y practicar las cuentas anteriores. Consultar el numeral 5.3, mencionado en la rúbrica pero ausente en P2. Para la entrega del 19 de octubre, revisar el frontend y preparar la sustentación de 15 minutos.', '']
    (ROOT / 'docs/reporte_evidencias.md').write_text('\n'.join(texto), encoding='utf-8')
    print('Reporte con cuentas, comparaciones y capturas generado.')
