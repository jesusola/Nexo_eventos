CREATE OR REPLACE FUNCTION fn_inscripcion_validar() RETURNS TRIGGER AS $$
DECLARE
    v_evento eventos%ROWTYPE;
    v_inscritos INTEGER;
BEGIN
    SELECT * INTO v_evento FROM eventos
    WHERE id = CASE WHEN TG_OP = 'DELETE' THEN OLD.evento_id ELSE NEW.evento_id END FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'EVENTO: El evento no existe.' USING ERRCODE = '23503'; END IF;
    IF v_evento.estado IN ('Cancelado', 'Finalizado') THEN
        RAISE EXCEPTION 'INSCRIPCION: El evento está % y no admite cambios de inscripción o asistencia.', v_evento.estado;
    END IF;
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    IF TG_OP = 'INSERT' THEN
        SELECT COUNT(*) INTO v_inscritos FROM inscripciones WHERE evento_id = NEW.evento_id;
        IF v_inscritos >= v_evento.aforo_esperado THEN
            RAISE EXCEPTION 'CUPO: El evento alcanzó su aforo contratado (%).', v_evento.aforo_esperado;
        END IF;
    ELSE
        IF NEW.evento_id IS DISTINCT FROM OLD.evento_id OR NEW.asistente_id IS DISTINCT FROM OLD.asistente_id THEN
            RAISE EXCEPTION 'INSCRIPCION: No se puede trasladar una inscripción a otra persona o evento.';
        END IF;
        IF OLD.hora_checkin IS NOT NULL AND NEW.hora_checkin IS DISTINCT FROM OLD.hora_checkin THEN
            RAISE EXCEPTION 'CHECKIN: La asistencia ya fue registrada; no se puede borrar ni cambiar.';
        END IF;
    END IF;
    IF NEW.hora_checkin IS NOT NULL THEN
        IF NEW.hora_checkin < v_evento.inicio - INTERVAL '1 hour' OR NEW.hora_checkin > v_evento.fin THEN
            RAISE EXCEPTION 'CHECKIN: Solo se permite entre % y %.', v_evento.inicio - INTERVAL '1 hour', v_evento.fin;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_inscripcion_validar ON inscripciones;
CREATE TRIGGER tr_inscripcion_validar BEFORE INSERT OR UPDATE OR DELETE ON inscripciones
FOR EACH ROW EXECUTE FUNCTION fn_inscripcion_validar();
