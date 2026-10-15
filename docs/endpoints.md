# Endpoints y ejemplos

Los ejemplos siguientes se registraron con la API encendida en una base de demostración. Los ids y las fechas cambian si se carga o ejecuta de nuevo. Antes de probar una mutación, consulta los catálogos e ids de tu propia base.

Base habitual: `http://localhost:8000`. Documentación interactiva: `/docs`. Todas las consultas SQL que reciben valores usan parámetros. Encabezado de auditoría: `X-Usuario: grupo_shalem_dayro_juan_jesus`.

Las colecciones grandes se muestran con su primer elemento para mantener legible este manual; la respuesta completa está en `ejemplos_endpoints.json`. Dinero y porcentajes usan cadenas decimales.

| Método | Ruta | Operación |
|---|---|---|
| POST | `/clientes` | Crear Cliente |
| GET | `/clientes` | Listar Clientes |
| GET | `/clientes/{cliente_id}/eventos` | Eventos Cliente |
| GET | `/clientes/{cliente_id}` | Obtener Cliente |
| GET | `/salones` | Listar Salones |
| GET | `/salones/disponibles` | Salones Disponibles |
| GET | `/salones/{salon_id}` | Obtener Salon |
| PATCH | `/salones/{salon_id}/activo` | Cambiar Estado Salon |
| GET | `/servicios` | Listar Servicios |
| GET | `/servicios/{servicio_id}` | Obtener Servicio |
| GET | `/staff` | Listar Staff |
| POST | `/staff` | Crear Staff |
| GET | `/staff/{staff_id}` | Obtener Staff |
| POST | `/asistentes` | Crear Asistente |
| GET | `/asistentes` | Listar Asistentes |
| GET | `/asistentes/{asistente_id}` | Obtener Asistente |
| POST | `/eventos` | Crear |
| GET | `/eventos` | Listar |
| GET | `/eventos/{evento_id}` | Detalle |
| PATCH | `/eventos/{evento_id}` | Reprogramar |
| PATCH | `/eventos/{evento_id}/estado` | Cambiar Estado |
| POST | `/eventos/{evento_id}/servicios` | Contratar |
| GET | `/eventos/{evento_id}/servicios` | Listar Servicios |
| PUT | `/eventos/{evento_id}/servicios/{linea_id}` | Modificar Servicio |
| DELETE | `/eventos/{evento_id}/servicios/{linea_id}` | Quitar Servicio |
| GET | `/eventos/{evento_id}/cotizacion` | Cotizacion |
| GET | `/eventos/{evento_id}/auditoria` | Auditoria |
| POST | `/eventos/{evento_id}/inscripciones` | Inscribir |
| GET | `/eventos/{evento_id}/inscripciones` | Listar Inscripciones |
| POST | `/eventos/{evento_id}/checkin` | Registrar Checkin |
| GET | `/reportes/organigrama` | Organigrama |
| GET | `/reportes/escalamiento/{staff_id}` | Escalamiento |
| GET | `/reportes/ranking-clientes` | Ranking |
| GET | `/reportes/ocupacion-salones` | Ocupacion |
| GET | `/` | Inicio |

## POST /clientes



Petición:

```http
POST /clientes
X-Usuario: grupo_shalem_dayro_juan_jesus
```

Cuerpo JSON:

```json
{
  "documento": "demo0eaf9461",
  "tipo_documento": "NIT",
  "nombre_razon_social": "Cliente de documentación",
  "correo": "documentacion@example.com",
  "telefono": "3001234567"
}
```

Respuesta HTTP 201:

```json
{
  "documento": "demo0eaf9461",
  "tipo_documento": "NIT",
  "nombre_razon_social": "Cliente de documentación",
  "correo": "documentacion@example.com",
  "telefono": "3001234567",
  "id": 9,
  "fecha_registro": "2026-10-06T20:50:06.715016"
}
```

## GET /clientes



Petición:

