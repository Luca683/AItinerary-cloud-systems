set -e

CONFIG_FILE="$(dirname "$0")/resource-param.json"
ACCOUNT_ID=$(jq -r '.account_id' "$CONFIG_FILE")

aws ecr create-repository --repository-name webapp
aws ecr create-repository --repository-name ollama

aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

cd "$(dirname "$0")/ollama"
docker build -t ollama .
cd ../webapp
docker build -t webapp .
cd ..

# Parametrizzare l'ID dell'account nel tag
docker tag webapp:latest $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/webapp:latest                               
docker tag ollama:latest $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/ollama:latest
docker push $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/ollama:latest 
docker push $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/webapp:latest

