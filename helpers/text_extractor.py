
import base64
import os
import requests
from googleapiclient.discovery import build
from dotenv import load_dotenv
load_dotenv()

GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

class GoogleAPI:
    api_key = GOOGLE_API_KEY

    def __init__(self):
        pass

class GoogleVision(GoogleAPI):
    def __init__(self):
        super().__init__()
        self.client = build("vision", "v1", developerKey=self.api_key)

    def extract_text_from_url(self, url):
        r = requests.get(url)
        content = base64.b64encode(r.content)
        from consumer import logging

        image = {"content": content.decode("utf-8")}

        request = {
            "image": image,
            "features": [{"type": "DOCUMENT_TEXT_DETECTION"}, {"type": "OBJECT_LOCALIZATION"}],
            "imageContext": {"languageHints": ["th", "en"]},
        }
        response = self.client.images().annotate(body={"requests": [request]}).execute()

        responses = (
            response["responses"][0]
            if "responses" in response and len(response["responses"]) > 0
            else {}
        )

        texts = responses["textAnnotations"] if "textAnnotations" in responses else []
        objects = (
            responses["localizedObjectAnnotations"]
            if "localizedObjectAnnotations" in responses
            else []
        )

        # Extract names for objects
        object_names = [obj["name"] for obj in objects]

        # Prepare the final description string
        description = (
            f"The image contains the following text: '{texts[0]['description']}'."
            if texts
            else "The image does not contain any recognizable text."
        )
        if object_names:
            description += f" The image includes objects such as: {', '.join(object_names)}."
        else:
            description += " The image does not contain any recognizable objects."

        return description, object_names

    def extract_text_vision(self, image_buffer):
        try:
            # Encode the image buffer as base64
            content = base64.b64encode(image_buffer)

            # Build the request object
            image = {"content": content.decode("utf-8")}
            request = {
                "image": image,
                "features": [{"type": "DOCUMENT_TEXT_DETECTION"}],
                "imageContext": {"languageHints": ["th"]},
            }

            # Make the request to Google Vision API
            response = self.client.images().annotate(body={"requests": [request]}).execute()

            # Extract the text annotations from the response
            texts = (
                response["responses"][0]["textAnnotations"]
                if "responses" in response
                and len(response["responses"]) > 0
                and "textAnnotations" in response["responses"][0]
                else []
            )

            # Return the extracted text
            return {"status": "SUCCESS", "text": texts[0]["description"] if texts else ""}

        except Exception as e:
            return {
                "status": "FAILED",
                "error_description": e.args[0],
            }
