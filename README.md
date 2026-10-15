# NexoEventos: entrega 1

Grupo: Shalem, Dayro, Juan y Jesús.

Este proyecto contiene la API, las entidades, los scripts SQL, los datos de prueba y una interfaz de Streamlit para demostrar las reglas. PostgreSQL controla las reservas, los cupos, los servicios, el cierre y la auditoría. Streamlit consulta la API y no abre conexiones a la base.

Puedes abrir `README.html` y los documentos HTML de `docs/` directamente en el navegador, sin encender la API. La carpeta incluye 25 capturas y el reporte con las cuentas de B1–B4. La validación en PostgreSQL 17 aprobó 39 pruebas; el registro está en `docs/pruebas.txt`.

## Ejecutar en Windows

Necesitas Python 3.12 y PostgreSQL 14 o superior. La verificación de esta entrega usa PostgreSQL 17. Abre PowerShell en esta carpeta.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

`requirements.txt` fija las dependencias principales. `requirements-lock.txt` conserva todas las versiones del entorno comprobado, incluidas las herramientas de pruebas y captura; puedes usarlo en lugar de `requirements.txt` si deseas reproducir ese entorno completo.

Edita `.env`: en `NEXO_DB_URL` cambia el usuario, la clave, el puerto y el nombre de la base. El nombre sugerido es `nexoeventos`. Si la contraseña contiene caracteres como `@` o `#`, codifícalos para una URL. El archivo `.env` es local y no forma parte del ZIP.

Crea una base vacía desde pgAdmin o con:

```powershell
createdb -U postgres nexoeventos
.\.venv\Scripts\python.exe init_db.py --con-datos
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

Si `createdb` no aparece como comando, usa su ruta, por ejemplo `C:\Program Files\PostgreSQL\17\bin\createdb.exe`, o crea la base en pgAdmin. PostgreSQL debe estar encendido.

La API queda en [localhost:8000](http://localhost:8000) y Swagger en [localhost:8000/docs](http://localhost:8000/docs). Deja esa terminal abierta. En una segunda terminal, desde esta misma carpeta:

```powershell
.\.venv\Scripts\python.exe -m streamlit run frontend/app.py
```

Streamlit abre [localhost:8501](http://localhost:8501). Su dirección de API aparece en la barra lateral. Para detener cada proceso, pulsa `Ctrl+C` en su terminal.

## Qué hace la carga

`init_db.py` crea las tablas con SQLAlchemy y aplica A1–A5 y B1–B4. Con `--con-datos` carga seis salones, nueve servicios, ocho clientes, quince empleados, doce eventos y sesenta asistentes. Los servicios, las inscripciones y los cambios de estado pasan por los triggers. Hay un evento que termina después de medianoche.

Las fechas se desplazan respecto al día de carga para conservar eventos pasados y futuros. Los nombres, las duraciones y los precios permanecen iguales. Los eventos pasados tienen tasas 84 %, 71,11 %, 90 %, 50 %, 0 % y una tasa vacía.

Si la base ya tiene clientes, el programa detiene la carga para evitar duplicados. Nunca borra datos. Puedes ejecutar `python init_db.py` sin `--con-datos` para volver a aplicar los scripts. `create_all` no cambia tablas existentes: usa una base nueva para la primera instalación de este esquema.

## Usar el sistema

1. En **Disponibilidad**, indica inicio, fin y aforo. Las fechas usan hora de Bogotá; también se aceptan fechas ISO con zona horaria.
2. En **Eventos**, selecciona cliente y coordinador, consulta salones libres y crea el evento. Nace Cotizado. Contrata servicios, consulta el desglose y confirma cuando corresponda.
3. En **Asistentes**, registra la persona, inscríbela y usa su documento al llegar. El check-in admite desde una hora antes del inicio hasta la hora de fin.
4. En **Eventos**, reprograma un evento abierto o revisa su historial. Para finalizar, primero debe estar Confirmado y su hora de fin debe haber pasado. Finalizado y Cancelado son definitivos.
5. En **Reportes**, consulta el organigrama, los jefes, el Pareto y la ocupación. El ranking incluye todos los eventos no cancelados, también los cotizados.
6. En **Pruebas de entrega**, ejecuta casos permitidos y bloqueados. Cada caso crea sus propios datos; úsalo en una base de demostración. Las consultas analíticas del reporte se comparan antes de añadir esos casos.

El campo **Usuario** identifica a quien hace los cambios. La API lo recibe en `X-Usuario` y la auditoría lo conserva. Es una identificación del operador para la práctica; no constituye autenticación.

## Probar la entrega

Las pruebas necesitan otra base. Nunca apuntes las pruebas a la base que usa el grupo.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
createdb -U postgres nexoeventos_pruebas
$env:NEXO_TEST_DB_URL = 'postgresql+psycopg2://postgres:TU_CLAVE@localhost:5432/nexoeventos_pruebas'
.\.venv\Scripts\python.exe -m pytest -q
```

La mayoría de las pruebas revierte sus cambios. Las pruebas de cupo y reserva concurrentes crean eventos temporales y los eliminan al terminar. La carga inicial permanece en la base de pruebas.

## Archivos para revisar

| Archivo | Contenido |
|---|---|
| `docs/decisiones.md` | Motivo de cada decisión y explicación para la sustentación |
| `docs/diagrama_relacional.md` | Tablas y cardinalidades |
| `docs/diccionario_datos.md` | Campos, tipos y restricciones |
| `docs/endpoints.md` | Rutas con ejemplos de petición y respuesta |
| `docs/reporte_evidencias.md` | Casos A1–A5 y comparación independiente de B1–B4 |
| `docs/capturas/` | Pantallas de la API y de Streamlit |
| `docs/verificacion.json` | Resultado de la verificación realizada |

Para la entrega, el ZIP debe contener esta carpeta, sin `.env`, `.venv`, cachés ni bases de datos locales. P2 pide nombrarlo con los apellidos del grupo. Los apellidos no están completos en los datos recibidos, por lo que el ZIP usa los nombres y debe renombrarse antes de enviarlo.

## Problemas frecuentes

- **Falta NEXO_DB_URL:** copia la plantilla como `.env` y configura la conexión.
- **Conexión rechazada:** revisa PostgreSQL, el puerto y la base indicada.
- **Password authentication failed:** corrige usuario o contraseña en `.env`.
- **HTTP 409:** una regla del negocio o una restricción rechazó la operación. Lee el mensaje; la transacción se revierte.
- **HTTP 422:** revisa campos, fechas, cantidades y valores permitidos.
- **No hay salones:** el aforo o el horario solicitado no tienen opciones. Prueba otra franja.
- **La base ya contiene clientes:** no repitas la carga de datos. Sigue usando esa base o crea otra vacía.
