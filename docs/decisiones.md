# Decisiones del proyecto

Grupo: Shalem, Dayro, Juan y Jesús.

El punto de partida fue el modelo de `trabajo`. Se mantuvieron sus nueve entidades, relaciones, nombres de columnas y restricciones. Del ZIP del segundo proyecto se retomaron la separación de routers, la dependencia del usuario y el manejo del commit. De la primera referencia se adaptaron la carga de datos y las ideas de las consultas recursivas y de Pareto. La revisión encontró reglas incompletas en ambas referencias; los scripts finales corrigen esos casos.

## 1. Separar las tres capas

Los modelos describen las tablas. Pydantic revisa los datos que entran y define las respuestas. Los routers buscan recursos, guardan cambios y traducen errores. Las decisiones del negocio viven en PostgreSQL. Así, una inserción hecha en pgAdmin tiene las mismas reglas que una petición de Swagger.

Streamlit llama a la API con HTTP. No importa SQLAlchemy ni recibe credenciales de PostgreSQL. La pantalla puede fallar o quedar cerrada sin perder las restricciones de la base.

## 2. Mantener el esquema existente

Se conservaron `nombre_razon_social`, `capacidad_maxima`, `unidad_cobro`, `servicios_evento`, `hora_checkin` y `auditoria`. Copiar las referencias sin adaptarlas habría generado columnas desconocidas y valores incompatibles. También se conservaron las tildes de Pequeño, Dirección y Logística.

Cada cliente, salón, servicio, empleado y asistente aparece una vez en su tabla. Los eventos guardan llaves foráneas, no copias de nombres y correos. Servicios e inscripciones usan tablas puente porque sus relaciones son de muchos a muchos. Cada puente tiene un `id` y una restricción única sobre el par de llaves. Esa combinación facilita las rutas de edición e impide duplicados.

Los atributos descriptivos dependen de la llave de su entidad. Los nombres del cliente o del salón no dependen del evento. El esquema se mantiene en tercera forma normal. Los valores de una tarifa contratada son datos históricos de la transacción; pueden ser distintos del precio actual del catálogo. El total y la tasa se almacenan porque P2 lo solicita, con triggers que controlan su cálculo.

## 3. Dinero y tarifas contratadas

El dinero usa `Numeric` en PostgreSQL y `Decimal` en los DTO. Las respuestas JSON representan los decimales como texto para evitar una conversión intermedia a punto flotante. El frontend solo convierte valores para dibujar gráficos; esa conversión no calcula lo que se cobra.

El precio del servicio se copia del catálogo al contratarlo. Modificar su cantidad conserva el precio original. Un cambio de catálogo no altera lo contratado. SQL directo tampoco puede cambiar `precio_congelado` en una línea existente.

Se añadió `precio_salon_congelado` al evento. P2 exige congelar expresamente los servicios; conservar también la tarifa del salón evita que una cotización histórica cambie cuando se modifica el catálogo. Al cambiar de salón, se toma la tarifa del nuevo salón. Al cambiar solo el horario, se conserva la tarifa contratada.

No se añadió una columna de subtotal al servicio contratado: cantidad y precio bastan para obtenerlo. El trigger calcula el total como horas exactas por tarifa del salón más la suma de cantidad por precio de cada servicio.

## 4. Duración y cantidades

Las fechas de inicio y fin contienen día y hora. Un evento de 23:00 a 01:00 del día siguiente dura dos horas y es válido. La regla `fin > inicio` evita duraciones negativas.

El alquiler usa la duración exacta. Una hora y media en Heliconia cuesta 480.000 COP. El redondeo hacia arriba se aplica a la cantidad por defecto de servicios por hora: una duración de 1,5 horas contrata dos unidades horarias. Un servicio por persona toma el aforo. Por unidad toma uno. Una cantidad enviada explícitamente debe ser positiva.

La cantidad se fija al contratar. Reprogramar recalcula el alquiler y conserva las cantidades ya contratadas. Si el cliente necesita más refrigerios o más horas de sonido, se modifica la línea. Esta elección evita sobrescribir cantidades que el cliente ajustó expresamente.

## 5. Una hora entre eventos

P2 exige una hora libre entre dos eventos del mismo salón. Se cuenta una sola vez. Si uno termina a las 12:00, el siguiente puede iniciar a las 13:00; a las 12:59 debe bloquearse. Las referencias que amplían ambos eventos una hora antes y otra después terminan exigiendo dos horas.

A1 valida capacidad, salón activo, cruces y reducción de aforo. Incluye los eventos finalizados al consultar el historial y excluye únicamente los cancelados. Si hay conflicto, el mensaje indica id, nombre, inicio y fin del evento existente. A5 utiliza la misma condición para ofrecer salones libres.

## 6. Cupos y concurrencia

Una inscripción bloquea primero el evento padre y después cuenta inscritos. Sin ese bloqueo, dos peticiones simultáneas podrían ver el mismo último cupo y aceptarse ambas. Los cambios de aforo y servicios también se coordinan con el evento. La disponibilidad bloquea el salón al validar una reserva.

Además, no se permite reducir el aforo por debajo del número ya inscrito. La unicidad de evento y asistente impide inscribir dos veces a la misma persona. Los salones y las personas permanecen identificados por llaves, aunque compartan nombres.

## 7. Check-in y hora de Bogotá

