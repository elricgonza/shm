"""
app/audit.py
============
Módulo centralizado de auditoría.

Uso básico en cualquier ruta:
    from app.audit import log_accion
    log_accion('CREATE', 'alumno', entidad_id=a.id, detalle={'nombre': a.nombre_completo})
"""
import json
from datetime import datetime

from flask import request
from flask_login import current_user

from app import db


def log_accion(accion: str, modulo: str, *,
               entidad_id: int = None,
               detalle: dict = None,
               status: int = 200) -> None:
    """
    Registra una acción en la tabla audit_log.

    Parámetros
    ----------
    accion     : 'CREATE' | 'UPDATE' | 'DELETE' | 'LOGIN' | 'LOGOUT' | 'BULK' | 'ERROR'
    modulo     : nombre de la tabla / módulo afectado  (ej. 'alumno', 'pago')
    entidad_id : PK del registro afectado (opcional)
    detalle    : dict con datos adicionales que se guarda como JSON (opcional)
    status     : código HTTP de la operación (default 200)
    """
    # Import aquí para evitar circularidad al importar en __init__
    from app.models import AuditLog

    try:
        usu_id  = current_user.id       if current_user.is_authenticated else None
        usuario = current_user.usuario  if current_user.is_authenticated else 'anónimo'

        entrada = AuditLog(
            usu_id     = usu_id,
            usuario    = usuario,
            accion     = accion[:20],
            modulo     = modulo[:50],
            entidad_id = entidad_id,
            detalle    = json.dumps(detalle, ensure_ascii=False, default=str) if detalle else None,
            ip         = _get_ip(),
            endpoint   = (request.endpoint or '')[:150] if request else None,
            metodo     = (request.method   or '')[:10]  if request else None,
            status     = status,
            creado     = datetime.utcnow(),
        )
        db.session.add(entrada)
        db.session.commit()          # commit independiente del flujo principal
    except Exception as exc:         # el log NUNCA debe romper la operación principal
        db.session.rollback()
        import logging
        logging.getLogger(__name__).warning('audit log failed: %s', exc)


def _get_ip() -> str:
    """Devuelve la IP real del cliente respetando proxies."""
    if not request:
        return None
    forwarded = request.headers.get('X-Forwarded-For')
    if forwarded:
        return forwarded.split(',')[0].strip()[:45]
    return (request.remote_addr or '')[:45]
