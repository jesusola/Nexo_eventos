BEGIN;

-- Usuario de aplicación para la auditoría (A4). Transaccional (true).
SELECT set_config('app.usuario', 'carga_inicial', true);


INSERT INTO salones (nombre, tamano, capacidad_maxima, precio_hora, activo) VALUES
('Salón Orquídea',     'Pequeño',   40,  250000,  true),
('Salón Heliconia',    'Pequeño',   60,  320000,  true),
('Salón Guayacán',     'Mediano',  150,  650000,  true),
('Salón Ceiba',        'Mediano',  200,  800000,  true),
('Gran Salón Cóndor',  'Grande',   600, 1800000,  true),
('Auditorio Principal','Grande',  1000, 2500000,  true);


INSERT INTO servicios (nombre, categoria, unidad_cobro, precio_unitario) VALUES
('Estación de agua',                        'Bebidas',       'Por persona',   3000),
('Estación de café',                        'Bebidas',       'Por persona',   6500),
('Refrigerio económico',                    'Refrigerios',   'Por persona',  12000),
('Refrigerio medio',                        'Refrigerios',   'Por persona',  22000),
('Refrigerio alto',                         'Refrigerios',   'Por persona',  38000),
('Sonido básico (2 micrófonos + parlantes)','Audiovisuales', 'Por hora',    120000),
('Sonido profesional (consola + 6 micrófonos)','Audiovisuales','Por hora',  350000),
('Multimedia (proyector + pantalla)',       'Audiovisuales', 'Por hora',     90000),
('Streaming y grabación',                   'Audiovisuales', 'Por hora',    450000) ON CONFLICT (nombre) DO NOTHING;


INSERT INTO clientes (documento, tipo_documento, nombre_razon_social, correo, telefono, fecha_registro) VALUES
('900111222', 'NIT', 'Tech Corp S.A.',     'contacto@techcorp.com',      '3001111111', '2026-01-15'),
('900333444', 'NIT', 'Innova Market',      'eventos@innovamarket.com',   '3002222222', '2026-01-20'),
('900555666', 'NIT', 'Fundación Educar',   'info@educar.org',            '3003333333', '2026-02-01'),
('900777888', 'NIT', 'Salud Vital EPS',    'logistica@saludvital.com',   '3004444444', '2026-02-10'),
('1010101010','Cedula',  'Carlos Mendoza',     'carlos.m@email.com',         '3101111111', '2026-02-18'),
('2020202020','Cedula',  'Lucía Fernández',    'lucia.f@email.com',          '3102222222', '2026-03-01'),
('3030303030','Cedula',  'Andrés Vargas',      'andres.v@email.com',         '3103333333', '2026-03-12'),
('4040404040','Cedula',  'Marta Rojas',        'marta.r@email.com',          '3104444444', '2026-03-20');


INSERT INTO staff (id, nombre, cargo, area, correo, fecha_ingreso, jefe_id) VALUES
(1, 'Elena Suárez', 'Directora General', 'Dirección', 'esuarez@nexo.com', '2020-01-15', NULL);

INSERT INTO staff (id, nombre, cargo, area, correo, fecha_ingreso, jefe_id) VALUES
(2, 'Roberto Gómez', 'Gerente de Operaciones', 'Operaciones', 'rgomez@nexo.com', '2020-02-01', 1),
(3, 'Diana Castro',  'Gerente Comercial',      'Comercial',   'dcastro@nexo.com', '2020-03-10', 1);

INSERT INTO staff (id, nombre, cargo, area, correo, fecha_ingreso, jefe_id) VALUES
(4, 'Mario Luna',  'Jefe de Logística',  'Logística',           'mluna@nexo.com', '2021-01-20', 2),
(5, 'Carmen Ruiz', 'Jefa de Alimentos',  'Alimentos y Bebidas', 'cruiz@nexo.com', '2021-05-11', 2),
(6, 'Luis Toro',   'Jefe Audiovisual',   'Audiovisuales',       'ltoro@nexo.com', '2022-08-01', 2),
(7, 'Ana Vega',    'Jefa de Ventas',     'Comercial',           'avega@nexo.com', '2021-11-15', 3);

