"""Helpers sin dependencias del dominio."""

import re
import unicodedata

_NO_ALFANUM = re.compile(r"[^a-z0-9]+")


def slugificar(texto: str) -> str:
    """Normaliza una etiqueta a slug ASCII.

    `"#Ansiedad Laboral"` -> `"ansiedad-laboral"`, `"Familia de Origen"` ->
    `"familia-de-origen"`. Se aplica a todo tag venga de donde venga (IA o
    usuario) para que el filtro por `tags && ARRAY[...]` no falle por tildes,
    mayúsculas o un `#` de más.
    """
    sin_tildes = "".join(
        caracter
        for caracter in unicodedata.normalize("NFD", texto.strip().lstrip("#"))
        if unicodedata.category(caracter) != "Mn"
    )
    return _NO_ALFANUM.sub("-", sin_tildes.lower()).strip("-")


def normalizar_etiqueta(texto: str) -> str:
    """Clave de comparación para las etiquetas de nodo del genograma.

    `"Mamá"`, `"mama"` y `" MAMÁ "` tienen que resolver al mismo nodo cuando la
    IA extrae entidades, sin que por eso se pierda el casing original que ve el
    terapeuta en el canvas.
    """
    sin_tildes = "".join(
        caracter
        for caracter in unicodedata.normalize("NFD", texto.strip())
        if unicodedata.category(caracter) != "Mn"
    )
    return " ".join(sin_tildes.lower().split())
