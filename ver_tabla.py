import boto3

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
tabla = dynamodb.Table("CorporateLog")

respuesta = tabla.scan(
    FilterExpression=boto3.dynamodb.conditions.Attr("UUID").eq("123456")
)

for log in respuesta.get("Items", []):
    print(log)