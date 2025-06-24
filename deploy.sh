set -e

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "✅ Account ID trovato: $ACCOUNT_ID"

CONFIG_FILE="resource-param.json"
TMP_FILE=$(mktemp)
jq --arg account_id "$ACCOUNT_ID" '.account_id = $account_id' "$CONFIG_FILE" > "$TMP_FILE" && mv "$TMP_FILE" "$CONFIG_FILE"
#echo "🔄 File $CONFIG_FILE aggiornato con account_id."

python scripts/setup_network.py
echo "🎉 Script setup_network.py eseguito con successo."

python scripts/create_table_CityStats.py
echo "🎉 Script create_table_CityStats.py eseguito con successo."

python scripts/create_table_ItineraryRequests.py
echo "🎉 Script create_table_ItineraryRequests.py eseguito con successo."

source ./scripts/s3_insert_lambda.sh
echo "🎉 Script s3_insert_lambda.sh eseguito con successo."

python scripts/create_lambda.py
echo "🎉 Script create_lambda.py eseguito con successo."

python scripts/create_API_classifica.py
echo "🎉 Script create_API_classifica.py eseguito con successo."

python scripts/add_route_richiesta_itinerario.py
echo "🎉 Script add_route_richiesta_itinerario.py eseguito con successo."

python scripts/add_route_risultato_itinerario.py
echo "🎉 Script add_route_risultato_itinerario.py eseguito con successo."

python scripts/create_queue_richieste_ollama.py
echo "🎉 Script create_queue_richieste_ollama.py eseguito con successo."

python scripts/create_sns_topic.py
echo "🎉 Script create_sns_topic.py  eseguito con successo."

source ./scripts/create_docker_images_ecr.sh
echo "🎉 Script create_docker_images_ecr.sh eseguito con successo."

python scripts/create_ECS_cluster.py
echo "🎉 Script create_ECS_cluster.py eseguito con successo."