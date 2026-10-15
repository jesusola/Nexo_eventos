# Diccionario de datos

Origen: entidades de `app/models.py`. Dinero en COP; los campos NUMERIC son exactos. Las fechas con hora se almacenan en hora local de Bogotá, sin zona horaria. Los ids son enteros generados por PostgreSQL.

## asistentes

| Campo | Tipo SQL | Acepta NULL | Claves y valor inicial |
|---|---|---|---|
| `id` | `INTEGER` | No | PK, autoincremento |
| `documento` | `VARCHAR(20)` | No | UNIQUE |
| `nombre` | `VARCHAR(150)` | No | — |
| `correo` | `VARCHAR(150)` | No | — |
| `empresa` | `VARCHAR(150)` | Sí | — |

Restricciones:

- UNIQUE: `documento`.

## clientes

| Campo | Tipo SQL | Acepta NULL | Claves y valor inicial |
|---|---|---|---|
| `id` | `INTEGER` | No | PK, autoincremento |
| `documento` | `VARCHAR(20)` | No | UNIQUE |
| `tipo_documento` | `VARCHAR(10)` | No | — |
| `nombre_razon_social` | `VARCHAR(150)` | No | — |
| `correo` | `VARCHAR(150)` | No | — |
| `telefono` | `VARCHAR(20)` | No | — |
| `fecha_registro` | `TIMESTAMP WITHOUT TIME ZONE` | No | DEFAULT CURRENT_TIMESTAMP |

Restricciones:

- UNIQUE: `documento`.
- `check_tipo_documento`: `tipo_documento IN ('NIT', 'Cedula')`.

## salones

| Campo | Tipo SQL | Acepta NULL | Claves y valor inicial |
|---|---|---|---|
| `id` | `INTEGER` | No | PK, autoincremento |
| `nombre` | `VARCHAR(100)` | No | UNIQUE |
| `tamano` | `VARCHAR(10)` | No | — |
| `capacidad_maxima` | `INTEGER` | No | — |
| `precio_hora` | `NUMERIC(12, 2)` | No | — |
| `activo` | `BOOLEAN` | No | DEFAULT TRUE |

Restricciones:

- UNIQUE: `nombre`.
- `check_capacidad_maxima`: `capacidad_maxima > 0`.
- `check_precio_hora`: `precio_hora > 0`.
- `check_tamano_salon`: `tamano IN ('Pequeño', 'Mediano', 'Grande')`.

## servicios

| Campo | Tipo SQL | Acepta NULL | Claves y valor inicial |
|---|---|---|---|
| `id` | `INTEGER` | No | PK, autoincremento |
| `nombre` | `VARCHAR(150)` | No | UNIQUE |
| `categoria` | `VARCHAR(30)` | No | — |
| `unidad_cobro` | `VARCHAR(15)` | No | — |
| `precio_unitario` | `NUMERIC(12, 2)` | No | — |

Restricciones:

- UNIQUE: `nombre`.
- `check_categoria_servicio`: `categoria IN ('Bebidas', 'Refrigerios', 'Audiovisuales')`.
- `check_precio_unitario`: `precio_unitario > 0`.
- `check_unidad_cobro`: `unidad_cobro IN ('Por persona', 'Por hora', 'Por unidad')`.

## staff

| Campo | Tipo SQL | Acepta NULL | Claves y valor inicial |
|---|---|---|---|
| `id` | `INTEGER` | No | PK, autoincremento |
| `correo` | `VARCHAR(150)` | No | UNIQUE |
| `jefe_id` | `INTEGER` | Sí | FK → staff.id |
| `nombre` | `VARCHAR(150)` | No | — |
| `cargo` | `VARCHAR(100)` | No | — |
| `area` | `VARCHAR(30)` | No | — |
| `fecha_ingreso` | `DATE` | No | — |

Restricciones:

- UNIQUE: `correo`.
- `check_area_staff`: `area IN ('Dirección', 'Operaciones', 'Comercial', 'Logística', 'Alimentos y Bebidas', 'Audiovisuales')`.
- `check_jefe_diferente`: `jefe_id <> id`.

## eventos

