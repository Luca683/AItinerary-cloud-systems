set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Path alla cartella lambda
LAMBDA_DIR="$SCRIPT_DIR/lambda"

BUCKET_NAME="my-travel-app-bucket2202"

aws s3api create-bucket --bucket "$BUCKET_NAME"
echo "✅ Bucket creato con successo: $BUCKET_NAME"

aws s3 cp "$LAMBDA_DIR/lambda_upd_db.zip" s3://my-travel-app-bucket2202
aws s3 cp "$LAMBDA_DIR/lambda_read_db.zip" s3://my-travel-app-bucket2202
aws s3 cp "$LAMBDA_DIR/lambda_request_it.zip" s3://my-travel-app-bucket2202
aws s3 cp "$LAMBDA_DIR/lambda_process_it.zip" s3://my-travel-app-bucket2202
aws s3 cp "$LAMBDA_DIR/lambda_result_it.zip" s3://my-travel-app-bucket2202 
echo "✅ Funzioni Lambda caricate con successo nel bucket S3: $BUCKET_NAME"