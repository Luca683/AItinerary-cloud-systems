import boto3

# Crea un client DynamoDB
dynamodb = boto3.client('dynamodb', region_name='us-east-1')  # Cambia regione se necessario

# Crea la tabella
response = dynamodb.create_table(
    TableName='CityStats',
    KeySchema=[
        {
            'AttributeName': 'city',
            'KeyType': 'HASH'  # Partition key
        }
    ],
    AttributeDefinitions=[
        {
            'AttributeName': 'city',
            'AttributeType': 'S'  # S = String
        }
    ],
    ProvisionedThroughput={
        'ReadCapacityUnits': 5,
        'WriteCapacityUnits': 5
    }
)

print("Creazione della tabella CityStats avviata...")
# Attendi che la tabella sia creata completamente
dynamodb_resource = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb_resource.Table('CityStats')
table.wait_until_exists()
print("✅ Tabella CityStats creata con successo!")