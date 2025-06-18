import boto3
from utils.json_state import update_state

ec2 = boto3.client('ec2')
region = boto3.session.Session().region_name

# Creazione VPC
vpc = ec2.create_vpc(
    CidrBlock='10.0.0.0/16',
    TagSpecifications=[{
        'ResourceType': 'vpc',
        'Tags': [{'Key': 'Name', 'Value': 'vpc-travel-app'}]
    }]
)

vpc_id = vpc['Vpc']['VpcId']
update_state("vpc_id", vpc_id)
ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsSupport={'Value': True})
ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={'Value': True})
print(f"✅ VPC creata: {vpc_id}")

# Creazione Internet Gateway e attach su VPC
igw = ec2.create_internet_gateway(
    TagSpecifications=[{
        'ResourceType': 'internet-gateway',
        'Tags': [{'Key': 'Name', 'Value': 'igw-travel-app'}]
    }]
)
igw_id = igw['InternetGateway']['InternetGatewayId']
update_state("igw_id", igw_id)
ec2.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
print(f"✅ Creato Internet Gateway: {igw_id}")

# Prime 2 AZ disponibili
az1 = ec2.describe_availability_zones()['AvailabilityZones'][0]['ZoneName']
az2 = ec2.describe_availability_zones()['AvailabilityZones'][1]['ZoneName']

# Creazione prima subnet pubblica
subnet_pub_1 = ec2.create_subnet(
    VpcId=vpc_id,
    CidrBlock='10.0.1.0/24',
    AvailabilityZone=az1,
    TagSpecifications=[{
        'ResourceType': 'subnet',
        'Tags': [{'Key': 'Name', 'Value': 'subnet-public-travel-app-1'}]
    }]
)
subnet_pub_id_1 = subnet_pub_1['Subnet']['SubnetId']
update_state("subnet_pub_id_1", subnet_pub_id_1)
ec2.modify_subnet_attribute(SubnetId=subnet_pub_id_1, MapPublicIpOnLaunch={'Value': True})
print(f"✅ Creata prima subnet pubblica: {subnet_pub_id_1} in {az1}")

# Creazione seconda subnet pubblica
subnet_pub_2 = ec2.create_subnet(
    VpcId=vpc_id,
    CidrBlock='10.0.3.0/24',  # Assicurati che non si sovrapponga alla prima
    AvailabilityZone=az2,
    TagSpecifications=[{
        'ResourceType': 'subnet',
        'Tags': [{'Key': 'Name', 'Value': 'subnet-public-travel-app-2'}]
    }]
)
subnet_pub_id_2 = subnet_pub_2['Subnet']['SubnetId']
update_state("subnet_pub_id_2", subnet_pub_id_2)
ec2.modify_subnet_attribute(SubnetId=subnet_pub_id_2, MapPublicIpOnLaunch={'Value': True})
print(f"✅ Creata seconda subnet pubblica: {subnet_pub_id_2} in {az2}")

# Creazione prima subnet privata
subnet_priv_1 = ec2.create_subnet(
    VpcId=vpc_id,
    CidrBlock='10.0.2.0/24',
    AvailabilityZone=az1,
    TagSpecifications=[{
        'ResourceType': 'subnet',
        'Tags': [{'Key': 'Name', 'Value': 'subnet-private-travel-app-1'}]
    }]
)
subnet_priv_id_1 = subnet_priv_1['Subnet']['SubnetId']
update_state("subnet_priv_id_1", subnet_priv_id_1)
print(f"✅ Creata prima subnet privata: {subnet_priv_id_1} in {az1}")

# Creazione seconda subnet privata
subnet_priv_2 = ec2.create_subnet(
    VpcId=vpc_id,
    CidrBlock='10.0.4.0/24',
    AvailabilityZone=az2,
    TagSpecifications=[{
        'ResourceType': 'subnet',
        'Tags': [{'Key': 'Name', 'Value': 'subnet-private-travel-app-2'}]
    }]
)
subnet_priv_id_2 = subnet_priv_2['Subnet']['SubnetId']
update_state("subnet_priv_id_2", subnet_priv_id_2)
print(f"✅ Creata seconda subnet privata: {subnet_priv_id_2} in {az2}")

