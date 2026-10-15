CREATE OR REPLACE FUNCTION fn_salones_disponibles(p_inicio TIMESTAMP, p_fin TIMESTAMP, p_aforo INTEGER)
RETURNS TABLE(salon_id INTEGER, nombre VARCHAR, tamano VARCHAR, capacidad INTEGER,
              precio_hora NUMERIC, costo_estimado NUMERIC) AS $$
BEGIN
    IF p_fin <= p_inicio OR p_aforo <= 0 OR p_inicio IS NULL OR p_fin IS NULL OR p_aforo IS NULL THEN
        RAISE EXCEPTION 'DISPONIBILIDAD: Indique fin posterior al inicio y aforo positivo.' USING ERRCODE = '23514';
    END IF;
    RETURN QUERY
    SELECT s.id, s.nombre, s.tamano, s.capacidad_maxima, s.precio_hora,
           ROUND(s.precio_hora * fn_horas_evento(p_inicio, p_fin), 2)
    FROM salones s WHERE s.activo AND s.capacidad_maxima >= p_aforo
    AND NOT EXISTS (
        SELECT 1 FROM eventos e WHERE e.salon_id = s.id AND e.estado <> 'Cancelado'
        AND p_inicio < e.fin + INTERVAL '1 hour' AND p_fin + INTERVAL '1 hour' > e.inicio
    ) ORDER BY s.capacidad_maxima, s.precio_hora, s.id;
END;
$$ LANGUAGE plpgsql STABLE;
