# Orchestrator-Workers con Claude (ejemplo simplificado)

Implementación mínima del patrón **orchestrator-workers**, inspirada en el
[cookbook oficial de Anthropic](https://github.com/anthropics/claude-cookbooks/blob/main/patterns/agents/orchestrator_workers.ipynb).

## Cómo funciona

1. Un LLM **orquestador** (modelo más potente, ej. Opus) recibe la tarea y decide
   dinámicamente en qué 2-3 enfoques conviene descomponerla. Las subtareas
   **no están hardcodeadas**: las genera el modelo según el input.
2. Cada subtarea se envía **en paralelo** a un LLM **worker** (modelo más económico,
   ej. Haiku), que la resuelve de forma independiente.
3. Se combinan los resultados de todos los workers en la respuesta final.

## Uso

```bash
pip install anthropic --break-system-packages
export ANTHROPIC_API_KEY="tu-api-key"
python orchestrator_workers.py
```

## Por qué separar orquestador y workers

- **Adaptabilidad**: sirve para tareas donde no se puede predecir de antemano
  cuántas subtareas van a hacer falta ni de qué tipo.
- **Costo/velocidad**: el orquestador solo planifica (tarea exigente → modelo caro),
  los workers ejecutan tareas acotadas y repetitivas (tarea simple → modelo barato),
  optimizando el costo total sin perder calidad donde más importa.

## Créditos

Basado en los patrones de agentes de Anthropic:
https://github.com/anthropics/claude-cookbooks/tree/main/patterns/agents
