import boto3

# Crea un client DynamoDB
dynamodb = boto3.client('dynamodb', region_name='us-east-1')  # Cambia regione se serve

# Crea la tabella
response = dynamodb.create_table(
    TableName='ItineraryRequests',
    KeySchema=[
        {
            'AttributeName': 'request_id',
            'KeyType': 'HASH'  # Partition key
        }
    ],
    AttributeDefinitions=[
        {
            'AttributeName': 'request_id',
            'AttributeType': 'S'  # S = String
        }
    ],
    ProvisionedThroughput={
        'ReadCapacityUnits': 5,
        'WriteCapacityUnits': 5
    }
)

print("Creazione della tabella ItineraryRequests avviata...")
# Attendi che la tabella sia creata completamente
dynamodb_resource = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb_resource.Table('ItineraryRequests')
table.wait_until_exists()

print("✅ Tabella ItineraryRequests creata con successo!")