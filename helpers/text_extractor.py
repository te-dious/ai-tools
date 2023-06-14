
import base64
import os
import requests
from googleapiclient.discovery import build
from dotenv import load_dotenv
load_dotenv()

GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
APPMAN_OCR_API_ENDPOINT = os.environ.get('APPMAN_OCR_API_ENDPOINT')
APPMAN_AUTHENTICATION_KEY = os.environ.get('APPMAN_AUTHENTICATION_KEY')

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


class AppmanOcrUtils:
    def convert_vendor_response(self, response):
        response = response.get("result", {})
        vehicle_brand = response.get("vehicle_brand", "").lower()
        vehicle_model = response.get("vehicle_model", "").lower()

        def process_mercedes_benz(vehicle_model):
            model = vehicle_model.replace(" ", "").replace("-", "")
            model_map = {
                "c220d": "c220 d",
                "gla200": "gla200",
                "520i": "520i",
                "clk320": "clk320",
                "s350d": "s350",
                "xl7": "xl-7",
            }
            return model_map.get(model, vehicle_model)

        def process_mazda(vehicle_model):
            return vehicle_model.replace("mazda", "").strip()

        def process_ford(vehicle_model):
            return vehicle_model.replace("ford", "").replace("-", "").strip()

        if vehicle_brand in ("mercedes benz", "benz"):
            response["vehicle_brand"] = "mercedes-benz"
            response["vehicle_model"] = process_mercedes_benz(vehicle_model)

        if vehicle_brand == "bmw":
            response["vehicle_model"] = process_mercedes_benz(vehicle_model)

        elif vehicle_brand == "honda" and vehicle_model == "crv":
            response["vehicle_model"] = "cr-v"

        elif vehicle_brand == "mg" and vehicle_model == "new mg3":
            response["vehicle_model"] = "mg3"

        elif vehicle_brand == "mazda":
            response["vehicle_model"] = process_mazda(vehicle_model)

        elif vehicle_brand == "ford":
            response["vehicle_model"] = process_ford(vehicle_model)

        vehicle_type = response.get("vehicle_type")
        passenger_models = [
            "stepwagon spada",
            "grand starex",
            "h-1",
            "staria",
            "carnival",
            "alphard",
            "alphard hybrid",
            "grand wagon",
            "vellfire",
            "ventury",
            "caravelle",
            "multivan",
            "majesty",
        ]
        pickup_models = [
            "hilux revo",
            "hilux-revo",
            "hilux vigo",
            "vigo",
            "d-max",
            "triton",
            "colorado",
            "ford ranger",
            "navara",
            "bt-50",
            "mg extender",
        ]

        if vehicle_model in passenger_models:
            model_appendix = " (110)" if vehicle_type == "รถยนต์นั่งส่วนบุคคลไม่เกิน 7 คน" else " (210)"
            response["vehicle_model"] += model_appendix

        if vehicle_model in pickup_models:
            model = vehicle_model.split("-")[0].split(" ")[-1]
            model_appendix = ""

            if vehicle_type == "รถยนต์บรรทุกส่วนบุคคล":
                model_appendix = " 2 doors"
            elif vehicle_type == "รถยนต์นั่งส่วนบุคคลไม่เกิน 7 คน":
                model_appendix = " 4 doors"

            response["vehicle_model"] = model + model_appendix

        return {"result": response}

    def _post_multipart(self, endpoint, files):
        url = f"{APPMAN_OCR_API_ENDPOINT}{endpoint}"
        headers = {
            "x-api-key": APPMAN_AUTHENTICATION_KEY,
        }

        r = requests.post(url, headers=headers, files=files)
        r.raise_for_status()

        return r.json()

    def scan_thai_identification(self, file):
        file.seek(0)
        attachments = [("image", file.read())]

        return self._post_multipart(
            endpoint="/v1/thailand-id-card/front", files=attachments
        )

    def scan_car_registration(self, file):
        file.seek(0)
        attachments = [("image", file.read())]

        return self._post_multipart(
            endpoint="/v1/thailand-car-book", files=attachments
        )