```http
GET /clientes
X-Usuario: grupo_shalem_dayro_juan_jesus
```

Respuesta HTTP 200:

```json
[
  {
    "documento": "900111222",
    "tipo_documento": "NIT",
    "nombre_razon_social": "Tech Corp S.A.",
    "correo": "contacto@techcorp.com",
    "telefono": "3001111111",
    "id": 1,
    "fecha_registro": "2026-01-15T00:00:00"
  }
]
```

## GET /clientes/{cliente_id}/eventos



Petición:

```http
GET /clientes/1/eventos
X-Usuario: grupo_shalem_dayro_juan_jesus
```

Respuesta HTTP 200:

```json
[
  {
    "id": 20,
    "cliente_id": 1,
    "salon_id": 2,
    "coordinador_id": 1,
    "nombre": "Prueba A4 permitido 95792b",
    "tipo": "Seminario",
    "aforo_esperado": 50,
    "inicio": "2026-06-27T09:00:00",
    "fin": "2026-06-27T11:00:00",
    "estado": "Finalizado",
    "valor_total": "640000.00",
    "precio_salon_congelado": "320000.00",
    "tasa_asistencia": "75.00"
  }
]
```

## GET /clientes/{cliente_id}



Petición:

```http
GET /clientes/1
X-Usuario: grupo_shalem_dayro_juan_jesus
```

Respuesta HTTP 200:

```json
{
  "documento": "900111222",
  "tipo_documento": "NIT",
  "nombre_razon_social": "Tech Corp S.A.",
  "correo": "contacto@techcorp.com",
  "telefono": "3001111111",
  "id": 1,
  "fecha_registro": "2026-01-15T00:00:00"
}
```

## GET /salones



Petición:

```http
GET /salones
X-Usuario: grupo_shalem_dayro_juan_jesus
```

Respuesta HTTP 200:

```json
[
  {
    "id": 1,
    "nombre": "Salón Orquídea",
    "tamano": "Pequeño",
    "capacidad_maxima": 40,
    "precio_hora": "250000.00",
    "activo": true
  }
]
```

## GET /salones/disponibles

A5: salones habilitados, con capacidad y libres en la franja,
ordenados de menor a mayor con su costo estimado.

Petición:

```http
GET /salones/disponibles
X-Usuario: grupo_shalem_dayro_juan_jesus
```

Parámetros de consulta:

```json
{
  "inicio": "2027-01-20T09:00:00",
  "fin": "2027-01-20T11:00:00",
  "aforo": 50
}
```

Respuesta HTTP 200:

```json
[
  {
    "salon_id": 3,
    "nombre": "Salón Guayacán",
    "tamano": "Mediano",
    "capacidad": 150,
    "precio_hora": "650000.00",
    "costo_estimado": "1300000.00"
  }
]
```

## GET /salones/{salon_id}



Petición:

```http
GET /salones/1
X-Usuario: grupo_shalem_dayro_juan_jesus
```

Respuesta HTTP 200:

```json
{
  "id": 1,
  "nombre": "Salón Orquídea",
  "tamano": "Pequeño",
  "capacidad_maxima": 40,
  "precio_hora": "250000.00",
  "activo": true
}
```

## PATCH /salones/{salon_id}/activo



Petición:

```http
PATCH /salones/1/activo
X-Usuario: grupo_shalem_dayro_juan_jesus
```

Parámetros de consulta:

```json
{
  "activo": "true"
}
```

Respuesta HTTP 200:

```json
{
  "id": 1,
  "nombre": "Salón Orquídea",
  "tamano": "Pequeño",
  "capacidad_maxima": 40,
  "precio_hora": "250000.00",
  "activo": true
}
```

## GET /servicios



Petición:

```http
GET /servicios
X-Usuario: grupo_shalem_dayro_juan_jesus
```

Respuesta HTTP 200:

