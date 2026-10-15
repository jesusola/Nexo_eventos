# Reporte de evidencias: entrega 1

Grupo: Shalem, Dayro, Juan y Jesús.

Verificación registrada: 2026-10-06T20:49:35.229453-05:00. PostgreSQL 17, Python 3.12, FastAPI y Streamlit.

Los casos y las pantallas provienen de ejecuciones reales. Las peticiones de la API se guardaron con un cliente HTTP en Python y se presentan en el visor incluido, equivalente a revisar el intercambio en Swagger. Las capturas de Streamlit se tomaron al ejecutar las mismas situaciones desde la interfaz. Cada ejecución prepara otro evento, por lo que sus ids y nombres de prueba pueden diferir.

Las comparaciones B1–B4 y sus pantallas usan la carga inicial, antes de añadir los casos A o los ejemplos de endpoints. Las cuentas se realizaron por separado con las fórmulas explicadas abajo; `scripts/evidencias.py` las volvió a calcular sobre los registros base y comprobó cada fila contra las vistas y funciones SQL. Los datos completos están en `verificacion.json`.

## Datos iniciales

| Recurso | Cantidad verificada |
| --- | --- |
| clientes | 8 |
| staff | 15 |
| eventos | 12 |
| asistentes | 60 |
| salones | 6 |
| servicios | 9 |

La carga tiene cuatro niveles del staff, doce eventos con servicios, eventos pasados y futuros y los cuatro estados. Hay 270 inscripciones y 122 llegadas en la carga inicial; un evento tiene cupo completo y otro termina después de medianoche. Los seis eventos finalizados tienen tasas 84 %, 71,11 %, 90 %, 50 %, 0 % y NULL. Se cargaron sin desactivar triggers.

## A1–A5: permitidos y bloqueados

| Caso | HTTP observado | Qué demuestra |
| --- | --- | --- |
| A1 permitido | 201 | Reserva en salón activo, libre y con capacidad. |
| A1 bloqueado | 409 | Media hora entre eventos no alcanza la hora de montaje. |
| A2 permitido | 201 | Inscripción cuando queda cupo. |
| A2 bloqueado | 409 | Segunda inscripción con aforo contratado de uno. |
| A3 permitido | 201 | Cantidad por defecto y total con salón y servicios. |
| A3 bloqueado | 409 | No se agregan servicios a eventos finalizados. |
| A4 permitido | 200 | Cierre pasado, tasa 75 % y auditoría del operador. |
| A4 bloqueado | 409 | Se impide finalizar antes de terminar. |
| A5 permitido | 200 | Opciones activas, libres, suficientes y ordenadas. |
| A5 sin opciones | 200 | Aforo 2.000: ninguna opción compatible. |

**A5 es una consulta.** La situación “bloqueada” se demuestra porque la función no ofrece salones que incumplen el aforo; devuelve `[]` con HTTP 200. No corresponde fabricar un error 409 para una consulta válida. El frontend informa que no hay opciones.

### A1 permitido

El evento nace Cotizado. Para 50 personas en Heliconia durante dos horas, el total inicial es 2 × $320.000 = $640.000.

Petición: `POST /eventos`. HTTP observado: **201**.

[Petición y respuesta completas](A1_permitido.html).

![API: A1 permitido](capturas/api_A1_permitido.png)

![Streamlit: A1 permitido](capturas/streamlit_A1_permitido.png)

### A1 bloqueado

El intento empieza treinta minutos después del evento preparado. PostgreSQL devuelve el nombre, id y horario del evento en conflicto; la nueva reserva no se guarda.

Petición: `POST /eventos`. HTTP observado: **409**.

[Petición y respuesta completas](A1_bloqueado.html).

![API: A1 bloqueado](capturas/api_A1_bloqueado.png)

![Streamlit: A1 bloqueado](capturas/streamlit_A1_bloqueado.png)

### A2 permitido

La fila de inscripción se crea con hora_checkin vacía. El aforo lo verifica el trigger, no una resta hecha por Streamlit.

Petición: `POST /eventos/16/inscripciones`. HTTP observado: **201**.

[Petición y respuesta completas](A2_permitido.html).

