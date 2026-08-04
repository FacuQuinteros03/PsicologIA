"""Construcción del prompt de procesamiento de notas."""

from app.services.ia.base import ContextoPaciente

INSTRUCCIONES = """\
Sos un asistente de registro clínico para profesionales de la salud mental. \
Recibís las notas crudas que un terapeuta tomó durante una sesión —bullets, \
abreviaturas, frases a medio escribir— y las convertís en un registro estructurado.

Reglas que no podés romper:

1. NO agregues información que no esté en las notas. Si algo no se menciona, \
queda vacío. No completes con lo que "suele pasar" en casos parecidos.
2. NO diagnostiques ni sugieras diagnósticos. Describí lo relatado, no lo \
interpretes clínicamente.
3. NO propongas tratamientos ni indicaciones. Las decisiones clínicas son del \
profesional.
4. El resumen va en tercera persona y en lenguaje profesional, pero sin inflar: \
si las notas son breves, el resumen es breve.
5. Usá lenguaje neutro respecto del género de la persona consultante, salvo que \
las notas lo especifiquen.
6. Los tags van en minúscula, sin '#', con guiones en lugar de espacios.
7. En `entidades`, la `etiqueta` tiene que ser cómo la nombra la persona en las \
notas ("Mamá", "el jefe"), no un nombre genérico.
"""


def construir_prompt(notas: str, contexto: ContextoPaciente | None = None) -> str:
    partes = [INSTRUCCIONES]

    if contexto is not None:
        bloque: list[str] = []
        if contexto.motivo_consulta:
            bloque.append(f"Motivo de consulta registrado: {contexto.motivo_consulta}")
        if contexto.etiquetas_conocidas:
            etiquetas = ", ".join(f'"{e}"' for e in contexto.etiquetas_conocidas)
            bloque.append(
                "Personas que ya existen en el genograma de esta persona: "
                f"{etiquetas}. Si alguna de ellas aparece en las notas, usá "
                "EXACTAMENTE esa misma etiqueta para que se vinculen."
            )
        if contexto.tags_previos:
            tags = ", ".join(contexto.tags_previos)
            bloque.append(
                f"Tags usados en sesiones anteriores: {tags}. Reutilizalos cuando "
                "corresponda en lugar de crear variantes nuevas."
            )
        if bloque:
            partes.append("--- CONTEXTO ---\n" + "\n".join(bloque))

    partes.append(f"--- NOTAS DE LA SESIÓN ---\n{notas.strip()}")
    return "\n\n".join(partes)
