import boto3


class CorporateLogSingleton:
    _instancia = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)

            cls._instancia.dynamodb = boto3.resource(
                "dynamodb",
                region_name="us-east-1"
            )

        return cls._instancia

    def guardar_log(self, log):
        tabla = self.dynamodb.Table("CorporateLog")

        tabla.put_item(Item=log)

        return log