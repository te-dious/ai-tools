# utils.py
import boto3
import hashlib
import json
import os
from helpers.chroma_db_util import ChromaDBUtil
from helpers.retrieval_qa_util import RetrievalQAUtil
from helpers.text_extractor import GoogleVision
from constants import DOCUMENT_TYPE_INFO_PROMPT
from extensions import db
from sqlalchemy import desc
from dotenv import load_dotenv
load_dotenv()

SQS_REGION_NAME = os.environ.get('SQS_REGION_NAME')
SQS_ACCESS_KEY_ID = os.environ.get('SQS_ACCESS_KEY_ID')
SQS_SECRET_ACCESS_KEY = os.environ.get('SQS_SECRET_ACCESS_KEY')
SQS_QUEUE_URL = os.environ.get('SQS_QUEUE_URL')

class InvalidInputError(Exception):
    pass


def get_db(collection_name):
    db_utils = ChromaDBUtil()
    return db_utils.get_db(collection_name)


def get_retriever(db):
    return db.as_retriever(search_type="similarity", search_kwargs={"k":1})


def get_qa_util(data):
    return RetrievalQAUtil(**data)


def get_qa_chain(qa_util):
    return qa_util.create_qa_chain()


def extract_text_from_image(url, vendor):
    if not url:
        raise InvalidInputError('Please provide image url')

    if vendor == "google_vision":
        vision = GoogleVision()
        return vision.extract_text_from_url(url)
    else:
        raise InvalidInputError("Incorrect vendor")

def extract_text_from_image_util(data):
    from models import ExtractedData

    collection_name = data.pop('collection_name', "default")
    identifier = data.get('identifier', "")
    url = data.get('url')
    vendor = data.get('vendor', "google_vision")
    model_name = data.get("model_name", 'gpt-4')
    prompt_template = data.get("prompt_template", DOCUMENT_TYPE_INFO_PROMPT)
    message, _ = extract_text_from_image(url, vendor)
    text = message + prompt_template
    text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()

    extracted_data = ExtractedData.query.filter_by(text_hash=text_hash, identifier=identifier).order_by(desc(ExtractedData.id)).first()
    if extracted_data:
        return extracted_data.information


    data = {
        "model_name": model_name,
        "prompt_template": prompt_template,
    }

    chroma_db = get_db(collection_name)
    data["retriever"] = get_retriever(chroma_db)

    qa_util = get_qa_util(data)
    qa_chain = get_qa_chain(qa_util)
    op = qa_chain(message)

    result = json.loads(op["result"])

    new_message = ExtractedData(
        text=text, # should we store the text?
        text_hash=text_hash,
        information=result,
        identifier=identifier,
    )

    db.session.add(new_message)
    db.session.commit()
    db.session.flush()

    return result


def send_sqs_messages(message):
    from app import app
    # Create a SQS client
    sqs = boto3.client(
        'sqs',
        region_name=SQS_REGION_NAME,
        aws_access_key_id=SQS_ACCESS_KEY_ID,
        aws_secret_access_key=SQS_SECRET_ACCESS_KEY,
    )

    queue_url = SQS_QUEUE_URL

    # The message you want to send (must be a String)
    # If you want to send a JSON, convert it to a string using json.dumps()
    conversation_id = message["conversation_id"]
    identifier = message["identifier"]
    message = json.dumps(message)

    response = sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=message,
        MessageGroupId=f"cww-{identifier}",
        MessageDeduplicationId=f"cww-{identifier}"
    )
    app.logger.info("SQS message pushed")
    app.logger.info(response)