```json
[
  {
    "id": 8,
    "nombre": "Multimedia (proyector + pantalla)",
    "categoria": "Audiovisuales",
    "unidad_cobro": "Por hora",
    "precio_unitario": "90000.00"
  }
]
```

## GET /servicios/{servicio_id}



Petición:

```http
GET /servicios/2
X-Usuario: grupo_shalem_dayro_juan_jesus
```

Respuesta HTTP 200:

```json
{
  "id": 2,
  "nombre": "Estación de café",
  "categoria": "Bebidas",
  "unidad_cobro": "Por persona",
  "precio_unitario": "6500.00"
}
```

## GET /staff



Petición:

```http
GET /staff
X-Usuario: grupo_shalem_dayro_juan_jesus
```

Respuesta HTTP 200:

```json
[
  {
    "nombre": "Elena Suárez",
    "cargo": "Directora General",
    "area": "Dirección",
    "correo": "esuarez@nexo.com",
    "fecha_ingreso": "2020-01-15",
    "jefe_id": null,
    "id": 1
  }
]
```

## POST /staff



Petición:

```http
POST /staff
X-Usuario: grupo_shalem_dayro_juan_jesus
```

Cuerpo JSON:

```json
{
  "nombre": "Apoyo de documentación",
  "cargo": "Auxiliar",
  "area": "Logística",
  "correo": "apoyo0eaf9461@example.com",
  "fecha_ingreso": "2026-10-01",
  "jefe_id": 4
}
```

Respuesta HTTP 201:

```json
{
  "nombre": "Apoyo de documentación",
  "cargo": "Auxiliar",
  "area": "Logística",
  "correo": "apoyo0eaf9461@example.com",
  "fecha_ingreso": "2026-10-01",
  "jefe_id": 4,
  "id": 16
}
```

## GET /staff/{staff_id}



Petición:

```http
GET /staff/12
X-Usuario: grupo_shalem_dayro_juan_jesus
```

Respuesta HTTP 200:

```json
{
  "nombre": "Diego Paz",
  "cargo": "Técnico de Sonido",
  "area": "Audiovisuales",
  "correo": "dpaz@nexo.com",
  "fecha_ingreso": "2022-09-10",
  "jefe_id": 6,
  "id": 12
}
```

## POST /asistentes



Petición:

```http
POST /asistentes
X-Usuario: grupo_shalem_dayro_juan_jesus
```

Cuerpo JSON:

```json
{
  "documento": "doc0eaf9461",
  "nombre": "Asistente de documentación",
  "correo": "asistente@example.com",
  "empresa": null
}
```

Respuesta HTTP 201:

```json
{
  "documento": "doc0eaf9461",
  "nombre": "Asistente de documentación",
  "correo": "asistente@example.com",
  "empresa": null,
  "id": 61
}
```

## GET /asistentes



Petición:

```http
GET /asistentes
X-Usuario: grupo_shalem_dayro_juan_jesus
```

Respuesta HTTP 200:

```json
[
  {
    "documento": "100000001",
    "nombre": "Asistente 1",
    "correo": "asistente1@correo.com",
    "empresa": "Innova Market",
    "id": 1
  }
]
```

## GET /asistentes/{asistente_id}



Petición:

```http
GET /asistentes/61
X-Usuario: grupo_shalem_dayro_juan_jesus
```

Respuesta HTTP 200:

```json
{
  "documento": "doc0eaf9461",
  "nombre": "Asistente de documentación",
  "correo": "asistente@example.com",
  "empresa": null,
  "id": 61
}
```

## POST /eventos



Petición:

```http
POST /eventos
X-Usuario: grupo_shalem_dayro_juan_jesus
```

Cuerpo JSON:

```json
{
  "cliente_id": 1,
  "salon_id": 2,
  "coordinador_id": 1,
  "nombre": "Prueba A1 permitido 2fd41e",
  "tipo": "Seminario",
  "aforo_esperado": 50,
  "inicio": "2027-01-20T09:00:00",
  "fin": "2027-01-20T11:00:00"
}
```

