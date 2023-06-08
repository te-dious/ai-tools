# models.py
from extensions import db
from sqlalchemy.dialects.postgresql import JSON

class ChatwootMessage(db.Model):
    __tablename__ = 'chatwoot_message'
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, nullable=False)
    conversation_id = db.Column(db.Integer, nullable=False)
    message_created_at = db.Column(db.Integer, nullable=False)
    message_type = db.Column(db.Integer, nullable=False)
    message_content = db.Column(db.Text, nullable=True)
    attachment_url = db.Column(db.Text, nullable=True)
    attachment_id = db.Column(db.Integer, nullable=True)

class ExtractedData(db.Model):
    __tablename__ = 'extracteddata'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text)
    text_hash = db.Column(db.Text)
    information = db.Column(JSON)
    identifier = db.Column(db.Text, nullable=True)
    # entity_type = db.Column(db.Text, nullable=True)
