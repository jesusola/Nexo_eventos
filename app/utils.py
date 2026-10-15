from fastapi import HTTPException


def obtener_o_404(db, entidad, identificador, nombre):
    registro = db.get(entidad, identificador)
    if registro is None:
        raise HTTPException(status_code=404, detail=f"{nombre} {identificador} no existe.")
    return registro
