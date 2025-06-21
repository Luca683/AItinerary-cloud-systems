import boto3
from utils.json_state import update_state
import time
sns = boto3.client('sns')


response = sns.create_topic(Name="email-itinerary-notification")
print("✅ Topic SNS creato, ARN:", response['TopicArn'])
update_state('sns_topic_arn', response['TopicArn'])

# Per test

# sns.subscribe(
#     TopicArn=response['TopicArn'],
#     Protocol='email',
#     Endpoint='stranoluca469955@gmail.com'
# )

# print("Attesa di conferma della sottoscrizione via email...")
# time.sleep(50)  # Attende 3 secondi
# print("Fine dopo 50 secondi")

# subject = "Questo è un test di notifica SNS"
# sns.publish(
#     TopicArn=response['TopicArn'],
#     Subject=subject,
#     Message="Test andato a buon fine!"
# )