import argparse
import json
import socket
import sys

parser = argparse.ArgumentParser()

parser.add_argument("-i", "--input", required=True)
parser.add_argument("-o", "--output")
parser.add_argument("-v", "--verbose", action="store_true")

args = parser.parse_args()

# -i / --input   → archivo JSON de entrada
# -o / --output  → archivo donde guardar la respuesta
# -v / --verbose → muestra información de diagnóstico


# Leer el JSON de entrada
with open(args.input, "r", encoding="utf-8") as archivo:
    datos = json.load(archivo)

# Validar la acción
accion = datos.get("ACTION")

if accion not in ["get", "set", "list"]:
    print("Error: ACTION debe ser get, set o list")
    sys.exit(1)

if args.verbose:
    print("JSON de entrada:", datos)
    print("Acción solicitada:", accion)


# Conexión con el servidor SingletonProxyObserverTPFI
HOST = "localhost"
PORT = 8080

# AF_INET     → comunicación usando IPv4
# SOCK_STREAM → comunicación usando TCP
cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cliente.settimeout(5)

try:
    cliente.connect((HOST, PORT))
except OSError as error:
    print(f"Error: no se pudo conectar al servidor: {error}")
    cliente.close()
    raise SystemExit(1)

if args.verbose:
    print("Conectado al servidor")


# Enviar el JSON al servidor
mensaje = json.dumps(datos)
cliente.sendall(mensaje.encode("utf-8"))

if args.verbose:
    print("JSON enviado al servidor")


# Recibir la respuesta
respuesta = b""

while True:
    parte = cliente.recv(4096)

    if not parte:
        break

    respuesta += parte

datos_respuesta = json.loads(respuesta.decode("utf-8"))

print("Respuesta del servidor:")
print(json.dumps(datos_respuesta, indent=4, ensure_ascii=False))

cliente.close()


# Guardar la respuesta si se indicó -o
if args.output:
    with open(args.output, "w", encoding="utf-8") as archivo:
        json.dump(datos_respuesta, archivo, indent=4, ensure_ascii=False)

    if args.verbose:
        print("Respuesta guardada en:", args.output)
