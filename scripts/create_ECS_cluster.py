import boto3
import time
import base64
from utils.json_state import load_state, update_state
state = load_state()

# Configurazione iniziale
REGION = "us-east-1"
AMI_ID = "ami-09cc96665c243d56f"  # ECS-optimized Amazon Linux 2 AMI
INSTANCE_TYPE = "t3.large"
KEY_NAME = "travel-app-key"
ECS_CLUSTER_NAME = "my-ecs-cluster"
WEBAPP_IMAGE = "780614560979.dkr.ecr.us-east-1.amazonaws.com/webapp:latest"
OLLAMA_IMAGE = "780614560979.dkr.ecr.us-east-1.amazonaws.com/ollama:latest"
EXECUTION_ROLE_ARN = "arn:aws:iam::780614560979:role/LabRole"
INSTANCE_PROFILE_NAME = "LabInstanceProfile"

VPC_ID = state["vpc_id"]
SUBNET_PUB_ID = state["subnet_pub_id_1"]
SUBNET_PUB_2_ID = state["subnet_pub_id_2"]
SUBNET_PRV_ID = state["subnet_priv_id_1"]
SUBNET_PRV_2_ID = state["subnet_priv_id_2"]
LB_PUB_SG = state["pub_lb_sg_id"]
LB_PRV_SG = state["prv_lb_sg_id"]
EC2_SG = state["ec2_sg_id"]

# Client
ec2 = boto3.client("ec2", region_name=REGION)
elbv2 = boto3.client("elbv2", region_name=REGION)
autoscaling = boto3.client("autoscaling", region_name=REGION)
ecs = boto3.client("ecs", region_name=REGION)

# 3. Load Balancer pubblico (internet-facing)
lb = elbv2.create_load_balancer(
    Name="ecs-lb",
    Subnets=[SUBNET_PUB_ID, SUBNET_PUB_2_ID],
    SecurityGroups=[LB_PUB_SG],
    Scheme="internet-facing",
    Type="application",
    IpAddressType="ipv4"
)
lb_arn = lb["LoadBalancers"][0]["LoadBalancerArn"]
print("✅ Creato il load balancer pubblico")

# 3b. Load Balancer privato (internal) per Ollama, porta 11434
lb_private = elbv2.create_load_balancer(
    Name="ecs-lb-private",
    Subnets=[SUBNET_PRV_ID, SUBNET_PRV_2_ID],
    SecurityGroups=[LB_PRV_SG],  # Assicurati che il security group permetta traffico sulla 11434
    Scheme="internal",
    Type="application",
    IpAddressType="ipv4",
)
lb_private_arn = lb_private["LoadBalancers"][0]["LoadBalancerArn"]

elbv2.modify_load_balancer_attributes(
    LoadBalancerArn=lb_private_arn,
    Attributes=[
        {
            'Key': 'idle_timeout.timeout_seconds',
            'Value': '300'
        }
    ]
)
print("✅ Creato il load balancer privato")

# 4. Target group e listener pubblico per webapp (porta 80)
tg = elbv2.create_target_group(
    Name="ecs-targets",
    Protocol="HTTP",
    Port=80,
    VpcId=VPC_ID,
    TargetType="instance",
    HealthCheckIntervalSeconds=10,
    HealthCheckTimeoutSeconds=5,
    HealthyThresholdCount=2,
    UnhealthyThresholdCount=5,
    Matcher={"HttpCode": "200"}
)

tg_arn = tg["TargetGroups"][0]["TargetGroupArn"]

elbv2.modify_target_group_attributes(
    TargetGroupArn=tg_arn,
    Attributes=[
        {
            'Key': 'deregistration_delay.timeout_seconds',
            'Value': '30'
        }
    ]
)

print("✅ Creato il target group pubblico")

elbv2.create_listener(
    LoadBalancerArn=lb_arn,
    Protocol="HTTP",
    Port=80,
    DefaultActions=[{"Type": "forward", "TargetGroupArn": tg_arn}]
)
print("✅ Creato il listener pubblico")

# 4b. Target group e listener privato per Ollama (porta 11434)
tg_private_ollama = elbv2.create_target_group(
    Name="ecs-targets-private-ollama",
    Protocol="HTTP",
    Port=11434,
    VpcId=VPC_ID,
    TargetType="instance",
    HealthCheckProtocol="HTTP",
    HealthCheckPort="11434",
    HealthCheckPath="/api/tags",
    HealthCheckIntervalSeconds=10,
    HealthCheckTimeoutSeconds=5,
    HealthyThresholdCount=2,
    UnhealthyThresholdCount=5,
    Matcher={"HttpCode": "200"}
)

tg_private_ollama_arn = tg_private_ollama["TargetGroups"][0]["TargetGroupArn"]

