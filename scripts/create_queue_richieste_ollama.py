import boto3
import time
import botocore.exceptions

sqs = boto3.client('sqs', region_name='us-east-1')
lambda_client = boto3.client('lambda', region_name='us-east-1')

QUEUE_NAME = 'richieste-ollama'
LAMBDA_NAME = 'process_itinerary'

# Crea la coda SQS
response = sqs.create_queue(QueueName=QUEUE_NAME)
queue_url = response['QueueUrl']

# Visibility timeout a 600 secondi (uguale al timeout Lambda)
sqs.set_queue_attributes(
    QueueUrl=queue_url,
    Attributes={
        'VisibilityTimeout': '600'
    }
)

# Ottieni l'ARN della coda
queue_attributes = sqs.get_queue_attributes(
    QueueUrl=queue_url,
    AttributeNames=['QueueArn']
)
queue_arn = queue_attributes['Attributes']['QueueArn']
print(f"✅ Coda creata: {queue_arn}")

# Ottieni l'ARN della Lambda
lambda_arn = lambda_client.get_function(FunctionName=LAMBDA_NAME)['Configuration']['FunctionArn']

# Dai permesso alla coda di invocare la Lambda
try:
    lambda_client.add_permission(
        FunctionName=LAMBDA_NAME,
        StatementId='Allow-SQS-Trigger',
        Action='lambda:InvokeFunction',
        Principal='sqs.amazonaws.com',
        SourceArn=queue_arn
    )
    print("✅ Permesso concesso a SQS di invocare la Lambda.")
except lambda_client.exceptions.ResourceConflictException:
    print("ℹ️ Permesso già esistente: nessuna azione necessaria.")

# Quando elimini la coda SQS, AWS non elimina automaticamente il trigger (EventSourceMapping) collegato alla Lambda.
# Quando ricrei una coda con lo stesso nome, riceve un nuovo ARN, ma il vecchio EventSourceMapping continua a esistere, puntando a un ARN che non è più valido.
# Quindi, prima di creare un nuovo trigger, rimuoviamo i vecchi EventSourceMapping associati alla Lambda.
existing_mappings = lambda_client.list_event_source_mappings(FunctionName=LAMBDA_NAME)

for mapping in existing_mappings['EventSourceMappings']:
    if mapping['EventSourceArn'] == queue_arn:
        uuid = mapping['UUID']
        lambda_client.delete_event_source_mapping(UUID=mapping['UUID'])
        print(f"🗑️ Rimosso vecchio trigger con UUID: {mapping['UUID']}")

        print("⏳ Attendo che il mapping venga eliminato completamente...")
        while True:
            try:
                check = lambda_client.get_event_source_mapping(UUID=uuid)
                if check['State'] in ['Deleting', 'Creating']:
                    time.sleep(2)
                else:
                    break
            except botocore.exceptions.ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'ResourceNotFoundException':
                    # Mapping eliminato, esci dal ciclo
                    break
                else:
                    # Altri errori: rilancia
                    raise
        print("✅ Mapping eliminato.")

# Collega la Lambda alla coda (trigger SQS → Lambda)
lambda_client.create_event_source_mapping(
    EventSourceArn=queue_arn,
    FunctionName=LAMBDA_NAME,
    Enabled=True,
    BatchSize=1  # uno per volta
)
print("✅ Trigger da SQS a Lambda configurato.")