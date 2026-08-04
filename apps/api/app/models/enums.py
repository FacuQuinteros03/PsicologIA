"""Enums del dominio clínico.

Todos son `StrEnum`. El **valor** en minúscula es lo que viaja por la API y lo
que se persiste en la base (ver `tipo_enum()` en `base.py`).
"""

from enum import StrEnum


class EstadoPaciente(StrEnum):
    ACTIVO = "activo"
    PAUSA = "pausa"
    ALTA = "alta"
    ARCHIVADO = "archivado"


class EstadoIA(StrEnum):
    """Ciclo de vida del procesamiento IA de una sesión."""

    PENDIENTE = "pendiente"
    PROCESANDO = "procesando"
    COMPLETADO = "completado"
    ERROR = "error"


class Prioridad(StrEnum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"


class RolNodo(StrEnum):
    """Rol de la persona en la red vincular del paciente."""

    INDICE = "indice"  # el paciente mismo
    MADRE = "madre"
    PADRE = "padre"
    HERMANO = "hermano"
    PAREJA = "pareja"
    HIJO = "hijo"
    ABUELO = "abuelo"
    TIO = "tio"
    AMIGO = "amigo"
    LABORAL = "laboral"
    TERAPEUTA = "terapeuta"
    OTRO = "otro"


class Genero(StrEnum):
    """Define la forma del nodo en el genograma (cuadrado / círculo / hexágono)."""

    FEMENINO = "femenino"
    MASCULINO = "masculino"
    NO_BINARIO = "no_binario"
    DESCONOCIDO = "desconocido"


class TipoVinculo(StrEnum):
    """Naturaleza estructural del vínculo: qué es esa persona respecto de la otra."""

    FILIAL = "filial"  # hijo -> padre/madre
    PARENTAL = "parental"  # padre/madre -> hijo
    PAREJA = "pareja"
    MATRIMONIO = "matrimonio"
    SEPARACION = "separacion"
    DIVORCIO = "divorcio"
    HERMANO = "hermano"
    AMISTAD = "amistad"
    LABORAL = "laboral"
    OTRO = "otro"


class CalidadVinculo(StrEnum):
    """Carga emocional del vínculo: define el estilo visual del edge.

    Es la capa clínicamente rica del genograma — un vínculo `filial` puede ser
    `fusionado` o `roto`, y esa diferencia es la que importa en la sesión.
    """

    CERCANO = "cercano"
    DISTANTE = "distante"
    CONFLICTIVO = "conflictivo"
    FUSIONADO = "fusionado"
    ROTO = "roto"
    AMBIVALENTE = "ambivalente"
    NEUTRAL = "neutral"
