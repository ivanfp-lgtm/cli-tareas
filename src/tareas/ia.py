# src/tareas/ia.py
"""La capa IA: lo único que el resto del programa sabe de la IA es completar()."""

from __future__ import annotations

import os
import ssl
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

import httpx
from dotenv import find_dotenv, load_dotenv

from .errores import IANoDisponible

MODELO_POR_DEFECTO = "Qwen38-DualSpark-medium"


@dataclass
class Respuesta:
    texto: str
    tokens_entrada: int
    tokens_salida: int
    segundos: float

    def resumen(self) -> str:
        return f"{self.tokens_entrada}+{self.tokens_salida} tokens · {self.segundos:.1f} s"


class ProveedorIA(ABC):
    """Lo único que el resto del programa sabe de la IA: le das texto y te devuelve texto."""

    @abstractmethod
    def completar(self, sistema: str, usuario: str, max_tokens: int = 800) -> Respuesta: ...


class ProveedorCentro(ProveedorIA):
    """Un servidor compatible con la API de OpenAI: el del centro (o cualquier otro)."""

    def __init__(
        self,
        url: str,
        clave: str,
        modelo: str = MODELO_POR_DEFECTO,
        ca: str | None = None,
    ):
        self.url = url.rstrip("/")
        self.modelo = modelo
        self._clave = clave  # «_»: es privada; nunca se imprime
        self._tls = ssl.create_default_context()
        if ca:
            self._tls.load_verify_locations(Path(ca).expanduser())

    @staticmethod
    def desde_entorno() -> ProveedorCentro:
        """Fábrica: lee .env (si lo hay) y las variables de entorno."""
        load_dotenv(find_dotenv(usecwd=True))  # no pisa las variables que ya existen
        url = os.environ.get("CENTRO_IA_URL")
        clave = os.environ.get("CENTRO_IA_KEY")
        if not url or not clave:
            raise IANoDisponible(
                "Faltan CENTRO_IA_URL o CENTRO_IA_KEY: ponlas en .env (mira .env.example)"
            )
        modelo = os.environ.get("CENTRO_IA_MODELO", MODELO_POR_DEFECTO)
        return ProveedorCentro(url, clave, modelo, os.environ.get("CENTRO_IA_CA"))

    def completar(self, sistema: str, usuario: str, max_tokens: int = 800) -> Respuesta:
        """Una petición al servidor, sin .env ni variables: para pruebas y casos feos."""
        return self._llamar(sistema, usuario, max_tokens)

    def _llamar(self, sistema: str, usuario: str, max_tokens: int) -> Respuesta:
        cuerpo = {
            "model": self.modelo,
            "messages": [
                {"role": "system", "content": sistema},
                {"role": "user", "content": usuario},
            ],
            "temperature": 0.2,
            "max_tokens": max_tokens,
        }
        inicio = time.perf_counter()
        try:
            r = httpx.post(
                f"{self.url}/chat/completions",
                json=cuerpo,
                headers={"Authorization": f"Bearer {self._clave}"},
                timeout=httpx.Timeout(60, connect=5),
                verify=self._tls,
            )
            r.raise_for_status()
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            if "CERTIFICATE" in str(e).upper():
                raise IANoDisponible(
                    "No me fío del servidor: falta el certificado del centro (CENTRO_IA_CA)"
                ) from e
            raise IANoDisponible(
                "No llego al servidor de IA: ¿estás en la red del centro?"
            ) from e
        except httpx.TimeoutException as e:
            raise IANoDisponible("El servidor de IA no ha respondido a tiempo") from e
        except httpx.HTTPStatusError as e:
            codigo = e.response.status_code
            motivo = {
                401: "la clave no es válida",
                429: "demasiadas peticiones, espera un minuto",
            }
            raise IANoDisponible(
                f"El servidor de IA responde {codigo}: {motivo.get(codigo, 'algo ha fallado')}"
            ) from e
        try:
            datos = r.json()
            texto = datos["choices"][0]["message"]["content"] or ""
        except (ValueError, KeyError, IndexError) as e:
            raise IANoDisponible("El servidor de IA ha contestado algo que no entiendo") from e
        uso = datos.get("usage") or {}
        return Respuesta(
            texto.strip(),
            uso.get("prompt_tokens", 0),
            uso.get("completion_tokens", 0),
            time.perf_counter() - inicio,
        )
