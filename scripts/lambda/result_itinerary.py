import json
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ItineraryRequests')

def lambda_handler(event, context):
    request_id = event['queryStringParameters']['requestId']

    try:
        response = table.get_item(Key={'request_id': request_id})
        item = response.get('Item')

        if not item:
            return {
                'statusCode': 404,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "OPTIONS,POST",
                    "Access-Control-Allow-Headers": "Content-Type"
                },
                'body': json.dumps({ 'error': 'Richiesta non trovata.' })
            }

        return {
            'statusCode': 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS,POST",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            'body': json.dumps({
                'status': item['status'],
                'risposta': item.get('risposta', '')
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS,POST",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            'body': json.dumps({ 'error': str(e) })
        }