import json
import socket
import subprocess
import sys
import threading
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]

CLIENTE = (
    RAIZ
    / "src"
    / "singleton_proxy_observer_tpfi"
    / "singletonclient.py"
)


def test_cliente_servidor_caido(tmp_path):
    entrada = tmp_path / "entrada.json"

    entrada.write_text(
        json.dumps({
            "UUID": "123456",
            "ACTION": "get",
            "ID": "TEST"
        }),
        encoding="utf-8"
    )

    resultado = subprocess.run(
        [
            sys.executable,
            str(CLIENTE),
            "-i",
            str(entrada)
        ],
        capture_output=True,
        text=True,
        timeout=10,
        check=False)

    assert resultado.returncode != 0
    assert "Error: no se pudo conectar" in resultado.stdout



def test_cliente_get(tmp_path):
    entrada = tmp_path / "entrada_get.json"

    entrada.write_text(
        json.dumps({
            "UUID": "123456",
            "ACTION": "get",
            "ID": "TEST"
        }),
        encoding="utf-8"
    )

    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(("localhost", 8080))
    servidor.listen(1)
    servidor.settimeout(5)

    def atender_cliente():
        conexion, _ = servidor.accept()
        with conexion:
            solicitud = json.loads(conexion.recv(4096).decode("utf-8"))

            assert solicitud["ACTION"] == "get"
            assert solicitud["ID"] == "TEST"

            respuesta = {
                "ACTION": "get",
                "DATA": {"id": "TEST", "sede": "UADER"}
            }

            conexion.sendall(json.dumps(respuesta).encode("utf-8"))

    hilo = threading.Thread(target=atender_cliente)
    hilo.start()

    try:
        resultado = subprocess.run(
            [sys.executable, str(CLIENTE), "-i", str(entrada)],
            capture_output=True,
            text=True,
            timeout=10,
        check=False)
    finally:
        hilo.join(timeout=6)
        servidor.close()

    assert resultado.returncode == 0
    assert '"sede": "UADER"' in resultado.stdout






@pytest.mark.parametrize(
    "accion, datos, respuesta",
    [
        (
            "set",
            {"UUID": "123456", "ACTION": "set", "ID": "TEST", "sede": "UADER"},
            {"ACTION": "set", "DATA": {"id": "TEST", "sede": "UADER"}},
        ),
        (
            "list",
            {"UUID": "123456", "ACTION": "list"},
            {"ACTION": "list", "DATA": [{"id": "TEST", "sede": "UADER"}]},
        ),
    ],
)
def test_cliente_set_y_list(tmp_path, accion, datos, respuesta):
    entrada = tmp_path / f"entrada_{accion}.json"
    entrada.write_text(json.dumps(datos), encoding="utf-8")

    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(("localhost", 8080))
    servidor.listen(1)
    servidor.settimeout(5)

    errores = []

    def atender_cliente():
        try:
            conexion, _ = servidor.accept()
            with conexion:
                solicitud = json.loads(
                    conexion.recv(4096).decode("utf-8")
                )

                assert solicitud == datos

                conexion.sendall(
                    json.dumps(respuesta).encode("utf-8")
                )
        except Exception as error:  # noqa: BLE001
            errores.append(error)

    hilo = threading.Thread(target=atender_cliente)
    hilo.start()

    try:
        resultado = subprocess.run(
            [sys.executable, str(CLIENTE), "-i", str(entrada)],
            capture_output=True,
            text=True,
            timeout=10,
        check=False)
    finally:
        hilo.join(timeout=6)
        servidor.close()

    assert not errores, f"Error del servidor simulado: {errores}"
    assert resultado.returncode == 0, resultado.stderr
    assert json.dumps(respuesta, indent=4, ensure_ascii=False) in resultado.stdout



def test_cliente_sin_argumentos():
    resultado = subprocess.run(
        [sys.executable, str(CLIENTE)],
        capture_output=True,
        text=True,
        timeout=10,
    check=False)

    assert resultado.returncode != 0
    assert "required" in resultado.stderr


def test_cliente_archivo_inexistente(tmp_path):
    archivo = tmp_path / "no_existe.json"

    resultado = subprocess.run(
        [sys.executable, str(CLIENTE), "-i", str(archivo)],
        capture_output=True,
        text=True,
        timeout=10,
    check=False)

    assert resultado.returncode != 0
    assert "FileNotFoundError" in resultado.stderr


def test_cliente_accion_invalida(tmp_path):
    entrada = tmp_path / "entrada_invalida.json"

    entrada.write_text(
        json.dumps({
            "UUID": "123456",
            "ACTION": "eliminar",
            "ID": "TEST"
        }),
        encoding="utf-8"
    )

    resultado = subprocess.run(
        [sys.executable, str(CLIENTE), "-i", str(entrada)],
        capture_output=True,
        text=True,
        timeout=10,
    check=False)

    assert "Error: ACTION debe ser get, set o list" in resultado.stdout
