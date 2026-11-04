
import argparse
import json
import socket
import time
import uuid

parser = argparse.ArgumentParser()

parser.add_argument("-s", "--server", default="localhost")
parser.add_argument("-p", "--port", type=int, default=8080)
parser.add_argument("-o", "--output")
parser.add_argument("-v", "--verbose", action="store_true")
parser.add_argument("--once", action="store_true")

args = parser.parse_args()

HOST = args.server
PORT = args.port

uuid_cliente = str(uuid.getnode())

datos = {
    "UUID": uuid_cliente,
    "ACTION": "subscribe"
}

while True:
    cliente = None

    try:
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect((HOST, PORT))

        if args.verbose:
            print("Conectado al servidor:", HOST, PORT)

        mensaje = json.dumps(datos)
        cliente.sendall(mensaje.encode("utf-8"))

        print("Cliente suscrito. Esperando notificaciones...")

        if args.verbose:
            print("UUID del cliente:", uuid_cliente)
            print("Solicitud enviada:", datos)

        while True:
            respuesta = cliente.recv(4096)

            if not respuesta:
                print("El servidor se desconectó")
                break

            notificacion = json.loads(respuesta.decode("utf-8"))
            print("Notificación recibida:", notificacion)

            if args.output:
                with open(args.output, "a", encoding="utf-8") as archivo:
                    archivo.write(
                        json.dumps(notificacion, ensure_ascii=False) + "\n"
                    )

                if args.verbose:
                    print("Notificación guardada en:", args.output)

            # Finalizar después de una notificación solo si se usa --once
            if args.once:
                raise SystemExit(0)

    except (ConnectionError, OSError) as error:
        print("Error de conexión:", error)

    finally:
        if cliente is not None:
            cliente.close()

    print("Reintentando conexión en 30 segundos...")
    time.sleep(30)
