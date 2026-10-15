from fastapi import Header
from sqlalchemy import text
from sqlalchemy.orm import Session


def get_usuario(x_usuario: str = Header(default="api")) -> str:
    usuario = x_usuario.strip()
    if not usuario or len(usuario) > 150:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="X-Usuario debe tener entre 1 y 150 caracteres.")
    return usuario


def set_usuario_db(db: Session, usuario: str) -> None:
    db.execute(
        text("SELECT set_config('app.usuario', :u, true)"),
        {"u": usuario},
    )