![API: A2 permitido](capturas/api_A2_permitido.png)

![Streamlit: A2 permitido](capturas/streamlit_A2_permitido.png)

### A2 bloqueado

El caso prepara un evento de aforo uno e inscribe a una persona. Al intentar inscribir una segunda, el trigger responde CUPO y mantiene una sola inscripción.

Petición: `POST /eventos/17/inscripciones`. HTTP observado: **409**.

[Petición y respuesta completas](A2_bloqueado.html).

![API: A2 bloqueado](capturas/api_A2_bloqueado.png)

![Streamlit: A2 bloqueado](capturas/streamlit_A2_bloqueado.png)

### A3 permitido

Se omite la cantidad de café. PostgreSQL toma el aforo de 50: café = 50 × $6.500 = $325.000. Salón = 1,5 × $320.000 = $480.000. Total = $805.000. La cantidad y el precio contratado quedan almacenados.

Petición: `POST /eventos/18/servicios`. HTTP observado: **201**.

[Petición y respuesta completas](A3_permitido.html).

![API: A3 permitido](capturas/api_A3_permitido.png)

![Streamlit: A3 permitido](capturas/streamlit_A3_permitido.png)

### A3 bloqueado

El evento pasado se confirma y se finaliza antes de contratar el servicio. El trigger rechaza la línea porque el evento ya está cerrado.

Petición: `POST /eventos/19/servicios`. HTTP observado: **409**.

[Petición y respuesta completas](A3_bloqueado.html).

![API: A3 bloqueado](capturas/api_A3_bloqueado.png)

![Streamlit: A3 bloqueado](capturas/streamlit_A3_bloqueado.png)

### A4 permitido

Se preparan cuatro inscripciones y tres llegadas válidas en un evento pasado. Al finalizar: 3 / 4 × 100 = 75,00 %. La consulta posterior de auditoría conserva el operador enviado en X-Usuario.

Petición: `PATCH /eventos/20/estado`. HTTP observado: **200**.

[Petición y respuesta completas](A4_permitido.html).

![API: A4 permitido](capturas/api_A4_permitido.png)

![Streamlit: A4 permitido](capturas/streamlit_A4_permitido.png)

### A4 bloqueado

El evento está Confirmado, pero su fin es futuro. El trigger rechaza el cambio y el estado no pasa a Finalizado.

Petición: `PATCH /eventos/21/estado`. HTTP observado: **409**.

[Petición y respuesta completas](A4_bloqueado.html).

![API: A4 bloqueado](capturas/api_A4_bloqueado.png)

![Streamlit: A4 bloqueado](capturas/streamlit_A4_bloqueado.png)

### A5 permitido

La franja de 1,5 horas para 50 personas excluye Orquídea (capacidad 40). Heliconia aparece primero con costo estimado $480.000; luego los salones de mayor capacidad.

Petición: `GET /salones/disponibles`. HTTP observado: **200**.

[Petición y respuesta completas](A5_permitido.html).

![API: A5 permitido](capturas/api_A5_permitido.png)

![Streamlit: A5 permitido](capturas/streamlit_A5_permitido.png)

### A5 sin opciones

El mayor salón admite 1.000 personas. Un aforo de 2.000 deja la lista vacía; la aplicación no ofrece un salón inválido.

Petición: `GET /salones/disponibles`. HTTP observado: **200**.

[Petición y respuesta completas](A5_sin_opciones.html).

![API: A5 sin opciones](capturas/api_A5_sin_opciones.png)

![Streamlit: A5 sin opciones](capturas/streamlit_A5_sin_opciones.png)

## B1: organigrama

A mano, se sigue el jefe_id de cada persona hasta la raíz. El número de ids de esa ruta da el nivel. Para contar personas a cargo se suman los hijos directos y todos los descendientes; no se incluye al propio empleado.

Elena tiene dos gerentes, cuatro jefaturas y ocho auxiliares o técnicos: 2 + 4 + 8 = 14. Roberto tiene tres jefaturas con dos personas cada una: 3 + 6 = 9. Diana tiene una jefatura y sus dos asesores: 1 + 2 = 3. Cada jefatura tiene dos subordinados y cada persona del último nivel tiene cero.

