
import argparse
import json
import socket
import threading
import uuid
from datetime import UTC, datetime

from core.log_singleton import CorporateLogSingleton
from core.observer import CorporateDataObserver
from core.proxy import CorporateDataProxy
from core.singleton import DynamoDBSingleton

# Argumentos de la terminal
parser = argparse.ArgumentParser()
parser.add_argument("-p", "--port", type=int, default=8080)
parser.add_argument("-v", "--verbose", action="store_true")
args = parser.parse_args()

HOST = "localhost"
PORT = args.port


# Instancias que se inicializan al iniciar el servidor
db = None
proxy = None
observer = None
log_db = None





# Función que atiende a un cliente
def atender_cliente(conexion, direccion):

    if args.verbose:
        print("Cliente conectado:", direccion)

    try:
        # Recibir el mensaje del cliente
        mensaje = conexion.recv(4096)

        if not mensaje:
            return

        if args.verbose:
            print("Mensaje recibido:", mensaje)

        # Convertir los bytes a un diccionario Python
        datos = json.loads(mensaje.decode("utf-8"))

        accion = datos["ACTION"]

        if args.verbose:
            print("Acción recibida:", accion)
            print("ID recibido:", datos.get("ID"))

        # Registrar auditoría en CorporateLog
        log = {
            "id": str(uuid.uuid4()),
            "UUID": datos["UUID"],
            "SESSION": str(uuid.uuid4()),
            "ACTION": accion,
            "TIMESTAMP": datetime.now(UTC).isoformat()
        }

        if accion == "get":
            log["ID"] = datos["ID"]

        log_db.guardar_log(log)

        if args.verbose:
            print("Auditoría guardada en CorporateLog")

        # Acción GET
        if accion == "get":
            id_registro = datos["ID"]

            registro = db.obtener_registro(id_registro)

            respuesta = {
                "ACTION": "get",
                "DATA": registro
            }

            mensaje_respuesta = json.dumps(respuesta, indent=4, ensure_ascii=False, default=str)
            conexion.sendall(mensaje_respuesta.encode("utf-8"))

        # Acción LIST
        elif accion == "list":
            registros = db.listar_registros()

            respuesta = {
                "ACTION": "list",
                "DATA": registros
            }

            mensaje_respuesta = json.dumps(respuesta, indent=4, ensure_ascii=False, default=str)
            conexion.sendall(mensaje_respuesta.encode("utf-8"))

        # Acción SET
        elif accion == "set":
            registro = proxy.guardar_registro(datos)

            # Notificar a los clientes suscritos
            observer.notificar(registro["id"], registro)

            respuesta = {
                "ACTION": "set",
                "DATA": registro
            }

            mensaje_respuesta = json.dumps(respuesta, indent=4, ensure_ascii=False, default=str)
            conexion.sendall(mensaje_respuesta.encode("utf-8"))

        # Acción SUBSCRIBE
        elif accion == "subscribe":
            uuid_cliente = datos["UUID"]

            observer.suscribir(uuid_cliente, conexion)

            if args.verbose:
                print(f"Cliente {uuid_cliente} suscrito")

            # Mantener la conexión abierta
            while conexion.recv(1024):
                pass

    finally:
        conexion.close()

        if args.verbose:
            print("Cliente desconectado:", direccion)


# Aceptar clientes continuamente
def iniciar_servidor():
    global db, proxy, observer, log_db

    db = DynamoDBSingleton()
    proxy = CorporateDataProxy()
    observer = CorporateDataObserver()
    log_db = CorporateLogSingleton()

    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        servidor.bind((HOST, PORT))
        servidor.listen()

        print(f"Servidor escuchando en {HOST}:{PORT}...")

        while True:
            conexion, direccion = servidor.accept()

            hilo = threading.Thread(
                target=atender_cliente,
                args=(conexion, direccion),
                daemon=True
            )

            hilo.start()
    finally:
        servidor.close()


if __name__ == "__main__":
    iniciar_servidor()