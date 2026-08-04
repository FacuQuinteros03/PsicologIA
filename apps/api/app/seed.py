"""Datos de demo. Idempotente: se puede correr las veces que haga falta.

    python -m app.seed

Los IDs son fijos a propósito para que la URL del genograma en el frontend
(`/pacientes/<id>/genograma`) no cambie entre reseteos de la base.
"""

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

from sqlmodel import select

from app.core.database import AsyncSessionLocal, engine
from app.core.loop import configurar_event_loop
from app.models import (
    CalidadVinculo,
    ConexionGenograma,
    EstadoIA,
    Genero,
    NodoGenograma,
    Paciente,
    Prioridad,
    Recordatorio,
    RolNodo,
    Sesion,
    SesionNodoLink,
    Terapeuta,
    TipoVinculo,
)

TERAPEUTA_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")
PACIENTE_ID = uuid.UUID("00000000-0000-4000-8000-000000000002")

NODO_INDICE_ID = uuid.UUID("00000000-0000-4000-8000-000000000010")
NODO_MADRE_ID = uuid.UUID("00000000-0000-4000-8000-000000000011")
NODO_PADRE_ID = uuid.UUID("00000000-0000-4000-8000-000000000012")

SESION_PROCESADA_ID = uuid.UUID("00000000-0000-4000-8000-000000000020")
SESION_PENDIENTE_ID = uuid.UUID("00000000-0000-4000-8000-000000000021")


