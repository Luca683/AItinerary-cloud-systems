import boto3
import json
import os
from utils.json_state import load_state, update_state

state = load_state()

# PARAMETRI ACCOUNT AWS
REGIONE = 'us-east-1'
ACCOUNT_ID = state['account_id']
STAGE_NAME = 'prod'
RESOURCE_PATH = 'classifica'

# NOMI LAMBDA FUNCTIONS
LAMBDA_POST = 'update_database'
LAMBDA_GET = 'get_top_list'

# CLIENT
apigw = boto3.client('apigateway', region_name=REGIONE)
lambda_client = boto3.client('lambda', region_name=REGIONE)

# Creazione API Gateway
response = apigw.create_rest_api(
    name='TravelAppAPI',
    description='API per aggiornare e ottenere la classifica delle città',
    endpointConfiguration={'types': ['REGIONAL']}
)
api_id = response['id']
print(f"✅ API creata: ID = {api_id}")
update_state('api_id', api_id)

# Recupero ID della risorsa root ("/")
resources = apigw.get_resources(restApiId=api_id)
root_id = next(item['id'] for item in resources['items'] if item['path'] == '/')

# Creaazione risorsa /classifica
response = apigw.create_resource(
    restApiId=api_id,
    parentId=root_id,
    pathPart=RESOURCE_PATH
)
resource_id = response['id']
print(f"✅ Risorsa '/{RESOURCE_PATH}' creata: ID = {resource_id}")

# Creazione metodi GET e POST con Lambda
for method, lambda_name in [('POST', LAMBDA_POST), ('GET', LAMBDA_GET)]:
    # Metodo
    apigw.put_method(
        restApiId=api_id,
        resourceId=resource_id,
        httpMethod=method,
        authorizationType='NONE'
    )
    print(f"✅ Metodo {method} configurato.")

    # Integrazione con Lambda
    lambda_arn = f'arn:aws:lambda:{REGIONE}:{ACCOUNT_ID}:function:{lambda_name}'
    integration_uri = f'arn:aws:apigateway:{REGIONE}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations'

    apigw.put_integration(
        restApiId=api_id,
        resourceId=resource_id,
        httpMethod=method,
        type='AWS_PROXY',
        integrationHttpMethod='POST',
        uri=integration_uri
    )
    print(f"✅ Metodo {method} integrato con Lambda '{lambda_name}'.")

    # Permessi alla Lambda
    source_arn = f'arn:aws:execute-api:{REGIONE}:{ACCOUNT_ID}:{api_id}/*/{method}/{RESOURCE_PATH}'
    statement_id = f'api-gateway-invoke-{method.lower()}'

    try:
        lambda_client.add_permission(
            FunctionName=lambda_name,
            StatementId=statement_id,
            Action='lambda:InvokeFunction',
            Principal='apigateway.amazonaws.com',
            SourceArn=source_arn
        )
        print(f"✅ Permessi concessi per il metodo {method}.")
    except lambda_client.exceptions.ResourceConflictException:
        print(f"ℹ️ Permesso già presente per il metodo {method}, ignorato.")

# Abilitazione CORS
apigw.put_method(
    restApiId=api_id,
    resourceId=resource_id,
    httpMethod='OPTIONS',
    authorizationType='NONE'
)
apigw.put_integration(
    restApiId=api_id,
    resourceId=resource_id,
    httpMethod='OPTIONS',
    type='MOCK',
    requestTemplates={
        'application/json': '{"statusCode": 200}'
    }
)
apigw.put_method_response(
    restApiId=api_id,
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
    restApiId=api_id,
    resourceId=resource_id,
    httpMethod='OPTIONS',
    statusCode='200',
    responseParameters={
        'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
        'method.response.header.Access-Control-Allow-Methods': "'GET,POST,OPTIONS'",
        'method.response.header.Access-Control-Allow-Origin': "'*'"
    },
    responseTemplates={
        'application/json': ''
    }
)
print("✅ Metodo OPTIONS configurato per CORS.")

# Deploy in stage "prod"
apigw.create_deployment(
    restApiId=api_id,
    stageName=STAGE_NAME
)
print(f"✅ API deployata nello stage '{STAGE_NAME}'.")

# Print URL finale
print(f"\n🌐 URL API BASE: https://{api_id}.execute-api.{REGIONE}.amazonaws.com/{STAGE_NAME}/{RESOURCE_PATH}")

config_path = os.path.join(os.path.dirname(__file__), "..", "webapp", "static", "config.json")

with open(config_path, "w") as f:
    json.dump({"API_URL": f"https://{api_id}.execute-api.{REGIONE}.amazonaws.com/{STAGE_NAME}"}, f)

print(f"✅ API_URL salvato in config.json")