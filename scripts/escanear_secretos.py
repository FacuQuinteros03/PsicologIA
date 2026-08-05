"""Detecta credenciales antes de que lleguen al repositorio.

    python scripts/escanear_secretos.py            # todo el historial de git
    python scripts/escanear_secretos.py --staged   # solo lo que está por commitear

Sale con código 1 si encuentra algo, para poder usarlo como hook de pre-commit
(ver README). Solo usa la librería estándar y `git`.

Por qué existe: una API key filtrada no se arregla borrando el commit. Queda en
los forks, en los mirrors y en los scrapers que indexan GitHub en tiempo real.
Lo único que sirve es revocarla. Este script busca que eso no haga falta.
"""

import argparse
import re
import subprocess
import sys

PATRONES: dict[str, bytes] = {
    "Google / Gemini API key": rb"AIza[0-9A-Za-z_\-]{35}",
    # AI Studio emite también keys con este prefijo, que no matchean el `AIza`
    # clásico. Sin esta línea, una key de Gemini pegada en un archivo trackeado
    # pasaba el hook sin que saltara nada.
    "Google AI Studio key": rb"AQ\.[A-Za-z0-9_\-]{30,}",
    "OpenAI API key": rb"sk-[A-Za-z0-9]{32,}",
    "Anthropic API key": rb"sk-ant-[A-Za-z0-9\-_]{20,}",
    "GitHub token": rb"gh[pousr]_[A-Za-z0-9]{36}",
    "Slack token": rb"xox[baprs]-[A-Za-z0-9\-]{10,}",
    "AWS access key": rb"AKIA[0-9A-Z]{16}",
    "Clave privada": rb"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "JSON Web Token": rb"eyJ[A-Za-z0-9_\-]{15,}\.eyJ[A-Za-z0-9_\-]{15,}",
    # Las comillas son OPCIONALES a propósito: en un `.env` los valores van sin
    # comillas (`GEMINI_API_KEY=xxxx`), y la versión anterior de este patrón las
    # exigía, así que se le escapaba justo el caso más probable.
    #
    # Pedir 20+ caracteres del charset de una credencial (sin espacios, sin
    # paréntesis) es lo que evita los falsos positivos: `key = os.getenv("X")`
    # corta en el paréntesis a los 9 caracteres y no llega al umbral.
    #
    # El punto queda FUERA del charset a propósito. Con punto, una lectura de
    # configuración como `api_key=settings.gemini_api_key` alcanzaba los 20
    # caracteres y se reportaba como credencial. Sin punto corta en `settings`
    # y no dispara. Las credenciales que sí llevan punto (las de AI Studio, los
    # JWT) tienen cada una su patrón propio más arriba.
    "Credencial asignada": (
        rb"(?i)(api[_-]?key|secret|token|passwd|password)\s*[=:]\s*"
        rb"['\"]?[A-Za-z0-9_\-]{20,}['\"]?"
    ),
}

# El Postgres de desarrollo vive en docker-compose y su contraseña está a la
# vista a propósito: el contenedor escucha solo en 127.0.0.1 y la base es
# descartable. Cualquier otra credencial embebida sí es un hallazgo.
EXCEPCIONES: set[str] = {
    "apps/api/.env.example",
    "docker-compose.yml",
    "scripts/escanear_secretos.py",
    "README.md",
}


def _git(*args: str) -> bytes:
    return subprocess.run(["git", *args], capture_output=True).stdout


def revisar(ruta: str, contenido: bytes) -> list[str]:
    if ruta in EXCEPCIONES:
        return []
    hallazgos = []
    for nombre, patron in PATRONES.items():
        encontrado = re.search(patron, contenido)
        if encontrado:
            muestra = encontrado.group(0)[:24].decode("utf-8", "replace")
            hallazgos.append(f"{nombre:24} en {ruta}  ({muestra}…)")
    return hallazgos


def escanear_staged() -> list[str]:
    """Revisa el contenido que está en el índice, no el del disco."""
    salida = _git("diff", "--cached", "--name-only", "--diff-filter=ACM")
    rutas = [r for r in salida.decode("utf-8", "replace").splitlines() if r]
    hallazgos = []
    for ruta in rutas:
        contenido = _git("show", f":{ruta}")
        hallazgos += revisar(ruta, contenido)
    return hallazgos


def escanear_historial() -> list[str]:
    """Revisa todos los blobs alcanzables desde cualquier rama o tag."""
    salida = _git("rev-list", "--objects", "--all").decode("utf-8", "replace")
    hallazgos = []
    for linea in salida.splitlines():
        partes = linea.split(" ", 1)
        if len(partes) != 2:
            continue
        sha, ruta = partes
        if _git("cat-file", "-t", sha).strip() != b"blob":
            continue
        hallazgos += revisar(ruta, _git("cat-file", "-p", sha))
    return hallazgos


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--staged", action="store_true", help="revisar solo el índice (modo pre-commit)"
    )
    args = parser.parse_args()

    hallazgos = escanear_staged() if args.staged else escanear_historial()
    alcance = "el índice" if args.staged else "el historial completo"

    if hallazgos:
        print(f"\n  BLOQUEADO: se encontraron posibles credenciales en {alcance}\n")
        for hallazgo in sorted(set(hallazgos)):
            print(f"    {hallazgo}")
        print(
            "\n  Sacá el valor del código y ponelo en `.env` (que está en .gitignore)."
            "\n  Si la credencial ya se usó alguna vez, REVOCALA: borrar el commit no alcanza.\n"
        )
        return 1

    print(f"Sin credenciales detectadas en {alcance}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
