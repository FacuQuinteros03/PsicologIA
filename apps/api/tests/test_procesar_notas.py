"""Contrato del endpoint de procesamiento de notas, contra el proveedor mock."""

from httpx import AsyncClient

URL = "/api/v1/sesiones/procesar-notas"

NOTAS = """\
- llegó angustiada, semana dura en el trabajo
- discusión fuerte con la mamá el domingo
- dice que el papá nunca se mete
- duerme mal hace 3 semanas
- preguntar la próxima cómo siguió lo del jefe
"""


async def test_devuelve_la_estructura_completa(cliente: AsyncClient):
    respuesta = await cliente.post(URL, json={"notas": NOTAS})
    assert respuesta.status_code == 200, respuesta.text

    cuerpo = respuesta.json()
    assert cuerpo["proveedor"] == "mock"
    assert cuerpo["persistido"] is False
    assert cuerpo["sesion_id"] is None
    assert cuerpo["resumen_clinico"]
    for clave in ("tags", "entidades", "alertas_proxima_sesion", "temas_principales"):
        assert isinstance(cuerpo[clave], list)


async def test_detecta_los_temas_de_las_notas(cliente: AsyncClient):
    cuerpo = (await cliente.post(URL, json={"notas": NOTAS})).json()
    tags = {tag["tag"] for tag in cuerpo["tags"]}
    assert {"ansiedad", "trabajo", "familia-de-origen", "sueño"} <= tags


async def test_extrae_las_personas_con_su_vinculo(cliente: AsyncClient):
    cuerpo = (await cliente.post(URL, json={"notas": NOTAS})).json()
    entidades = {e["etiqueta"]: e for e in cuerpo["entidades"]}

    assert {"Mamá", "Papá", "Jefe"} <= set(entidades)
    assert entidades["Mamá"]["rol"] == "madre"
    assert entidades["Mamá"]["vinculo_con_paciente"] == "filial"
    # "discusión fuerte" tiene que leerse como vínculo conflictivo.
    assert entidades["Mamá"]["calidad_vinculo"] == "conflictivo"
    # "nunca se mete" tiene que leerse como distancia.
    assert entidades["Papá"]["calidad_vinculo"] == "distante"


async def test_genera_alertas_para_la_proxima_sesion(cliente: AsyncClient):
    cuerpo = (await cliente.post(URL, json={"notas": NOTAS})).json()
    alertas = cuerpo["alertas_proxima_sesion"]
    assert alertas
    assert any("jefe" in alerta["texto"].lower() for alerta in alertas)


async def test_rechaza_notas_demasiado_cortas(cliente: AsyncClient):
    respuesta = await cliente.post(URL, json={"notas": "corto"})
    assert respuesta.status_code == 422


async def test_persistir_exige_sesion_id(cliente: AsyncClient):
    respuesta = await cliente.post(URL, json={"notas": NOTAS, "persistir": True})
    assert respuesta.status_code == 422
    assert "sesion_id" in respuesta.text


async def test_health_reporta_el_proveedor(cliente: AsyncClient):
    cuerpo = (await cliente.get("/health")).json()
    assert cuerpo["status"] == "ok"
    assert cuerpo["proveedor_ia"] == "mock"