| Empleado | Nivel manual / SQL | Directos manual / SQL | Total manual / SQL |
| --- | --- | --- | --- |
| Elena Suárez | 1 / 1 | 2 / 2 | 14 / 14 |
| Roberto Gómez | 2 / 2 | 3 / 3 | 9 / 9 |
| Mario Luna | 3 / 3 | 2 / 2 | 2 / 2 |
| Pedro Díaz | 4 / 4 | 0 / 0 | 0 / 0 |
| Sara Peña | 4 / 4 | 0 / 0 | 0 / 0 |
| Carmen Ruiz | 3 / 3 | 2 / 2 | 2 / 2 |
| Juan Melo | 4 / 4 | 0 / 0 | 0 / 0 |
| Rosa Gil | 4 / 4 | 0 / 0 | 0 / 0 |
| Luis Toro | 3 / 3 | 2 / 2 | 2 / 2 |
| Diego Paz | 4 / 4 | 0 / 0 | 0 / 0 |
| Hugo Rey | 4 / 4 | 0 / 0 | 0 / 0 |
| Diana Castro | 2 / 2 | 1 / 1 | 3 / 3 |
| Ana Vega | 3 / 3 | 2 / 2 | 2 / 2 |
| Mía Cruz | 4 / 4 | 0 / 0 | 0 / 0 |
| Leo Ríos | 4 / 4 | 0 / 0 | 0 / 0 |

Ejemplo de ruta: Elena Suárez > Roberto Gómez > Luis Toro > Diego Paz. La consulta de la rama de Roberto entrega sus nueve descendientes. Se compararon la organización completa y las quince ramas, incluyendo ramas vacías.

![B1 en Streamlit](capturas/streamlit_B1.png)

## B2: cadena de escalamiento

A mano, se empieza por el jefe inmediato y se sigue hasta el empleado sin jefe. Diego Paz (12) depende de Luis Toro (6), luego Roberto Gómez (2) y finalmente Elena Suárez (1). La lista es [6, 2, 1]; Diego no se incluye. Para Elena, el resultado es vacío.

| Empleado | Ids de jefes a mano | Ids de jefes SQL | Coincide |
| --- | --- | --- | --- |
| Elena Suárez | [] | [] | Sí |
| Roberto Gómez | [1] | [1] | Sí |
| Diana Castro | [1] | [1] | Sí |
| Mario Luna | [2, 1] | [2, 1] | Sí |
| Carmen Ruiz | [2, 1] | [2, 1] | Sí |
| Luis Toro | [2, 1] | [2, 1] | Sí |
| Ana Vega | [3, 1] | [3, 1] | Sí |
| Pedro Díaz | [4, 2, 1] | [4, 2, 1] | Sí |
| Sara Peña | [4, 2, 1] | [4, 2, 1] | Sí |
| Juan Melo | [5, 2, 1] | [5, 2, 1] | Sí |
| Rosa Gil | [5, 2, 1] | [5, 2, 1] | Sí |
| Diego Paz | [6, 2, 1] | [6, 2, 1] | Sí |
| Hugo Rey | [6, 2, 1] | [6, 2, 1] | Sí |
| Mía Cruz | [7, 3, 1] | [7, 3, 1] | Sí |
| Leo Ríos | [7, 3, 1] | [7, 3, 1] | Sí |

También se comprobó que orden toma los valores 1, 2, 3… en ese mismo orden.

![B2 en Streamlit](capturas/streamlit_B2.png)

## B3: ranking y Pareto

Primero se excluyen los dos eventos Cancelado. Para cada evento se calcula (fin − inicio) en horas × precio_salon_congelado, y se suma cantidad × precio_congelado de sus líneas. Las diez cuentas de la carga inicial son:

