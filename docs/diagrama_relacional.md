# Diagrama relacional

El modelo tiene nueve tablas. `servicios_evento` resuelve la relación muchos a muchos entre eventos y servicios; `inscripciones` hace lo mismo entre eventos y asistentes. El staff tiene una relación consigo mismo para identificar al jefe inmediato.

Versiones gráficas: [SVG](diagrama_relacional.svg) y [PNG](diagrama_relacional.png). En `diagrama_relacional.html` el gráfico se muestra directamente. El siguiente código conserva las cardinalidades en Mermaid.

```mermaid
erDiagram
    CLIENTES ||--o{ EVENTOS : contrata
    SALONES ||--o{ EVENTOS : recibe
    STAFF ||--o{ EVENTOS : coordina
    STAFF o|--o{ STAFF : dirige
    EVENTOS ||--o{ SERVICIOS_EVENTO : contrata
    SERVICIOS ||--o{ SERVICIOS_EVENTO : pertenece
    EVENTOS ||--o{ INSCRIPCIONES : admite
    ASISTENTES ||--o{ INSCRIPCIONES : realiza
    EVENTOS ||--o{ AUDITORIA : registra
    CLIENTES {
        integer id PK
        varchar documento UK
        varchar tipo_documento
        varchar nombre_razon_social
        varchar correo
        varchar telefono
        timestamp fecha_registro
    }
    SALONES {
        integer id PK
        varchar nombre UK
        varchar tamano
        integer capacidad_maxima
        numeric precio_hora
        boolean activo
    }
    STAFF {
        integer id PK
        integer jefe_id FK
        varchar nombre
        varchar cargo
        varchar area
        varchar correo UK
        date fecha_ingreso
    }
    EVENTOS {
        integer id PK
        integer cliente_id FK
        integer salon_id FK
        integer coordinador_id FK
        varchar nombre
        varchar tipo
        integer aforo_esperado
        timestamp inicio
        timestamp fin
        varchar estado
        numeric precio_salon_congelado
        numeric valor_total
        numeric tasa_asistencia
    }
    SERVICIOS {
        integer id PK
        varchar nombre UK
        varchar categoria
        varchar unidad_cobro
        numeric precio_unitario
    }
    SERVICIOS_EVENTO {
        integer id PK
        integer evento_id FK "UNIQUE con servicio_id"
        integer servicio_id FK
        numeric cantidad
        numeric precio_congelado
    }
    ASISTENTES {
        integer id PK
        varchar documento UK
        varchar nombre
        varchar correo
        varchar empresa
    }
    INSCRIPCIONES {
        integer id PK
        integer evento_id FK "UNIQUE con asistente_id"
        integer asistente_id FK
        timestamp fecha_inscripcion
        timestamp hora_checkin
    }
    AUDITORIA {
        integer id PK
        integer evento_id FK
        varchar campo
        text valor_anterior
        text valor_nuevo
        timestamp fecha
        varchar usuario_app
    }
```

`||` representa exactamente uno; `o{`, cero o muchos; `o|`, cero o uno. Un empleado puede no tener jefe, pero cada evento tiene cliente, salón y coordinador obligatorios.

Los datos de cliente, salón, asistente y servicio se almacenan una sola vez. Las tablas puente tienen claves únicas compuestas para impedir duplicar una contratación o una inscripción. El precio congelado es un dato de la contratación, distinto de la tarifa vigente del catálogo. `valor_total` y `tasa_asistencia` se conservan porque el enunciado pide almacenarlos y los triggers mantienen su consistencia.

Las longitudes, la precisión y las restricciones completas están en [diccionario_datos.md](diccionario_datos.md). El esquema generado corresponde a `app/models.py`.
