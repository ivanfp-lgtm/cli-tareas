# src/tareas/acciones.py
"""Cada clase sabe hacer UNA cosa con un fichero. La fábrica elige la clase."""

from __future__ import annotations

import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .errores import AccionNoValida, TareasError


@dataclass
class Resultado:
    origen: Path
    destino: Path | None
    estado: str  # "hecho", "simulado" o "saltado"


def destino_libre(destino: Path, reservados: set[Path] | None = None) -> Path:
    """Nunca sobrescribe: si existe, prueba 'nombre (1).ext', 'nombre (2).ext'...

    «reservados» evita colisiones dentro de una misma simulación, donde el
    primer destino aún no existe en el disco.
    """
    reservados = reservados or set()
    libre, n = destino, 1
    while libre.exists() or libre in reservados:
        libre = destino.with_name(f"{destino.stem} ({n}){destino.suffix}")
        n += 1
    return libre


class Accion(ABC):
    tipo = ""
    destructiva = False
    _registro: dict[str, type[Accion]] = {}

    def __init__(self, config: dict):
        self.nombre = config["nombre"]
        self.descripcion = config["descripcion"]
        self.config = config

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.tipo:
            Accion._registro[cls.tipo] = cls  # cada subclase se apunta sola

    @staticmethod
    def desde_config(config: dict) -> Accion:
        """Fábrica: del diccionario del JSON a la clase que toca."""
        clase = Accion._registro.get(config["tipo"])
        if clase is None:
            raise AccionNoValida(
                config["nombre"], "tipo", "no hay ninguna clase para ese tipo"
            )
        return clase(config)

    def ejecutar(self, ficheros: list[Path], simular: bool) -> list[Resultado]:
        resultados, reservados = [], set()
        for n, fichero in enumerate(ficheros, start=1):
            resultado = self.aplicar(fichero, n, simular, reservados)
            if resultado.destino is not None:
                reservados.add(resultado.destino)
            resultados.append(resultado)
        return resultados

    @abstractmethod
    def aplicar(
        self, fichero: Path, n: int, simular: bool, reservados: set[Path]
    ) -> Resultado: ...

    def _nombre_nuevo(self, fichero: Path, n: int) -> str:
        fecha = datetime.fromtimestamp(fichero.stat().st_mtime)
        try:
            return str(
                self.config["plantilla"].format(
                    fecha=fecha, n=n, ext=fichero.suffix.lower(), nombre=fichero.stem
                )
            )
        except OSError as e:  # sin permisos para leer la fecha
            raise TareasError(f"No puedo leer la fecha de {fichero}: {e}") from e


class Mover(Accion):
    tipo = "mover"

    def aplicar(self, fichero, n, simular, reservados):
        carpeta = Path(self.config["destino"]).expanduser()
        destino = destino_libre(carpeta / fichero.name, reservados)
        if not simular:
            try:
                carpeta.mkdir(parents=True, exist_ok=True)
                shutil.move(fichero, destino)
            except OSError as e:
                raise TareasError(f"No puedo mover «{fichero.name}»: {e}") from e
        return Resultado(fichero, destino, "simulado" if simular else "hecho")


class Copiar(Accion):
    tipo = "copiar"

    def aplicar(self, fichero, n, simular, reservados):
        carpeta = Path(self.config["destino"]).expanduser()
        destino = destino_libre(carpeta / fichero.name, reservados)
        if not simular:
            try:
                carpeta.mkdir(parents=True, exist_ok=True)
                shutil.copy2(fichero, destino)
            except OSError as e:
                raise TareasError(f"No puedo copiar «{fichero.name}»: {e}") from e
        return Resultado(fichero, destino, "simulado" if simular else "hecho")


class Renombrar(Accion):
    tipo = "renombrar"

    def aplicar(self, fichero, n, simular, reservados):
        nuevo = self._nombre_nuevo(fichero, n)
        if nuevo == fichero.name:
            return Resultado(fichero, None, "saltado")
        destino = destino_libre(fichero.with_name(nuevo), reservados)
        if not simular:
            try:
                fichero.rename(destino)
            except OSError as e:
                raise TareasError(f"No puedo renombrar «{fichero.name}»: {e}") from e
        return Resultado(fichero, destino, "simulado" if simular else "hecho")


class Borrar(Accion):
    tipo = "borrar"
    destructiva = True

    def aplicar(self, fichero, n, simular, reservados):
        if not simular:
            try:
                fichero.unlink()
            except OSError as e:
                raise TareasError(f"No puedo borrar «{fichero.name}»: {e}") from e
        return Resultado(fichero, None, "simulado" if simular else "hecho")
