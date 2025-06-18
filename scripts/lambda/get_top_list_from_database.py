# Lambda: getTopClassifica
import boto3
import json

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('CityStats')

def lambda_handler(event, context):
    try:
        # Scan tutta la tabella
        response = table.scan()
        items = response.get('Items', [])

        # Ordina per conteggio decrescente
        items.sort(key=lambda x: x.get('count', 0), reverse=True)

        # Prendi top 5
        top_5 = items[:5]

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS,GET",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            "body": json.dumps(top_5, default=str)  # Usa default=str per gestire eventuali tipi non serializzabili
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS,GET",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            "body": json.dumps({"error": str(e)})
        }