INSERT INTO staff (id, nombre, cargo, area, correo, fecha_ingreso, jefe_id) VALUES
(8,  'Pedro Díaz',  'Auxiliar de Montaje',  'Logística',           'pdiaz@nexo.com', '2023-01-10', 4),
(9,  'Sara Peña',   'Auxiliar de Limpieza', 'Logística',           'spena@nexo.com', '2023-02-15', 4),
(10, 'Juan Melo',   'Cocinero',             'Alimentos y Bebidas', 'jmelo@nexo.com', '2022-03-20', 5),
(11, 'Rosa Gil',    'Mesera',               'Alimentos y Bebidas', 'rgil@nexo.com',  '2023-07-05', 5),
(12, 'Diego Paz',   'Técnico de Sonido',    'Audiovisuales',       'dpaz@nexo.com',  '2022-09-10', 6),
(13, 'Hugo Rey',    'Técnico de Video',     'Audiovisuales',       'hrey@nexo.com',  '2023-10-01', 6),
(14, 'Mía Cruz',    'Asesora Comercial',    'Comercial',           'mcruz@nexo.com', '2022-01-15', 7),
(15, 'Leo Ríos',    'Asesor Comercial',     'Comercial',           'lrios@nexo.com', '2023-05-20', 7);

DO $$
DECLARE seq text := pg_get_serial_sequence('staff','id');
BEGIN
    IF seq IS NOT NULL THEN
        PERFORM setval(seq, (SELECT MAX(id) FROM staff));
    END IF;
END $$;


INSERT INTO asistentes (documento, nombre, correo, empresa)
SELECT
    (100000000 + g)::text,
    'Asistente ' || g,
    'asistente' || g || '@correo.com',
    CASE g % 4
        WHEN 0 THEN 'Tech Corp S.A.'
        WHEN 1 THEN 'Innova Market'
        WHEN 2 THEN 'Independiente'
        ELSE        'Salud Vital EPS'
    END
FROM generate_series(1, 60) AS g;


INSERT INTO eventos (nombre, tipo, cliente_id, salon_id, coordinador_id, aforo_esperado, inicio, fin, estado)
SELECT v.nombre, v.tipo,
       (SELECT id FROM clientes WHERE documento = v.cli),
       (SELECT id FROM salones  WHERE nombre    = v.salon),
       (SELECT id FROM staff    WHERE correo     = v.coord),
       v.aforo, CURRENT_DATE + (v.inicio::date - DATE '2026-10-06') + v.inicio::time,
       CURRENT_DATE + (v.fin::date - DATE '2026-10-06') + v.fin::time, 'Cotizado'
FROM (VALUES
  ('Jornada Científica Solvida',   'Congreso',   '900111222', 'Salón Guayacán',      'avega@nexo.com',   120, '2026-09-08 08:00', '2026-09-08 12:00'),
  ('Capacitación en Ciberseguridad','Seminario',  '900777888', 'Salón Ceiba',         'rgomez@nexo.com',   60, '2026-09-15 09:00', '2026-09-15 14:00'),
  ('Club de Lectura Páramo',       'Social',     '2020202020','Salón Orquídea',      'mcruz@nexo.com',    20, '2026-09-20 15:00', '2026-09-21 01:00'),
  ('Feria de Innovación Nexo',     'Feria',      '900333444', 'Gran Salón Cóndor',   'dcastro@nexo.com', 300, '2026-09-25 09:00', '2026-09-25 18:00'),
  ('Simposio de Educación',        'Seminario',  '900555666', 'Salón Heliconia',     'lrios@nexo.com',    55, '2026-09-28 08:00', '2026-09-28 11:00'),
  ('Encuentro Interno Nexo',       'Corporativo','900111222', 'Salón Orquídea',      'esuarez@nexo.com',  30, '2026-09-30 14:00', '2026-09-30 16:00'),
  ('Gala Benéfica',                'Social',     '1010101010','Auditorio Principal', 'dcastro@nexo.com', 800, '2026-09-12 19:00', '2026-09-12 23:00'),
  ('Conferencia Pospuesta',        'Conferencia','3030303030','Salón Ceiba',         'avega@nexo.com',   100, '2026-11-05 09:00', '2026-11-05 12:00'),
  ('Congreso Nacional de Salud',   'Congreso',   '900777888', 'Gran Salón Cóndor',   'rgomez@nexo.com',  500, '2026-11-18 08:00', '2026-11-18 17:00'),
  ('Seminario Corporativo Q4',     'Seminario',  '900111222', 'Salón Ceiba',         'mcruz@nexo.com',   150, '2026-11-20 09:00', '2026-11-20 13:00'),
  ('Taller de Economía Circular',  'Seminario',     '2020202020','Salón Guayacán',      'lrios@nexo.com',    50, '2026-12-02 14:00', '2026-12-02 17:00'),
  ('Feria Navideña',               'Feria',      '900333444', 'Auditorio Principal', 'dcastro@nexo.com', 900, '2026-12-15 10:00', '2026-12-15 20:00')
) AS v(nombre, tipo, cli, salon, coord, aforo, inicio, fin);


