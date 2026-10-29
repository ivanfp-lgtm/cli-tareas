# src/tareas/motor.py
"""El Motor elige los ficheros que cumplen el filtro y se los pasa a la acción."""

import re
import time
from pathlib import Path

from .acciones import Accion, Resultado
from .errores import TareasError


class Motor:
    def __init__(self, acciones: list[dict]):
        self.acciones = {a["nombre"]: Accion.desde_config(a) for a in acciones}

    @staticmethod
    def seleccionar(carpeta: Path, filtro: dict) -> list[Path]:
        exts = {e.lower() for e in filtro.get("extensiones", [])}
        patron = re.compile(filtro["patron"]) if "patron" in filtro else None
        patron_nombre = (
            re.compile(filtro["patron_nombre"]) if "patron_nombre" in filtro else None
        )
        dias = filtro.get("mas_antiguo_que_dias")
        mb = filtro.get("mayor_que_mb")
        ahora = time.time()
        elegidos = []
        for f in sorted(carpeta.iterdir()):
            try:
                if not f.is_file():
                    continue
                if exts and f.suffix.lower() not in exts:
                    continue
                if patron and not patron.search(f.name):
                    continue
                if patron_nombre and not patron_nombre.search(f.stem):
                    continue
                datos = f.stat()
                if dias is not None and ahora - datos.st_mtime < dias * 86400:
                    continue
                if mb is not None and datos.st_size < mb * 1024 * 1024:
                    continue
            except OSError:
                continue  # enlace roto o sin permisos: lo saltamos
            elegidos.append(f)
        return elegidos

    def ejecutar(
        self, nombre: str, carpeta: Path | None, simular: bool
    ) -> list[Resultado]:
        accion = self.acciones.get(nombre)
        if accion is None:
            raise TareasError(
                f"No hay ninguna acción «{nombre}». Mira la lista con: tareas acciones"
            )
        carpeta = (carpeta or Path(accion.config.get("origen", "."))).expanduser()
        if not carpeta.is_dir():
            raise TareasError(f"La carpeta {carpeta} no existe")
        ficheros = self.seleccionar(carpeta, accion.config.get("filtro", {}))
        return accion.ejecutar(ficheros, simular)