async def sembrar() -> None:
    async with AsyncSessionLocal() as sesion_db:
        # --- Terapeuta y paciente ---
        if await sesion_db.get(Terapeuta, TERAPEUTA_ID) is None:
            sesion_db.add(
                Terapeuta(
                    id=TERAPEUTA_ID,
                    email="demo@psicoia.local",
                    nombre_completo="Lic. Demo",
                    matricula="MP-0000",
                )
            )

        if await sesion_db.get(Paciente, PACIENTE_ID) is None:
            sesion_db.add(
                Paciente(
                    id=PACIENTE_ID,
                    terapeuta_id=TERAPEUTA_ID,
                    nombre="Ana",
                    apellido="Demo",
                    motivo_consulta="Ansiedad laboral y conflictos con la familia de origen.",
                )
            )
        await sesion_db.commit()

        # --- Genograma inicial: los 3 nodos que renderiza el PoC del frontend ---
        nodos = [
            NodoGenograma(
                id=NODO_INDICE_ID,
                paciente_id=PACIENTE_ID,
                etiqueta="Ana",
                nombre="Ana Demo",
                rol=RolNodo.INDICE,
                genero=Genero.FEMENINO,
                es_indice=True,
                pos_x=140.0,
                pos_y=220.0,
            ),
            NodoGenograma(
                id=NODO_MADRE_ID,
                paciente_id=PACIENTE_ID,
                etiqueta="Mamá",
                rol=RolNodo.MADRE,
                genero=Genero.FEMENINO,
                pos_x=0.0,
                pos_y=0.0,
                notas="Vínculo muy demandante según el relato.",
            ),
            NodoGenograma(
                id=NODO_PADRE_ID,
                paciente_id=PACIENTE_ID,
                etiqueta="Papá",
                rol=RolNodo.PADRE,
                genero=Genero.MASCULINO,
                pos_x=300.0,
                pos_y=0.0,
            ),
        ]
        for nodo in nodos:
            if await sesion_db.get(NodoGenograma, nodo.id) is None:
                sesion_db.add(nodo)
        await sesion_db.commit()

        # --- Vínculos ---
        conexiones = [
            ConexionGenograma(
                paciente_id=PACIENTE_ID,
                origen_id=NODO_INDICE_ID,
                destino_id=NODO_MADRE_ID,
                tipo_vinculo=TipoVinculo.FILIAL,
                calidad_vinculo=CalidadVinculo.FUSIONADO,
            ),
            ConexionGenograma(
                paciente_id=PACIENTE_ID,
                origen_id=NODO_INDICE_ID,
                destino_id=NODO_PADRE_ID,
                tipo_vinculo=TipoVinculo.FILIAL,
                calidad_vinculo=CalidadVinculo.DISTANTE,
            ),
            ConexionGenograma(
                paciente_id=PACIENTE_ID,
                origen_id=NODO_MADRE_ID,
                destino_id=NODO_PADRE_ID,
                tipo_vinculo=TipoVinculo.MATRIMONIO,
                calidad_vinculo=CalidadVinculo.CONFLICTIVO,
            ),
        ]
        for conexion in conexiones:
            existente = await sesion_db.exec(
                select(ConexionGenograma).where(
                    ConexionGenograma.origen_id == conexion.origen_id,
                    ConexionGenograma.destino_id == conexion.destino_id,
                    ConexionGenograma.tipo_vinculo == conexion.tipo_vinculo,
                )
            )
            if existente.first() is None:
                sesion_db.add(conexion)
        await sesion_db.commit()

        # --- Sesión ya procesada: sirve para probar el filtro por tags y el
        #     panel de "sesiones donde aparece este nodo".
        if await sesion_db.get(Sesion, SESION_PROCESADA_ID) is None:
            procesada = Sesion(
                id=SESION_PROCESADA_ID,
                paciente_id=PACIENTE_ID,
                numero_sesion=1,
                fecha_sesion=datetime.now(UTC) - timedelta(days=7),
                notas_borrador=(
                    "- llegó angustiada, semana dura en el trabajo\n"
                    "- discusión fuerte con la mamá el domingo\n"
                    "- dice que el papá 'nunca se mete'\n"
                    "- duerme mal hace 3 semanas"
                ),
                resumen_ia=(
                    "La consultante refiere un incremento de la sintomatología ansiosa "
                    "asociada a sobrecarga laboral. Relata un episodio de conflicto con "
                    "su madre y describe una posición periférica de su padre frente a "
                    "los conflictos familiares. Reporta insomnio de conciliación de "
                    "aproximadamente tres semanas de evolución."
                ),
                tags=["ansiedad", "trabajo", "familia-de-origen", "sueño"],
                estado_emocional="angustia",
                ia_estado=EstadoIA.COMPLETADO,
                ia_modelo="seed",
                ia_procesado_at=datetime.now(UTC) - timedelta(days=7),
            )
            sesion_db.add(procesada)
            # Flush obligatorio antes de los links: `SesionNodoLink` no tiene
            # `Relationship` con `Sesion` (ver models/links.py), así que la unit
            # of work no conoce la dependencia y puede intentar insertar la fila
            # de `sesion_nodo` antes que la de `sesiones`.
            await sesion_db.flush()

            sesion_db.add(
                Recordatorio(
                    sesion_id=SESION_PROCESADA_ID,
                    paciente_id=PACIENTE_ID,
                    texto="Retomar el episodio con la madre y explorar el lugar del padre.",
                    prioridad=Prioridad.ALTA,
                )
            )
            sesion_db.add_all(
                [
                    SesionNodoLink(
                        sesion_id=SESION_PROCESADA_ID,
                        nodo_id=NODO_MADRE_ID,
                        menciones=2,
                        contexto="discusión fuerte con la mamá el domingo",
                    ),
                    SesionNodoLink(
                        sesion_id=SESION_PROCESADA_ID,
                        nodo_id=NODO_PADRE_ID,
                        menciones=1,
                        contexto="dice que el papá 'nunca se mete'",
                    ),
                ]
            )

        # --- Sesión sin procesar: la entrada para probar /procesar-notas ---
        if await sesion_db.get(Sesion, SESION_PENDIENTE_ID) is None:
            sesion_db.add(
                Sesion(
                    id=SESION_PENDIENTE_ID,
                    paciente_id=PACIENTE_ID,
                    numero_sesion=2,
                    notas_borrador=(
                        "- vino más tranquila\n"
                        "- habló del jefe nuevo, le genera presión\n"
                        "- llamó a la mamá, charla corta pero sin pelea\n"
                        "- pregunta si puede espaciar las sesiones"
                    ),
                    ia_estado=EstadoIA.PENDIENTE,
                )
            )

        await sesion_db.commit()

    await engine.dispose()

    print("Seed listo.")
    print(f"  terapeuta_id : {TERAPEUTA_ID}")
    print(f"  paciente_id  : {PACIENTE_ID}")
    print(f"  genograma    : /pacientes/{PACIENTE_ID}/genograma")


if __name__ == "__main__":
    configurar_event_loop()
    asyncio.run(sembrar())
