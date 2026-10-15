CREATE OR REPLACE FUNCTION fn_evento_cierre() RETURNS TRIGGER AS $$
DECLARE v_inscritos INTEGER; v_llegaron INTEGER;
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NEW.estado <> 'Cotizado' THEN RAISE EXCEPTION 'ESTADO: Todo evento debe nacer Cotizado.'; END IF;
        NEW.tasa_asistencia := NULL;
        RETURN NEW;
    END IF;
    IF OLD.estado IN ('Finalizado', 'Cancelado') THEN
        RAISE EXCEPTION 'ESTADO: % es definitivo; no se puede modificar el evento.', OLD.estado;
    END IF;
    IF NEW.estado IS DISTINCT FROM OLD.estado THEN
        IF NOT ((OLD.estado = 'Cotizado' AND NEW.estado IN ('Confirmado', 'Cancelado'))
             OR (OLD.estado = 'Confirmado' AND NEW.estado IN ('Finalizado', 'Cancelado'))) THEN
            RAISE EXCEPTION 'ESTADO: Transición no permitida de % a %.', OLD.estado, NEW.estado;
        END IF;
        IF NEW.estado = 'Finalizado' THEN
            IF NEW.fin >= CURRENT_TIMESTAMP AT TIME ZONE 'America/Bogota' THEN
                RAISE EXCEPTION 'CIERRE: El evento todavía no ha terminado (%).', NEW.fin;
            END IF;
            SELECT COUNT(*), COUNT(hora_checkin) INTO v_inscritos, v_llegaron
            FROM inscripciones WHERE evento_id = NEW.id;
            NEW.tasa_asistencia := CASE WHEN v_inscritos = 0 THEN NULL
                ELSE ROUND(v_llegaron * 100.0 / v_inscritos, 2) END;
        END IF;
    ELSE
        NEW.tasa_asistencia := OLD.tasa_asistencia;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_10_evento_cierre ON eventos;
CREATE TRIGGER tr_10_evento_cierre BEFORE INSERT OR UPDATE ON eventos
FOR EACH ROW EXECUTE FUNCTION fn_evento_cierre();

CREATE OR REPLACE FUNCTION fn_evento_auditoria() RETURNS TRIGGER AS $$
DECLARE
    v_usuario TEXT := COALESCE(NULLIF(current_setting('app.usuario', true), ''), 'sistema');
    v_campo TEXT;
    v_anterior TEXT;
    v_nuevo TEXT;
BEGIN
    FOREACH v_campo IN ARRAY ARRAY['estado', 'salon_id', 'inicio', 'fin'] LOOP
        v_anterior := to_jsonb(OLD)->>v_campo;
        v_nuevo := to_jsonb(NEW)->>v_campo;
        IF v_anterior IS DISTINCT FROM v_nuevo THEN
            INSERT INTO auditoria(evento_id, campo, valor_anterior, valor_nuevo, usuario_app)
            VALUES(NEW.id, v_campo, v_anterior, v_nuevo, v_usuario);
        END IF;
    END LOOP;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_evento_auditoria ON eventos;
CREATE TRIGGER tr_evento_auditoria AFTER UPDATE ON eventos
FOR EACH ROW EXECUTE FUNCTION fn_evento_auditoria();

CREATE OR REPLACE FUNCTION fn_staff_sin_ciclos() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.jefe_id IS NOT NULL AND EXISTS (
        WITH RECURSIVE jefes AS (
            SELECT id, jefe_id, ARRAY[id] AS ruta FROM staff WHERE id = NEW.jefe_id
            UNION ALL
            SELECT s.id, s.jefe_id, j.ruta || s.id FROM staff s JOIN jefes j ON s.id = j.jefe_id
            WHERE NOT s.id = ANY(j.ruta)
        ) SELECT 1 FROM jefes WHERE id = NEW.id
    ) THEN RAISE EXCEPTION 'STAFF: El jefe seleccionado crea un ciclo en la jerarquía.'; END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS tr_staff_sin_ciclos ON staff;
CREATE TRIGGER tr_staff_sin_ciclos BEFORE INSERT OR UPDATE OF jefe_id ON staff
FOR EACH ROW EXECUTE FUNCTION fn_staff_sin_ciclos();
