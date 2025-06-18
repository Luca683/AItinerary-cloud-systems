# Lambda: updateClassifica
import boto3
import json

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('CityStats')

def lambda_handler(event, context):
    body = json.loads(event['body'])
    citta = body.get('citta')

    if not citta:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Parametro 'citta' mancante"})
        }

    try:
        table.update_item(
            Key={'city': citta},
            UpdateExpression='SET #cnt = if_not_exists(#cnt, :zero) + :uno',
            ExpressionAttributeNames={
                '#cnt': 'count'  # alias per l'attributo count
            },
            ExpressionAttributeValues={
                ':uno': 1,
                ':zero': 0
            }
        )

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS,POST",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            "body": json.dumps({"message": f"Classifica aggiornata per {citta}"})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS,POST",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            "body": json.dumps({"error": str(e)})
        }