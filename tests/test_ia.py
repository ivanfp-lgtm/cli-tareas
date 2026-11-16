# tests/test_ia.py: la IA probada sin red, sin clave y sin gastar un token
import pytest

from tareas.acciones import a_nombre_seguro
from tareas.errores import IANoDisponible
from tareas.ia import ProveedorCentro
from tareas.motor import Motor


@pytest.mark.parametrize(
    "respuesta, esperado",
    [
        ("Tema 3: ¡Linux & Bash!", "tema-3-linux-bash"),
        ("../../etc/passwd", "etc-passwd"),
        ("redes-ip-protocolos.pdf", "redes-ip-protocolos"),
        ("", ""),
    ],
    ids=["tildes-y-signos", "ruta-peligrosa", "con-extension", "vacia"],
)
def test_la_respuesta_del_modelo_se_limpia(respuesta, esperado):
    assert a_nombre_seguro(respuesta) == esperado


def apuntes(tmp_path):
    carpeta = tmp_path / "Apuntes"
    carpeta.mkdir()
    (carpeta / "tema-1.txt").write_text("La CPU ejecuta instrucciones.", encoding="utf-8")
    return carpeta


def test_resumir_con_un_modelo_falso(tmp_path, modelo_falso):
    falso = modelo_falso("- La CPU ejecuta instrucciones")
    accion = {
        "nombre": "resumir",
        "descripcion": "x",
        "tipo": "resumir",
        "destino": str(tmp_path / "Res"),
    }
    [r] = Motor([accion], proveedor=falso).ejecutar("resumir", apuntes(tmp_path), simular=False)
    assert r.estado == "hecho"
    assert "La CPU" in (tmp_path / "Res" / "tema-1.resumen.md").read_text(encoding="utf-8")
    assert "<documento>" in falso.preguntas[0]


def test_simular_no_pregunta_al_modelo(tmp_path, modelo_falso):
    falso = modelo_falso("no debería usarse")
    accion = {"nombre": "resumir", "descripcion": "x", "tipo": "resumir"}
    [r] = Motor([accion], proveedor=falso).ejecutar("resumir", apuntes(tmp_path), simular=True)
    assert r.estado == "simulado"
    assert falso.preguntas == []


def test_categoria_rara_va_a_sin_clasificar(tmp_path, modelo_falso):
    accion = {
        "nombre": "clasificar",
        "descripcion": "x",
        "tipo": "clasificar",
        "categorias": ["redes", "linux"],
        "destino": str(tmp_path / "Asig"),
    }
    Motor([accion], proveedor=modelo_falso("Creo que es de mates")).ejecutar(
        "clasificar", apuntes(tmp_path), False
    )
    assert (tmp_path / "Asig" / "sin-clasificar" / "tema-1.txt").exists()


def test_renombrar_ia_usa_el_nombre_limpio(tmp_path, modelo_falso):
    carpeta = tmp_path / "Escaneos"
    carpeta.mkdir()
    (carpeta / "escaneo_0042.txt").write_text("redes y protocolos", encoding="utf-8")
    accion = {"nombre": "renombrar", "descripcion": "x", "tipo": "renombrar-ia"}
    Motor([accion], proveedor=modelo_falso("Redes: Protocolos e IP!")).ejecutar(
        "renombrar", carpeta, False
    )
    assert (carpeta / "redes-protocolos-e-ip.txt").exists()
    assert not (carpeta / "escaneo_0042.txt").exists()


def test_sin_clave_no_hay_ia():
    with pytest.raises(IANoDisponible, match="CENTRO_IA_KEY"):
        ProveedorCentro.desde_entorno()


def test_sin_red_el_mensaje_es_humano():
    proveedor = ProveedorCentro("http://127.0.0.1:9/v1", "clave-de-prueba")
    with pytest.raises(IANoDisponible, match="No llego"):
        proveedor.completar("sistema", "usuario")