| Campo | Tipo SQL | Acepta NULL | Claves y valor inicial |
|---|---|---|---|
| `id` | `INTEGER` | No | PK, autoincremento |
| `cliente_id` | `INTEGER` | No | FK → clientes.id |
| `salon_id` | `INTEGER` | No | FK → salones.id |
| `coordinador_id` | `INTEGER` | No | FK → staff.id |
| `nombre` | `VARCHAR(150)` | No | — |
| `tipo` | `VARCHAR(30)` | No | — |
| `aforo_esperado` | `INTEGER` | No | — |
| `inicio` | `TIMESTAMP WITHOUT TIME ZONE` | No | — |
| `fin` | `TIMESTAMP WITHOUT TIME ZONE` | No | — |
| `estado` | `VARCHAR(15)` | No | DEFAULT 'Cotizado' |
| `valor_total` | `NUMERIC(14, 2)` | No | DEFAULT 0 |
| `precio_salon_congelado` | `NUMERIC(12, 2)` | No | Trigger A3 copia la tarifa del salón |
| `tasa_asistencia` | `NUMERIC(5, 2)` | Sí | NULL sin inscritos; porcentaje al finalizar |

Restricciones:

- `check_aforo_esperado`: `aforo_esperado > 0`.
- `check_estado_evento`: `estado IN ('Cotizado', 'Confirmado', 'Finalizado', 'Cancelado')`.
- `check_fechas_evento`: `fin > inicio`.
- `check_tarifa_salon`: `precio_salon_congelado > 0`.
- `check_tasa_asistencia`: `tasa_asistencia IS NULL OR (tasa_asistencia >= 0 AND tasa_asistencia <= 100)`.
- `check_tipo_evento`: `tipo IN ('Congreso', 'Conferencia', 'Feria', 'Seminario', 'Corporativo', 'Social')`.
- `check_valor_total`: `valor_total >= 0`.

## auditoria

| Campo | Tipo SQL | Acepta NULL | Claves y valor inicial |
|---|---|---|---|
| `id` | `INTEGER` | No | PK, autoincremento |
| `evento_id` | `INTEGER` | No | FK → eventos.id |
| `campo` | `VARCHAR(30)` | No | — |
| `valor_anterior` | `TEXT` | Sí | — |
| `valor_nuevo` | `TEXT` | Sí | — |
| `fecha` | `TIMESTAMP WITHOUT TIME ZONE` | No | DEFAULT CURRENT_TIMESTAMP |
| `usuario_app` | `VARCHAR(150)` | No | — |

Restricciones:

- `check_campo_auditoria`: `campo IN ('estado', 'salon_id', 'inicio', 'fin')`.

## inscripciones

| Campo | Tipo SQL | Acepta NULL | Claves y valor inicial |
|---|---|---|---|
| `id` | `INTEGER` | No | PK, autoincremento |
| `evento_id` | `INTEGER` | No | FK → eventos.id |
| `asistente_id` | `INTEGER` | No | FK → asistentes.id |
| `fecha_inscripcion` | `TIMESTAMP WITHOUT TIME ZONE` | No | DEFAULT CURRENT_TIMESTAMP |
| `hora_checkin` | `TIMESTAMP WITHOUT TIME ZONE` | Sí | NULL mientras no llegue; A2 valida ventana y unicidad |

Restricciones:

- UNIQUE: `evento_id`, `asistente_id`.

## servicios_evento

| Campo | Tipo SQL | Acepta NULL | Claves y valor inicial |
|---|---|---|---|
| `id` | `INTEGER` | No | PK, autoincremento |
| `evento_id` | `INTEGER` | No | FK → eventos.id |
| `servicio_id` | `INTEGER` | No | FK → servicios.id |
| `cantidad` | `NUMERIC(10, 2)` | No | Trigger A3 asigna aforo, techo de horas o 1 si se omite |
| `precio_congelado` | `NUMERIC(12, 2)` | No | Trigger A3 copia la tarifa del servicio |

Restricciones:

- `check_cantidad_servicio`: `cantidad > 0`.
- `check_precio_congelado`: `precio_congelado > 0`.
- UNIQUE: `evento_id`, `servicio_id`.

## Reglas entre filas

| Regla | Validación en PostgreSQL |
|---|---|
| A1 | Salón activo, capacidad, una hora entre eventos no cancelados y aforo no menor que inscritos |
| A2 | Evento abierto, cupo, inscripción única, llegada en ventana y una sola llegada |
| A3 | Total automático; precio y cantidad del servicio; bloqueo de líneas de eventos cerrados |
| A4 | Inicio Cotizado, transiciones, fecha de cierre, porcentaje y auditoría |
| Staff | Autorreferencia válida y ausencia de ciclos en la cadena de jefes |

Las llaves foráneas no tienen borrado en cascada. La API no publica rutas para borrar clientes, salones, asistentes ni eventos. El historial queda asociado a su evento.

En las respuestas JSON, los importes y porcentajes decimales se representan como cadenas para conservar precisión. Esto no cambia el tipo NUMERIC de PostgreSQL.
