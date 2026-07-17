"""
Ejemplo simplificado del patrón Orchestrator-Workers con Claude.

Basado en el cookbook oficial de Anthropic:
https://github.com/anthropics/claude-cookbooks/blob/main/patterns/agents/orchestrator_workers.ipynb

Idea general:
1. Un LLM "orquestador" analiza la tarea y decide QUÉ subtareas hacen falta
   (no están predefinidas, las inventa según el input).
2. Cada subtarea se manda en paralelo a un LLM "worker" que la resuelve.
3. Se combinan los resultados en una respuesta final.

Requiere:
    pip install anthropic --break-system-packages

Configurar la API key:
    export ANTHROPIC_API_KEY="tu-api-key"
"""

import os
import re
import concurrent.futures
from anthropic import Anthropic

client = Anthropic()  # toma la key de la variable de entorno ANTHROPIC_API_KEY

# Modelo más potente para planificar (el orquestador "piensa" el plan)
ORCHESTRATOR_MODEL = "claude-opus-4-8"
# Modelo más económico/rápido para ejecutar cada subtarea en paralelo
WORKER_MODEL = "claude-haiku-4-5-20251001"


ORCHESTRATOR_PROMPT = """Analiza esta tarea y descompónla en 2 o 3 enfoques distintos y valiosos.

Tarea: {task}

Devolvé tu respuesta en este formato exacto:

<analysis>
Explicá tu entendimiento de la tarea y qué variaciones convendría generar.
</analysis>

<tasks>
<task>
<type>nombre corto del enfoque</type>
<description>instrucción detallada y específica para que un worker la ejecute</description>
</task>
<task>
<type>nombre corto del enfoque</type>
<description>instrucción detallada y específica para que un worker la ejecute</description>
</task>
</tasks>
"""

WORKER_PROMPT = """Resolvé la siguiente subtarea, siguiendo exactamente estas instrucciones:

{description}

Tarea original de contexto: {original_task}
"""


def call_claude(model: str, prompt: str) -> str:
    """Llamada simple a la API de mensajes de Claude."""
    response = client.messages.create(
        model=model,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


def parse_tasks(orchestrator_output: str) -> list[dict]:
    """Extrae las subtareas generadas por el orquestador desde el XML."""
    tasks = []
    for match in re.finditer(
        r"<task>\s*<type>(.*?)</type>\s*<description>(.*?)</description>\s*</task>",
        orchestrator_output,
        re.DOTALL,
    ):
        tasks.append({"type": match.group(1).strip(), "description": match.group(2).strip()})
    return tasks


def run_worker(task: dict, original_task: str) -> dict:
    """Ejecuta una subtarea individual con el modelo worker."""
    prompt = WORKER_PROMPT.format(description=task["description"], original_task=original_task)
    result = call_claude(WORKER_MODEL, prompt)
    return {"type": task["type"], "result": result}


def orchestrate(task: str) -> dict:
    # 1. El orquestador analiza la tarea y genera subtareas dinámicamente
    orchestrator_output = call_claude(ORCHESTRATOR_MODEL, ORCHESTRATOR_PROMPT.format(task=task))
    subtasks = parse_tasks(orchestrator_output)

    if not subtasks:
        raise ValueError("El orquestador no generó subtareas parseables. Salida cruda:\n" + orchestrator_output)

    # 2. Los workers resuelven cada subtarea EN PARALELO
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(subtasks)) as executor:
        futures = [executor.submit(run_worker, t, task) for t in subtasks]
        worker_results = [f.result() for f in futures]

    return {
        "orchestrator_analysis": orchestrator_output,
        "worker_results": worker_results,
    }


if __name__ == "__main__":
    tarea = "Escribí un copy de marketing para una botella de agua reutilizable y ecológica."

    resultado = orchestrate(tarea)

    print("=" * 60)
    print("ANÁLISIS DEL ORQUESTADOR")
    print("=" * 60)
    print(resultado["orchestrator_analysis"])

    for w in resultado["worker_results"]:
        print("\n" + "=" * 60)
        print(f"RESULTADO DEL WORKER — Enfoque: {w['type']}")
        print("=" * 60)
        print(w["result"])
