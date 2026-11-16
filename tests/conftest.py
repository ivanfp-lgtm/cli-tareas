# tests/conftest.py
"""El andamiaje: ninguna prueba toca mis carpetas reales ni llama al servidor de IA."""

import json
import os
import time
from pathlib import Path

import pytest

from tareas import cli
from tareas.errores import IANoDisponible
from tareas.ia import ProveedorIA, Respuesta

mkdir_original = Path.mkdir


def _mkdir_dentro_de(tmp_path):
    """Una versión de Path.mkdir que solo crea carpetas dentro de tmp_path.

    Si una prueba intentara escribir en mi HOME real (un ~ mal expandido),
    saltaría PermissionError en vez de crear carpetas en mis ficheros.
    """

    def mkdir(self, *args, **kwargs):
        try:
            self.relative_to(tmp_path)
        except ValueError:
            raise PermissionError(f"Una prueba no puede crear {self} (fuera de tmp_path)")
        return mkdir_original(self, *args, **kwargs)

    return mkdir


def _sin_ia():
    raise IANoDisponible(
        "Faltan CENTRO_IA_URL o CENTRO_IA_KEY: ponlas en .env (mira .env.example)"
    )


@pytest.fixture(autouse=True)
def aislado(tmp_path, monkeypatch):
    """Cada prueba, en su carpeta temporal y sin el servidor de IA de verdad."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))  # ~ apunta aquí (Linux, macOS)
    monkeypatch.setenv("USERPROFILE", str(tmp_path))  # y aquí en Windows
    for var in ("CENTRO_IA_URL", "CENTRO_IA_KEY", "CENTRO_IA_CA"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("DOTENV_PATH", str(tmp_path / "no-hay.env"))  # que no lea mi .env
    monkeypatch.setattr(cli, "proveedor_desde_entorno", _sin_ia)  # en la CLI, nunca IA real
    # que "~" no pueda crear carpetas dentro del HOME real durante una prueba
    monkeypatch.setattr(Path, "mkdir", _mkdir_dentro_de(tmp_path))


@pytest.fixture
def descargas(tmp_path) -> Path:
    """Una carpeta con ficheros feos: tildes, espacios, mayúsculas y uno viejo."""
    carpeta = tmp_path / "Descargas"
    carpeta.mkdir()
    for nombre in [
        "factura.pdf",
        "apuntes de redes.docx",
        "FOTO1.JPG",
        "cumpleaños 2.png",
        "viejo.tmp",
    ]:
        (carpeta / nombre).write_text("contenido de prueba", encoding="utf-8")
    hace_40_dias = time.time() - 40 * 86400
    os.utime(carpeta / "viejo.tmp", (hace_40_dias, hace_40_dias))
    return carpeta


@pytest.fixture
def escribir_config(tmp_path):
    """Escribe un acciones.json (lista de acciones o texto tal cual) y devuelve su ruta."""

    def escribir(acciones) -> Path:
        ruta = tmp_path / "acciones.json"
        texto = (
            acciones
            if isinstance(acciones, str)
            else json.dumps({"version": 1, "acciones": acciones}, ensure_ascii=False)
        )
        ruta.write_text(texto, encoding="utf-8")
        return ruta

    return escribir


class ProveedorFalso(ProveedorIA):
    """Un «modelo» que contesta siempre lo mismo y apunta lo que le preguntan."""

    def __init__(self, respuesta: str):
        self.respuesta = respuesta
        self.preguntas: list[str] = []

    def completar(self, sistema, usuario, max_tokens=800):
        self.preguntas.append(usuario)
        return Respuesta(self.respuesta, 10, 5, 0.0)


@pytest.fixture
def modelo_falso():
    return ProveedorFalso
