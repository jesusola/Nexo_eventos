CREATE OR REPLACE FUNCTION fn_horas_evento(p_inicio TIMESTAMP, p_fin TIMESTAMP)
RETURNS NUMERIC LANGUAGE sql IMMUTABLE AS $$
    SELECT EXTRACT(EPOCH FROM (p_fin - p_inicio)) / 3600.0;
$$;

CREATE OR REPLACE FUNCTION fn_evento_liquidar() RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        SELECT precio_hora INTO NEW.precio_salon_congelado FROM salones WHERE id = NEW.salon_id;
    ELSIF NEW.salon_id IS DISTINCT FROM OLD.salon_id THEN
        SELECT precio_hora INTO NEW.precio_salon_congelado FROM salones WHERE id = NEW.salon_id;
    ELSE
        NEW.precio_salon_congelado := OLD.precio_salon_congelado;
    END IF;
    NEW.valor_total := ROUND(NEW.precio_salon_congelado * fn_horas_evento(NEW.inicio, NEW.fin)
        + COALESCE((SELECT SUM(cantidad * precio_congelado)
                    FROM servicios_evento WHERE evento_id = NEW.id), 0), 2);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_30_evento_liquidar ON eventos;
CREATE TRIGGER tr_30_evento_liquidar BEFORE INSERT OR UPDATE ON eventos
FOR EACH ROW EXECUTE FUNCTION fn_evento_liquidar();

CREATE OR REPLACE FUNCTION fn_servicio_liquidar() RETURNS TRIGGER AS $$
DECLARE
    v_evento eventos%ROWTYPE;
    v_servicio servicios%ROWTYPE;
BEGIN
    -- El bloqueo del padre serializa cambios de servicios e inscripciones.
    SELECT * INTO v_evento FROM eventos
    WHERE id = CASE WHEN TG_OP = 'DELETE' THEN OLD.evento_id ELSE NEW.evento_id END FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'EVENTO: El evento no existe.' USING ERRCODE = '23503';
    END IF;
    IF v_evento.estado IN ('Finalizado', 'Cancelado') THEN
        RAISE EXCEPTION 'SERVICIOS: No se pueden modificar servicios de un evento %.', v_evento.estado;
    END IF;
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    IF TG_OP = 'UPDATE' THEN
        IF NEW.evento_id IS DISTINCT FROM OLD.evento_id OR NEW.servicio_id IS DISTINCT FROM OLD.servicio_id THEN
            RAISE EXCEPTION 'SERVICIOS: Para cambiar de evento o servicio, quite la línea y contrátela de nuevo.';
        END IF;
        IF NEW.precio_congelado IS DISTINCT FROM OLD.precio_congelado THEN
            RAISE EXCEPTION 'PRECIO: No se puede cambiar el precio contratado.';
        END IF;
    END IF;
    SELECT * INTO v_servicio FROM servicios WHERE id = NEW.servicio_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'SERVICIO: El servicio no existe.' USING ERRCODE = '23503';
    END IF;
    IF TG_OP = 'INSERT' THEN NEW.precio_congelado := v_servicio.precio_unitario; END IF;
    IF NEW.cantidad IS NULL THEN
        NEW.cantidad := CASE v_servicio.unidad_cobro
            WHEN 'Por persona' THEN v_evento.aforo_esperado
            WHEN 'Por hora' THEN CEIL(fn_horas_evento(v_evento.inicio, v_evento.fin))
            ELSE 1 END;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_servicio_liquidar ON servicios_evento;
CREATE TRIGGER tr_servicio_liquidar BEFORE INSERT OR UPDATE OR DELETE ON servicios_evento
FOR EACH ROW EXECUTE FUNCTION fn_servicio_liquidar();

CREATE OR REPLACE FUNCTION fn_servicio_actualizar_total() RETURNS TRIGGER AS $$
BEGIN
    -- El BEFORE de eventos calcula el total con las líneas ya modificadas.
    UPDATE eventos SET valor_total = valor_total
    WHERE id = CASE WHEN TG_OP = 'DELETE' THEN OLD.evento_id ELSE NEW.evento_id END;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_servicio_total ON servicios_evento;
CREATE TRIGGER tr_servicio_total AFTER INSERT OR UPDATE OR DELETE ON servicios_evento
FOR EACH ROW EXECUTE FUNCTION fn_servicio_actualizar_total();
