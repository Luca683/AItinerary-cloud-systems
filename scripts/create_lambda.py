import boto3
import subprocess
from utils.json_state import load_state

ec2_client = boto3.client('ec2')
client = boto3.client('lambda', region_name='us-east-1')

state = load_state()
account_id = state['account_id']
subnet_priv_id_1 = state['subnet_priv_id_1']
subnet_priv_id_2 = state['subnet_priv_id_2']
lambda_sg_id = state['lambda_sg_id']

ROLE = f'arn:aws:iam::{account_id}:role/LabRole' #ARN del ruolo IAM che ha accesso a DynamoDB (LabRole)

# Prima assicuriamoci di caricare sul bucket S3 gli zip delle funzioni lambda con il comando: aws s3 cp lambda_function.zip s3://my-travel-app-bucket2202 

# Prima Lambda: update_database
response1 = client.create_function(
    FunctionName='update_database', # Questo è il nome che viene dato alla funzione lambda visibile nella console AWS.
    Runtime='python3.10',
    Role=ROLE,
    Handler='update_database.lambda_handler', # Qui si deve inserire il nome del file Python che contiene la funzione lambda_handler: nomefile.lambda_handler
    Code={
        'S3Bucket': 'my-travel-app-bucket2202',
        'S3Key': 'lambda_upd_db.zip'
    }
)
print(f"✅ Lambda 1 update_database creata")

# Seconda Lambda: get_top_list
response2 = client.create_function(
    FunctionName='get_top_list',
    Runtime='python3.10',
    Role=ROLE,
    Handler='get_top_list_from_database.lambda_handler',
    Code={
        'S3Bucket': 'my-travel-app-bucket2202',
        'S3Key': 'lambda_read_db.zip'
    },
)
print(f"✅ Lambda 2 get_top_list creata")

# Terza Lambda: request_itinerary
response3 = client.create_function(
    FunctionName='request_itinerary',
    Runtime='python3.10',
    Role=ROLE,
    Handler='request_itinerary.lambda_handler',
    Code={
        'S3Bucket': 'my-travel-app-bucket2202',
        'S3Key': 'lambda_request_it.zip'
    },
)

print(f"✅ Lambda 3 request_itinerary creata")

# Quarta Lambda: process_itinerary
response4 = client.create_function(
    FunctionName='process_itinerary',
    Runtime='python3.10',
    Role=ROLE,
    Handler='process_itinerary.lambda_handler',
    Code={
        'S3Bucket': 'my-travel-app-bucket2202',
        'S3Key': 'lambda_process_it.zip'
    },
    VpcConfig={
        'SubnetIds': [subnet_priv_id_1, subnet_priv_id_2],
        'SecurityGroupIds': [lambda_sg_id]
    },
    Timeout=600,
)

print(f"✅ Lambda 4 process_itinerary creata")

# Quinta Lambda: result_itinerary
response5 = client.create_function(
    FunctionName='result_itinerary',
    Runtime='python3.10',
    Role=ROLE,
    Handler='result_itinerary.lambda_handler',
    Code={
        'S3Bucket': 'my-travel-app-bucket2202',
        'S3Key': 'lambda_result_it.zip'
    },
)
print(f"✅ Lambda 5 result_itinerary creata")
