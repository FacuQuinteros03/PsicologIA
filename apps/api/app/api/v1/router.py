"""Router de la v1 de la API."""

from fastapi import APIRouter

from app.api.v1.endpoints import genograma, pacientes, sesiones

router = APIRouter()
router.include_router(pacientes.router)
router.include_router(sesiones.router)
router.include_router(genograma.router)
