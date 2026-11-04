
import json
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

OBSERVER = (
    RAIZ
    / "src"
    / "singleton_proxy_observer_tpfi"
    / "observerclient.py"
)


def test_observer_recibe_y_guarda_notificacion(tmp_path):
    salida = tmp_path / "notificaciones.jsonl"
    solicitudes = []
    errores = []
    listo = threading.Event()

    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind(("127.0.0.1", 0))
    servidor.listen(1)
    servidor.settimeout(5)

    puerto = servidor.getsockname()[1]

    def atender():
        try:
            conexion, _ = servidor.accept()

            with conexion:
                conexion.settimeout(5)

                solicitud = json.loads(
                    conexion.recv(4096).decode("utf-8")
                )
                solicitudes.append(solicitud)

                notificacion = {
                    "ACTION": "notification",
                    "DATA": {
                        "id": "TEST",
                        "sede": "UADER"
                    }
                }

                conexion.sendall(
                    json.dumps(notificacion).encode("utf-8")
                )

                listo.wait(timeout=5)

        except Exception as error:  # noqa: BLE001
            errores.append(error)

    hilo = threading.Thread(target=atender, daemon=True)
    hilo.start()

    proceso = None

    try:
        proceso = subprocess.Popen(
            [
                sys.executable,
                "-u",
                str(OBSERVER),
                "-s",
                "127.0.0.1",
                "-p",
                str(puerto),
                "-o",
                str(salida),
                "--once",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        limite = time.monotonic() + 5

        while time.monotonic() < limite:
            if salida.exists() and salida.stat().st_size > 0:
                break

            if proceso.poll() is not None:
                break

        proceso.wait(timeout=5)

        stdout, stderr = proceso.communicate()

        print("STDOUT:", stdout)
        print("STDERR:", stderr)
        print("RETURN CODE:", proceso.returncode)

        assert proceso.returncode == 0

        assert salida.exists(), "No se creÃ³ el archivo JSONL"

        lineas = salida.read_text(encoding="utf-8").splitlines()

        assert len(lineas) == 1

        notificacion = json.loads(lineas[0])

        assert notificacion["ACTION"] == "notification"
        assert notificacion["DATA"]["id"] == "TEST"
        assert notificacion["DATA"]["sede"] == "UADER"

        assert len(solicitudes) == 1
        assert solicitudes[0]["ACTION"] == "subscribe"
        assert solicitudes[0]["UUID"]

        assert not errores

    finally:
        listo.set()

        if proceso is not None:
            proceso.terminate()

            try:
                proceso.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                proceso.kill()
                proceso.communicate()

        hilo.join(timeout=5)
        servidor.close()
