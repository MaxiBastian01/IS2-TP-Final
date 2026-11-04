
import boto3


class DynamoDBSingleton:
    _instancia = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)

            cls._instancia.dynamodb = boto3.resource(
                "dynamodb",
                region_name="us-east-1"
            )

        return cls._instancia

    def obtener_registro(self, id):
        tabla = self.dynamodb.Table("CorporateData")

        respuesta = tabla.get_item(
            Key={"id": id}
        )

        return respuesta.get("Item")

    def listar_registros(self):
        tabla = self.dynamodb.Table("CorporateData")

        respuesta = tabla.scan()

        registros = respuesta.get("Items", [])# esto hace que si no hay items devuelva una lista vacia y no un none

        while "LastEvaluatedKey" in respuesta:
            respuesta = tabla.scan(
                ExclusiveStartKey=respuesta["LastEvaluatedKey"]
            )
            registros.extend(respuesta.get("Items", []))

        return registros

    def guardar_registro(self, registro):
        tabla = self.dynamodb.Table("CorporateData")
        tabla.put_item(Item=registro)
        return registro