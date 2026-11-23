# tests/conftest.py
"""El andamiaje: ninguna prueba toca mis carpetas reales ni llama al servidor de IA."""

import json
import os
import shutil
import time
import uuid
from pathlib import Path

import pytest

from tareas import cli
from tareas.errores import IANoDisponible
from tareas.ia import ProveedorIA, Respuesta

mkdir_original = Path.mkdir

# El escenario de las pruebas NO se monta en el TEMP del sistema: en Windows
# el TEMP es C:\Users\RUNNER~1\... (alias 8.3 del «runneradmin», con ñ en el
# nombre real) y las comparaciones de nombres por ahí son un caos: dos
# nombres que solo se diferencian en mayúsculas/acentos pueden parecer EL
# MISMO y la norma «nunca sobrescribir» manda el fichero a «(1)» (lo vimos
# en Actions: solo petaba windows-latest). Lo montamos en una ruta ASCII
# limpia y corta del repo. OJO con el USB del aula: vive en DAM/Programación
# (con ñ), que NO es ASCII; en ese equipo hay que clonar el repo en una ruta
# sin acentos (o copiarlo) para pasar las pruebas, y mientras tanto pytest lo
# dice con un skip en vez de dar falsos rojos. En GitHub Actions la ruta sí es
# ASCII (/home/runner/work/…) y se pasan enteras.
BASE_TMP = Path(__file__).resolve().parent.parent / ".caja-de-arena"
RUTA_NO_ASCII = not str(BASE_TMP).isascii()


def pytest_sessionfinish(session, exitstatus):
    """Al acabar la sesión, la caja de arena no deja ni rastro en el repo."""
    try:
        shutil.rmtree(BASE_TMP)
    except (FileNotFoundError, PermissionError, OSError):
        pass  # la caja ya no estaba, o el disco no deja borrar: no es un fallo


@pytest.fixture
def tmp_path() -> Path:
    """Mi propio tmp_path, sin el TEMP de Windows por medio."""
    if RUTA_NO_ASCII:
        pytest.skip(
            "el repo está en una ruta con acentos: copia o clona el proyecto "
            "en una ruta ASCII para pasar las pruebas (ver conftest.py)"
        )
    try:
        viejos = list(BASE_TMP.glob("prueba-*"))
    except OSError:
        viejos = []  # un disco raro o sin permisos: no es motivo para petar la sesión
    for viejo in viejos:
        shutil.rmtree(viejo, ignore_errors=True)
    caja = BASE_TMP / f"prueba-{uuid.uuid4().hex[:8]}"
    caja.mkdir(parents=True)
    yield caja
    shutil.rmtree(caja, ignore_errors=True)


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
    """Una carpeta con ficheros feos: tildes, espacios, mayúsculas y uno viejo.

    El nombre de los ficheros NO puede depender del alias 8.3 de Windows:
    un nombre con ñ se translitera al recortarlo (CUMPL~1) y dos nombres
    distintos pueden quedarse con la MISMA forma corta, con lo que la
    comparación de Windows los ve iguales y la norma «nunca sobrescribir»
    acaba mandando el fichero a « (1)». Por eso el escenario vive en
    BASE_TMP (ruta ASCII y limpia del repo), no en el TEMP del sistema: en
    Windows el TEMP es C:\\Users\\RUNNER~1\\... y ahí el alias 8.3 del
    usuario ya nos lió dos comparaciones en Actions.
    """
    carpeta = tmp_path / "Descargas"
    carpeta.mkdir()
    # «FOTO1.JPG» con nombre ASCII y sin ñ: en Windows la comparación de
    # nombres pasa por el alias 8.3, y un nombre con ñ (como «cumpleaños»)
    # se empareja con su recortado (CUMPLE~1). El escenario NO puede depender
    # de ese capricho.
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
