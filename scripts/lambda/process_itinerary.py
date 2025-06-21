import json
import boto3
import requests

dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
table = dynamodb.Table('ItineraryRequests')
elbv2 = boto3.client('elbv2', region_name='us-east-1')

# Nome del LB privato
LB_NAME = 'ecs-lb-private'

# Recupera tutti i Load Balancer
lbs = elbv2.describe_load_balancers()

# Cerca quello con il nome desiderato
for lb in lbs['LoadBalancers']:
    if lb['LoadBalancerName'] == LB_NAME:
        dns_name = lb['DNSName']
        break
# Ricerca topic SNS
TOPIC_NAME = 'email-itinerary-notification'

list_topics_sns = sns.list_topics()
for topic in list_topics_sns['Topics']:
    arn_topic = topic['TopicArn']
    if arn_topic.endswith(f":{TOPIC_NAME}"):
        break

OLLAMA_URL = f'http://{dns_name}:11434/api/generate'

def lambda_handler(event, context):
    print("Lambda handler avviato. Event:", event)
    
    for record in event['Records']:
        payload = json.loads(record['body'])  # Fallisce se non è JSON
        request_id = payload['request_id']    # Fallisce se mancano i campi
        citta = payload['citta']
        giorni = payload['giorni']
        email = payload['email']

        print(f"Elaboro richiesta: request_id={request_id}, citta={citta}, giorni={giorni}")

        try:
            # CHIAMATA A OLLAMA
            prompt = f"Crea un itinerario di {giorni} giorni a {citta}, in italiano."
            print(f"Invio prompt a Ollama: {prompt}")
            response = requests.post(OLLAMA_URL, json={
                "model": "gemma3:1b",
                "prompt": prompt,
                "stream": False
            }, timeout=600)
            response.raise_for_status()
            risposta = response.json().get("response", "Nessuna risposta ricevuta.")
            status = 'completed'
            print(f"Stato della risposta: {status}")
        except Exception as ollama_error:
            print("❌ Errore Ollama:", str(ollama_error))
            risposta = f"Errore Ollama: {str(ollama_error)}"
            status = 'failed'

        try:
            # AGGIORNAMENTO DYNAMODB
            print(f"Tento aggiornamento DynamoDB per request_id={request_id}...")
            table.update_item(
                Key={'request_id': request_id},
                UpdateExpression='SET #s = :s, risposta = :r',
                ExpressionAttributeNames={'#s': 'status'},
                ExpressionAttributeValues={
                    ':s': status,
                    ':r': risposta
                },
                ConditionExpression='attribute_exists(request_id)'
            )
            print("✅ Aggiornamento DynamoDB completato.")
        except Exception as db_error:
            print("❌ Errore DynamoDB:", str(db_error))
        
        try:
            # SNS publish
            print(f"Invio messaggio itinerario nel topic: {arn_topic}")
            
            subject = "Il tuo itinerario è pronto!" if status == "completed" else "Errore nella generazione"
            sns.publish(
                TopicArn=arn_topic,
                Subject=subject,
                Message=risposta
            )
            print(f"📧 Notifica SNS inviata a {email}")
        except Exception as sns_error:
            print("❌ Errore invio notifica SNS:", str(sns_error))
