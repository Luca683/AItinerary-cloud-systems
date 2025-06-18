import json
import uuid
import boto3
import time

dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')
sts = boto3.client('sts')
account_id = sts.get_caller_identity()['Account']

DYNAMODB_TABLE = 'ItineraryRequests'
SQS_URL = f'https://sqs.us-east-1.amazonaws.com/{account_id}/richieste-ollama'

def lambda_handler(event, context):
    body = json.loads(event['body'])
    citta = body['citta']
    giorni = body['giorni']
    request_id = str(uuid.uuid4())

    if not citta or not giorni:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Parametri mancanti"})
        }
    
    try:
        # Salva stato iniziale su DynamoDB
        table = dynamodb.Table(DYNAMODB_TABLE)
        table.put_item(Item={
            'request_id': request_id,
            'status': 'pending',
            'timestamp': int(time.time()),
            'citta': citta,
            'giorni': giorni
        })

        print(f"Ho caricato una nuova richiesta nel database: {request_id}")

        # Invia a SQS
        sqs.send_message(
            QueueUrl=SQS_URL,
            MessageBody=json.dumps({
                'request_id': request_id,
                'citta': citta,
                'giorni': giorni
            })
        )

        print(f"Ho caricato un nuovo messaggio nella coda: {request_id}")
        
        return {
            'statusCode': 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS,POST",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            'body': json.dumps({ 'request_id': request_id })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS,POST",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            'body': json.dumps({'error': str(e)})
        }