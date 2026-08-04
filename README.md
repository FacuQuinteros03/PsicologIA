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

## Seguridad

Esto maneja datos de salud. Las reglas no son negociables.

### Credenciales

**Ninguna API key entra al repositorio, en ningún formato.** Van únicamente en
`apps/api/.env`, que está en `.gitignore`. Tampoco en comentarios, ni en tests,
ni en un archivo "temporal".

Instalá el hook que lo verifica antes de cada commit:

```bash
cp scripts/pre-commit .git/hooks/pre-commit
```

Y para auditar el historial completo en cualquier momento:

```bash
python scripts/escanear_secretos.py
```

Si alguna vez se filtra una key, **revocala en la consola del proveedor**.
Borrar el commit no sirve: queda en los forks, en los mirrors y en los bots que
indexan GitHub en tiempo real, que la encuentran en minutos.

La contraseña del Postgres de desarrollo sí está a la vista en
`docker-compose.yml` y en `.env.example`. Es deliberado y no es un secreto: el
contenedor escucha **solo en `127.0.0.1`** y la base es descartable.

### Configuración

Los defaults de `Settings` son los más restrictivos (*fail closed*): sin `.env`,
la app arranca con `environment=production`, `debug=False` y `cors_origins=[]`.
En producción no se publican `/docs`, `/redoc` ni `/openapi.json` — le darían a
cualquiera el mapa completo de la API y los nombres de campo del historial
clínico.

El puerto de Postgres se publica como `127.0.0.1:5433:5432`. **Ese prefijo no es
decorativo**: sin él Docker lo abre en todas las interfaces, y una base expuesta
con credenciales conocidas es exactamente lo que buscan los bots que instalan
mineros.

### Datos clínicos

- No se loguean `notas_borrador` ni `resumen_ia`: los logs sólo llevan IDs. Por
  eso `DB_ECHO` viene en `false` — el echo de SQL imprimiría las notas.
- Los errores del proveedor de IA se loguean por tipo de excepción, nunca con el
  texto de las notas.
- `notas_borrador` es la fuente de verdad y el reprocesado de IA nunca la pisa.
- `ia_payload` guarda la respuesta cruda del modelo para poder auditar qué generó.
- Todo endpoint que recibe un `paciente_id` pasa por `obtener_paciente_propio()`,
  que verifica la pertenencia y devuelve **404 y no 403**, para no revelar que el
  paciente existe pero es de otra persona.

### Deuda explícita del MVP

Esto todavía **no está listo para producción**:

- **No hay autenticación.** `get_terapeuta_actual()` devuelve un terapeuta fijo.
  Cualquiera que llegue a la API ve esos datos. No desplegarlo en público hasta
  que haya login.
- Sin Row Level Security en Postgres: el aislamiento depende sólo de la capa de
  aplicación.
- Sin cifrado a nivel campo, sin auditoría de accesos y sin rate limiting.
