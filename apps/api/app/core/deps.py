"""Dependencias compartidas de FastAPI.

Acá vive el punto único donde se resuelve "de quién es esta request". Hoy está
mockeado contra el terapeuta seed, pero todos los endpoints ya lo consumen y ya
filtran por `terapeuta_id`: cuando entre el login sólo cambia el cuerpo de
`get_terapeuta_actual()`, ni la firma ni los llamadores.
"""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.database import get_session
from app.models import Paciente, Recordatorio, Terapeuta

SesionDB = Annotated[AsyncSession, Depends(get_session)]


async def get_terapeuta_actual(sesion: SesionDB) -> Terapeuta:
    """El terapeuta dueño de los datos de esta request.

    TODO(auth): reemplazar el cuerpo por la validación del JWT (leer el `sub`,
    buscar el terapeuta, 401 si no valida). Nada más necesita cambiar.
    """
    terapeuta = await sesion.get(Terapeuta, settings.terapeuta_seed_id)
    if terapeuta is None:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No existe el terapeuta seed. Corré `python -m app.seed`.",
        )
    return terapeuta


TerapeutaActual = Annotated[Terapeuta, Depends(get_terapeuta_actual)]


async def obtener_paciente_propio(
    sesion: AsyncSession, paciente_id: uuid.UUID, terapeuta: Terapeuta
) -> Paciente:
    """Trae un paciente **verificando que sea del terapeuta de la request**.

    Es el chokepoint del aislamiento multi-tenant: todo endpoint que reciba un
    `paciente_id` por la URL tiene que pasar por acá. Devuelve 404 —no 403— para
    no revelar que el paciente existe pero es de otra persona.
    """
    resultado = await sesion.exec(
        select(Paciente).where(
            Paciente.id == paciente_id,
            Paciente.terapeuta_id == terapeuta.id,
        )
    )
    paciente = resultado.first()
    if paciente is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Paciente no encontrado.")
    return paciente


async def obtener_recordatorio_propio(
    sesion: AsyncSession, recordatorio_id: uuid.UUID, terapeuta: Terapeuta
) -> Recordatorio:
    """Igual que `obtener_paciente_propio`, para los endpoints que se direccionan
    por el id del recordatorio y no por el del paciente.

    El join con `pacientes` es el que hace el trabajo: sin él bastaría conocer un
    UUID ajeno para marcar resuelto —o borrar— el recordatorio de un paciente de
    otro terapeuta. También devuelve 404 y no 403, por lo mismo de siempre.
    """
    resultado = await sesion.exec(
        select(Recordatorio)
        .join(Paciente, Paciente.id == Recordatorio.paciente_id)  # type: ignore[arg-type]
        .where(
            Recordatorio.id == recordatorio_id,
            Paciente.terapeuta_id == terapeuta.id,
        )
    )
    recordatorio = resultado.first()
    if recordatorio is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Recordatorio no encontrado.")
    return recordatorio