INSERT INTO servicios_evento (evento_id, servicio_id, cantidad)
SELECT e.id, s.id,
       CASE s.unidad_cobro
           WHEN 'Por persona' THEN e.aforo_esperado
           WHEN 'Por hora'    THEN CEIL(EXTRACT(EPOCH FROM (e.fin - e.inicio)) / 3600)::int
           ELSE 1
       END
FROM eventos e
JOIN servicios s ON s.nombre = ANY (
    CASE e.nombre
        WHEN 'Jornada Científica Solvida'    THEN ARRAY['Estación de café','Sonido profesional (consola + 6 micrófonos)','Multimedia (proyector + pantalla)']
        WHEN 'Capacitación en Ciberseguridad'THEN ARRAY['Estación de agua','Refrigerio medio','Sonido básico (2 micrófonos + parlantes)','Streaming y grabación']
        WHEN 'Club de Lectura Páramo'        THEN ARRAY['Estación de café','Refrigerio económico']
        WHEN 'Feria de Innovación Nexo'      THEN ARRAY['Estación de agua','Refrigerio alto','Sonido profesional (consola + 6 micrófonos)','Multimedia (proyector + pantalla)','Streaming y grabación']
        WHEN 'Simposio de Educación'         THEN ARRAY['Estación de café','Refrigerio medio','Multimedia (proyector + pantalla)']
        WHEN 'Encuentro Interno Nexo'        THEN ARRAY['Estación de agua','Refrigerio económico']
        WHEN 'Gala Benéfica'                 THEN ARRAY['Refrigerio alto','Sonido profesional (consola + 6 micrófonos)']
        WHEN 'Conferencia Pospuesta'         THEN ARRAY['Estación de café','Sonido básico (2 micrófonos + parlantes)']
        WHEN 'Congreso Nacional de Salud'    THEN ARRAY['Estación de agua','Refrigerio medio','Sonido profesional (consola + 6 micrófonos)','Streaming y grabación']
        WHEN 'Seminario Corporativo Q4'      THEN ARRAY['Estación de café','Refrigerio medio','Multimedia (proyector + pantalla)']
        WHEN 'Taller de Economía Circular'   THEN ARRAY['Estación de café','Sonido básico (2 micrófonos + parlantes)']
        WHEN 'Feria Navideña'                THEN ARRAY['Estación de agua','Refrigerio alto','Sonido profesional (consola + 6 micrófonos)','Streaming y grabación']
    END
);


UPDATE eventos SET estado = 'Confirmado'
WHERE estado = 'Cotizado'
  AND nombre NOT IN ('Taller de Economía Circular', 'Feria Navideña');


-- Jornada Científica Solvida: 50 inscritos
INSERT INTO inscripciones (evento_id, asistente_id, fecha_inscripcion)
SELECT e.id, a.id, e.inicio - INTERVAL '7 days'
FROM eventos e JOIN asistentes a ON a.documento::bigint BETWEEN 100000001 AND 100000050
WHERE e.nombre = 'Jornada Científica Solvida';