Respuesta HTTP 201:

```json
{
  "id": 22,
  "cliente_id": 1,
  "salon_id": 2,
  "coordinador_id": 1,
  "nombre": "Prueba A1 permitido 2fd41e",
  "tipo": "Seminario",
  "aforo_esperado": 50,
  "inicio": "2027-01-20T09:00:00",
  "fin": "2027-01-20T11:00:00",
  "estado": "Cotizado",
  "valor_total": "640000.00",
  "precio_salon_congelado": "320000.00",
  "tasa_asistencia": null
}
```

## GET /eventos



Petición:

```http
GET /eventos
X-Usuario: grupo_shalem_dayro_juan_jesus
```

Respuesta HTTP 200:

```json
[
  {
    "id": 20,
    "cliente_id": 1,
    "salon_id": 2,
    "coordinador_id": 1,
    "nombre": "Prueba A4 permitido 95792b",
    "tipo": "Seminario",
    "aforo_esperado": 50,
    "inicio": "2026-06-27T09:00:00",
    "fin": "2026-06-27T11:00:00",
    "estado": "Finalizado",
    "valor_total": "640000.00",
    "precio_salon_congelado": "320000.00",
    "tasa_asistencia": "75.00"
  }
]
```

## GET /eventos/{evento_id}



Petición:

```http
GET /eventos/22
X-Usuario: grupo_shalem_dayro_juan_jesus
```

Respuesta HTTP 200:

```json
{
  "id": 22,
  "cliente_id": 1,
  "salon_id": 2,
  "coordinador_id": 1,
  "nombre": "Prueba A1 permitido 2fd41e",
  "tipo": "Seminario",
  "aforo_esperado": 40,
  "inicio": "2027-01-20T09:00:00",
  "fin": "2027-01-20T11:30:00",
  "estado": "Confirmado",
  "valor_total": "800000.00",
  "precio_salon_congelado": "320000.00",
  "tasa_asistencia": null,
  "servicios": [],
  "inscritos": 1,
  "llegaron": 1
}
```

## PATCH /eventos/{evento_id}



Petición:

```http
PATCH /eventos/22
X-Usuario: grupo_shalem_dayro_juan_jesus
```

Cuerpo JSON:

```json
{
  "fin": "2027-01-20T11:30:00",
  "aforo_esperado": 40
}
```

Respuesta HTTP 200:

```json
{
  "id": 22,
  "cliente_id": 1,
  "salon_id": 2,
  "coordinador_id": 1,
  "nombre": "Prueba A1 permitido 2fd41e",
  "tipo": "Seminario",
  "aforo_esperado": 40,
  "inicio": "2027-01-20T09:00:00",
  "fin": "2027-01-20T11:30:00",
  "estado": "Cotizado",
  "valor_total": "800000.00",
  "precio_salon_congelado": "320000.00",
  "tasa_asistencia": null
}
```

## PATCH /eventos/{evento_id}/estado



Petición:

```http
PATCH /eventos/22/estado
X-Usuario: grupo_shalem_dayro_juan_jesus
```

Cuerpo JSON:

```json
{
  "estado": "Confirmado"
}
```

Respuesta HTTP 200:

```json
{
  "id": 22,
  "cliente_id": 1,
  "salon_id": 2,
  "coordinador_id": 1,
  "nombre": "Prueba A1 permitido 2fd41e",
  "tipo": "Seminario",
  "aforo_esperado": 40,
  "inicio": "2027-01-20T09:00:00",
  "fin": "2027-01-20T11:30:00",
  "estado": "Confirmado",
  "valor_total": "800000.00",
  "precio_salon_congelado": "320000.00",
  "tasa_asistencia": null
}
```

## POST /eventos/{evento_id}/servicios



Petición:

```http
POST /eventos/22/servicios
X-Usuario: grupo_shalem_dayro_juan_jesus
```

Cuerpo JSON:

