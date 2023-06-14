import json
import os
import boto3
import threading
import logging
from app import app
from utils import extract_text_from_image_util

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SQS_REGION_NAME = os.environ.get('SQS_REGION_NAME')
SQS_ACCESS_KEY_ID = os.environ.get('SQS_ACCESS_KEY_ID')
SQS_SECRET_ACCESS_KEY = os.environ.get('SQS_SECRET_ACCESS_KEY')
SQS_QUEUE_URL = os.environ.get('SQS_QUEUE_URL')

logging.info(SQS_QUEUE_URL)

def process_sqs_messages():
    session = boto3.Session(
        aws_access_key_id=SQS_ACCESS_KEY_ID,
        aws_secret_access_key=SQS_SECRET_ACCESS_KEY,
        region_name=SQS_REGION_NAME,
    )
    sqs = session.client('sqs')

    queue_url = SQS_QUEUE_URL

    while True:
        response = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=4,
            WaitTimeSeconds=20  # Long-polling with a 20-second timeout
        )

        if 'Messages' in response:
            message = response['Messages'][0]
            logging.info("Message received")
            logging.info(message)
            receipt_handle = message['ReceiptHandle']

            try:
                try:
                    data = json.loads(message['Body'])
                    # Call your extract_meaningful_info function here with 'data'
                except Exception as e:
                    logging.error(f'Error processing message body: {e}')
                    pass

                with app.app_context():
                    extract_text_from_image_util(data)

                sqs.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=receipt_handle
                )
            except Exception as e:
                logging.error(f'Error deleting message from queue: {e}')
                pass

if __name__ == '__main__':
    threading.Thread(target=process_sqs_messages).start()