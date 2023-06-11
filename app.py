import hashlib
import json
from constants import CW_CONVERSATION_PROMPT, CW_CONVERSATION_TO_SD_PROMPT
from flask import Flask, request, jsonify
from utils import extract_text_from_image_util, generate_random_string, get_db, get_retriever, get_qa_util, get_qa_chain, extract_text_from_image, InvalidInputError, send_sqs_messages
from helpers.chroma_db_util import ChromaDBUtil
from extensions import db
from sqlalchemy import desc
from dotenv import load_dotenv

load_dotenv()

import os

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')

    db.init_app(app)

    with app.app_context():
        from models import ChatwootMessage, ExtractedData
        db.create_all()  # Create tables for the models

    return app

app = create_app()
with app.app_context():
    from models import ChatwootMessage, ExtractedData
    db.create_all()  # Create tables for the models


@app.route('/create_db', methods=['POST'])
def create_db():
    try:
        # docs is list of files in text format
        data = request.json
        db_util = ChromaDBUtil()
        db_util.create_db(data['docs'], data['collection_name'])
        return jsonify({'message': 'Database created successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/ask_qa_chain', methods=['POST'])
def ask_qa_chain():
    try:
        data = request.json
        collection_name = data.pop('collection_name', "default")
        if collection_name:
            chroma_db = get_db(collection_name)
            data["retriever"] = get_retriever(chroma_db)
        message = data.pop("message")

        qa_util = get_qa_util(data)
        qa_chain = get_qa_chain(qa_util)
        op = qa_chain(message)

        return jsonify({'message': op})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/extract_image_text', methods=['POST'])
def extract_image_text():
    try:
        data = request.json
        text, _ = extract_text_from_image(data.get('url'), data.get('vendor', "google_vision"))
        return jsonify({'message': text})
    except InvalidInputError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/extract_meaningful_info', methods=['POST'])
def extract_meaningful_info():
    try:
        data = request.json
        if "identifier" not in data:
            return jsonify({'error': "identifier required in request data"}), 400
        result = extract_text_from_image_util(data)
        return jsonify({'message': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/get_image_structured_data/<identifier>', methods=['GET'])
def get_image_structured_data(identifier):
    from models import ExtractedData
    extracted_data = ExtractedData.query.filter_by(identifier=identifier).order_by(ExtractedData.id.desc()).first()
    if extracted_data:
        return jsonify({'message': extracted_data.information})
    return jsonify({'error': "identifier not found"}), 400


@app.route('/update_image_structured_data/<identifier>', methods=['PATCH'])
def update_image_structured_data(identifier):
    data = request.json
    if 'result' not in data:
        return jsonify({'error': "Invalid request, missing 'result' in data"}), 400

    extracted_data = ExtractedData.query.filter_by(identifier=identifier).order_by(ExtractedData.id.desc()).first()
    if extracted_data:
        extracted_data.information = data["result"]
        try:
            db.session.commit()
            return jsonify({'message': extracted_data.information})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': "Database error: " + str(e)}), 500

    return jsonify({'error': "identifier not found"}), 404


@app.route('/get_chatwoot_conversation_structured_data/<conversation_id>', methods=['GET'])
def get_chatwoot_conversation_structured_data(conversation_id):
    from helpers.chatwoot_util import ChatwootClient
    from models import ExtractedData, ChatwootMessage

    chatwoot_client = ChatwootClient()
    data = ExtractedData.query.filter_by(identifier=f"cw-conversation-id-{conversation_id}").order_by(desc(ExtractedData.id)).first()

    result = {}
    if data:
        result["conversation_summary"] = data.information
    else:
        result["conversation_summary"] = {
            "status": "in_progress"
        }

    messages = (
        ChatwootMessage.query
        .filter_by(conversation_id=conversation_id)
        .filter(ChatwootMessage.attachment_id.isnot(None))
        .order_by(ChatwootMessage.message_id)
        .all()
    )



    conversation_text, docs = chatwoot_client.get_formatted_message_from_message_list(messages)
    lis = []
    for doc in docs:
        attachment_id = doc[1]
        attachment_url = doc[0]
        result["documents"] = lis
        extracted_data = ExtractedData.query.filter_by(identifier=f"cw-attachment-{attachment_id}").order_by(desc(ExtractedData.id)).first()
        if extracted_data:
            lis.append({
                "url": attachment_url,
                "result": extracted_data.information,
                "ai_tools_identifier": f"cw-attachment-{attachment_id}",
            })
        else:
            lis.append({
                "url": attachment_url,
                "status": "in_progress",
            })

    result["documents"] = lis

    return jsonify({'message': result})


@app.route('/extract_chatwoot_conversation_info', methods=['POST'])
def extract_chatwoot_conversation_info():
    try:
        from helpers.chatwoot_util import ChatwootClient
        from models import ExtractedData

        data = request.json

        conversation_id = data.get('conversation_id', '')
        identifier = data.get("identifier", f"cw-conversation-id-{conversation_id}")
        prompt_template = data.get("prompt_template", CW_CONVERSATION_PROMPT)
        chatwoot_client = ChatwootClient()
        (conversation_text, docs), contact = chatwoot_client.get_chatwoot_conversation_text(conversation_id)
        text = conversation_text + prompt_template
        text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()

        # add docs to sqs queue
        for doc in docs:
            document_id = doc[1]
            document_url = doc[0]
            extracted_data = ExtractedData.query.filter_by(identifier=f"cw-attachment-{document_id}").all()
            app.logger.info(extracted_data)
            if not extracted_data:
                send_sqs_messages({
                    "url": document_url,
                    "identifier": f"cw-attachment-{document_id}",
                    "conversation_id": conversation_id
                })

        extracted_data = ExtractedData.query.filter_by(text_hash=text_hash).order_by(desc(ExtractedData.id)).first()

        if extracted_data:
            return jsonify({'message': extracted_data.information})


        collection_name = data.pop('collection_name', "default")
        chroma_db = get_db(collection_name)
        data = {
            "model_name": "gpt-4",
            "prompt_template": prompt_template,
            "retriever":  get_retriever(chroma_db),
        }
        qa_util = get_qa_util(data)
        qa_chain = get_qa_chain(qa_util)
        op = qa_chain(conversation_text)

        result = json.loads(op["result"])
        result["contact"] = contact

        new_message = ExtractedData(
            text=conversation_text, # Should we store the whole text?
            text_hash=text_hash,
            information=result,
            identifier=identifier
        )

        db.session.add(new_message)
        db.session.commit()
        db.session.flush()


        return jsonify({'message': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/analyse_chatwoot_conversation', methods=['POST'])
def analyse_chatwoot_conversation():
    try:
        from helpers.chatwoot_util import ChatwootClient
        from models import ExtractedData

        data = request.json

        conversation_id = data.get('conversation_id', '')
        random_string = generate_random_string(10)
        identifier = data.get("identifier", random_string)
        prompt_template = data.get("prompt_template", CW_CONVERSATION_PROMPT)
        chatwoot_client = ChatwootClient()
        (conversation_text, docs), contact = chatwoot_client.get_chatwoot_conversation_text(conversation_id, True)
        text = conversation_text + prompt_template
        text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()

        extracted_data = ExtractedData.query.filter_by(text_hash=text_hash).order_by(desc(ExtractedData.id)).first()

        if extracted_data:
            return jsonify({'message': extracted_data.information})

        collection_name = data.pop('collection_name', "default")
        chroma_db = get_db(collection_name)
        data = {
            "model_name": "gpt-4",
            "prompt_template": prompt_template,
            "retriever":  get_retriever(chroma_db),
        }
        qa_util = get_qa_util(data)
        qa_chain = get_qa_chain(qa_util)
        op = qa_chain(conversation_text)

        result = json.loads(op["result"])
        result["identifier"] = identifier
        result["contact"] = contact

        new_message = ExtractedData(
            text=conversation_text, # Should we store the whole text?
            text_hash=text_hash,
            information=result,
            identifier=identifier
        )

        db.session.add(new_message)
        db.session.commit()
        db.session.flush()


        return jsonify({'message': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/chatwoot_docs_webhook', methods=['POST'])
def chatwoot_docs_webhook():
    data = request.json
    app.logger.info(data)
    if data["message_type"] != "incoming":
        return
    for attachment in data.get("attachments", []):
        send_sqs_messages({
            "url": attachment["data_url"],
            "identifier": f"cw-attachment-{attachment['id']}",
            "conversation_id": data["conversation"]["id"]
        })
    return jsonify({'message': "success"})

@app.route('/get_chatwoot_conversation_structured_data_with_documents/<conversation_id>', methods=['GET'])
def get_chatwoot_conversation_structured_data_with_documents(conversation_id):
    from helpers.chatwoot_util import ChatwootClient
    from models import ExtractedData, ChatwootMessage

    chatwoot_client = ChatwootClient()
    data = ExtractedData.query.filter_by(identifier=f"cw-conversation-id-{conversation_id}").order_by(desc(ExtractedData.id)).first()
    prompt_template = CW_CONVERSATION_TO_SD_PROMPT

    result = {}
    if data:
        result["conversation_summary"] = data.information
    result["conversation_summary"].pop("user", None)
    messages = (
        ChatwootMessage.query
        .filter_by(conversation_id=conversation_id)
        .filter(ChatwootMessage.attachment_id.isnot(None))
        .order_by(ChatwootMessage.message_id)
        .all()
    )

    conversation_text, docs = chatwoot_client.get_formatted_message_from_message_list(messages)
    lis = []
    for doc in docs:
        attachment_id = doc[1]
        attachment_url = doc[0]
        result["documents"] = lis
        extracted_data = ExtractedData.query.filter_by(identifier=f"cw-attachment-{attachment_id}").order_by(desc(ExtractedData.id)).first()
        if extracted_data:
            lis.append({
                "url": attachment_url,
                "result": extracted_data.information,
            })

    result["documents"] = lis
    result = json.dumps(result)

    collection_name = "default"
    chroma_db = get_db(collection_name)
    data = {
        "model_name": "gpt-4",
        "prompt_template": prompt_template,
        "retriever":  get_retriever(chroma_db),
    }
    qa_util = get_qa_util(data)
    qa_chain = get_qa_chain(qa_util)
    op = qa_chain(result)
    result = json.loads(op["result"])

    return jsonify({'message': result})


@app.route('/extract_text_from_image_util_view', methods=['POST'])
def extract_text_from_image_util_view():
    data = request.json
    return extract_text_from_image_util(data)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)