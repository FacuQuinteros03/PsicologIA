"""Endpoints de pacientes, su historial y su genograma."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import ARRAY, Text, cast, text
from sqlmodel import col, func, select

from app.core.deps import SesionDB, TerapeutaActual, obtener_paciente_propio
from app.models import ConexionGenograma, NodoGenograma, Paciente, Recordatorio, Sesion
from app.schemas.genograma import ConexionRespuesta, GenogramaRespuesta, NodoRespuesta
from app.schemas.paciente import PacienteCrear, PacienteRespuesta, RecordatorioRespuesta
from app.schemas.sesion import SesionResumen, TagConteo
from app.utils import slugificar

router = APIRouter(prefix="/pacientes", tags=["pacientes"])

# Escrito como SQL literal a propósito. Construirlo con `func.to_tsvector(...)` y
# concatenación de Python mete bind params (`coalesce(x, %(p1)s) || %(p2)s || ...`)
# en lugar de las constantes `''` y `' '`, y entonces la expresión deja de
# coincidir con la del índice `ix_sesiones_fts` y Postgres cae a seq scan.
# Sólo el texto que busca el usuario va parametrizado.
_FILTRO_FTS = text(
    "to_tsvector('spanish',"
    " coalesce(sesiones.resumen_ia, '') || ' ' || coalesce(sesiones.notas_borrador, ''))"
    " @@ plainto_tsquery('spanish', :consulta_fts)"
)


@router.get("", response_model=list[PacienteRespuesta])
async def listar_pacientes(sesion_db: SesionDB, terapeuta: TerapeutaActual):
    resultado = await sesion_db.exec(
        select(Paciente)
        .where(Paciente.terapeuta_id == terapeuta.id)
        .order_by(col(Paciente.apellido), col(Paciente.nombre))
    )
    return list(resultado.all())


@router.post("", response_model=PacienteRespuesta, status_code=201)
async def crear_paciente(datos: PacienteCrear, sesion_db: SesionDB, terapeuta: TerapeutaActual):
    paciente = Paciente(terapeuta_id=terapeuta.id, **datos.model_dump())
    sesion_db.add(paciente)
    await sesion_db.commit()
    await sesion_db.refresh(paciente)
    return paciente


@router.get("/{paciente_id}", response_model=PacienteRespuesta)
async def obtener_paciente(paciente_id: uuid.UUID, sesion_db: SesionDB, terapeuta: TerapeutaActual):
    return await obtener_paciente_propio(sesion_db, paciente_id, terapeuta)


@router.get("/{paciente_id}/sesiones", response_model=list[SesionResumen])
async def listar_sesiones(
    paciente_id: uuid.UUID,
    sesion_db: SesionDB,
    terapeuta: TerapeutaActual,
    tags: Annotated[
        list[str] | None,
        Query(description="Filtra sesiones que tengan alguno de estos tags."),
    ] = None,
    q: Annotated[str | None, Query(description="Búsqueda full-text en español.")] = None,
    limite: Annotated[int, Query(le=200)] = 50,
):
    paciente = await obtener_paciente_propio(sesion_db, paciente_id, terapeuta)

    consulta = select(Sesion).where(Sesion.paciente_id == paciente.id)

    if tags:
        slugs = [slug for slug in (slugificar(tag) for tag in tags) if slug]
        if slugs:
            # `&&` = "los arrays se solapan". Usa ix_sesiones_tags (GIN).
            consulta = consulta.where(col(Sesion.tags).op("&&")(cast(slugs, ARRAY(Text))))

    if q and q.strip():
        consulta = consulta.where(_FILTRO_FTS.bindparams(consulta_fts=q.strip()))

    consulta = consulta.order_by(col(Sesion.fecha_sesion).desc()).limit(limite)
    resultado = await sesion_db.exec(consulta)
    return list(resultado.all())


@router.get("/{paciente_id}/tags", response_model=list[TagConteo])
async def nube_de_tags(paciente_id: uuid.UUID, sesion_db: SesionDB, terapeuta: TerapeutaActual):
    """Tags del paciente con su frecuencia — alimenta el filtro del historial."""
    paciente = await obtener_paciente_propio(sesion_db, paciente_id, terapeuta)

    # `unnest` es una set-returning function y Postgres la expande DESPUÉS del
    # GROUP BY, así que agrupar sobre su alias directamente falla con
    # "set-returning functions are not allowed in GROUP BY". Hay que
    # materializarla en una subconsulta y recién ahí agrupar.
    expandidos = (
        select(func.unnest(Sesion.tags).label("tag"))
        .where(Sesion.paciente_id == paciente.id)
        .subquery()
    )
    resultado = await sesion_db.exec(
        select(expandidos.c.tag, func.count().label("cantidad"))
        .group_by(expandidos.c.tag)
        .order_by(func.count().desc(), expandidos.c.tag)
    )
    return [TagConteo(tag=fila[0], cantidad=fila[1]) for fila in resultado.all()]


@router.get("/{paciente_id}/genograma", response_model=GenogramaRespuesta)
async def obtener_genograma(
    paciente_id: uuid.UUID, sesion_db: SesionDB, terapeuta: TerapeutaActual
):
    """Grafo completo en dos queries — por eso `conexiones` lleva `paciente_id`."""
    paciente = await obtener_paciente_propio(sesion_db, paciente_id, terapeuta)

    nodos = await sesion_db.exec(
        select(NodoGenograma).where(NodoGenograma.paciente_id == paciente.id)
    )
    conexiones = await sesion_db.exec(
        select(ConexionGenograma).where(ConexionGenograma.paciente_id == paciente.id)
    )
    return GenogramaRespuesta(
        paciente_id=paciente.id,
        nodos=[NodoRespuesta.model_validate(nodo) for nodo in nodos.all()],
        conexiones=[ConexionRespuesta.model_validate(c) for c in conexiones.all()],
    )


@router.get("/{paciente_id}/recordatorios", response_model=list[RecordatorioRespuesta])
async def listar_recordatorios(
    paciente_id: uuid.UUID,
    sesion_db: SesionDB,
    terapeuta: TerapeutaActual,
    solo_pendientes: bool = True,
):
    paciente = await obtener_paciente_propio(sesion_db, paciente_id, terapeuta)
    consulta = select(Recordatorio).where(Recordatorio.paciente_id == paciente.id)
    if solo_pendientes:
        # Pega en ix_recordatorios_pendientes (índice parcial).
        consulta = consulta.where(col(Recordatorio.resuelto).is_(False))
    resultado = await sesion_db.exec(consulta.order_by(col(Recordatorio.created_at).desc()))
    return list(resultado.all())
