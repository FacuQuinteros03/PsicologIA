# PsicoIA — Copiloto Terapéutico

SaaS de gestión clínica para psicólogos y terapeutas. A diferencia de una agenda,
opera **dentro de la sesión**: el terapeuta escribe bullets crudos, la IA los
convierte en resumen clínico + tags + entidades + alertas, y esas entidades
alimentan un **genograma interactivo** donde tocar un nodo ("Mamá") filtra todo el
historial asociado.

## Stack

| Capa | Tecnología |
|---|---|
| Frontend | Next.js 16 (App Router) · React 19 · CSS Modules · `@xyflow/react` 12 |
| Backend | FastAPI · SQLModel · Alembic · Pydantic v2 |
| Base de datos | PostgreSQL (Neon / Supabase) vía psycopg 3 async |
| IA | Gemini (`google-genai`), con proveedor `mock` sin red como fallback |

## Estructura

```
PsicoIA/
├─ apps/
│  ├─ api/     FastAPI + SQLModel + Alembic
│  └─ web/     Next.js
└─ docs/
   └─ modelo-datos.md
```

## Puesta en marcha — backend

Requiere **Docker Desktop** (para la base) y Python 3.11+.

**1. Levantar Postgres** (queda en el puerto **5433** del host, para no chocar con
un Postgres nativo si alguna vez instalás uno):

```bash
docker compose up -d
```

**2. Instalar dependencias:**

```bash
cd apps/api && python -m venv .venv && .venv/Scripts/python -m pip install -e ".[dev]"
```

**3. Config:** copiar `apps/api/.env.example` a `apps/api/.env`. Los valores por
defecto ya apuntan al Postgres de Docker. `GEMINI_API_KEY` es opcional — sin ella
el sistema usa el proveedor `mock` y todo funciona igual, sin salir a la red.

**4. Migrar y sembrar datos demo:**

```bash
cd apps/api && .venv/Scripts/alembic upgrade head && .venv/Scripts/python -m app.seed
```

**5. Verificar que todo el backend funciona de punta a punta:**

```bash
cd apps/api && .venv/Scripts/python scripts/verificar_backend.py
```

Ejercita el esquema, el procesamiento de notas, la persistencia, el upsert del
genograma, los filtros por tag, la búsqueda full-text y el aislamiento
multi-tenant. Si algo está roto, lo dice con nombre y apellido.

**6. Levantar la API:**

```bash
cd apps/api && .venv/Scripts/uvicorn app.main:app --reload --port 8000 --loop asyncio:SelectorEventLoop
```

Docs interactivas en <http://localhost:8000/docs>.

> **El flag `--loop` es obligatorio en Windows.** psycopg 3 async no funciona
> sobre `ProactorEventLoop`, que es el default de asyncio en Windows y el que
> elige uvicorn. Sin el flag, cualquier request que toque la base falla con
> `Psycopg cannot use the 'ProactorEventLoop'`. Ojo con el formato: uvicorn pide
> `módulo:atributo`, no `asyncio.SelectorEventLoop`. En Linux el flag es inocuo.
> Para los scripts (migraciones, seed, verificador) esto ya está resuelto en
> `app/core/loop.py`.

### Pasar a una base gestionada

`app/core/config.py` normaliza el driver a psycopg 3, así que alcanza con pegar el
connection string tal cual lo entregue el proveedor (`postgresql://...?sslmode=require`)
en `DATABASE_URL`. No hay que tocar nada más: los prepared statements ya vienen
desactivados para que funcione detrás de un pooler.

## Comandos útiles

Ver el SQL de las migraciones sin tocar la base:

```bash
cd apps/api && .venv/Scripts/alembic upgrade head --sql
```

Generar una migración nueva después de cambiar los modelos:

```bash
cd apps/api && .venv/Scripts/alembic revision --autogenerate -m "descripcion del cambio"
```

Lint:

```bash
cd apps/api && .venv/Scripts/ruff check app alembic
```

## Datos clínicos

Son datos de salud. Reglas que aplican desde el día uno:

- `.env` nunca se commitea (está en `.gitignore`), y `alembic.ini` no lleva la URL.
- No se loguean `notas_borrador` ni `resumen_ia`: los logs sólo llevan IDs.
  Por eso `DB_ECHO` viene en `false` — el echo de SQL imprimiría las notas.
- `notas_borrador` es la fuente de verdad y el reprocesado de IA nunca la pisa.
- `ia_payload` guarda la respuesta cruda del modelo para poder auditar qué generó.

**Deuda explícita del MVP:** no hay cifrado a nivel campo ni auditoría de accesos.
