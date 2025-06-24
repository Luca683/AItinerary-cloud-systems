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

print("🔄 Creazione della tabella CityStats avviata...")
# Attendi che la tabella sia creata completamente
dynamodb_resource = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb_resource.Table('CityStats')
table.wait_until_exists()
print("✅ Tabella CityStats creata con successo!")

cities = [
    {"city": "Budapest", "count": 120},
    {"city": "Madrid", "count": 95},
    {"city": "Firenze", "count": 85},
    {"city": "Amsterdam", "count": 60},
    {"city": "New York", "count": 40},
    {"city": "Roma", "count": 30},
    {"city": "Lisbona", "count": 50},
    {"city": "Siviglia", "count": 70},
    {"city": "Praga", "count": 55},
    {"city": "Venezia", "count": 25}
]

# Inserisci ciascun elemento
for item in cities:
    table.put_item(Item=item)

print("✅ Elementi inseriti correttamente nella tabella CityStats!")