import os
from datetime import datetime, timedelta
from pathlib import Path
import sys

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
sys.path.insert(0, str(ROOT))

st.set_page_config(page_title="NexoEventos", layout="wide")
st.title("NexoEventos")
api = st.sidebar.text_input("Dirección de la API", os.getenv("API_URL", "http://localhost:8000")).rstrip("/")
usuario = st.sidebar.text_input("Usuario", "equipo_nexo")
pagina = st.sidebar.radio("Módulo", ["Inicio", "Disponibilidad", "Eventos", "Asistentes", "Clientes y staff", "Reportes", "Pruebas de entrega"])


def llamar(metodo, ruta, datos=None, parametros=None, mostrar=False):
    try:
        respuesta = requests.request(metodo, api + ruta, json=datos, params=parametros,
                                    headers={"X-Usuario": usuario}, timeout=12)
        contenido = respuesta.json() if respuesta.content else None
    except (requests.RequestException, ValueError):
        st.error("No se pudo contactar con la API. Compruebe la dirección y que esté encendida.")
        return None
    if respuesta.status_code >= 400:
        detalle = contenido.get("detail", "La operación no se pudo completar.")
        if isinstance(detalle, list):
            detalle = "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in detalle)
        st.error(detalle)
        st.caption(f"HTTP {respuesta.status_code}")
        return None
    if mostrar:
        st.success("Operación realizada.")
        st.caption(f"HTTP {respuesta.status_code}")
        if contenido is not None: st.json(contenido)
    return contenido


def tabla(datos):
    if datos: st.dataframe(pd.DataFrame(datos), use_container_width=True, hide_index=True)
    else: st.info("No hay registros para mostrar.")


def elegir(etiqueta, registros, campo="nombre", clave=None):
    return st.selectbox(etiqueta, registros, format_func=lambda r: f"{r['id']} · {r[campo]}", key=clave)


if pagina == "Inicio":
    eventos = llamar("GET", "/eventos")
    if eventos is not None:
        columnas = st.columns(4)
        for columna, estado in zip(columnas, ["Cotizado", "Confirmado", "Finalizado", "Cancelado"]):
            columna.metric(estado, sum(e["estado"] == estado for e in eventos))
        tasas = [float(e["tasa_asistencia"]) for e in eventos if e["tasa_asistencia"] is not None]
        st.metric("Asistencia promedio", f"{sum(tasas) / len(tasas):.2f}%" if tasas else "Sin datos")
        st.subheader("Próximos eventos")
        tabla([e for e in eventos if datetime.fromisoformat(e["inicio"]) > datetime.now() and e["estado"] != "Cancelado"])

