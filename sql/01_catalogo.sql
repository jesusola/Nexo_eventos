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