-- Capacitación en Ciberseguridad: 45 inscritos
INSERT INTO inscripciones (evento_id, asistente_id, fecha_inscripcion)
SELECT e.id, a.id, e.inicio - INTERVAL '7 days'
FROM eventos e JOIN asistentes a ON a.documento::bigint BETWEEN 100000001 AND 100000045
WHERE e.nombre = 'Capacitación en Ciberseguridad';

-- Club de Lectura Páramo: 20 inscritos = aforo (cupo lleno)
INSERT INTO inscripciones (evento_id, asistente_id, fecha_inscripcion)
SELECT e.id, a.id, e.inicio - INTERVAL '7 days'
FROM eventos e JOIN asistentes a ON a.documento::bigint BETWEEN 100000001 AND 100000020
WHERE e.nombre = 'Club de Lectura Páramo';

-- Feria de Innovación Nexo: 60 inscritos
INSERT INTO inscripciones (evento_id, asistente_id, fecha_inscripcion)
SELECT e.id, a.id, e.inicio - INTERVAL '7 days'
FROM eventos e JOIN asistentes a ON a.documento::bigint BETWEEN 100000001 AND 100000060
WHERE e.nombre = 'Feria de Innovación Nexo';

-- Simposio de Educación: 40 inscritos (0 check-ins -> tasa 0%)
INSERT INTO inscripciones (evento_id, asistente_id, fecha_inscripcion)
SELECT e.id, a.id, e.inicio - INTERVAL '7 days'
FROM eventos e JOIN asistentes a ON a.documento::bigint BETWEEN 100000001 AND 100000040
WHERE e.nombre = 'Simposio de Educación';

INSERT INTO inscripciones (evento_id, asistente_id, fecha_inscripcion)
SELECT e.id, a.id, CURRENT_DATE
FROM eventos e JOIN asistentes a ON a.documento::bigint BETWEEN 100000001 AND 100000055
WHERE e.nombre = 'Congreso Nacional de Salud';

-- (Encuentro Interno Nexo queda sin inscritos -> al finalizar su tasa será NULL)


-- Jornada Científica Solvida: 42 de 50 -> 84.00%
UPDATE inscripciones i SET hora_checkin = e.inicio + INTERVAL '20 min'
FROM eventos e, asistentes a
WHERE i.evento_id = e.id AND i.asistente_id = a.id
  AND e.nombre = 'Jornada Científica Solvida'
  AND a.documento::bigint BETWEEN 100000001 AND 100000042;

-- Capacitación en Ciberseguridad: 32 de 45 -> 71.11%
UPDATE inscripciones i SET hora_checkin = e.inicio + INTERVAL '20 min'
FROM eventos e, asistentes a
WHERE i.evento_id = e.id AND i.asistente_id = a.id
  AND e.nombre = 'Capacitación en Ciberseguridad'
  AND a.documento::bigint BETWEEN 100000001 AND 100000032;

-- Club de Lectura Páramo: 18 de 20 -> 90.00%
UPDATE inscripciones i SET hora_checkin = e.inicio + INTERVAL '20 min'
FROM eventos e, asistentes a
WHERE i.evento_id = e.id AND i.asistente_id = a.id
  AND e.nombre = 'Club de Lectura Páramo'
  AND a.documento::bigint BETWEEN 100000001 AND 100000018;

-- Feria de Innovación Nexo: 30 de 60 -> 50.00%
UPDATE inscripciones i SET hora_checkin = e.inicio + INTERVAL '20 min'
FROM eventos e, asistentes a
WHERE i.evento_id = e.id AND i.asistente_id = a.id
  AND e.nombre = 'Feria de Innovación Nexo'
  AND a.documento::bigint BETWEEN 100000001 AND 100000030;

-- Simposio de Educación: 0 check-ins -> 0.00%  (no se hace nada)


UPDATE eventos SET estado = 'Finalizado'
WHERE nombre IN (
    'Jornada Científica Solvida',
    'Capacitación en Ciberseguridad',
    'Club de Lectura Páramo',
    'Feria de Innovación Nexo',
    'Simposio de Educación',
    'Encuentro Interno Nexo'   -- sin inscritos -> tasa NULL
);


UPDATE eventos SET estado = 'Cancelado'
WHERE nombre IN ('Gala Benéfica', 'Conferencia Pospuesta');


COMMIT;