| Evento | Horas | Salón COP | Servicios COP | Total COP |
| --- | --- | --- | --- | --- |
| Jornada Científica Solvida | 4.0 | 2600000.000 | 2540000.0000 | 5140000.00 |
| Capacitación en Ciberseguridad | 5.0 | 4000000.000 | 4350000.0000 | 8350000.00 |
| Club de Lectura Páramo | 10.0 | 2500000.000 | 370000.0000 | 2870000.00 |
| Feria de Innovación Nexo | 9.0 | 16200000.000 | 20310000.0000 | 36510000.00 |
| Simposio de Educación | 3.0 | 960000.000 | 1837500.0000 | 2797500.00 |
| Encuentro Interno Nexo | 2.0 | 500000.000 | 450000.0000 | 950000.00 |
| Congreso Nacional de Salud | 9.0 | 16200000.000 | 19700000.0000 | 35900000.00 |
| Seminario Corporativo Q4 | 4.0 | 3200000.000 | 4635000.0000 | 7835000.00 |
| Taller de Economía Circular | 3.0 | 1950000.000 | 685000.0000 | 2635000.00 |
| Feria Navideña | 10.0 | 25000000.000 | 44900000.0000 | 69900000.00 |

Se agrupan esos totales por cliente: Innova = $36.510.000 + $69.900.000 = $106.410.000; Salud = $8.350.000 + $35.900.000 = $44.250.000; Tech = $5.140.000 + $950.000 + $7.835.000 = $13.925.000; Lucía = $2.870.000 + $2.635.000 = $5.505.000; Fundación = $2.797.500.

Total general manual y SQL: **$172887500.00**. Participación = facturación del cliente / total × 100. Acumulado = suma de los clientes hasta esa fila / total × 100. El ranking es 1 más el número de clientes con facturación mayor.

Por ejemplo, Innova representa 106.410.000 / 172.887.500 × 100 = 61,55 %. Con Salud, el acumulado es 150.660.000 / 172.887.500 × 100 = 87,14 %. Ambos forman el segmento A porque Salud es quien cruza el 80 %; los siguientes quedan en B. Los tres clientes sin ingreso empatan en rango 6 y siguen presentes.

| Cliente | Eventos | Facturación manual / SQL | Rango manual / SQL | Participación manual / SQL | Acumulado manual / SQL | Pareto |
| --- | --- | --- | --- | --- | --- | --- |
| Innova Market | 2 | 106410000.00 / 106410000.00 | 1 / 1 | 61.55 / 61.55 | 61.55 / 61.55 | A (80%) |
| Salud Vital EPS | 2 | 44250000.00 / 44250000.00 | 2 / 2 | 25.59 / 25.59 | 87.14 / 87.14 | A (80%) |
| Tech Corp S.A. | 3 | 13925000.00 / 13925000.00 | 3 / 3 | 8.05 / 8.05 | 95.20 / 95.20 | B (resto) |
| Lucía Fernández | 2 | 5505000.00 / 5505000.00 | 4 / 4 | 3.18 / 3.18 | 98.38 / 98.38 | B (resto) |
| Fundación Educar | 1 | 2797500.00 / 2797500.00 | 5 / 5 | 1.62 / 1.62 | 100.00 / 100.00 | B (resto) |
| Carlos Mendoza | 0 | 0 / 0 | 6 / 6 | 0.00 / 0.00 | 100.00 / 100.00 | B (resto) |
| Andrés Vargas | 0 | 0 / 0 | 6 / 6 | 0.00 / 0.00 | 100.00 / 100.00 | B (resto) |
| Marta Rojas | 0 | 0 / 0 | 6 / 6 | 0.00 / 0.00 | 100.00 / 100.00 | B (resto) |

![B3 en Streamlit](capturas/streamlit_B3.png)

## B4: ocupación y tiempos muertos

Se separan los eventos no cancelados por salón y se ordenan por inicio e id. El primer evento es número uno y no tiene anterior ni días libres. Para cada siguiente evento: días libres = (inicio actual − fin anterior) / 24 horas. Las horas acumuladas son la suma de las duraciones hasta esa fila.

En Orquídea, Club de Lectura ocupa diez horas, desde las 15:00 hasta la 01:00 del día siguiente. Encuentro Interno ocupa dos horas: acumulado = 10 + 2 = 12. Entre el final del Club y el inicio del Encuentro hay nueve días y trece horas: 9 + 13 / 24 = 9,54 días. En Guayacán, la Jornada ocupa cuatro horas y el Taller tres: acumulado 7; el tiempo libre es 85 días y dos horas = 85,08 días.

