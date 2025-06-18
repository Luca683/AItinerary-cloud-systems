set -e

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "✅ Account ID trovato: $ACCOUNT_ID"

CONFIG_FILE="resource-param.json"
TMP_FILE=$(mktemp)
jq --arg account_id "$ACCOUNT_ID" '.account_id = $account_id' "$CONFIG_FILE" > "$TMP_FILE" && mv "$TMP_FILE" "$CONFIG_FILE"
echo "🔄 File $CONFIG_FILE aggiornato con account_id."

python scripts/setup_network.py
echo "✅ Script setup_network.py eseguito con successo."

python scripts/create_table_CityStats.py
echo "✅ Script create_table_CityStats.py eseguito con successo."

python scripts/create_table_ItineraryRequests.py
echo "✅ Script create_table_ItineraryRequests.py eseguito con successo."

source ./scripts/s3_insert_lambda.sh
echo "✅ Script s3_insert_lambda.sh eseguito con successo."

python scripts/create_lambda.py
echo "✅ Script create_lambda.py eseguito con successo."
