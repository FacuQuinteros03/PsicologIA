"""Endpoints de recordatorios que se direccionan por su propio id.

El alta vive en `pacientes.py` porque cuelga de `/pacientes/{id}/recordatorios`;
acá están los que operan sobre uno ya existente.
"""

import uuid

from fastapi import APIRouter, Response, status

from app.core.deps import SesionDB, TerapeutaActual, obtener_recordatorio_propio
from app.models.base import ahora_utc
from app.schemas.paciente import RecordatorioActualizar, RecordatorioRespuesta

router = APIRouter(prefix="/recordatorios", tags=["recordatorios"])


@router.patch("/{recordatorio_id}", response_model=RecordatorioRespuesta)
async def actualizar_recordatorio(
    recordatorio_id: uuid.UUID,
    datos: RecordatorioActualizar,
    sesion_db: SesionDB,
    terapeuta: TerapeutaActual,
):
    """Marca resuelto, o corrige el texto y la prioridad.

    `resuelto_at` no se recibe del cliente: lo pone el servidor al cambiar el
    estado. Que el frontend mande la hora significaría confiar en el reloj del
    navegador, y ese dato después se lee como parte de la historia clínica.

    Desmarcar un recordatorio lo vuelve a dejar sin fecha, en vez de conservar la
    del cierre anterior: si vuelve a estar pendiente, la fecha vieja miente.
    """
    recordatorio = await obtener_recordatorio_propio(sesion_db, recordatorio_id, terapeuta)

    cambios = datos.model_dump(exclude_unset=True)
    if "resuelto" in cambios and cambios["resuelto"] != recordatorio.resuelto:
        recordatorio.resuelto_at = ahora_utc() if cambios["resuelto"] else None

    for campo, valor in cambios.items():
        setattr(recordatorio, campo, valor)

    sesion_db.add(recordatorio)
    await sesion_db.commit()
    await sesion_db.refresh(recordatorio)
    return recordatorio


@router.delete("/{recordatorio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_recordatorio(
    recordatorio_id: uuid.UUID,
    sesion_db: SesionDB,
    terapeuta: TerapeutaActual,
):
    """Borra el recordatorio.

    Acá sí se borra de verdad, a diferencia de un paciente: un recordatorio mal
    inferido por la IA es ruido, no historia clínica. Para los que sí se
    cumplieron, el camino es `PATCH {"resuelto": true}`, que los conserva.
    """
    recordatorio = await obtener_recordatorio_propio(sesion_db, recordatorio_id, terapeuta)
    await sesion_db.delete(recordatorio)
    await sesion_db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
