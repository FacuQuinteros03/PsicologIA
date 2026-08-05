"""Verificación end-to-end del backend contra la base real.

    python verificar_backend.py

Levanta la app en proceso (no hace falta uvicorn) y ejercita el flujo completo:
esquema, seed, procesamiento de notas, persistencia, upsert del genograma,
filtros por tag, búsqueda full-text y aislamiento multi-tenant.

Requiere `docker compose up -d` + `alembic upgrade head` + `python -m app.seed`.
"""

import asyncio
import sys
import uuid

from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.core.config import settings
from app.core.database import AsyncSessionLocal, engine
from app.core.loop import configurar_event_loop
from app.main import app

# Cuando la salida no es una terminal —una tubería, un redirect a archivo, el
# panel de tareas— Python en Windows deja de usar UTF-8 y cae a cp1252, que no
# sabe codificar los acentos ni el '↔' de los títulos. El script moría con
# UnicodeEncodeError a mitad de camino y sin haber fallado ningún check.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

TABLAS_ESPERADAS = {
    "terapeutas",
    "pacientes",
    "sesiones",
    "recordatorios",
    "nodos_genograma",
    "conexiones_genograma",
    "sesion_nodo",
}

INDICES_ESPERADOS = {
    "ix_sesiones_paciente_fecha",
    "ix_sesiones_tags",
    "ix_sesiones_fts",
    "ix_recordatorios_pendientes",
    "ix_sesion_nodo_nodo_id",
    "uq_nodo_paciente_etiqueta",
}

NOTAS = """\
- llegó angustiada, semana dura en el trabajo
- discusión fuerte con la mamá el domingo
- dice que el papá nunca se mete
- duerme mal hace 3 semanas
- preguntar la próxima cómo siguió lo del jefe
"""

fallos: list[str] = []
paso = 0


def check(condicion: bool, titulo: str, detalle: str = "") -> bool:
    global paso
    paso += 1
    marca = "OK  " if condicion else "FALLA"
    print(f"  [{marca}] {paso:2}. {titulo}")
    if detalle:
        print(f"              {detalle}")
    if not condicion:
        fallos.append(titulo)
    return condicion


