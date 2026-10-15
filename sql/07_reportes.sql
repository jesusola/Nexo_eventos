CREATE OR REPLACE VIEW vw_organigrama AS
WITH RECURSIVE arbol AS (
    SELECT id, nombre, cargo, area, jefe_id, 1 AS nivel,
           ARRAY[id] AS ruta_ids, nombre::TEXT AS ruta_mando
    FROM staff WHERE jefe_id IS NULL
    UNION ALL
    SELECT s.id, s.nombre, s.cargo, s.area, s.jefe_id, a.nivel + 1,
           a.ruta_ids || s.id, a.ruta_mando || ' > ' || s.nombre
    FROM staff s JOIN arbol a ON s.jefe_id = a.id WHERE NOT s.id = ANY(a.ruta_ids)
)
SELECT a.id, a.nombre, a.cargo, a.area, a.jefe_id, a.nivel, a.ruta_mando, a.ruta_ids,
       (SELECT COUNT(*) FROM staff s WHERE s.jefe_id = a.id) AS a_cargo_directos,
       (SELECT COUNT(*) FROM arbol sub WHERE a.id = ANY(sub.ruta_ids) AND sub.id <> a.id) AS total_a_cargo
FROM arbol a;

CREATE OR REPLACE FUNCTION fn_escalamiento(p_staff INTEGER)
RETURNS TABLE(orden INTEGER, id INTEGER, nombre VARCHAR, cargo VARCHAR, area VARCHAR)
LANGUAGE sql STABLE AS $$
    WITH RECURSIVE cadena AS (
        SELECT s.id, s.nombre, s.cargo, s.area, s.jefe_id, 0 AS orden, ARRAY[s.id] AS ruta
        FROM staff s WHERE s.id = p_staff
        UNION ALL
        SELECT j.id, j.nombre, j.cargo, j.area, j.jefe_id, c.orden + 1, c.ruta || j.id
        FROM staff j JOIN cadena c ON j.id = c.jefe_id WHERE NOT j.id = ANY(c.ruta)
    ) SELECT c.orden, c.id, c.nombre, c.cargo, c.area FROM cadena c WHERE c.orden > 0 ORDER BY c.orden;
$$;

CREATE OR REPLACE VIEW vw_ranking_clientes AS
WITH ingresos AS (
    SELECT c.id AS cliente_id, c.nombre_razon_social AS nombre,
           COUNT(e.id) AS eventos_no_cancelados, COALESCE(SUM(e.valor_total), 0) AS facturacion
    FROM clientes c LEFT JOIN eventos e ON e.cliente_id = c.id AND e.estado <> 'Cancelado'
    GROUP BY c.id, c.nombre_razon_social
), ventanas AS (
    SELECT i.*, RANK() OVER (ORDER BY facturacion DESC) AS ranking,
           SUM(facturacion) OVER () AS total_general,
           SUM(facturacion) OVER (ORDER BY facturacion DESC, cliente_id
               ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS facturacion_acumulada
    FROM ingresos i
)
SELECT cliente_id, nombre, eventos_no_cancelados, facturacion, ranking,
       COALESCE(ROUND(100 * facturacion / NULLIF(total_general, 0), 2), 0) AS participacion_pct,
       COALESCE(ROUND(100 * facturacion_acumulada / NULLIF(total_general, 0), 2), 0) AS acumulado_pct,
       CASE WHEN facturacion > 0 AND 100 * (facturacion_acumulada - facturacion) / NULLIF(total_general, 0) < 80
            THEN 'A (80%)' ELSE 'B (resto)' END AS segmento_pareto
FROM ventanas;

CREATE OR REPLACE VIEW vw_ocupacion_salones AS
SELECT e.salon_id, s.nombre AS salon, e.id AS evento_id, e.nombre AS evento,
       e.estado, e.inicio, e.fin,
       ROW_NUMBER() OVER w AS num_evento_salon,
       LAG(e.id) OVER w AS evento_anterior_id,
       LAG(e.nombre) OVER w AS evento_anterior,
       ROUND(EXTRACT(EPOCH FROM(e.inicio - LAG(e.fin) OVER w)) / 86400.0, 2) AS dias_libres,
       ROUND(fn_horas_evento(e.inicio, e.fin), 2) AS horas_reservadas,
       ROUND(SUM(fn_horas_evento(e.inicio, e.fin)) OVER w, 2) AS horas_acumuladas
FROM eventos e JOIN salones s ON s.id = e.salon_id WHERE e.estado <> 'Cancelado'
WINDOW w AS (PARTITION BY e.salon_id ORDER BY e.inicio, e.id ROWS UNBOUNDED PRECEDING);