La ventana de llegada incluye sus límites: una hora antes del inicio y la hora de fin. El control se ejecuta en INSERT y UPDATE, por lo que también revisa una inscripción creada con llegada incluida desde SQL. Una llegada registrada no puede borrarse ni reemplazarse. Los eventos cerrados no admiten cambios de asistencia que alteren la tasa ya guardada.

Las fechas sin zona horaria se interpretan en Bogotá. Si la API recibe una fecha con zona, la convierte a Bogotá antes de guardar. PostgreSQL trabaja con esa misma zona. Se conserva `timestamp` sin zona en las columnas originales porque el centro opera en una sola sede; el contrato de la API deja explícita esta interpretación.

## 8. Estados y cierre

Todo evento nace Cotizado, incluso al insertar con SQL. Puede pasar a Confirmado o Cancelado. Confirmado puede pasar a Finalizado o Cancelado. Los estados definitivos no vuelven a abrirse. Aunque A1 se ejecuta al cambiar estado, un intento de reactivar un Cancelado se bloquea por A4.

Para finalizar, la hora de fin debe haber pasado. La tasa se calcula como llegadas dividido entre inscritos por cien, con dos decimales. Sin inscritos, se guarda NULL porque no existe denominador. Con inscritos y ninguna llegada, se guarda 0,00. Los eventos cerrados se conservan para reportes y auditoría.

## 9. Auditoría del operador

La cuenta de PostgreSQL es compartida por la API, así que `current_user` identificaría la conexión y no al operador. `X-Usuario` se pasa con `set_config` dentro de la transacción. El trigger lee ese valor con `current_setting` y guarda una fila por estado, salón, inicio o fin que cambió.

Se usan los campos que ya permite el modelo: `estado`, `salon_id`, `inicio` y `fin`. Si el cambio proviene de SQL sin usuario de aplicación, se registra `sistema`. El encabezado no verifica una identidad: para esta entrega aporta trazabilidad, no autenticación.

## 10. Reportes en SQL

B1 baja por la jerarquía con una CTE recursiva. Conserva la ruta de ids para contar subordinados directos e indirectos y consultar una rama. B2 sube desde el empleado hasta la dirección y entrega solo los jefes, desde el inmediato. Las consultas llevan ids visitados para detener ciclos; un trigger también impide crear ciclos nuevos en staff.

B3 incluye eventos Cotizado, Confirmado y Finalizado. Un LEFT JOIN mantiene los clientes sin eventos o con todos sus eventos cancelados. `RANK` calcula la posición, `SUM OVER ()` el total y otra ventana el acumulado. El cliente que cruza el 80 % pertenece al segmento A; los siguientes quedan en el resto. Ante empates, el id estabiliza el orden del acumulado.

B4 separa los salones con `PARTITION BY`. `ROW_NUMBER` numera eventos, `LAG` obtiene el anterior y su fin, y `SUM` acumula horas. Los días libres son el tiempo transcurrido dividido entre 24 horas, con dos decimales. El primer evento no tiene anterior y su tiempo libre queda vacío.

La API consulta vistas y funciones con parámetros. No reconstruye los reportes con el ORM.

## 11. Errores y recuperación

Pydantic rechaza campos inválidos con 422. Una regla de negocio lanzada por PostgreSQL responde 409 con su mensaje principal. Los duplicados responden 409, las restricciones de valores 422 y un recurso inexistente consultado por la API 404. Los fallos inesperados responden 500 sin exponer una traza.

Cuando falla un commit, la sesión revierte la transacción. Un evento bloqueado no queda guardado parcialmente. Después de un commit correcto, `refresh` recupera el total o la tasa que calculó el trigger. Streamlit muestra el mensaje de la API y continúa; si no logra conectarse, muestra un aviso.

## 12. Carga, pruebas y alcance

Los scripts de funciones y triggers se pueden reaplicar. Las entidades crean las tablas antes de instalar las reglas. Los datos de demostración se cargan después de los triggers y recorren estados, servicios, inscripciones y llegadas antes del cierre. El cargador rechaza una base con clientes para evitar duplicados y no hace TRUNCATE.

La prueba se realiza en otra base. Las pruebas de integración revisan la API, SQL directo, límites horarios, estados definitivos, dinero y solicitudes concurrentes. Las evidencias guardan las peticiones y respuestas observadas; los resultados de B1–B4 se comparan con cuentas independientes sobre los datos iniciales.

La interfaz incluida permite ejecutar y demostrar el backend. Para la entrega 2 conviene revisar su presentación visual y probar con el grupo todos los recorridos de usuario. P2 menciona una funcionalidad 5.3 que no aparece en el documento recibido y pide pantallas de Streamlit en la entrega del backend. Se incluye Streamlit para cubrir esas pantallas; el requisito 5.3 queda por aclarar con el profesor.

## Preparar la sustentación

Shalem, Dayro, Juan y Jesús deben poder recorrer una petición desde Streamlit hasta el trigger, explicar por qué se devuelve 409 y comprobar que una inserción directa en pgAdmin también se bloquea. Para practicar, calculen primero una cotización de 1,5 horas, la tasa de 3 llegadas entre 4 inscritos y los subordinados de un gerente. Después comparen esas cuentas con la plataforma.

Las fuentes técnicas del proyecto son P2, el material local reutilizado y las documentaciones de [PostgreSQL](https://www.postgresql.org/docs/17/), [SQLAlchemy](https://docs.sqlalchemy.org/en/20/), [FastAPI](https://fastapi.tiangolo.com/) y [Pydantic](https://docs.pydantic.dev/latest/).