async def main() -> int:
    print(f"\nBase: {settings.database_url.split('@')[-1]}")
    print(f"Proveedor IA: {settings.proveedor_ia_efectivo}\n")

    # ---------- Esquema ----------
    print("ESQUEMA")
    async with AsyncSessionLocal() as db:
        version = (await db.exec(text("SHOW server_version"))).scalar()  # type: ignore[attr-defined]
        check(True, "Conexión establecida", f"PostgreSQL {version}")

        filas = await db.exec(
            text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")  # type: ignore[arg-type]
        )
        tablas = {fila[0] for fila in filas}
        faltantes = TABLAS_ESPERADAS - tablas
        check(not faltantes, "Las 7 tablas existen", f"faltan: {faltantes}" if faltantes else "")

        filas = await db.exec(
            text("SELECT indexname FROM pg_indexes WHERE schemaname = 'public'")  # type: ignore[arg-type]
        )
        indices = {fila[0] for fila in filas}
        faltan_idx = INDICES_ESPERADOS - indices
        check(
            not faltan_idx,
            "Índices críticos creados",
            f"faltan: {faltan_idx}" if faltan_idx else "GIN de tags, FTS y parcial de recordatorios",
        )

        # Los bind params van como objetos `uuid.UUID`, no como str: contra una
        # columna `uuid` psycopg tiparía el string como VARCHAR y Postgres
        # rechaza la comparación con "operator does not exist: uuid = varchar".
        terapeuta = (
            await db.exec(
                text("SELECT id FROM terapeutas WHERE id = :i").bindparams(  # type: ignore[arg-type]
                    i=settings.terapeuta_seed_id
                )
            )
        ).first()
        if not check(
            terapeuta is not None,
            "Seed aplicado",
            "" if terapeuta is not None else "falta correr `python -m app.seed`",
        ):
            return 1

        paciente_id = (
            await db.exec(
                text("SELECT id FROM pacientes ORDER BY created_at LIMIT 1")  # type: ignore[arg-type]
            )
        ).scalar()

    transporte = ASGITransport(app=app)
    async with AsyncClient(transport=transporte, base_url="http://test", timeout=60) as cli:
        # ---------- Procesamiento sin persistir ----------
        print("\nPROCESAMIENTO DE NOTAS")
        r = await cli.post("/api/v1/sesiones/procesar-notas", json={"notas": NOTAS})
        ok = r.status_code == 200
        cuerpo = r.json() if ok else {}
        check(ok, "POST /procesar-notas (stateless)", f"HTTP {r.status_code}")
        check(bool(cuerpo.get("resumen_clinico")), "Devuelve resumen clínico")
        check(len(cuerpo.get("tags", [])) >= 3, "Devuelve tags", str([t["tag"] for t in cuerpo.get("tags", [])]))
        check(len(cuerpo.get("entidades", [])) >= 3, "Detecta personas",
              str([e["etiqueta"] for e in cuerpo.get("entidades", [])]))
        check(cuerpo.get("persistido") is False, "No persistió (era stateless)")

        # ---------- Persistencia ----------
        print("\nPERSISTENCIA Y UPSERT DEL GENOGRAMA")
        r = await cli.post("/api/v1/sesiones", json={"paciente_id": str(paciente_id),
                                                    "notas_borrador": NOTAS})
        if not check(r.status_code == 201, "POST /sesiones crea sesión", f"HTTP {r.status_code} {r.text[:120]}"):
            return 1
        sesion_id = r.json()["id"]
        sesion_uuid = uuid.UUID(sesion_id)

        async with AsyncSessionLocal() as db:
            nodos_antes = (await db.exec(
                text("SELECT count(*) FROM nodos_genograma WHERE paciente_id = :p").bindparams(p=paciente_id)  # type: ignore[arg-type]
            )).scalar()

        r = await cli.post("/api/v1/sesiones/procesar-notas",
                           json={"notas": NOTAS, "sesion_id": sesion_id, "persistir": True})
        check(r.status_code == 200 and r.json().get("persistido") is True,
              "POST /procesar-notas con persistir=true", f"HTTP {r.status_code}")

        async with AsyncSessionLocal() as db:
            nodos_despues = (await db.exec(
                text("SELECT count(*) FROM nodos_genograma WHERE paciente_id = :p").bindparams(p=paciente_id)  # type: ignore[arg-type]
            )).scalar()
            duplicadas = (await db.exec(
                text("SELECT count(*) FROM nodos_genograma "
                     "WHERE paciente_id = :p AND lower(etiqueta) = 'mamá'").bindparams(p=paciente_id)  # type: ignore[arg-type]
            )).scalar()
            enlaces = (await db.exec(
                text("SELECT count(*) FROM sesion_nodo WHERE sesion_id = :s").bindparams(s=sesion_uuid)  # type: ignore[arg-type]
            )).scalar()
            recordatorios = (await db.exec(
                text("SELECT count(*) FROM recordatorios WHERE sesion_id = :s").bindparams(s=sesion_uuid)  # type: ignore[arg-type]
            )).scalar()

        check(duplicadas == 1, "El upsert NO duplicó 'Mamá'",
              f"{duplicadas} fila(s); nodos {nodos_antes} -> {nodos_despues}")
        check(enlaces >= 3, "Creó los vínculos sesión↔nodo", f"{enlaces} filas en sesion_nodo")
        check(recordatorios >= 1, "Creó recordatorios", f"{recordatorios} alertas")

        # ---------- Consultas ----------
        print("\nCONSULTAS E ÍNDICES")
        r = await cli.get(f"/api/v1/pacientes/{paciente_id}/sesiones", params={"tags": ["ansiedad"]})
        check(r.status_code == 200 and len(r.json()) >= 1,
              "Filtro por tags (GIN, operador &&)", f"{len(r.json()) if r.status_code == 200 else '-'} sesiones")

        r = await cli.get(f"/api/v1/pacientes/{paciente_id}/sesiones", params={"q": "discusión madre"})
        check(r.status_code == 200 and len(r.json()) >= 1,
              "Búsqueda full-text en español", f"HTTP {r.status_code}, {len(r.json()) if r.status_code == 200 else '-'} resultados")

        r = await cli.get(f"/api/v1/pacientes/{paciente_id}/tags")
        check(r.status_code == 200 and len(r.json()) >= 1,
              "Nube de tags (unnest + group by)", f"HTTP {r.status_code} {r.text[:100]}")

        r = await cli.get(f"/api/v1/pacientes/{paciente_id}/genograma")
        genograma = r.json() if r.status_code == 200 else {}
        check(r.status_code == 200 and len(genograma.get("nodos", [])) >= 3,
              "GET genograma completo",
              f"{len(genograma.get('nodos', []))} nodos, {len(genograma.get('conexiones', []))} conexiones")

        # ---------- Feature estrella ----------
        print("\nFEATURE ESTRELLA")
        nodo_mama = next((n for n in genograma.get("nodos", []) if n["etiqueta"].lower() == "mamá"), None)
        if check(nodo_mama is not None, "Existe el nodo 'Mamá'"):
            r = await cli.get(f"/api/v1/genograma/nodos/{nodo_mama['id']}/sesiones")
            check(r.status_code == 200 and len(r.json()) >= 1,
                  "Tocar un nodo filtra su historial", f"{len(r.json()) if r.status_code == 200 else '-'} sesiones")

            r = await cli.patch(f"/api/v1/genograma/nodos/{nodo_mama['id']}/posicion",
                                json={"pos_x": 123.5, "pos_y": 456.5})
            check(r.status_code == 200 and r.json()["pos_x"] == 123.5,
                  "Persiste la posición del nodo (drag)")

        # ---------- CRUD de pacientes ----------
        print("\nCRUD DE PACIENTES")
        ficha = {
            "nombre": "Test", "apellido": "CRUD", "documento": "99887766",
            "fecha_nacimiento": "1990-05-20", "genero": "no_binario",
            "ocupacion": "Docente", "email": "test.crud@ejemplo.com",
            "telefono": "11 4444-0000", "contacto_emergencia": "Alguien",
            "telefono_emergencia": "11 4444-1111", "obra_social": "Swiss Medical",
            "numero_afiliado": "AB-999", "motivo_consulta": "Consulta de prueba.",
            "fecha_inicio": "2026-07-01",
            "modalidad": "virtual", "frecuencia": "quincenal",
            "honorarios": "18500.50", "notas_administrativas": "Nota administrativa.",
        }
        r = await cli.post("/api/v1/pacientes", json=ficha)
        creado = r.json() if r.status_code == 201 else {}
        if not check(r.status_code == 201, "POST crea con la ficha completa", f"HTTP {r.status_code} {r.text[:140]}"):
            return 1
        nuevo_id = creado["id"]

        faltantes = [c for c in ficha if creado.get(c) in (None, "")]
        # El total sale de `ficha` y no de un número escrito a mano: agregar o
        # sacar un campo de la admisión no deja el título del check mintiendo.
        check(not faltantes, f"Persiste los {len(ficha)} campos de la ficha",
              f"vacíos: {faltantes}" if faltantes else "ninguno vino vacío")
        check(creado.get("edad") == 36, "Calcula la edad desde la fecha de nacimiento",
              f"edad={creado.get('edad')}")

        # El documento es único por terapeuta.
        r = await cli.post("/api/v1/pacientes", json={**ficha, "nombre": "Otro"})
        check(r.status_code == 409, "Rechaza documento repetido con 409", f"HTTP {r.status_code}")

        # PATCH parcial: lo omitido no se toca.
        r = await cli.patch(f"/api/v1/pacientes/{nuevo_id}", json={"telefono": "11 0000-9999"})
        actualizado = r.json() if r.status_code == 200 else {}
        check(r.status_code == 200 and actualizado.get("telefono") == "11 0000-9999",
              "PATCH actualiza el campo enviado", f"HTTP {r.status_code}")
        check(actualizado.get("ocupacion") == "Docente" and actualizado.get("obra_social") == "Swiss Medical",
              "PATCH NO pisa los campos omitidos")

        # Enviar null sí borra: es la diferencia entre omitir y vaciar.
        r = await cli.patch(f"/api/v1/pacientes/{nuevo_id}", json={"ocupacion": None})
        check(r.status_code == 200 and r.json().get("ocupacion") is None,
              "PATCH con null vacía el campo")

        # Archivar = baja lógica. Sale del listado sin destruir nada.
        r = await cli.patch(f"/api/v1/pacientes/{nuevo_id}", json={"estado": "archivado"})
        check(r.status_code == 200 and r.json()["estado"] == "archivado", "PATCH archiva el paciente")

        r = await cli.get("/api/v1/pacientes")
        check(nuevo_id not in {p["id"] for p in r.json()}, "El archivado sale del listado por defecto")
        r = await cli.get("/api/v1/pacientes", params={"incluir_archivados": "true"})
        check(nuevo_id in {p["id"] for p in r.json()}, "Y reaparece con incluir_archivados=true")

        r = await cli.get("/api/v1/pacientes", params={"q": "99887766", "incluir_archivados": "true"})
        check(r.status_code == 200 and len(r.json()) == 1, "Busca por documento con ?q=")

        r = await cli.delete(f"/api/v1/pacientes/{nuevo_id}")
        check(r.status_code == 204, "DELETE elimina el paciente", f"HTTP {r.status_code}")
        r = await cli.get(f"/api/v1/pacientes/{nuevo_id}")
        check(r.status_code == 404, "El paciente borrado ya no existe")

        # ---------- Aislamiento multi-tenant ----------
        print("\nAISLAMIENTO MULTI-TENANT")
        otro_terapeuta, otro_paciente = uuid.uuid4(), uuid.uuid4()
        async with AsyncSessionLocal() as db:
            await db.exec(text(  # type: ignore[arg-type]
                "INSERT INTO terapeutas (id, email, nombre_completo) "
                "VALUES (:i, :e, 'Intruso')").bindparams(i=otro_terapeuta, e=f"{otro_terapeuta}@x.test"))
            await db.exec(text(  # type: ignore[arg-type]
                "INSERT INTO pacientes (id, terapeuta_id, nombre, apellido, estado) "
                "VALUES (:p, :t, 'Ajeno', 'Ajeno', 'activo')").bindparams(
                    p=otro_paciente, t=otro_terapeuta))
            await db.commit()

        r = await cli.get(f"/api/v1/pacientes/{otro_paciente}")
        check(r.status_code == 404, "Paciente de otro terapeuta devuelve 404", f"HTTP {r.status_code}")

        r = await cli.get("/api/v1/pacientes")
        ids = {p["id"] for p in r.json()} if r.status_code == 200 else set()
        check(str(otro_paciente) not in ids, "El listado no filtra pacientes ajenos")

        async with AsyncSessionLocal() as db:
            await db.exec(text("DELETE FROM terapeutas WHERE id = :i").bindparams(i=otro_terapeuta))  # type: ignore[arg-type]
            await db.commit()

        # ---------- Limpieza ----------
        async with AsyncSessionLocal() as db:
            await db.exec(text("DELETE FROM sesiones WHERE id = :s").bindparams(s=sesion_uuid))  # type: ignore[arg-type]
            await db.commit()

    await engine.dispose()

    print("\n" + "=" * 62)
    if fallos:
        print(f"  {len(fallos)} verificación(es) FALLARON:")
        for fallo in fallos:
            print(f"    - {fallo}")
        return 1
    print(f"  Backend verificado: {paso}/{paso} checks OK.")
    return 0


if __name__ == "__main__":
    configurar_event_loop()
    sys.exit(asyncio.run(main()))