# Creazione route table pubblica e associazione con subnet pubblica
rtb_pub = ec2.create_route_table(
    VpcId=vpc_id,
    TagSpecifications=[{
        'ResourceType': 'route-table',
        'Tags': [{'Key': 'Name', 'Value': 'rt-travel-app'}]
    }]
)
rtb_pub_id = rtb_pub['RouteTable']['RouteTableId']
update_state("rtb_pub_id", rtb_pub_id)
ec2.create_route(RouteTableId=rtb_pub_id, DestinationCidrBlock='0.0.0.0/0', GatewayId=igw_id)
ec2.associate_route_table(RouteTableId=rtb_pub_id, SubnetId=subnet_pub_id_1)
ec2.associate_route_table(RouteTableId=rtb_pub_id, SubnetId=subnet_pub_id_2)
print(f"✅ Creata route table pubblica: {rtb_pub_id}")

# Creazione NAT Gateway
eip = ec2.allocate_address(Domain='vpc')
eip_alloc_id = eip['AllocationId']
update_state("eip_alloc_id", eip_alloc_id)
print(f"✅ Allocato elastic ip: {eip}, coin id: {eip_alloc_id}")

nat_gw = ec2.create_nat_gateway(
    SubnetId=subnet_pub_id_1,
    AllocationId=eip_alloc_id,
    TagSpecifications=[{
        'ResourceType': 'natgateway',
        'Tags': [{'Key': 'Name', 'Value': 'nat-travel-app'}]
    }]
)
nat_gw_id = nat_gw['NatGateway']['NatGatewayId']
update_state("nat_gw_id", nat_gw_id)
waiter = ec2.get_waiter('nat_gateway_available')
waiter.wait(NatGatewayIds=[nat_gw_id])
print(f"✅ Creato NAT gateway: {nat_gw_id}")

# Creazione route table per NAT e associazione con subnet privata
rtb_priv = ec2.create_route_table(
    VpcId=vpc_id,
    TagSpecifications=[{
        'ResourceType': 'route-table',
        'Tags': [{'Key': 'Name', 'Value': 'rt-nat-travel-app'}]
    }]
)
rtb_priv_id = rtb_priv['RouteTable']['RouteTableId']
update_state("rtb_priv_id", rtb_priv_id)
ec2.create_route(RouteTableId=rtb_priv_id, DestinationCidrBlock='0.0.0.0/0', NatGatewayId=nat_gw_id)
ec2.associate_route_table(RouteTableId=rtb_priv_id, SubnetId=subnet_priv_id_1)
ec2.associate_route_table(RouteTableId=rtb_priv_id, SubnetId=subnet_priv_id_2)
print(f"✅ Creata route table privata: {rtb_priv_id}")

# Creazione security group

# SG per LB pubblico
pub_lb_sg = ec2.create_security_group(
    GroupName='public-LB-sg',
    Description='Security group for public load balancer',
    VpcId=vpc_id,
    TagSpecifications=[{
        'ResourceType': 'security-group',
        'Tags': [{'Key': 'Name', 'Value': 'public-LB-sg'}]
    }]
)

pub_lb_sg_id = pub_lb_sg['GroupId']
update_state("pub_lb_sg_id", pub_lb_sg_id)
print(f"✅ Creato security group per LB pubblico: {pub_lb_sg_id}")

# SG per LB privato
prv_lb_sg = ec2.create_security_group(
    GroupName='private-LB-sg',
    Description='Security group for private load balancer',
    VpcId=vpc_id,
    TagSpecifications=[{
        'ResourceType': 'security-group',
        'Tags': [{'Key': 'Name', 'Value': 'private-LB-sg'}]
    }]
)

prv_lb_sg_id = prv_lb_sg['GroupId']
update_state("prv_lb_sg_id", prv_lb_sg_id)
print(f"✅ Creato security group per LB privato: {prv_lb_sg_id}")

