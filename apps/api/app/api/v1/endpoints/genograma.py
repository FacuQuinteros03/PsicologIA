"""Endpoints del genograma: nodos, conexiones y el filtro por nodo."""

import uuid

from fastapi import APIRouter, HTTPException, status

from app.core.deps import SesionDB, TerapeutaActual, obtener_paciente_propio
from app.models import ConexionGenograma, NodoGenograma
from app.schemas.genograma import (
    ConexionCrear,
    ConexionRespuesta,
    MencionSesion,
    NodoCrear,
    NodoRespuesta,
    Posicion,
)
from app.services.sesiones import sesiones_de_nodo

router = APIRouter(prefix="/genograma", tags=["genograma"])


async def _nodo_propio(sesion_db: SesionDB, nodo_id: uuid.UUID, terapeuta) -> NodoGenograma:
    nodo = await sesion_db.get(NodoGenograma, nodo_id)
    if nodo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Nodo no encontrado.")
    # Valida la pertenencia por la vía del paciente.
    await obtener_paciente_propio(sesion_db, nodo.paciente_id, terapeuta)
    return nodo


@router.post("/pacientes/{paciente_id}/nodos", response_model=NodoRespuesta, status_code=201)
async def crear_nodo(
    paciente_id: uuid.UUID, datos: NodoCrear, sesion_db: SesionDB, terapeuta: TerapeutaActual
):
    paciente = await obtener_paciente_propio(sesion_db, paciente_id, terapeuta)
    nodo = NodoGenograma(paciente_id=paciente.id, **datos.model_dump())
    sesion_db.add(nodo)
    await sesion_db.commit()
    await sesion_db.refresh(nodo)
    return nodo


@router.patch("/nodos/{nodo_id}/posicion", response_model=NodoRespuesta)
async def mover_nodo(
    nodo_id: uuid.UUID, posicion: Posicion, sesion_db: SesionDB, terapeuta: TerapeutaActual
):
    """Persiste el arrastre del nodo en el canvas (`onNodeDragStop`)."""
    nodo = await _nodo_propio(sesion_db, nodo_id, terapeuta)
    nodo.pos_x = posicion.pos_x
    nodo.pos_y = posicion.pos_y
    sesion_db.add(nodo)
    await sesion_db.commit()
    await sesion_db.refresh(nodo)
    return nodo


@router.get("/nodos/{nodo_id}/sesiones", response_model=list[MencionSesion])
async def sesiones_del_nodo(nodo_id: uuid.UUID, sesion_db: SesionDB, terapeuta: TerapeutaActual):
    """El feature estrella: tocás "Mamá" y ves sólo las sesiones donde aparece."""
    nodo = await _nodo_propio(sesion_db, nodo_id, terapeuta)
    filas = await sesiones_de_nodo(sesion_db, nodo.id)
    return [
        MencionSesion(
            sesion_id=sesion.id,
            fecha_sesion=sesion.fecha_sesion.isoformat(),
            menciones=enlace.menciones,
            contexto=enlace.contexto,
            resumen_ia=sesion.resumen_ia,
            tags=list(sesion.tags),
        )
        for sesion, enlace in filas
    ]


@router.post(
    "/pacientes/{paciente_id}/conexiones", response_model=ConexionRespuesta, status_code=201
)
async def crear_conexion(
    paciente_id: uuid.UUID, datos: ConexionCrear, sesion_db: SesionDB, terapeuta: TerapeutaActual
):
    paciente = await obtener_paciente_propio(sesion_db, paciente_id, terapeuta)

    # Los dos extremos tienen que ser del mismo paciente: sin este chequeo se
    # podría enlazar el genograma de una persona con el de otra.
    for extremo in (datos.origen_id, datos.destino_id):
        nodo = await sesion_db.get(NodoGenograma, extremo)
        if nodo is None or nodo.paciente_id != paciente.id:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Los nodos deben pertenecer al mismo paciente.",
            )

    conexion = ConexionGenograma(paciente_id=paciente.id, **datos.model_dump())
    sesion_db.add(conexion)
    await sesion_db.commit()
    await sesion_db.refresh(conexion)
    return conexion
