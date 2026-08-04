"""Lógica de sesiones: contexto para el modelo y persistencia del resultado."""

import uuid
from datetime import UTC, datetime

from sqlmodel import col, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import (
    ConexionGenograma,
    EstadoIA,
    NodoGenograma,
    Paciente,
    Recordatorio,
    Sesion,
    SesionNodoLink,
    TipoVinculo,
)
from app.schemas.ia import SalidaIA
from app.services.ia import ContextoPaciente
from app.utils import normalizar_etiqueta, slugificar

# Separación horizontal y vertical al ubicar nodos nuevos en el canvas.
_PASO_X = 200.0
_PASO_Y = 180.0


async def construir_contexto(sesion_db: AsyncSession, paciente: Paciente) -> ContextoPaciente:
    """Arma el contexto que se le pasa al modelo.

    Las `etiquetas_conocidas` son lo importante: sin ellas el modelo devuelve
    "mi madre" donde el genograma ya tiene "Mamá", y el upsert crea un duplicado.
    """
    nodos = await sesion_db.exec(
        select(NodoGenograma.etiqueta).where(NodoGenograma.paciente_id == paciente.id)
    )
    tags = await sesion_db.exec(
        select(func.unnest(Sesion.tags))
        .where(Sesion.paciente_id == paciente.id)
        .distinct()
        .limit(30)
    )
    return ContextoPaciente(
        nombre=paciente.nombre,
        motivo_consulta=paciente.motivo_consulta,
        etiquetas_conocidas=tuple(nodos.all()),
        tags_previos=tuple(tags.all()),
    )


async def persistir_resultado(
    sesion_db: AsyncSession,
    sesion: Sesion,
    paciente: Paciente,
    salida: SalidaIA,
    proveedor: str,
    modelo: str,
) -> None:
    """Escribe el resultado del procesamiento. No commitea: eso es del endpoint.

    Nunca toca `notas_borrador`: lo que escribió el terapeuta es la fuente de
    verdad y reprocesar la IA no puede pisarlo.
    """
    sesion.resumen_ia = salida.resumen_clinico
    sesion.tags = _normalizar_tags(salida)
    sesion.estado_emocional = salida.estado_emocional_percibido or None
    sesion.ia_estado = EstadoIA.COMPLETADO
    sesion.ia_modelo = f"{proveedor}:{modelo}"
    sesion.ia_procesado_at = datetime.now(UTC)
    sesion.ia_payload = salida.model_dump(mode="json")
    sesion_db.add(sesion)

    await _sincronizar_entidades(sesion_db, sesion, paciente, salida)
    await _crear_recordatorios(sesion_db, sesion, paciente, salida)


def marcar_error(sesion: Sesion, crudo: str | None) -> None:
    """Deja constancia del fallo en lugar de perderlo.

    Guardar la respuesta cruda permite ver después qué devolvió el modelo cuando
    no validó, sin tener que volver a pagar la llamada.
    """
    sesion.ia_estado = EstadoIA.ERROR
    sesion.ia_procesado_at = datetime.now(UTC)
    if crudo:
        sesion.ia_payload = {"error": "respuesta_invalida", "crudo": crudo[:10_000]}


def _normalizar_tags(salida: SalidaIA) -> list[str]:
    """Slugifica y deduplica preservando el orden por relevancia."""
    ordenados = sorted(salida.tags, key=lambda t: t.relevancia, reverse=True)
    vistos: list[str] = []
    for tag in ordenados:
        slug = slugificar(tag.tag)
        if slug and slug not in vistos:
            vistos.append(slug)
    return vistos


