"""Compatibilidad del event loop en Windows.

psycopg 3 en modo async **no funciona sobre `ProactorEventLoop`**, que es el
event loop por defecto de asyncio en Windows desde Python 3.8. Cualquier intento
de conectar falla con:

    psycopg.InterfaceError: Psycopg cannot use the 'ProactorEventLoop'
    to run in async mode.

La política hay que fijarla **antes** de que se cree el loop, así que esto se
llama al principio de cada entry point (migraciones, seed, scripts, tests).

Para el servidor no alcanza con esto: uvicorn 0.36+ ya no usa políticas sino un
`loop_factory` propio. Ahí la solución es el flag `--loop asyncio.SelectorEventLoop`
(ver README). En Linux no aplica nada de esto: el default ya es un loop compatible.
"""

import asyncio
import sys


def configurar_event_loop() -> None:
    """Fuerza el selector loop en Windows. No-op en el resto de las plataformas."""
    if sys.platform != "win32":
        return
    politica = getattr(asyncio, "WindowsSelectorEventLoopPolicy", None)
    if politica is not None:
        asyncio.set_event_loop_policy(politica())
