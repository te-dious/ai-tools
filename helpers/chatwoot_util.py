import requests
from datetime import datetime
from typing import Dict, List, Tuple
from requests.exceptions import RequestException
import pymysql
from models import ChatwootMessage
from app import db
import os
from dotenv import load_dotenv
load_dotenv()

CHATWOOT_API_URL = os.environ.get('CHATWOOT_API_URL')
CHATWOOT_API_TOKEN = os.environ.get('CHATWOOT_API_TOKEN')

class InvalidInputError(Exception):
    pass

class ChatwootClient:
    @staticmethod
    def convert_epoch_to_datetime_string(epoch_time: int) -> str:
        """Converts epoch time to a formatted string."""
        try:
            datetime_obj = datetime.fromtimestamp(epoch_time)
            formatted_string = datetime_obj.strftime("%Y-%m-%d %H:%M:%S")
            return formatted_string
        except TypeError:
            raise InvalidInputError("epoch_time must be an integer.")

    def _make_get_request(self, url: str, headers: Dict[str, str]) -> Dict:
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            raise RequestException(f"Failed to fetch data due to error: {e}")

    def get_chatwoot_conversation_details(self, conversation_id: int) -> Dict:
        """Fetches the conversation details from Chatwoot."""
        url = f"{CHATWOOT_API_URL}/api/v1/accounts/1/conversations/{conversation_id}"
        headers = {
            "api_access_token": CHATWOOT_API_TOKEN,
        }
        return self._make_get_request(url, headers)

    def get_chatwoot_conversation_text(self, conversation_id: int, include_all=False):
        """Fetches and formats the conversation text from Chatwoot."""
        if not isinstance(conversation_id, int):
            raise InvalidInputError("conversation_id must be an integer.")

        url = f"{CHATWOOT_API_URL}/api/v1/accounts/1/conversations/{conversation_id}/messages"
        headers = {
            "api_access_token": CHATWOOT_API_TOKEN,
        }
        messages, contact = self._fetch_messages(url, headers, conversation_id)
        return self._format_messages(messages, include_all), contact

    def _fetch_messages(self, url: str, headers: Dict[str, str], conversation_id: int):
        # Use your own database credentials here
        messages = ChatwootMessage.query.filter_by(conversation_id=conversation_id).order_by(ChatwootMessage.message_id).all()

        last_message_id = 0
        last_saved_message_id = 0
        if messages:
            last_saved_message_id = messages[-1].message_id
        main_url = url
        while True:
            data = self._make_get_request(url, headers)
            payload = data["payload"]
            contact = data["meta"]["contact"]
            payload.reverse()
            if not payload:
                break

            if last_message_id == payload[-1]["id"]:
                break
            last_message_id = payload[-1]["id"]
            url = f"{main_url}?before={last_message_id}"
            # Process messages and add to the database
            for message in payload:
                if message["private"]:
                    continue
                if message['id'] == last_saved_message_id:
                    break
                attachment_id = None
                attachment_url = None
                if message.get("attachments") and message['message_type'] == 0:
                    attachment = message["attachments"][0]
                    attachment_id = attachment["id"]
                    attachment_url = attachment["data_url"]

                new_message = ChatwootMessage(
                    message_id=message['id'],
                    conversation_id=conversation_id,
                    message_created_at=message['created_at'],
                    message_type=message['message_type'],
                    message_content=message['content'] if message.get("content") else "attachment",
                    message_staff_id=message.get("sender", {}).get("id"),
                    attachment_id=attachment_id,
                    attachment_url=attachment_url,
                )

                db.session.add(new_message)

                db.session.commit()
                db.session.flush()


            if message['id'] == last_saved_message_id:
                break

        messages = ChatwootMessage.query.filter_by(conversation_id=conversation_id).order_by(ChatwootMessage.message_id).all()
        return messages, contact


    def get_formatted_message_from_message_list(self, messages):
        return self._format_messages(messages)

    def _format_messages(self, messages: List, include_all=False) -> Tuple[str, List[Tuple[str, str]]]:
        msg_str = ""
        docs = []
        for message in sorted(messages, key=lambda i: i.message_id):
            message_type = message.message_type
            if message_type not in (0, 1) and not include_all:
                continue

            formatted_string = self.convert_epoch_to_datetime_string(message.message_created_at)
            msg_st, doc = self._format_message_string(message, formatted_string, message_type)
            msg_str += msg_st
            if doc:
                docs.append(doc)

        return msg_str, docs

    @staticmethod
    def _format_message_string(message, formatted_string: str, message_type: int):
        msg_str = f"{formatted_string}: "

        if message_type == 1:
            msg_str += "Staff: "
            if message.message_staff_id:
                msg_str += f"User Id: {message.message_staff_id}"

        elif message_type == 0:
            msg_str += "Agent: "
        elif message_type == 2:
            msg_str += "System Generated: "

        if message.message_content:
            msg_str += message.message_content
        doc = None
        if message.attachment_id:
            doc = (message.attachment_url, message.attachment_id)
            msg_str += "An image is attached"

        msg_str += "\n"
        return msg_str, doc