async def _sincronizar_entidades(
    sesion_db: AsyncSession, sesion: Sesion, paciente: Paciente, salida: SalidaIA
) -> None:
    """Upsert de nodos por etiqueta + vínculo sesión↔nodo + conexión al índice."""
    resultado = await sesion_db.exec(
        select(NodoGenograma).where(NodoGenograma.paciente_id == paciente.id)
    )
    existentes = list(resultado.all())
    por_clave = {normalizar_etiqueta(nodo.etiqueta): nodo for nodo in existentes}
    indice = next((nodo for nodo in existentes if nodo.es_indice), None)

    enlaces = await sesion_db.exec(
        select(SesionNodoLink).where(SesionNodoLink.sesion_id == sesion.id)
    )
    enlaces_por_nodo = {enlace.nodo_id: enlace for enlace in enlaces.all()}

    creados = 0
    for entidad in salida.entidades:
        clave = normalizar_etiqueta(entidad.etiqueta)
        if not clave:
            continue

        nodo = por_clave.get(clave)
        if nodo is None:
            nodo = NodoGenograma(
                paciente_id=paciente.id,
                etiqueta=entidad.etiqueta.strip(),
                nombre=entidad.nombre or None,
                rol=entidad.rol,
                genero=entidad.genero,
                pos_x=_PASO_X * creados,
                pos_y=_altura_libre(existentes),
            )
            sesion_db.add(nodo)
            # Necesitamos el id para las FK de abajo; el flush no cierra la transacción.
            await sesion_db.flush()
            por_clave[clave] = nodo
            existentes.append(nodo)
            creados += 1
        elif entidad.nombre and not nodo.nombre:
            # Sólo completamos huecos: no pisamos lo que el terapeuta haya editado.
            nodo.nombre = entidad.nombre
            sesion_db.add(nodo)

        enlace = enlaces_por_nodo.get(nodo.id)
        if enlace is None:
            sesion_db.add(
                SesionNodoLink(
                    sesion_id=sesion.id,
                    nodo_id=nodo.id,
                    menciones=1,
                    contexto=entidad.contexto or None,
                )
            )
        else:
            enlace.menciones += 1
            sesion_db.add(enlace)

        if indice is not None and nodo.id != indice.id:
            await _asegurar_conexion(sesion_db, paciente.id, indice.id, nodo.id, entidad)


async def _asegurar_conexion(
    sesion_db: AsyncSession,
    paciente_id: uuid.UUID,
    origen_id: uuid.UUID,
    destino_id: uuid.UUID,
    entidad,  # noqa: ANN001 — EntidadIA, sin import para no ciclar
) -> None:
    if entidad.vinculo_con_paciente == TipoVinculo.OTRO:
        return
    existente = await sesion_db.exec(
        select(ConexionGenograma).where(
            ConexionGenograma.origen_id == origen_id,
            ConexionGenograma.destino_id == destino_id,
            ConexionGenograma.tipo_vinculo == entidad.vinculo_con_paciente,
        )
    )
    if existente.first() is not None:
        return
    sesion_db.add(
        ConexionGenograma(
            paciente_id=paciente_id,
            origen_id=origen_id,
            destino_id=destino_id,
            tipo_vinculo=entidad.vinculo_con_paciente,
            calidad_vinculo=entidad.calidad_vinculo,
        )
    )


async def _crear_recordatorios(
    sesion_db: AsyncSession, sesion: Sesion, paciente: Paciente, salida: SalidaIA
) -> None:
    """Inserta las alertas nuevas.

    Compara por texto en lugar de borrar y reinsertar: reprocesar una sesión no
    puede hacer desaparecer un recordatorio que el terapeuta ya marcó resuelto.
    """
    previos = await sesion_db.exec(
        select(Recordatorio.texto).where(Recordatorio.sesion_id == sesion.id)
    )
    textos = set(previos.all())

    for alerta in salida.alertas_proxima_sesion:
        texto = alerta.texto.strip()
        if not texto or texto in textos:
            continue
        textos.add(texto)
        sesion_db.add(
            Recordatorio(
                sesion_id=sesion.id,
                paciente_id=paciente.id,
                texto=texto,
                prioridad=alerta.prioridad,
            )
        )


def _altura_libre(existentes: list[NodoGenograma]) -> float:
    return max((nodo.pos_y for nodo in existentes), default=0.0) + _PASO_Y


async def sesiones_de_nodo(
    sesion_db: AsyncSession, nodo_id: uuid.UUID
) -> list[tuple[Sesion, SesionNodoLink]]:
    """El query del feature estrella: tocar un nodo y ver dónde aparece."""
    resultado = await sesion_db.exec(
        select(Sesion, SesionNodoLink)
        .join(SesionNodoLink, col(SesionNodoLink.sesion_id) == col(Sesion.id))
        .where(SesionNodoLink.nodo_id == nodo_id)
        .order_by(col(Sesion.fecha_sesion).desc())
    )
    return list(resultado.all())