| Salón | Evento | N.º manual / SQL | Anterior | Días libres manual / SQL | Horas acumuladas manual / SQL |
| --- | --- | --- | --- | --- | --- |
| Salón Orquídea | Club de Lectura Páramo | 1 / 1 | — | None / None | 10.00 / 10.00 |
| Salón Orquídea | Encuentro Interno Nexo | 2 / 2 | Club de Lectura Páramo | 9.54 / 9.54 | 12.00 / 12.00 |
| Salón Heliconia | Simposio de Educación | 1 / 1 | — | None / None | 3.00 / 3.00 |
| Salón Guayacán | Jornada Científica Solvida | 1 / 1 | — | None / None | 4.00 / 4.00 |
| Salón Guayacán | Taller de Economía Circular | 2 / 2 | Jornada Científica Solvida | 85.08 / 85.08 | 7.00 / 7.00 |
| Salón Ceiba | Capacitación en Ciberseguridad | 1 / 1 | — | None / None | 5.00 / 5.00 |
| Salón Ceiba | Seminario Corporativo Q4 | 2 / 2 | Capacitación en Ciberseguridad | 65.79 / 65.79 | 9.00 / 9.00 |
| Gran Salón Cóndor | Feria de Innovación Nexo | 1 / 1 | — | None / None | 9.00 / 9.00 |
| Gran Salón Cóndor | Congreso Nacional de Salud | 2 / 2 | Feria de Innovación Nexo | 53.58 / 53.58 | 18.00 / 18.00 |
| Auditorio Principal | Feria Navideña | 1 / 1 | — | None / None | 10.00 / 10.00 |

Las diez filas coinciden. Se incluyen los eventos Cotizado; el tiempo libre mide el intervalo completo entre eventos, incluida la hora reservada para montaje y aseo.

![B4 en Streamlit](capturas/streamlit_B4.png)

## Pruebas adicionales

Se ejecutó `python -m pytest -q` contra una base separada con PostgreSQL 17: **39 pruebas aprobadas**. Cubren los límites de 59, 60 y 61 minutos; salones inactivos; capacidad; cupos; cambio de aforo; check-in en los extremos y fuera de ventana; doble llegada; precio congelado; cantidades por hora; alta, modificación y retiro de servicios; reprogramación; eventos de medianoche; tasas NULL, 0 y 75; auditoría; ciclos del staff; validaciones HTTP; SQL directo, competencia por el último cupo y dos reservas simultáneas en el mismo salón. También se comprobó que las dependencias instaladas son compatibles.

El aviso de deprecación de AnyIO emitido por TestClient no afecta los resultados. Los casos A se repitieron desde Streamlit: la interfaz siguió funcionando después de los rechazos. El gráfico de B3 y las pantallas de B1–B4 se revisaron en el navegador.

## Reproducir las evidencias

Usa una base nueva de demostración y cárgala con `init_db.py --con-datos`. Enciende API y Streamlit. Instala `requirements-dev.txt` para las herramientas de captura. Las reglas y los ejemplos agregan datos, así que respeta este orden para mantener los reportes iniciales:

```powershell
.\.venv\Scripts\python.exe -m scripts.capturar --modo reportes
.\.venv\Scripts\python.exe -m scripts.evidencias --api http://localhost:8000
.\.venv\Scripts\python.exe -m scripts.documentar --api http://localhost:8000
.\.venv\Scripts\python.exe -m scripts.capturar --modo reglas
.\.venv\Scripts\python.exe -m scripts.reporte
```

Si Playwright no tiene Chromium instalado, ejecuta `python -m playwright install chromium`. También puedes pasar `--navegador` con la ruta de un Chromium compatible. Los scripts de documentación leen NEXO_DB_URL del entorno o .env para importar las entidades; las peticiones de ejemplo se hacen por HTTP.

## Pendientes del grupo

Renombrar el ZIP con los apellidos completos. Recorrer los módulos en los computadores del grupo y practicar las cuentas anteriores. Consultar el numeral 5.3, mencionado en la rúbrica pero ausente en P2. Para la entrega del 19 de octubre, revisar el frontend y preparar la sustentación de 15 minutos.