# SG per istanze EC2
ec2_sg = ec2.create_security_group(
    GroupName='ec2-instances-sg',
    Description='Security group for EC2 instances',
    VpcId=vpc_id,
    TagSpecifications=[{
        'ResourceType': 'security-group',
        'Tags': [{'Key': 'Name', 'Value': 'ec2-instances-sg'}]
    }]
)

ec2_sg_id = ec2_sg['GroupId']
update_state("ec2_sg_id", ec2_sg_id)
print(f"✅ Creato security group per istanza EC2: {ec2_sg_id}")

# SG per lambda
lambda_sg = ec2.create_security_group(
    GroupName='lambda-sg',
    Description='Security group for lambda',
    VpcId=vpc_id,
    TagSpecifications=[{
        'ResourceType': 'security-group',
        'Tags': [{'Key': 'Name', 'Value': 'lambda-sg'}]
    }]
)

lambda_sg_id = lambda_sg['GroupId']
update_state("lambda_sg_id", lambda_sg_id)
print(f"✅ Creato security group per Lambda: {lambda_sg_id}")

# Configurazione regole SG

# Regole SG LB pubblico

ec2.authorize_security_group_ingress( # Regola in ingresso: consente traffico HTTP (porta 80) da qualsiasi IP
    GroupId=pub_lb_sg_id,
    IpPermissions=[{
        'IpProtocol': 'tcp',
        'FromPort': 80,
        'ToPort': 80,
        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
    }]
)

ec2.authorize_security_group_egress( # Regola in uscita: consente solo traffico HTTP (porta 80) verso qualsiasi IP
    GroupId=pub_lb_sg_id,
    IpPermissions=[{
        'IpProtocol': 'tcp',
        'FromPort': 80,
        'ToPort': 80,
        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
    }]
)

# Regole SG LB privato

ec2.authorize_security_group_ingress( # Regola in ingresso: permette traffico sulla porta 11434 solo dalla Lambda
    GroupId=prv_lb_sg_id,
    IpPermissions=[{
        'IpProtocol': 'tcp',
        'FromPort': 11434,
        'ToPort': 11434,
        'UserIdGroupPairs': [{
            'GroupId': lambda_sg_id
        }]
    }]
)


ec2.authorize_security_group_egress( # Regola in uscita: permette traffico sulla porta 11434 solo verso l'istanza EC2
    GroupId=prv_lb_sg_id,
    IpPermissions=[{
        'IpProtocol': 'tcp',
        'FromPort': 11434,
        'ToPort': 11434,
        'UserIdGroupPairs': [{
            'GroupId': ec2_sg_id
        }]
    }]
)

# Regole SG istanza EC2

ec2.authorize_security_group_ingress( # Regola in ingresso 1: permette traffico TCP porta 11434 dal Load Balancer privato
    GroupId=ec2_sg_id,
    IpPermissions=[{
        'IpProtocol': 'tcp',
        'FromPort': 11434,
        'ToPort': 11434,
        'UserIdGroupPairs': [{
            'GroupId': prv_lb_sg_id
        }]
    }]
)

ec2.authorize_security_group_ingress( # Regola in ingresso 2: permette traffico HTTP (porta 80) dal Load Balancer pubblico
    GroupId=ec2_sg_id,
    IpPermissions=[{
        'IpProtocol': 'tcp',
        'FromPort': 80,
        'ToPort': 80,
        'UserIdGroupPairs': [{
            'GroupId': pub_lb_sg_id
        }]
    }]
)

# Regole SG lambda
ec2.authorize_security_group_egress( # Regola in uscita: permette traffico TCP sulla porta 11434 solo verso il LB privato
    GroupId=lambda_sg_id,
    IpPermissions=[{
        'IpProtocol': 'tcp',
        'FromPort': 11434,
        'ToPort': 11434,
        'UserIdGroupPairs': [{
            'GroupId': prv_lb_sg_id
        }]
    }]
)

print("\n✅ Regole dei security group configurate.")

# Done
print("\n✅ Architettura rete pronta.")
