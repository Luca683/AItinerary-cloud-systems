import boto3
from utils.json_state import load_state
state = load_state()

# CONFIGURAZIONE
REGIONE = 'us-east-1'
ACCOUNT_ID = state['account_id']
STAGE_NAME = 'prod'
API_ID = state['api_id'] 
RESOURCE_PATH = 'richiesta-itinerario'
LAMBDA_POST = 'request_itinerary'  

# CLIENT AWS
apigw = boto3.client('apigateway', region_name=REGIONE)
lambda_client = boto3.client('lambda', region_name=REGIONE)

# ID risorsa root "/"
resources = apigw.get_resources(restApiId=API_ID)
root_id = next(item['id'] for item in resources['items'] if item['path'] == '/')

# Creazione risorsa /richiesta-itinerario
response = apigw.create_resource(
    restApiId=API_ID,
    parentId=root_id,
    pathPart=RESOURCE_PATH
)
resource_id = response['id']
print(f"✅ Risorsa '/{RESOURCE_PATH}' creata con ID = {resource_id}")

# Metodo POST
apigw.put_method(
    restApiId=API_ID,
    resourceId=resource_id,
    httpMethod='POST',
    authorizationType='NONE'
)

lambda_arn = f'arn:aws:lambda:{REGIONE}:{ACCOUNT_ID}:function:{LAMBDA_POST}'
integration_uri = f'arn:aws:apigateway:{REGIONE}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations'

apigw.put_integration(
    restApiId=API_ID,
    resourceId=resource_id,
    httpMethod='POST',
    type='AWS_PROXY',
    integrationHttpMethod='POST',
    uri=integration_uri
)

# Permessi Lambda
source_arn = f'arn:aws:execute-api:{REGIONE}:{ACCOUNT_ID}:{API_ID}/*/POST/{RESOURCE_PATH}'
try:
    lambda_client.add_permission(
        FunctionName=LAMBDA_POST,
        StatementId='api-gateway-invoke-post',
        Action='lambda:InvokeFunction',
        Principal='apigateway.amazonaws.com',
        SourceArn=source_arn
    )
    print("✅ Permessi concessi per POST.")
except lambda_client.exceptions.ResourceConflictException:
    print("ℹ️ Permesso già presente per POST, ignorato.")

# CORS (OPTIONS)
apigw.put_method(
    restApiId=API_ID,
    resourceId=resource_id,
    httpMethod='OPTIONS',
    authorizationType='NONE'
)
apigw.put_integration(
    restApiId=API_ID,
    resourceId=resource_id,
    httpMethod='OPTIONS',
    type='MOCK',
    requestTemplates={
        'application/json': '{"statusCode": 200}'
    }
)
apigw.put_method_response(
    restApiId=API_ID,
    resourceId=resource_id,
    httpMethod='OPTIONS',
    statusCode='200',
    responseModels={
        'application/json': 'Empty'
    },
    responseParameters={
        'method.response.header.Access-Control-Allow-Headers': True,
        'method.response.header.Access-Control-Allow-Methods': True,
        'method.response.header.Access-Control-Allow-Origin': True
    }
)
apigw.put_integration_response(
    restApiId=API_ID,
    resourceId=resource_id,
    httpMethod='OPTIONS',
    statusCode='200',
    responseParameters={
        'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
        'method.response.header.Access-Control-Allow-Methods': "'POST,OPTIONS'",
        'method.response.header.Access-Control-Allow-Origin': "'*'"
    },
    responseTemplates={
        'application/json': ''
    }
)
print("✅ Metodo OPTIONS configurato per CORS.")

# Deploy
apigw.create_deployment(restApiId=API_ID, stageName=STAGE_NAME)
print(f"✅ API deployata nello stage '{STAGE_NAME}'.")
print(f"🌐 URL API: https://{API_ID}.execute-api.{REGIONE}.amazonaws.com/{STAGE_NAME}/{RESOURCE_PATH}")