```json
{
  "servicio_id": 2
}
```

Respuesta HTTP 201:

```json
{
  "id": 39,
  "evento_id": 22,
  "servicio_id": 2,
  "cantidad": "50.00",
  "precio_congelado": "6500.00"
}
```

## GET /eventos/{evento_id}/servicios



Petición:

```http
GET /eventos/22/servicios
X-Usuario: grupo_shalem_dayro_juan_jesus
```

Respuesta HTTP 200:

```json
[
  {
    "id": 39,
    "evento_id": 22,
    "servicio_id": 2,
    "cantidad": "25.00",
    "precio_congelado": "6500.00"
  }
]
```

## PUT /eventos/{evento_id}/servicios/{linea_id}



Petición:

```http
PUT /eventos/22/servicios/39
X-Usuario: grupo_shalem_dayro_juan_jesus
```

Cuerpo JSON:

```json
{
  "cantidad": "25"
}
```

Respuesta HTTP 200:

```json
{
  "id": 39,
  "evento_id": 22,
  "servicio_id": 2,
  "cantidad": "25.00",
  "precio_congelado": "6500.00"
}
```

## DELETE /eventos/{evento_id}/servicios/{linea_id}



Petición:

```http
DELETE /eventos/22/servicios/39
X-Usuario: grupo_shalem_dayro_juan_jesus
```

Respuesta HTTP 204:

```json
(sin cuerpo)
```

## GET /eventos/{evento_id}/cotizacion



Petición:

```http
GET /eventos/22/cotizacion
X-Usuario: grupo_shalem_dayro_juan_jesus
```

Respuesta HTTP 200:

```json
{
  "evento_id": 22,
  "nombre": "Prueba A1 permitido 2fd41e",
  "estado": "Cotizado",
  "salon": "Salón Heliconia",
  "horas": "2.0000000000000000",
  "precio_hora": "320000.00",
  "costo_salon": "640000.00",
  "servicios": [
    {
      "id": 39,
      "servicio_id": 2,
      "nombre": "Estación de café",
      "unidad_cobro": "Por persona",
      "cantidad": "25.00",
      "precio_congelado": "6500.00",
      "subtotal": "162500.0000"
    }
  ],
  "subtotal_servicios": "162500.00",
  "total": "802500.00"
}
```

## GET /eventos/{evento_id}/auditoria



Petición:

```http
GET /eventos/22/auditoria
X-Usuario: grupo_shalem_dayro_juan_jesus
```

Respuesta HTTP 200:

```json
[
  {
    "id": 24,
    "evento_id": 22,
    "campo": "fin",
    "valor_anterior": "2027-01-20T11:00:00",
    "valor_nuevo": "2027-01-20T11:30:00",
    "usuario_app": "grupo_shalem_dayro_juan_jesus",
    "fecha": "2026-10-06T20:50:06.896027"
  }
]
```

## POST /eventos/{evento_id}/inscripciones



Petición:

```http
POST /eventos/22/inscripciones
X-Usuario: grupo_shalem_dayro_juan_jesus
```

Cuerpo JSON:

```json
{
  "asistente_id": 61
}
```

Respuesta HTTP 201:

```json
{
  "id": 278,
  "evento_id": 22,
  "asistente_id": 61,
  "fecha_inscripcion": "2026-10-06T20:50:06.819360",
  "hora_checkin": null
}
```

## GET /eventos/{evento_id}/inscripciones



Petición:

```http
GET /eventos/22/inscripciones
X-Usuario: grupo_shalem_dayro_juan_jesus
```

Respuesta HTTP 200:

```json
[
  {
    "id": 278,
    "evento_id": 22,
    "asistente_id": 61,
    "fecha_inscripcion": "2026-10-06T20:50:06.819360",
    "hora_checkin": "2027-01-20T09:00:00"
  }
]
```

## POST /eventos/{evento_id}/checkin

