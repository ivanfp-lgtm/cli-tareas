# tareas · CLI de tareas con ficheros (proyecto de 1º DAM)

## Stack y órdenes
- Python 3.12 + Typer + Rich, gestionado con uv (src layout, paquete src/tareas).
- Ejecutar: `uv run tareas --help` · Validar config: `uv run tareas validar` · Pruebas (semana 4): `uv run pytest`.
- Nota del desarrollo en este equipo: el proyecto vive en un USB sin symlinks; el entorno virtual real está en `~/.venvs/tareas`. Usa siempre `UV_PROJECT_ENVIRONMENT=~/.venvs/tareas uv run ...`.

## Normas
- Mensajes y comentarios en español; código claro antes que listo.
- pathlib siempre, encoding="utf-8", nada de os.system ni shell=True: tiene que funcionar en Linux, Windows y macOS.
- Nunca ejecutes acciones sobre carpetas reales: solo en ~/pruebas-tareas y con --simular.
- No toques .env ni escribas claves en ningún fichero. Los commits los hace el alumno; en la semana 4 (release v1.0.0) se autoriza a opencode a hacer el push, la rama release-1.0, la etiqueta v1.0.0 y la release en GitHub.
- Antes de cambiar un fichero, explica en 2-3 líneas qué vas a hacer.
