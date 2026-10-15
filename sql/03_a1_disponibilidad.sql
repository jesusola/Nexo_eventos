CREATE OR REPLACE FUNCTION fn_evento_disponibilidad() RETURNS TRIGGER AS $$
DECLARE
    v_salon salones%ROWTYPE;
    v_conflicto RECORD;
    v_inscritos INTEGER;
BEGIN
    IF NEW.estado = 'Cancelado' THEN RETURN NEW; END IF;
    SELECT * INTO v_salon FROM salones WHERE id = NEW.salon_id FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'SALON: El salón no existe.' USING ERRCODE = '23503'; END IF;
    IF NOT v_salon.activo THEN RAISE EXCEPTION 'SALON: El salón % está deshabilitado.', v_salon.nombre; END IF;
    IF NEW.aforo_esperado > v_salon.capacidad_maxima THEN
        RAISE EXCEPTION 'AFORO: % personas superan la capacidad de % (%).',
            NEW.aforo_esperado, v_salon.nombre, v_salon.capacidad_maxima;
    END IF;
    SELECT COUNT(*) INTO v_inscritos FROM inscripciones WHERE evento_id = NEW.id;
    IF v_inscritos > NEW.aforo_esperado THEN
        RAISE EXCEPTION 'CUPO: No se puede reducir el aforo a % porque hay % inscritos.', NEW.aforo_esperado, v_inscritos;
    END IF;
    -- Una hora entre eventos; la separación se cuenta una sola vez.
    SELECT id, nombre, inicio, fin INTO v_conflicto FROM eventos
    WHERE salon_id = NEW.salon_id AND id IS DISTINCT FROM NEW.id AND estado <> 'Cancelado'
      AND NEW.inicio < fin + INTERVAL '1 hour'
      AND NEW.fin + INTERVAL '1 hour' > inicio
    ORDER BY inicio, id LIMIT 1;
    IF FOUND THEN
        RAISE EXCEPTION 'DISPONIBILIDAD: Cruce con el evento #% "%" (% a %). Se requiere una hora entre eventos.',
            v_conflicto.id, v_conflicto.nombre, v_conflicto.inicio, v_conflicto.fin;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_20_evento_disponibilidad ON eventos;
CREATE TRIGGER tr_20_evento_disponibilidad
BEFORE INSERT OR UPDATE OF salon_id, inicio, fin, aforo_esperado, estado ON eventos
FOR EACH ROW EXECUTE FUNCTION fn_evento_disponibilidad();