elif pagina == "Disponibilidad":
    st.subheader("Consultar salones libres")
    with st.form("disponibilidad"):
        inicio = st.text_input("Inicio", (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%dT09:00"))
        fin = st.text_input("Fin", (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%dT12:00"))
        aforo = st.number_input("Personas", min_value=1, value=50)
        consultar = st.form_submit_button("Consultar")
    if consultar:
        resultado = llamar("GET", "/salones/disponibles", parametros={"inicio": inicio, "fin": fin, "aforo": aforo})
        if resultado is not None: tabla(resultado)

elif pagina == "Eventos":
    clientes = llamar("GET", "/clientes") or []
    staff = llamar("GET", "/staff") or []
    with st.expander("Crear evento"):
        if clientes and staff:
            nombre = st.text_input("Nombre del evento")
            tipo = st.selectbox("Tipo", ["Congreso", "Conferencia", "Feria", "Seminario", "Corporativo", "Social"])
            cliente = elegir("Cliente", clientes, "nombre_razon_social")
            coordinador = elegir("Coordinador", staff)
            inicio = st.text_input("Inicio del evento", (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%dT09:00"))
            fin = st.text_input("Fin del evento", (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%dT12:00"))
            aforo = st.number_input("Aforo esperado", min_value=1, value=50)
            if st.button("Buscar salones disponibles"):
                libres = llamar("GET", "/salones/disponibles", parametros={"inicio": inicio, "fin": fin, "aforo": aforo})
                st.session_state["libres"] = {"consulta": (inicio, fin, aforo), "salones": libres or []}
            guardado = st.session_state.get("libres", {})
            if guardado.get("consulta") == (inicio, fin, aforo) and guardado.get("salones"):
                salon = st.selectbox("Salón", guardado["salones"], format_func=lambda s: s["nombre"])
                if st.button("Crear evento"):
                    llamar("POST", "/eventos", {"nombre": nombre, "tipo": tipo, "cliente_id": cliente["id"],
                           "coordinador_id": coordinador["id"], "salon_id": salon["salon_id"],
                           "inicio": inicio, "fin": fin, "aforo_esperado": aforo}, mostrar=True)
    eventos = llamar("GET", "/eventos") or []
    if eventos:
        evento = elegir("Evento", eventos)
        eid = evento["id"]
        st.json(llamar("GET", f"/eventos/{eid}") or {})
        estado = st.selectbox("Cambiar estado", ["Confirmado", "Finalizado", "Cancelado"])
        if st.button("Aplicar estado"): llamar("PATCH", f"/eventos/{eid}/estado", {"estado": estado}, mostrar=True)
        with st.expander("Servicios y cotización"):
            servicios = llamar("GET", "/servicios") or []
            if servicios:
                servicio = elegir("Servicio", servicios)
                defecto = st.checkbox("Calcular cantidad según aforo u horas", value=True)
                cantidad = st.number_input("Cantidad", min_value=0.01, value=1.0)
                if st.button("Contratar servicio"):
                    llamar("POST", f"/eventos/{eid}/servicios", {"servicio_id": servicio["id"],
                           "cantidad": None if defecto else str(cantidad)}, mostrar=True)
            lineas = llamar("GET", f"/eventos/{eid}/servicios") or []
            tabla(lineas)
            if lineas:
                linea = st.selectbox("Línea contratada", lineas, format_func=lambda x: f"Línea {x['id']} · servicio {x['servicio_id']}")
                nueva = st.number_input("Nueva cantidad", min_value=0.01, value=float(linea["cantidad"]))
                if st.button("Modificar cantidad"):
                    llamar("PUT", f"/eventos/{eid}/servicios/{linea['id']}", {"cantidad": str(nueva)}, mostrar=True)
                if st.button("Quitar servicio"): llamar("DELETE", f"/eventos/{eid}/servicios/{linea['id']}", mostrar=True)
            st.json(llamar("GET", f"/eventos/{eid}/cotizacion") or {})
        with st.expander("Reprogramar"):
            nuevo_inicio = st.text_input("Nuevo inicio", evento["inicio"])
            nuevo_fin = st.text_input("Nuevo fin", evento["fin"])
            nuevo_aforo = st.number_input("Nuevo aforo", min_value=1, value=evento["aforo_esperado"])
            salones = llamar("GET", "/salones") or []
            salon = elegir("Nuevo salón", salones) if salones else None
            if st.button("Guardar reprogramación") and salon:
                llamar("PATCH", f"/eventos/{eid}", {"inicio": nuevo_inicio, "fin": nuevo_fin,
                       "salon_id": salon["id"], "aforo_esperado": nuevo_aforo}, mostrar=True)
        with st.expander("Historial de cambios"): tabla(llamar("GET", f"/eventos/{eid}/auditoria"))

elif pagina == "Asistentes":
    with st.form("asistente"):
        documento = st.text_input("Documento")
        nombre = st.text_input("Nombre")
        correo = st.text_input("Correo")
        empresa = st.text_input("Empresa (opcional)")
        guardar = st.form_submit_button("Registrar asistente")
    if guardar: llamar("POST", "/asistentes", {"documento": documento, "nombre": nombre, "correo": correo, "empresa": empresa or None}, mostrar=True)
    busqueda = st.text_input("Buscar por nombre o documento")
    asistentes = llamar("GET", "/asistentes", parametros={"q": busqueda}) or []
    tabla(asistentes)
    eventos = llamar("GET", "/eventos") or []
    if eventos:
        evento = elegir("Evento para inscripción o llegada", eventos)
        if asistentes:
            asistente = elegir("Asistente", asistentes)
            if st.button("Inscribir"): llamar("POST", f"/eventos/{evento['id']}/inscripciones", {"asistente_id": asistente["id"]}, mostrar=True)
        documento_puerta = st.text_input("Documento en puerta")
        if st.button("Registrar llegada"):
            llamar("POST", f"/eventos/{evento['id']}/checkin", {"documento": documento_puerta}, mostrar=True)
        tabla(llamar("GET", f"/eventos/{evento['id']}/inscripciones"))

elif pagina == "Clientes y staff":
    with st.form("cliente"):
        tipo = st.selectbox("Tipo de documento", ["NIT", "Cedula"])
        doc = st.text_input("Documento del cliente")
        nombre = st.text_input("Nombre o razón social")
        correo = st.text_input("Correo del cliente")
        telefono = st.text_input("Teléfono")
        guardar = st.form_submit_button("Registrar cliente")
    if guardar: llamar("POST", "/clientes", {"tipo_documento": tipo, "documento": doc, "nombre_razon_social": nombre, "correo": correo, "telefono": telefono}, mostrar=True)
    clientes = llamar("GET", "/clientes", parametros={"q": st.text_input("Buscar cliente")}) or []
    tabla(clientes)
    if clientes:
        cliente = elegir("Ver eventos del cliente", clientes, "nombre_razon_social")
        tabla(llamar("GET", f"/clientes/{cliente['id']}/eventos"))
    staff = llamar("GET", "/staff") or []
    with st.form("staff"):
        nombre = st.text_input("Nombre del empleado")
        cargo = st.text_input("Cargo")
        area = st.selectbox("Área", ["Dirección", "Operaciones", "Comercial", "Logística", "Alimentos y Bebidas", "Audiovisuales"])
        correo = st.text_input("Correo del empleado")
        fecha = st.date_input("Fecha de ingreso")
        jefe = st.selectbox("Jefe", [None] + staff, format_func=lambda x: "Sin jefe" if x is None else x["nombre"])
        guardar = st.form_submit_button("Registrar empleado")
    if guardar: llamar("POST", "/staff", {"nombre": nombre, "cargo": cargo, "area": area, "correo": correo, "fecha_ingreso": fecha.isoformat(), "jefe_id": jefe["id"] if jefe else None}, mostrar=True)
    tabla(staff)

elif pagina == "Reportes":
    reporte = st.selectbox("Reporte", ["Organigrama", "Escalamiento", "Ranking de clientes", "Ocupación de salones"])
    parametros = None
    if reporte in ("Organigrama", "Escalamiento"):
        staff = llamar("GET", "/staff") or []
        empleado = st.selectbox("Empleado", [None] + staff if reporte == "Organigrama" else staff,
                               format_func=lambda x: "Toda la organización" if x is None else x["nombre"])
        if reporte == "Organigrama":
            ruta = "/reportes/organigrama"
            parametros = {"staff_id": empleado["id"]} if empleado else None
        else: ruta = f"/reportes/escalamiento/{empleado['id']}" if empleado else None
    else: ruta = "/reportes/ranking-clientes" if reporte == "Ranking de clientes" else "/reportes/ocupacion-salones"
    if ruta:
        datos = llamar("GET", ruta, parametros=parametros)
        tabla(datos)
        if reporte == "Ranking de clientes" and datos:
            df = pd.DataFrame(datos)
            df["facturacion"] = pd.to_numeric(df["facturacion"])
            st.bar_chart(df.set_index("nombre")[["facturacion"]])

elif pagina == "Pruebas de entrega":
    from scripts.casos import CASOS, ejecutar
    st.subheader("Verificación de reglas")
    st.write("Cada caso prepara sus propios datos y ejecuta una petición real a la API.")
    caso = st.selectbox("Caso", list(CASOS))
    st.write(CASOS[caso]["descripcion"])
    if st.button("Ejecutar caso"):
        try:
            resultado = ejecutar(api, usuario, caso)
            st.session_state["prueba"] = (caso, resultado)
        except (requests.RequestException, ValueError, RuntimeError) as exc:
            st.error(f"No se pudo ejecutar el caso: {exc}")
    guardado = st.session_state.get("prueba")
    if guardado and guardado[0] == caso:
        resultado = guardado[1]
        if resultado["status"] >= 400: st.error(resultado["respuesta"].get("detail", "Operación bloqueada"))
        elif resultado["respuesta"] == []: st.info("No hay salones que cumplan la solicitud.")
        else: st.success("Operación permitida.")
        st.caption(f"HTTP {resultado['status']}")
        st.code(f"{resultado['metodo']} {resultado['ruta']}")
        if resultado.get("datos"): st.json(resultado["datos"])
        st.json(resultado["respuesta"])
        if "comprobacion" in resultado: st.json(resultado["comprobacion"])
