"""Tests de las piezas que sostienen el contrato con el proveedor de IA."""

import json

import pytest

from app.services.ia.gemini import ESQUEMA_SALIDA
from app.utils import normalizar_etiqueta, slugificar


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("#Ansiedad", "ansiedad"),
        ("Familia de Origen", "familia-de-origen"),
        ("  #DUELO  ", "duelo"),
        ("Relación de pareja", "relacion-de-pareja"),
        ("sueño", "sueno"),
        ("---", ""),
    ],
)
def test_slugificar(entrada: str, esperado: str):
    assert slugificar(entrada) == esperado


def test_normalizar_etiqueta_unifica_variantes():
    """Las tres formas tienen que resolver al mismo nodo del genograma."""
    assert normalizar_etiqueta("Mamá") == normalizar_etiqueta("mama")
    assert normalizar_etiqueta("Mamá") == normalizar_etiqueta(" MAMÁ ")


def test_el_schema_para_el_modelo_no_tiene_referencias():
    """Los `$ref`/`$defs` de Pydantic tienen que quedar inlineados.

    El soporte de referencias en los structured outputs de los proveedores es
    irregular; si esto se rompe, Gemini empieza a devolver JSON que no valida.
    """
    serializado = json.dumps(ESQUEMA_SALIDA)
    assert "$ref" not in serializado
    assert "$defs" not in serializado


def test_el_schema_conserva_los_campos_del_dominio():
    propiedades = ESQUEMA_SALIDA["properties"]
    assert {
        "resumen_clinico",
        "tags",
        "entidades",
        "alertas_proxima_sesion",
        "estado_emocional_percibido",
    } <= set(propiedades)

    # Los enums tienen que llegar como lista de valores, no como referencia.
    rol = propiedades["entidades"]["items"]["properties"]["rol"]
    assert "madre" in rol["enum"]


def test_ningun_campo_del_schema_es_nullable():
    """`anyOf: [x, null]` rompe el structured output de varios proveedores.

    Por eso `SalidaIA` usa centinelas (`""`, `OTRO`, `NEUTRAL`) en lugar de
    opcionales, y la conversión a `None` se hace del lado nuestro.
    """
    assert "null" not in json.dumps(ESQUEMA_SALIDA)
