"""Interfaz de línea de órdenes: aquí solo hay órdenes, opciones y salida."""

from datetime import datetime
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table

from tareas import __version__
from tareas.config import cargar
from tareas.errores import TareasError
from tareas.motor import Motor

app = typer.Typer(
    help="tareas: automatiza tareas repetitivas con tus ficheros.",
    no_args_is_help=True,
    add_completion=False,
)
consola = Console(highlight=False)
consola_err = Console(stderr=True, highlight=False)


def tamano_legible(n: int) -> str:
    """Convierte bytes en texto: 532 B, 1.2 KB, 3.4 MB..."""
    if n < 1024:
        return f"{n} B"
    tamano = float(n)
    unidad = "B"
    for unidad in ("KB", "MB", "GB", "TB"):
        tamano /= 1024
        if tamano < 1024:
            break
    return f"{tamano:.1f} {unidad}"


@app.callback()
def principal(
    ctx: typer.Context,
    config: Annotated[
        Path,
        typer.Option("--config", help="Ruta de acciones.json (por defecto ./acciones.json)."),
    ] = Path("acciones.json"),
) -> None:
    """tareas: automatiza tareas repetitivas con tus ficheros."""
    ctx.obj = config


@app.command()
def version() -> None:
    """Muestra la versión instalada."""
    consola.print(f"tareas {__version__}")


@app.command()
def listar(
    carpeta: Annotated[
        Path, typer.Argument(help="Carpeta que quieres ver (por defecto, la actual).")
    ] = Path("."),
) -> None:
    """Lista los ficheros de una carpeta en una tabla."""
    carpeta = carpeta.expanduser()
    if not carpeta.is_dir():
        consola_err.print(
            f"[red]Error:[/red] «{escape(str(carpeta))}» no existe o no es una carpeta."
        )
        raise typer.Exit(code=1)

    elementos = sorted(carpeta.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    if not elementos:
        consola.print(f"La carpeta «{escape(str(carpeta))}» está vacía.")
        return

    tabla = Table(title=f"Contenido de {escape(str(carpeta.resolve()))}")
    tabla.add_column("Nombre")
    tabla.add_column("Tipo")
    tabla.add_column("Tamaño", justify="right")
    tabla.add_column("Modificado")

    for ruta in elementos:
        try:
            datos = ruta.stat()
        except OSError:
            continue  # enlace roto o sin permisos: lo saltamos
        es_carpeta = ruta.is_dir()
        tipo = "carpeta" if es_carpeta else (ruta.suffix.lower() or "(sin extensión)")
        tamano = "—" if es_carpeta else tamano_legible(datos.st_size)
        fecha = datetime.fromtimestamp(datos.st_mtime).strftime("%Y-%m-%d %H:%M")
        tabla.add_row(escape(ruta.name), tipo, tamano, fecha)

    consola.print(tabla)


@app.command()
def validar(
    ctx: typer.Context,
) -> None:
    """Comprueba que el fichero de acciones es correcto sin tocar ningún fichero."""
    try:
        acciones = cargar(ctx.obj)
    except TareasError as e:
        consola_err.print(f"[red]✘ {escape(str(e))}[/red]")
        raise typer.Exit(code=e.codigo_salida)
    consola.print(f"[green]✔ {len(acciones)} acciones válidas[/green]")


@app.command()
def acciones(
    ctx: typer.Context,
) -> None:
    """Muestra la lista de acciones definidas en acciones.json."""
    try:
        lista = cargar(ctx.obj)
    except TareasError as e:
        consola_err.print(f"[red]✘ {escape(str(e))}[/red]")
        raise typer.Exit(code=e.codigo_salida)

    tabla = Table(title=f"Acciones de {escape(str(ctx.obj))}")
    tabla.add_column("Nombre")
    tabla.add_column("Tipo")
    tabla.add_column("Descripción")
    for a in lista:
        tabla.add_row(escape(a["nombre"]), escape(a["tipo"]), escape(a["descripcion"]))
    consola.print(tabla)


def pintar_tabla(resultados: list, simular: bool) -> None:
    """Tabla Rich: fichero → destino → estado, más el resumen final."""
    hechos = sum(1 for r in resultados if r.estado == "hecho")
    simulados = sum(1 for r in resultados if r.estado == "simulado")
    saltados = sum(1 for r in resultados if r.estado == "saltado")
    if not resultados:
        consola.print("Ningún fichero cumple el filtro; no hay nada que hacer.")
        return

    titulo = "SIMULACIÓN: no se ha tocado nada" if simular else "Resultado"
    tabla = Table(title=f"{escape(str(resultados[0].origen.parent))} · {titulo}")
    tabla.add_column("Fichero")
    tabla.add_column("Destino")
    tabla.add_column("Estado")
    for r in resultados:
        destino = str(r.destino) if r.destino else "—"
        tabla.add_row(escape(r.origen.name), escape(destino), escape(r.estado))
    consola.print(tabla)
    consola.print(
        f"{len(resultados)} ficheros · {hechos} hechos · {simulados} simulados · {saltados} saltados"
    )
    if simular:
        consola.print("Para hacerlo de verdad, repite la orden sin [bold]--simular[/bold].")


@app.command()
def ejecutar(
    ctx: typer.Context,
    nombre: Annotated[
        str, typer.Argument(help="Nombre de la acción (ver: tareas acciones).")
    ],
    carpeta: Annotated[
        Path | None, typer.Argument(help="Carpeta sobre la que actuar (por defecto, la «origen» de la acción).")
    ] = None,
    simular: Annotated[
        bool, typer.Option("--simular", help="Enseña qué haría sin tocar nada.")
    ] = False,
    si: Annotated[
        bool, typer.Option("--si", help="No pedir confirmación en acciones destructivas.")
    ] = False,
) -> None:
    """Ejecuta una acción definida en acciones.json."""
    try:
        motor = Motor(cargar(ctx.obj))
        accion = motor.acciones.get(nombre)
        if accion and accion.destructiva and accion.config.get("confirmar", True) and not simular and not si:
            typer.confirm(f"«{nombre}» borra ficheros. ¿Seguro?", abort=True)
        resultados = motor.ejecutar(nombre, carpeta, simular)
    except TareasError as e:
        consola_err.print(f"[red]✘ {escape(str(e))}[/red]")
        raise typer.Exit(code=e.codigo_salida)
    except typer.Abort:
        consola.print("Cancelado: no se ha tocado nada.")
        raise typer.Exit(code=1)
    pintar_tabla(resultados, simular)