elbv2.modify_target_group_attributes(
    TargetGroupArn=tg_private_ollama_arn,
    Attributes=[
        {
            'Key': 'deregistration_delay.timeout_seconds',
            'Value': '30'
        }
    ]
)
print("✅ Creato il target group privato per Ollama")

elbv2.create_listener(
    LoadBalancerArn=lb_private_arn,
    Protocol="HTTP",
    Port=11434,
    DefaultActions=[{"Type": "forward", "TargetGroupArn": tg_private_ollama_arn}]
)
print("✅ Creato il listener privato per Ollama")

user_data_script = f"""#!/bin/bash
echo ECS_CLUSTER={ECS_CLUSTER_NAME} >> /etc/ecs/ecs.config
"""

# 5. Launch template
lt = ec2.create_launch_template(
    LaunchTemplateName="ecs-lt",
    LaunchTemplateData={
        "ImageId": AMI_ID,
        "InstanceType": INSTANCE_TYPE,
        "KeyName": KEY_NAME,
        "IamInstanceProfile": {"Name": INSTANCE_PROFILE_NAME},
        "SecurityGroupIds": [EC2_SG],
        "UserData": base64.b64encode(user_data_script.encode("utf-8")).decode("utf-8")
    }
)
print("✅ Creato il launch template")

# 6. Auto Scaling Group
autoscaling.create_auto_scaling_group(
    AutoScalingGroupName="ecs-asg",
    LaunchTemplate={"LaunchTemplateName": "ecs-lt"},
    MinSize=1,
    MaxSize=3,
    DesiredCapacity=1,
    VPCZoneIdentifier= f"{SUBNET_PRV_ID},{SUBNET_PRV_2_ID}", 
    TargetGroupARNs=[tg_arn, tg_private_ollama_arn],  # Associa entrambi i target group all'ASG
    Tags=[{"Key": "Name", "Value": "ECS Instance", "PropagateAtLaunch": True}]
)

print("✅ Creato l'Auto Scaling Group")

# 7. ECS Cluster & Task
ecs.create_cluster(clusterName=ECS_CLUSTER_NAME)
print("✅ Creato il Cluster ECS")

# Task Definition - Webapp
ecs.register_task_definition(
    family="webapp-task",
    networkMode="bridge",
    requiresCompatibilities=["EC2"],
    cpu="256",
    memory="512",
    executionRoleArn=EXECUTION_ROLE_ARN,
    containerDefinitions=[
        {
            "name": "webapp",
            "image": WEBAPP_IMAGE,
            "memory": 512,
            "essential": True,
            "portMappings": [
                {"containerPort": 5000, "hostPort": 80}
            ]
        }
    ]
)
print("✅ Creato il task definition per webapp")

# Task Definition - Ollama
ecs.register_task_definition(
    family="ollama-task",
    networkMode="bridge",
    requiresCompatibilities=["EC2"],
    cpu="1024",
    memory="7168",
    executionRoleArn=EXECUTION_ROLE_ARN,
    containerDefinitions=[
        {
            "name": "ollama",
            "image": OLLAMA_IMAGE,
            "memory": 7168,
            "essential": True,
            "portMappings": [
                {"containerPort": 11434, "hostPort": 11434}
            ],
            "mountPoints": [
                {
                    "sourceVolume": "ollama-data",
                    "containerPath": "/root/.ollama",
                    "readOnly": False
                }
            ]
        }
    ],
    volumes=[
        {
            "name": "ollama-data",
            "host": {
                "sourcePath": "/var/app/data/ollama"
            }
        }
    ]
)

print("✅ Creato il task definition per ollama")

# ECS Services separati
# Webapp
ecs.create_service(
    cluster=ECS_CLUSTER_NAME,
    serviceName="webapp-service",
    taskDefinition="webapp-task",
    desiredCount=1,
    launchType="EC2",
    loadBalancers=[
        {
            "targetGroupArn": tg_arn,
            "containerName": "webapp",
            "containerPort": 5000
        }
    ],
    deploymentConfiguration={"maximumPercent": 100, "minimumHealthyPercent": 0}
)
print("✅ Creato il service per webapp")
# Ollama
ecs.create_service(
    cluster=ECS_CLUSTER_NAME,
    serviceName="ollama-service",
    taskDefinition="ollama-task",
    desiredCount=1,
    launchType="EC2",
    loadBalancers=[
        {
            "targetGroupArn": tg_private_ollama_arn,
            "containerName": "ollama",
            "containerPort": 11434
        }
    ],
    deploymentConfiguration={"maximumPercent": 100, "minimumHealthyPercent": 0}
)
print("✅ Creato il service per ollama")

print("Tutto creato correttamente: LB (pubblico e privato), EC2, ECS cluster e service.")