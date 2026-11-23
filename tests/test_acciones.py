# tests/test_acciones.py: las acciones con ficheros reales, pero en tmp_path
import os
from pathlib import Path

import pytest

from tareas.errores import TareasError
from tareas.motor import Motor


def motor_con(**accion) -> Motor:
    return Motor([{"nombre": "prueba", "descripcion": "acción de prueba", **accion}])


def test_mover_solo_lo_que_cumple_el_filtro(descargas, tmp_path):
    destino = tmp_path / "PDF"
    motor = motor_con(
        tipo="mover", filtro={"extensiones": [".pdf", ".docx"]}, destino=str(destino)
    )
    resultados = motor.ejecutar("prueba", descargas, simular=False)
    assert sorted(f.name for f in destino.iterdir()) == [
        "apuntes de redes.docx",
        "factura.pdf",
    ]
    assert [r.estado for r in resultados] == ["hecho", "hecho"]
    assert (descargas / "FOTO1.JPG").exists()


def test_simular_no_toca_el_disco(descargas, tmp_path):
    destino = tmp_path / "PDF"
    antes = sorted(descargas.iterdir())
    motor = motor_con(
        tipo="mover", filtro={"extensiones": [".pdf"]}, destino=str(destino)
    )
    motor.ejecutar("prueba", descargas, simular=True)
    assert sorted(descargas.iterdir()) == antes
    assert not destino.exists()  # ni siquiera un mkdir


def test_nunca_sobrescribe(descargas, tmp_path):
    destino = tmp_path / "PDF"
    destino.mkdir()
    (destino / "factura.pdf").write_text("la que ya estaba", encoding="utf-8")
    motor_con(
        tipo="mover", filtro={"extensiones": [".pdf"]}, destino=str(destino)
    ).ejecutar("prueba", descargas, False)
    vieja, nueva = destino / "factura.pdf", destino / "factura (1).pdf"
    assert vieja.read_text(encoding="utf-8") == "la que ya estaba"
    assert nueva.exists()


def test_la_extension_en_mayusculas_cuenta(descargas):
    elegidos = Motor.seleccionar(descargas, {"extensiones": [".jpg"]})
    assert [f.name for f in elegidos] == ["FOTO1.JPG"]


def test_borrar_solo_los_viejos(descargas):
    (descargas / "nuevo.tmp").write_text("", encoding="utf-8")
    filtro = {"patron": r"\.tmp$", "mas_antiguo_que_dias": 30}
    motor_con(tipo="borrar", filtro=filtro).ejecutar("prueba", descargas, simular=False)
    assert not (descargas / "viejo.tmp").exists()
    assert (descargas / "nuevo.tmp").exists()


def test_renombrar_con_plantilla(descargas):
    motor = motor_con(
        tipo="renombrar",
        filtro={"extensiones": [".png"]},
        plantilla="foto-{n:03}{ext}",
    )
    resultados = motor.ejecutar("prueba", descargas, simular=False)
    # «cumpleaños 2.png» → foto-001.png: el nombre base cambia de verdad, así
    # que se renombra en cualquier SO (con cualquier alias 8.3). Lo que no
    # puede salir NUNCA es « (1)» (no hay otro fichero con ese nombre).
    assert (descargas / "foto-001.png").exists()
    assert not (descargas / "cumpleaños 2.png").exists()
    assert not (descargas / "foto-001 (1).png").exists()
    assert not (descargas / "foto-002 (1).png").exists()


def test_mismo_nombre_solo_mayusculas_no_achasta(descargas):
    # «FOTO1.JPG» → «FOTO1-nuevo.JPG»: el nombre base cambia, así que en
    # cualquier SO (distinga o no mayúsculas) se renombra. Lo que NO puede
    # pasar es que acabe en « (1)», que era el bug del casefold en
    # destino_libre.
    motor = motor_con(
        tipo="renombrar",
        filtro={"patron_nombre": "^FOTO1$"},
        plantilla="{nombre}-nuevo{ext}",
    )
    resultados = motor.ejecutar("prueba", descargas, simular=False)
    r = resultados[0]
    assert r.estado == "hecho"
    # la extensión SIEMPRE acaba en minúsculas (con plantilla o sin ella)
    assert r.destino.name in ("FOTO1-nuevo.jpg", "FOTO1-nuevo.JPG")
    assert (descargas / r.destino.name).exists()
    assert not (descargas / "FOTO1.JPG").exists()


def _rename_de_mayusculas_es_real(carpeta: Path) -> bool:
    """La misma pregunta que se hace el motor en _rename_de_mayusculas_es_real
    (ver src/tareas/acciones.py): ¿en ESTE disco el rename SOLO de
    mayúsculas se refleja de verdad? Se sondea con un temporero que lleva la
    MISMA extensión que el fichero de la prueba (en exfat el comportamiento
    depende de la extensión: por eso el motor también la usa). None = no se
    puede probar (sin permisos, disco raro): en una prueba, SKIP antes que
    suponer el sistema operativo."""
    from tareas.acciones import _rename_de_mayusculas_es_real

    resultado = _rename_de_mayusculas_es_real(carpeta, ".jpg")
    if resultado is None:
        pytest.skip("este disco no permite sondear los mayúsculas")
    return resultado


def test_cambio_de_mayusculas_es_un_rename_normal(descargas):
    # «FOTO1.JPG» → «foto1.jpg» (renombrar SOLO de mayúsculas). Qué debe
    # pasar depende del disco, y lo pregunto con el MISMO sondeo real que usa
    # el motor:
    #   · rename que se refleja de verdad (ext4, APFS sensible, el TEMP de un
    #     runner): se renombra, «hecho».
    #   · rename que no se refleja (NTFS, APFS insensible, exfat+ignore_case
    #     como el USB del aula): el fichero se marca «saltado» y no se toca
    #     nada (en Windows forzarlo PETA, y en los demás no cambiaría nada).
    # Lo que NO puede pasar en ningún caso es acabar en « (1)», que era el
    # bug: «foto1.jpg» sería EL MISMO nombre que «FOTO1.JPG» y la norma
    # «nunca sobrescribir» lo mandaría a « (1)».
    reflejado = _rename_de_mayusculas_es_real(descargas)
    motor = motor_con(
        tipo="renombrar",
        filtro={"patron_nombre": "^FOTO1$"},
        plantilla="foto1.jpg",
    )
    resultados = motor.ejecutar("prueba", descargas, simular=False)
    r = resultados[0]
    assert r.estado == ("hecho" if reflejado else "saltado")
    assert " (1)" not in (r.destino.name if r.destino else "")
    nombres = {f.name for f in descargas.iterdir()}
    if reflejado:
        assert "foto1.jpg" in nombres and "FOTO1.JPG" not in nombres
    else:
        assert "FOTO1.JPG" in nombres and "foto1.jpg" not in nombres


def test_la_accion_inexistente_da_error_claro(descargas):
    motor = motor_con(tipo="borrar")
    with pytest.raises(TareasError, match="tareas acciones"):
        motor.ejecutar("no-existe", descargas, simular=True)