Registra la asistencia real de un asistente (por su documento).
Usa la hora indicada o el instante actual. A2 valida la ventana y el
'una sola vez'.

Petición:

```http
POST /eventos/22/checkin
X-Usuario: grupo_shalem_dayro_juan_jesus
```

Cuerpo JSON:

```json
{
  "documento": "doc0eaf9461",
  "hora_checkin": "2027-01-20T09:00:00"
}
```

Respuesta HTTP 200:

```json
{
  "id": 278,
  "evento_id": 22,
  "asistente_id": 61,
  "fecha_inscripcion": "2026-10-06T20:50:06.819360",
  "hora_checkin": "2027-01-20T09:00:00"
}
```

## GET /reportes/organigrama

Lista toda la organización o los subordinados de un empleado.

Petición:

```http
GET /reportes/organigrama
X-Usuario: grupo_shalem_dayro_juan_jesus
```

Respuesta HTTP 200:

```json
[
  {
    "id": 1,
    "nombre": "Elena Suárez",
    "cargo": "Directora General",
    "area": "Dirección",
    "jefe_id": null,
    "nivel": 1,
    "ruta_mando": "Elena Suárez",
    "ruta_ids": [
      1
    ],
    "a_cargo_directos": 2,
    "total_a_cargo": 15
  }
]
```

## GET /reportes/escalamiento/{staff_id}

Devuelve los jefes desde el inmediato hasta la dirección.

Petición:

```http
GET /reportes/escalamiento/12
X-Usuario: grupo_shalem_dayro_juan_jesus
```

Respuesta HTTP 200:

```json
[
  {
    "orden": 1,
    "id": 6,
    "nombre": "Luis Toro",
    "cargo": "Jefe Audiovisual",
    "area": "Audiovisuales"
  }
]
```

## GET /reportes/ranking-clientes

Facturación, ranking y Pareto de eventos no cancelados.

Petición:

```http
GET /reportes/ranking-clientes
X-Usuario: grupo_shalem_dayro_juan_jesus
```

Respuesta HTTP 200:

```json
[
  {
    "cliente_id": 2,
    "nombre": "Innova Market",
    "eventos_no_cancelados": 2,
    "facturacion": "106410000.00",
    "ranking": 1,
    "participacion_pct": "59.46",
    "acumulado_pct": "59.46",
    "segmento_pareto": "A (80%)"
  }
]
```

## GET /reportes/ocupacion-salones

Eventos por salón, días libres y horas reservadas acumuladas.

Petición:

```http
GET /reportes/ocupacion-salones
X-Usuario: grupo_shalem_dayro_juan_jesus
```

Respuesta HTTP 200:

```json
[
  {
    "salon_id": 1,
    "salon": "Salón Orquídea",
    "evento_id": 3,
    "evento": "Club de Lectura Páramo",
    "estado": "Finalizado",
    "inicio": "2026-09-20T15:00:00",
    "fin": "2026-09-21T01:00:00",
    "num_evento_salon": 1,
    "evento_anterior_id": null,
    "evento_anterior": null,
    "dias_libres": null,
    "horas_reservadas": "10.00",
    "horas_acumuladas": "10.00"
  }
]
```

## GET /



Petición:

```http
GET /
X-Usuario: grupo_shalem_dayro_juan_jesus
```

Respuesta HTTP 200:

```json
{
  "servicio": "NexoEventos",
  "docs": "/docs"
}
```

## Filtros y errores

`GET /clientes?q=Tech` y `GET /asistentes?q=100000001` buscan por nombre o documento. `GET /eventos?estado=Confirmado&cliente_id=1` combina filtros. B1 admite `staff_id` opcional. A5 necesita `inicio`, `fin` y `aforo` positivo.

201: creación; 200: consulta o modificación; 204: servicio eliminado; 404: recurso inexistente; 409: regla de PostgreSQL, cupo o duplicado; 422: campos inválidos. Los ejemplos permitidos y bloqueados se documentan en `reporte_evidencias.md`.
