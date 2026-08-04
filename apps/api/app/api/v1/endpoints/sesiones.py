"""Endpoints de sesiones, incluido el procesamiento de notas con IA."""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status

from app.core.deps import SesionDB, TerapeutaActual, obtener_paciente_propio
from app.models import Paciente, Sesion
from app.schemas.ia import NotasEstructuradas, ProcesarNotasRequest
from app.schemas.sesion import SesionActualizar, SesionCrear, SesionDetalle
from app.services.ia import ErrorProveedorIA, obtener_proveedor
from app.services.sesiones import construir_contexto, marcar_error, persistir_resultado

router = APIRouter(prefix="/sesiones", tags=["sesiones"])


async def _sesion_propia(
    sesion_db: SesionDB, sesion_id: uuid.UUID, terapeuta
) -> tuple[Sesion, Paciente]:
    """Trae la sesión y su paciente verificando que sean del terapeuta actual."""
    sesion = await sesion_db.get(Sesion, sesion_id)
    if sesion is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Sesión no encontrada.")
    paciente = await obtener_paciente_propio(sesion_db, sesion.paciente_id, terapeuta)
    return sesion, paciente


@router.post("/procesar-notas", response_model=NotasEstructuradas)
async def procesar_notas(
    payload: ProcesarNotasRequest, sesion_db: SesionDB, terapeuta: TerapeutaActual
):
    """Convierte notas crudas en estructura clínica.

    Es **stateless por defecto**: sin `persistir=true` no escribe nada, así que
    sirve para previsualizar el resultado antes de guardarlo. Sin `GEMINI_API_KEY`
    el proveedor es `mock` y responde igual, sin salir a la red.
    """
    proveedor = obtener_proveedor()

    sesion: Sesion | None = None
    paciente: Paciente | None = None

    if payload.sesion_id is not None:
        sesion, paciente = await _sesion_propia(sesion_db, payload.sesion_id, terapeuta)
    elif payload.paciente_id is not None:
        paciente = await obtener_paciente_propio(sesion_db, payload.paciente_id, terapeuta)

    contexto = await construir_contexto(sesion_db, paciente) if paciente else None

    try:
        salida = await proveedor.procesar(payload.notas, contexto)
    except ErrorProveedorIA as error:
        if sesion is not None and payload.persistir:
            marcar_error(sesion, error.crudo)
            sesion_db.add(sesion)
            await sesion_db.commit()
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error

    persistido = False
    if payload.persistir and sesion is not None and paciente is not None:
        await persistir_resultado(
            sesion_db, sesion, paciente, salida, proveedor.nombre, proveedor.modelo
        )
        await sesion_db.commit()
        persistido = True

    return NotasEstructuradas(
        **salida.model_dump(),
        proveedor=proveedor.nombre,
        modelo=proveedor.modelo,
        procesado_en=datetime.now(UTC),
        sesion_id=sesion.id if sesion else None,
        persistido=persistido,
    )


@router.post("", response_model=SesionDetalle, status_code=201)
async def crear_sesion(datos: SesionCrear, sesion_db: SesionDB, terapeuta: TerapeutaActual):
    paciente = await obtener_paciente_propio(sesion_db, datos.paciente_id, terapeuta)
    sesion = Sesion(
        paciente_id=paciente.id,
        notas_borrador=datos.notas_borrador,
        numero_sesion=datos.numero_sesion,
        **({"fecha_sesion": datos.fecha_sesion} if datos.fecha_sesion else {}),
    )
    sesion_db.add(sesion)
    await sesion_db.commit()
    await sesion_db.refresh(sesion)
    return sesion


@router.get("/{sesion_id}", response_model=SesionDetalle)
async def obtener_sesion(sesion_id: uuid.UUID, sesion_db: SesionDB, terapeuta: TerapeutaActual):
    sesion, _ = await _sesion_propia(sesion_db, sesion_id, terapeuta)
    return sesion


@router.patch("/{sesion_id}", response_model=SesionDetalle)
async def guardar_borrador(
    sesion_id: uuid.UUID,
    datos: SesionActualizar,
    sesion_db: SesionDB,
    terapeuta: TerapeutaActual,
):
    """Autoguardado de las notas mientras el terapeuta tipea."""
    sesion, _ = await _sesion_propia(sesion_db, sesion_id, terapeuta)
    sesion.notas_borrador = datos.notas_borrador
    sesion_db.add(sesion)
    await sesion_db.commit()
    await sesion_db.refresh(sesion)
    return sesion
